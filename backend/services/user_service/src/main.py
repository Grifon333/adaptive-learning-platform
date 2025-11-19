from contextlib import asynccontextmanager
from typing import cast

from fastapi import Depends, FastAPI, HTTPException, status
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
) -> models.User:
    """
    Decodes the token, finds the user in the database, and returns it.
    This protects endpoints.
    """
    token_data = security.decode_access_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected 'access'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return cast(models.User, user)


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
    user_credentials: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    """
    Logs in a user and returns an access token.
    """
    cred_email = user_credentials.email
    cred_password = user_credentials.password
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
    subject_data = {"sub": str(db_user.id)}
    access_token = security.create_access_token(data=subject_data)
    refresh_token = security.create_refresh_token(data=subject_data)

    # Updating the last login time
    db_user.last_login = func.now()
    db.commit()

    logger.success(f"User successfully logged in: {db_user.email}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


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


@app.post(
    "/api/v1/learning-paths",
    response_model=schemas.LearningPath,
    status_code=status.HTTP_201_CREATED,
)
def create_learning_path(
    path_data: schemas.LearningPathCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new learning path for the currently authenticated student.
    """
    logger.info(f"Creating learning path for user {current_user.email}")

    # 1. Creating the main LearningPath record
    db_path = models.LearningPath(
        student_id=current_user.id,
        goal_concepts=path_data.goal_concepts,
        estimated_time=path_data.estimated_time,
    )
    db.add(db_path)

    # 2. Creating steps (LearningStep)
    db_steps = []
    for step_data in path_data.steps:
        db_step = models.LearningStep(
            path=db_path,
            step_number=step_data.step_number,
            concept_id=step_data.concept_id,
            resource_ids=step_data.resource_ids,
            estimated_time=step_data.estimated_time,
            difficulty=step_data.difficulty,
        )
        db_steps.append(db_step)
    db.add_all(db_steps)

    try:
        db.commit()
        db.refresh(db_path)
        logger.success(f"Learning path {db_path.id} created successfully.")
        return db_path
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create learning path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create learning path",
        ) from e


@app.post("api/v1/auth/refresh", response_model=schemas.Token)
def refresh_access_token(
    refresh_request: schemas.TokenRefresh, db: Session = Depends(get_db)
):
    """
    Update the Access Token, using the Refresh Token
    """
    token_data = security.decode_access_token(refresh_request.refresh_token)
    if token_data.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected 'refresh'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user existing
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token signature or user not found",
        )

    # Generate a new pair of tokens
    subject_data = {"sub": str(user.id)}
    new_access_token = security.create_access_token(data=subject_data)
    new_refresh_token = security.create_refresh_token(data=subject_data)

    logger.info(f"Token refreshed for user: {user.email}")
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
