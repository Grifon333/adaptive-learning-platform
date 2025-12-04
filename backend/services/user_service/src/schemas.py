import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str
    last_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: uuid.UUID | None = None
    token_type: str = "access"


class StudentProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    cognitive_profile: dict[str, Any]
    learning_preferences: dict[str, Any]
    timezone: str | None = None


class StudentProfileUpdate(BaseModel):
    cognitive_profile: dict[str, Any] | None = None
    learning_preferences: dict[str, Any] | None = None
    timezone: str | None = None


class ResourceData(BaseModel):
    id: str
    title: str
    type: str
    url: str
    duration: int


class LearningStepCreate(BaseModel):
    step_number: int
    concept_id: str
    resources: list[dict[str, Any]]
    estimated_time: int | None = None
    difficulty: float | None = None
    status: str = "pending"
    is_remedial: bool = False
    description: str | None = None


class LearningPathCreate(BaseModel):
    goal_concepts: list[str]
    steps: list[LearningStepCreate]
    estimated_time: int | None = None


class LearningStep(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    path_id: uuid.UUID
    step_number: int
    concept_id: str
    resources: list[dict[str, Any]]
    status: str
    score: float | None = None
    estimated_time: int | None = None
    difficulty: float | None = None
    is_remedial: bool = False
    description: str | None = None

    @field_validator("is_remedial", mode="before")
    @classmethod
    def set_default_false(cls, v):
        return v or False


class LearningPath(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    goal_concepts: list[str]
    status: str
    completion_percentage: float
    steps: list[LearningStep]


class TokenRefresh(BaseModel):
    refresh_token: str


# --- Progress Tracking Schemas ---


class StepProgressUpdate(BaseModel):
    time_delta: int = Field(..., ge=0, description="Time spent in seconds since last update")


class StepCompleteResponse(BaseModel):
    step_id: uuid.UUID
    status: str
    path_completion_percentage: float
    path_is_completed: bool


# --- Quiz ---


class StepQuizUpdate(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Quiz score from 0.0 to 1.0")
    passed: bool


# --- Adaptation ---


class AdaptationRequest(BaseModel):
    trigger_type: str
    strategy: str
    insert_at_step: int
    new_steps: list[LearningStepCreate]  # The remedial steps to insert


class AdaptationResponse(BaseModel):
    success: bool
    message: str
    path_id: uuid.UUID
