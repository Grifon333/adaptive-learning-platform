from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings

# --- PostgreSQL (Sync) ---
pg_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)


def get_pg_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- MongoDB (Async) ---
mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
mongo_db = mongo_client[settings.MONGODB_DB_NAME]


def get_mongo_events():
    return mongo_db["events"]
