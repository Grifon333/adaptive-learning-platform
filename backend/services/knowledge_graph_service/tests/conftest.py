import asyncio
import os
import sys
from collections.abc import AsyncGenerator

import httpx
import pytest_asyncio
from httpx import ASGITransport
from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

# Add project root to sys.path to allow imports from 'src'
project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import settings
from src.database import close_driver, get_db_session, init_driver
from src.main import app


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """
    Creates a single event loop for the entire test session.
    This is necessary for pytest-asyncio.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_driver() -> AsyncGenerator[AsyncDriver, None]:
    """
    (Executed once per session)
    Initializes and provides the Neo4j asynchronous driver.
    Reads settings from .env.test (thanks to pytest.ini).
    """
    # Ensure we are using test settings
    settings.NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    settings.NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    settings.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

    await init_driver()

    # Create a separate driver for `conftest` for cleanup
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )

    try:
        await driver.verify_connectivity()
        yield driver
    finally:
        await driver.close()
        await close_driver()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_driver: AsyncDriver) -> AsyncGenerator[AsyncSession, None]:
    """
    (Performed for EVERY test)
    Provides a Neo4j test session and, most importantly, CLEANS the entire Neo4j database AFTER the test is complete.
    This ensures test isolation.
    """
    async with db_driver.session() as session:
        try:
            yield session
        finally:
            # Complete cleanup of Neo4j.
            await session.run("MATCH (n) DETACH DELETE n")


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    (Performed for EVERY test)
    Creates an asynchronous HTTP client (httpx) for testing the API.
    Most importantly, it “replaces” the `get_db_session` dependency in FastAPI
    so that endpoints use our clean test session `db_session`.
    """

    # Substitute the dependency to use the test session
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    # Launch the client
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear the override after the test
    app.dependency_overrides.clear()
