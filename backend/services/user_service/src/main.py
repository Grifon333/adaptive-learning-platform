from fastapi import Depends, FastAPI, Form, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src import models, schemas, security
from src.database import get_db

# Creating a table in the database
# models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="User Service")


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
    # Checking if a user with this email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
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

    if not cred_email or not cred_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email and password are required",
        )

    db_user = db.query(models.User).filter(models.User.email == cred_email).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    assert isinstance(db_user.password_hash, str)
    if not security.verify_password(cred_password, db_user.password_hash):
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
