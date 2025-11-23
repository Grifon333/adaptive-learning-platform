from celery import Celery
from .config import settings

# Create a Celery instance just for sending tasks
celery_app = Celery(
    "event_producer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
