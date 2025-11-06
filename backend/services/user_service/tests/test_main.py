from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import User
from src.security import get_password_hash

test_user_data = {
    "email": "test@example.com",
    "password": "StrongPassword123!",
    "first_name": "Test",
    "last_name": "User",
}


def test_register_user_success(client: TestClient):
    """
    Test 1: Successful registration of a new user.
    Expect HTTP 201 Created.
    """
    response = client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code == 201
    assert (
        response.json()["message"]
        == "User registered successfully. Please verify your email."
    )


def test_register_user_duplicate_email(client: TestClient):
    """
    Test 2: Error when registering with an existing email address.
    Expect HTTP 409 Conflict.
    """
    client.post("/api/v1/auth/register", json=test_user_data)
    response = client.post("/api/v1/auth/register", json=test_user_data)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_login_user_success(client: TestClient, db_session: Session):
    """
    Test 3: Successful login with correct data.
    Expect HTTP 200 OK and JWT token.
    """
    hashed_password = get_password_hash(test_user_data["password"])
    db_user = User(
        email=test_user_data["email"],
        password_hash=hashed_password,
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
    )
    db_session.add(db_user)
    db_session.commit()

    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 200
    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"


def test_login_user_wrong_password(client: TestClient, db_session: Session):
    """
    Test 4: Login error with incorrect password.
    Expect HTTP 401 Unauthorized.
    """
    hashed_password = get_password_hash(test_user_data["password"])
    db_user = User(
        email=test_user_data["email"],
        password_hash=hashed_password,
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
    )
    db_session.add(db_user)
    db_session.commit()

    login_data = {"email": test_user_data["email"], "password": "WrongPassword!"}
    response = client.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
