import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class LearningStepCreate(BaseModel):
    step_number: int
    concept_id: str
    resource_ids: list[str]
    estimated_time: int | None = None
    difficulty: float | None = None


class LearningPathCreate(BaseModel):
    goal_concepts: list[str]
    steps: list[LearningStepCreate]
    estimated_time: int | None = None


class LearningStep(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    step_number: int
    concept_id: str
    resource_ids: list[str]
    status: str
    score: float | None = None
    estimated_time: int | None = None
    difficulty: float | None = None


class LearningPath(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    goal_concepts: list[str]
    status: str
    completion_percentage: float
    steps: list[LearningStep]
