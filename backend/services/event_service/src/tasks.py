import asyncio

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

    loop.run_until_complete(_save_to_mongo(event_data))

    # Trigger ML Pipeline
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

    # 2. Check triggers for every event in the batch
    # (e.g. user completed a quiz offline, now we sync and must update ML)
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
        # insert_many is much faster for lists
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
        # Send the task to the 'celery' queue (where ML Worker listens).
        celery_app.send_task(
            "process_student_interaction",
            args=[student_id, concept_id, is_correct],
            queue="celery",
        )
