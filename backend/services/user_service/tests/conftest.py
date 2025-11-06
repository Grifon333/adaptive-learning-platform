import os
import sys

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database import Base, get_db
from src.main import app

TEST_DATABASE_URL = os.getenv("DATABASE_URL")


@pytest.fixture(scope="session")
def engine():
    """Створює 'engine' для тестової БД на всю сесію тестів."""
    return create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="session")
def setup_database(engine):
    """
    (Runs once per session)
    Creates a test database, runs Alembic migrations, and deletes everything after the tests.
    """
    conn = engine.connect()
    conn = conn.execution_options(isolation_level="AUTOCOMMIT")
    try:
        conn.exec_driver_sql(f'CREATE DATABASE "{engine.url.database}"')
    except Exception:
        pass
    finally:
        conn.close()

    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    # In case the migration is empty or does not create tables, let's create them from models
    Base.metadata.create_all(bind=engine)

    yield  # Run tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(setup_database, engine):
    """
    (Runs for EVERY test)
    Creates a clean database session for a single test and rolls back all changes after it.
    This ensures that tests are independent of each other.
    """
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    # Clean up data between tests to avoid uniqueness conflicts.
    try:
        db.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """
    Creates a FastAPI test client that uses our
    test 'db_session' instead of the real 'get_db'.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # substitute dependence
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
