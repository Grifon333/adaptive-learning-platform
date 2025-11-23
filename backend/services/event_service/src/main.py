from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, status, HTTPException
from loguru import logger
import sys

from . import schemas, config
from .database import connect_to_mongo, close_mongo_connection, db
from .celery_producer import celery_app

logger.remove()
logger.add(sys.stdout, level=config.settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="Event Service", lifespan=lifespan)


def trigger_ml_pipeline(event_data: dict):
    """
    Sends a task to Celery if the event relates to test results.
    """
    event_type = event_data.get("event_type")

    if event_type == "QUIZ_SUBMIT":
        context = event_data.get("metadata", {}) # Flutter sends data in metadata
        student_id = event_data.get("student_id")

        # Extract the data needed for DKT
        concept_id = context.get("concept_id")
        is_correct = context.get("is_correct")

        if concept_id and is_correct is not None:
            logger.info(f"🧠 Triggering ML task for student {student_id}")

            celery_app.send_task(
                "process_student_interaction",
                args=[student_id, concept_id, is_correct],
                queue="celery"
            )
        else:
            logger.warning(f"QUIZ_SUBMIT event missing required metadata: {context}")


async def save_event_to_db(event_data: dict):
    """Background task: Save to Mongo AND trigger ML if needed."""
    try:
        # 1. Stored in a "Data Lake"
        collection = db.get_db()["events"]
        await collection.insert_one(event_data)

        # 2. Trigger ML Pipeline (Fire and Forget)
        # Doing this synchronously because sending to Redis is very fast.
        trigger_ml_pipeline(event_data)

    except Exception as e:
        logger.error(f"Failed to process event: {e}")

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
