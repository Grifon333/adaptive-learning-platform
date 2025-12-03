import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_type: str = Field(
        ..., description="Event type: VIDEO_PLAY, QUIZ_SUBMIT, etc."
    )
    student_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary event data"
    )


class Event(EventCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
