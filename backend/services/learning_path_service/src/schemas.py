from typing import Any
from uuid import UUID

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


class KGSPathCandidate(BaseModel):
    id: str
    concepts: list[KGSConcept]
    total_difficulty: float
    total_time: int


class KGSMultiPathResponse(BaseModel):
    candidates: list[KGSPathCandidate]


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
    id: UUID
    step_number: int
    concept_id: str
    resources: list[dict[str, Any]]
    status: str
    estimated_time: int | None = None
    difficulty: float | None = None
    is_remedial: bool = False
    description: str | None = None


class LearningPathResponse(BaseModel):
    id: UUID
    student_id: UUID
    goal_concepts: list[str]
    status: str
    completion_percentage: float
    steps: list[LearningStep]


class RecommendationResponse(BaseModel):
    recommendations: list[LearningStep]


# --- Quiz Schemas ---


class QuestionOption(BaseModel):
    text: str
    is_correct: bool = False


class Question(BaseModel):
    id: str
    text: str
    options: list[QuestionOption]


class QuizResponse(BaseModel):
    questions: list[Question]


# --- Assessment Schemas ---


class AssessmentStartRequest(BaseModel):
    student_id: UUID
    goal_concept_id: str


class AssessmentQuestion(BaseModel):
    id: str
    text: str
    options: list[dict[str, Any]]
    concept_id: str
    difficulty: float


class AssessmentSession(BaseModel):
    session_id: str
    total_questions: int
    questions: list[AssessmentQuestion]


class AssessmentSubmission(BaseModel):
    student_id: UUID
    goal_concept_id: str
    answers: dict[str, int]  # {question_id: selected_option_index}


class AssessmentResult(BaseModel):
    student_id: UUID
    mastery_scores: dict[str, float]  # {concept_id: score}


# --- User Service Integration Schemas ---


class StudentProfile(BaseModel):
    id: UUID
    user_id: UUID
    cognitive_profile: dict[str, Any] = {}  # {"attention": 0.5, "memory": 0.6}
    learning_preferences: dict[str, Any] = {}  # {"visual": 0.8, "reading": 0.2}
    timezone: str | None = None
