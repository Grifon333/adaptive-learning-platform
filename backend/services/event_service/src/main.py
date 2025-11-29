from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from loguru import logger
import sys

from . import schemas, config
from .celery_app import celery_app
from . import tasks

logger.remove()
logger.add(sys.stdout, level=config.settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Event Service API initializing...")
    yield
    logger.info("Event Service API shutting down...")

app = FastAPI(title="Event Service", lifespan=lifespan)


@app.post(
    "/api/v1/events",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Accept event for processing"
)
async def ingest_event(event: schemas.EventCreate):
    """
    Accepts the event and puts it in the queue for saving.
    Returns 202 Accepted without waiting for the database entry.
    """
    event_dict = event.model_dump()

    if event_dict.get("timestamp"):
        event_dict["timestamp"] = event_dict["timestamp"].isoformat()

    task_result = celery_app.send_task(
        "process_event_ingestion",
        args=[event_dict],
        queue="event_queue"
    )

    logger.info(f"Event queued. Task ID: {task_result.id}")

    return {"status": "accepted", "task_id": task_result.id}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Event Service"}
