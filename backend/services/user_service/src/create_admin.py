import os
import sys

# Add project root to python path to allow imports
sys.path.append(os.getcwd())

from src import models, security
from src.database import SessionLocal


def create_super_admin(email, password):
    db = SessionLocal()
    if db.query(models.User).filter(models.User.email == email).first():
        print("User already exists")
        return

    admin = models.User(
        email=email,
        password_hash=security.get_password_hash(password),
        first_name="Super",
        last_name="Admin",
        role=models.UserRole.admin,
        is_verified=True,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print(f"Admin {email} created successfully.")
    db.close()


if __name__ == "__main__":
    create_super_admin("admin@alp.com", "secure_password_123")
