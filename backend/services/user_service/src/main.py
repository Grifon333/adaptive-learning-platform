from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, HTTPException, status
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from src import models, schemas, security
from src.database import get_db
from src.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("User service initializing...")
    yield
    # Shutdown
    logger.info("User service shutting down...")


setup_logging()
app = FastAPI(title="User Service", lifespan=lifespan)


def get_current_user(
    token: str = Depends(security.oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Decodes the token, finds the user in the database, and returns it.
    This protects endpoints.
    """
    payload = security.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registering user: {user.email}")
    # Checking if a user with this email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        logger.warning(f"User with email {user.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    # Hashing the password and creating a new user
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        role=models.UserRole.student,
    )

    if new_user.role == models.UserRole.student:
        new_profile = models.StudentProfile(user=new_user)
        db.add(new_profile)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # TODO: Add email verification logic
    logger.success(f"User {new_user.email} registered successfully (ID: {new_user.id})")
    return {"message": "User registered successfully. Please verify your email."}


@app.post("/api/v1/auth/login", response_model=schemas.Token)
def login_for_access_token(
    user_credentials: schemas.UserLogin | None = None,
    email: str | None = Form(None),
    password: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """
    Logs in a user and returns an access token.
    """
    cred_email = user_credentials.email if user_credentials else email
    cred_password = user_credentials.password if user_credentials else password
    logger.info(f"Logging in user: {cred_email}")

    if not cred_email or not cred_password:
        logger.error("Email and password are required")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email and password are required",
        )

    db_user = db.query(models.User).filter(models.User.email == cred_email).first()

    if not db_user:
        logger.error(f"Failed to log in: {cred_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    assert isinstance(db_user.password_hash, str)
    if not security.verify_password(cred_password, db_user.password_hash):
        logger.error(f"Failed to log in: {cred_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Creating a JWT token
    access_token = security.create_access_token(
        data={"sub": db_user.email, "role": db_user.role}
    )

    # Updating the last login time
    db_user.last_login = func.now()
    db.commit()

    logger.success(f"User successfully logged in: {db_user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/users/me/profile", response_model=schemas.StudentProfile)
def get_user_profile(current_user: models.User = Depends(get_current_user)):
    """
    Receives the profile of the currently logged-in student
    """
    if current_user.role != models.UserRole.student or current_user.profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )
    return current_user.profile


@app.put("/api/v1/users/me/profile", response_model=schemas.StudentProfile)
def update_user_profile(
    profile_data: schemas.StudentProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the profile of the currently logged-in student
    """
    profile = current_user.profile
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    update_data = profile_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
