import asyncio

import httpx
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from .celery_app import celery_app
from .config import settings

# Global client for worker (initialized lazily)
_mongo_client = None


def get_mongo_collection():
    global _mongo_client
    if _mongo_client is None:
        logger.info("Initializing MongoDB connection for Worker...")
        _mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = _mongo_client[settings.MONGODB_DB_NAME]
    return db["events"]


async def _trigger_analytics_update(student_id: str):
    """
    Calls Analytics Service to recalculate B_t (Behavioral Profile)
    and push it to ML Service.
    """
    url = f"{settings.ANALYTICS_SERVICE_URL}/api/v1/analytics/calculate-behavior/{student_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url)
            if resp.status_code == 200:
                logger.info(f"Triggered behavioral update for {student_id}")
            else:
                logger.warning(f"Failed to trigger analytics for {student_id}: {resp.status_code}")
    except Exception as e:
        logger.error(f"Error calling Analytics Service: {e}")


@celery_app.task(name="process_event_ingestion")
def process_event_ingestion(event_data: dict):
    """
    Single event processing.
    """
    logger.info(f"Worker received event: {event_data.get('event_type')}")

    # Since Celery is synchronous and Motor is asynchronous,
    # need to run an event loop for the insert operation.
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 1. Save to MongoDB
    loop.run_until_complete(_save_to_mongo(event_data))

    # 2. Trigger Real-Time Behavioral Update
    # We do this for every significant event to ensure S_{t+1} is fresh
    student_id = event_data.get("student_id")
    if student_id:
        loop.run_until_complete(_trigger_analytics_update(student_id))

    # 3. Trigger Specific ML Processing (e.g. DKT for Quizzes)
    if event_data.get("event_type") == "QUIZ_SUBMIT":
        _trigger_ml_processing(event_data)


@celery_app.task(name="process_batch_event_ingestion")
def process_batch_event_ingestion(events_data: list[dict]):
    """
    Batch event processing (optimized).
    """
    count = len(events_data)
    logger.info(f"Worker received BATCH of {count} events")

    if count == 0:
        return

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 1. Bulk Save
    loop.run_until_complete(_save_batch_to_mongo(events_data))

    # 2. Trigger Real-Time Behavioral Update (Unique Students only)
    unique_students = set(e.get("student_id") for e in events_data if e.get("student_id"))

    # Run these concurrently
    async def notify_all():
        tasks = [_trigger_analytics_update(uid) for uid in unique_students]
        await asyncio.gather(*tasks)

    loop.run_until_complete(notify_all())

    # 3. Check triggers for specific ML tasks
    for event in events_data:
        if event.get("event_type") == "QUIZ_SUBMIT":
            _trigger_ml_processing(event)


async def _save_to_mongo(data: dict):
    try:
        collection = get_mongo_collection()
        await collection.insert_one(data)
        logger.debug(f"Event saved to MongoDB: {data.get('id')}")
    except Exception as e:
        logger.error(f"Failed to save event to Mongo: {e}")


async def _save_batch_to_mongo(data_list: list[dict]):
    try:
        collection = get_mongo_collection()
        result = await collection.insert_many(data_list)
        logger.info(f"Batch saved {len(result.inserted_ids)} events to MongoDB")
    except Exception as e:
        logger.error(f"Failed to save batch to Mongo: {e}")


def _trigger_ml_processing(event_data: dict):
    context = event_data.get("metadata", {})
    student_id = event_data.get("student_id")
    concept_id = context.get("concept_id")

    # TODO
    # Evaluation logic (simplified)
    # In reality, this can be passed from the client or calculated here.
    is_correct = context.get("is_correct", False)

    if concept_id:
        logger.info(f"Triggering ML task for student {student_id}")
        celery_app.send_task(
            "process_student_interaction",
            args=[student_id, concept_id, is_correct],
            queue="celery",
        )
