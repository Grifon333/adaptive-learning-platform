from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src import models, schemas, security
from src.database import get_db

# Створення таблиці в БД
# models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="User Service")


@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Перевірка, чи існує користувач з таким email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    # Хешування пароля та створення нового користувача
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # TODO: Можна додати логіку підтверження email

    return {"message": "User registered successfully. Please verify your email."}


@app.post("/api/v1/auth/login", response_model=schemas.Token)
def login_for_access_token(
    user_credentials: schemas.UserLogin, db: Session = Depends(get_db)
):
    db_user = (
        db.query(models.User)
        .filter(models.User.email == user_credentials.email)
        .first()
    )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    assert isinstance(db_user.password_hash, str)
    if not security.verify_password(user_credentials.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Створення JWT токена
    access_token = security.create_access_token(
        data={"sub": db_user.email, "role": db_user.role}
    )

    # Оновлення часу останнього входу
    db_user.last_login = func.now()
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}
