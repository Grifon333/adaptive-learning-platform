import uuid
from typing import Any

from pydantic import BaseModel

# --- Request ---


class LearningPathCreateRequest(BaseModel):
    start_concept_id: str | None = None
    goal_concept_id: str


# --- Schemas from Knowledge Graph Service ---


class KGSResource(BaseModel):
    id: str
    title: str
    type: str
    url: str
    duration: int


class KGSConcept(BaseModel):
    id: str
    name: str
    description: str | None = None
    difficulty: float
    estimated_time: int
    resources: list[KGSResource] = []


class KGSPathResponse(BaseModel):
    path: list[KGSConcept]


# --- Schemas to User Service ---


class USLearningStepCreate(BaseModel):
    step_number: int
    concept_id: str
    resources: list[dict[str, Any]]
    estimated_time: int
    difficulty: float
    status: str = "pending"
    is_remedial: bool = False
    description: str | None = None


class USLearningPathCreate(BaseModel):
    goal_concepts: list[str]
    steps: list[USLearningStepCreate]
    estimated_time: int


# --- Response (To Client) ---


class LearningStep(BaseModel):
    id: uuid.UUID
    step_number: int
    concept_id: str
    resources: list[dict[str, Any]]
    status: str
    estimated_time: int | None = None
    difficulty: float | None = None
    is_remedial: bool = False
    description: str | None = None


class LearningPathResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    goal_concepts: list[str]
    status: str
    completion_percentage: float
    steps: list[LearningStep]


class RecommendationResponse(BaseModel):
    recommendations: list[LearningStep]


# --- Quiz Schemas ---


class QuestionOption(BaseModel):
    text: str
    is_correct: bool


class Question(BaseModel):
    id: str
    text: str
    options: list[QuestionOption]


class QuizResponse(BaseModel):
    questions: list[Question]
