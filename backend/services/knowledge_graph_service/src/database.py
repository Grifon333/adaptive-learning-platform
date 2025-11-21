from loguru import logger
from neo4j import AsyncDriver, AsyncGraphDatabase

from .config import settings

driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    """Gets the global instance of the driver."""
    global driver
    if driver is None:
        logger.error("Neo4j driver not initialized.")
        raise RuntimeError("Neo4j driver not initialized.")
    return driver


async def init_driver():
    """Initializes the Neo4j asynchronous driver."""
    global driver
    try:
        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        await driver.verify_connectivity()
        logger.info("Neo4j driver initialized and connectivity verified.")
    except Exception as e:
        logger.critical(f"Failed to initialize Neo4j driver: {e}")
        raise


async def close_driver():
    """Closes the Neo4j driver connection."""
    global driver
    if driver:
        await driver.close()
        logger.info("Neo4j driver closed.")


async def get_db_session():
    """FastAPI dependency for getting a Neo4j session."""
    global driver
    if driver is None:
        logger.error("Attempted to get session, but driver is not initialized.")
        raise RuntimeError("Neo4j driver not initialized.")

    async with driver.session() as session:
        yield session
