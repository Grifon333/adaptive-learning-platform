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
    The main task of the worker:
    1. Save to MongoDB.
    2. If it is a test -> send the task to ML Worker.
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

    # 2. Trigger ML Pipeline (Cross-service communication via Redis)
    if event_data.get("event_type") == "QUIZ_SUBMIT":
        _trigger_ml_processing(event_data)

async def _save_to_mongo(data: dict):
    try:
        collection = get_mongo_collection()
        await collection.insert_one(data)
        logger.info(f"Event saved to MongoDB: {data.get('id')}")
    except Exception as e:
        logger.error(f"Failed to save event to Mongo: {e}")
        # Maybe add self.retry() here.

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
            queue="celery"
        )
