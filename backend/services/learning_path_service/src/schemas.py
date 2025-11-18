import uuid

from pydantic import BaseModel

# --- Schemas for Learning Path Service ---


class LearningPathCreateRequest(BaseModel):
    """Request received by this service (LPS)."""

    start_concept_id: str
    goal_concept_id: str


# --- Schemas for Knowledge Graph Service ---


class KGSConcept(BaseModel):
    """The KGS concept returns."""

    id: str
    name: str
    description: str | None = None
    difficulty: float
    estimated_time: int


class KGSPathResponse(BaseModel):
    """The response from KGS."""

    path: list[KGSConcept]


# --- Schemas for User Service ---


class USLearningStepCreate(BaseModel):
    """Send to the US for one step."""

    step_number: int
    concept_id: str
    resource_ids: list[str]  # Fake for now
    estimated_time: int
    difficulty: float


class USLearningPathCreate(BaseModel):
    """Sending it to the US to create a path."""

    goal_concepts: list[str]
    steps: list[USLearningStepCreate]
    estimated_time: int


class LearningStep(BaseModel):
    """Receive in response from the US for a step."""

    id: uuid.UUID
    step_number: int
    concept_id: str
    resource_ids: list[str]
    status: str
    estimated_time: int | None = None
    difficulty: float | None = None


class LearningPathResponse(BaseModel):
    """Final response received from the US and returned to the client."""

    id: uuid.UUID
    student_id: uuid.UUID
    goal_concepts: list[str]
    status: str
    completion_percentage: float
    steps: list[LearningStep]
