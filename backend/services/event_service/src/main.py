from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, status, HTTPException
from loguru import logger
import sys

from . import schemas, config
from .database import connect_to_mongo, close_mongo_connection, db

logger.remove()
logger.add(sys.stdout, level=config.settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="Event Service", lifespan=lifespan)

async def save_event_to_db(event_data: dict):
    """Background task to save an event to MongoDB."""
    try:
        collection = db.get_db()["events"]
        await collection.insert_one(event_data)
        # logger.debug(f"Event saved: {event_data['event_type']} for user {event_data['student_id']}")
    except Exception as e:
        logger.error(f"Failed to save event asynchronously: {e}")

@app.post(
    "/api/v1/events",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Accept event for processing"
)
async def ingest_event(
    event: schemas.EventCreate,
    background_tasks: BackgroundTasks
):
    """
    Accepts the event and puts it in the queue for saving.
    Returns 202 Accepted without waiting for the database entry.
    """
    # Convert Pydantic model to dict
    event_dict = event.model_dump()
    if event_dict.get("timestamp"):
        event_dict["timestamp"] = event_dict["timestamp"].isoformat()

    # Add task to background
    background_tasks.add_task(save_event_to_db, event_dict)

    return {"status": "accepted", "message": "Event queued for processing"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Event Service"}
