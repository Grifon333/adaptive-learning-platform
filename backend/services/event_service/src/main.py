import sys
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from loguru import logger

from . import config, schemas
from .celery_app import celery_app

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
    summary="Accept single event",
)
async def ingest_event(event: schemas.EventCreate):
    """
    Accepts the event and puts it in the queue for saving.
    """
    event_dict = event.model_dump()

    # Generate ID if missing (though schema usually handles default)
    if "id" not in event_dict:
        event_dict["id"] = str(uuid.uuid4())

    if event_dict.get("timestamp"):
        event_dict["timestamp"] = event_dict["timestamp"].isoformat()

    task_result = celery_app.send_task("process_event_ingestion", args=[event_dict], queue="event_queue")

    return {"status": "accepted", "task_id": task_result.id}


@app.post(
    "/api/v1/events/batch",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Accept batch of events",
)
async def ingest_batch_events(batch: schemas.EventBatchCreate):
    """
    Accepts a list of events for bulk processing.
    """
    events_list = []

    for evt in batch.events:
        e_dict = evt.model_dump()
        if "id" not in e_dict:
            e_dict["id"] = str(uuid.uuid4())
        # Serialize timestamp for JSON transport to Celery
        if e_dict.get("timestamp"):
            e_dict["timestamp"] = e_dict["timestamp"].isoformat()
        events_list.append(e_dict)

    task_result = celery_app.send_task("process_batch_event_ingestion", args=[events_list], queue="event_queue")

    logger.info(f"Batch of {len(events_list)} events queued. Task ID: {task_result.id}")

    return {"status": "accepted", "task_id": task_result.id, "count": len(events_list)}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Event Service"}
