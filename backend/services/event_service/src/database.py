from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from .config import settings

class Database:
    client: AsyncIOMotorClient | None = None

    def get_db(self):
        if self.client is None:
            raise RuntimeError("Database client not initialized")
        return self.client[settings.MONGODB_DB_NAME]

db = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Connection check (ping)
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
    except Exception as e:
        logger.critical(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed.")
