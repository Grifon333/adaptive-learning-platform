import uuid
from datetime import UTC, datetime, timedelta

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
    token_type: str,  # access, refresh, verification, reset
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)

    if expires_delta:
        expire = now + expires_delta
    else:
        # Default expirations
        if token_type == "access":
            minutes = ACCESS_TOKEN_EXPIRE_MINUTES  # 1440 (24h)
        elif token_type == "verification":
            minutes = 1440 * 7  # 7 days
        elif token_type == "reset":
            minutes = 60  # 1 hour
        else:
            minutes = REFRESH_TOKEN_EXPIRE_MINUTES
        expire = now + timedelta(minutes=minutes)

    to_encode.update({"exp": expire, "iat": now, "type": token_type})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token(data: dict) -> str:
    return create_token(data, "access")


def create_refresh_token(data: dict) -> str:
    return create_token(data, "refresh")


def create_verification_token(email: str) -> str:
    return create_token({"sub": email}, "verification")


def create_password_reset_token(email: str) -> str:
    return create_token({"sub": email}, "reset")


def decode_token(token: str, expected_type: str) -> str | None:
    """Decodes token and returns the subject (e.g., user_id or email) if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            return None
        return str(payload.get("sub"))
    except JWTError:
        return None


def decode_access_token(token: str) -> schemas.TokenData | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if user_id_str is None or token_type != "access":
            return None
        return schemas.TokenData(user_id=uuid.UUID(user_id_str), token_type=token_type)

    except (JWTError, ValueError):
        return None
