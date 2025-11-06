from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models
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


def login_user(client: TestClient) -> str:
    """
    Logs in a user and returns the access token.
    """
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


def test_get_user_profile_success(client: TestClient, db_session: Session):
    """
    Test 5: Verify that StudentProfile is created automatically when a student registers.
    """
    response = client.post("/api/v1/auth/register", json=test_user_data)
    assert response.status_code == 201

    user = (
        db_session.query(models.User).filter_by(email=test_user_data["email"]).first()
    )
    assert user is not None
    assert user.role == "student"

    assert user.profile is not None
    assert user.profile.user_id == user.id
    assert user.profile.cognitive_profile["memory"] == 0.5


def test_get_profile_authenticated(client: TestClient, db_session: Session):
    """
    Test 6: Successful retrieval of profile by authenticated user.
    """
    client.post("/api/v1/auth/register", json=test_user_data)
    access_token = login_user(client)

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/users/me/profile", headers=headers)

    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["user_id"] is not None
    assert profile_data["learning_preferences"]["visual"] == 0.25


def test_get_profile_unauthenticated(client: TestClient):
    """
    Test 7: Error 401 when trying to get profile without a token.
    """
    response = client.get("/api/v1/users/me/profile")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_profile_success(client: TestClient, db_session: Session):
    """
    Тест 8: Успішне оновлення профілю.
    """
    client.post("/api/v1/auth/register", json=test_user_data)
    access_token = login_user(client)

    headers = {"Authorization": f"Bearer {access_token}"}
    update_data = {
        "timezone": "Europe/Kyiv",
        "learning_preferences": {
            "visual": 0.8,
            "auditory": 0.1,
            "kinesthetic": 0.1,
            "reading": 0.0,
        },
    }

    response = client.put("/api/v1/users/me/profile", headers=headers, json=update_data)
    assert response.status_code == 200

    profile_data = response.json()
    assert profile_data["timezone"] == "Europe/Kyiv"
    assert profile_data["learning_preferences"]["visual"] == 0.8

    user = (
        db_session.query(models.User).filter_by(email=test_user_data["email"]).first()
    )
    assert user.profile.timezone == "Europe/Kyiv"
