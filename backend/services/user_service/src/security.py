import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from . import schemas
from .config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_token(
    data: dict,
    token_type: Literal["access", "refresh"],
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)

    if expires_delta:
        expire = now + expires_delta
    else:
        if token_type == "access":
            minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        else:
            minutes = REFRESH_TOKEN_EXPIRE_MINUTES
        expire = now + timedelta(minutes=minutes)

    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return create_token(data=data, token_type="access", expires_delta=expires_delta)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return create_token(data=data, token_type="refresh", expires_delta=expires_delta)


def decode_access_token(token: str) -> schemas.TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        token_type: str | None = payload.get("token_type")
        if user_id_str is None or token_type is None:
            raise credentials_exception
        return schemas.TokenData(user_id=uuid.UUID(user_id_str), token_type=token_type)
    except (JWTError, ValueError):
        raise credentials_exception from None
