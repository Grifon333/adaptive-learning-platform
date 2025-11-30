from pydantic import BaseModel, Field

# --- Resource Schemas ---


class ResourceBase(BaseModel):
    title: str
    type: str = Field(..., description="video, article, quiz, etc.")
    url: str
    duration: int = Field(default=0, description="Duration in minutes")


class ResourceCreate(ResourceBase):
    pass


class Resource(ResourceBase):
    id: str
    model_config = {"from_attributes": True}


class ResourceUpdate(BaseModel):
    title: str | None = None
    type: str | None = Field(default=None, description="video, article, quiz, etc.")
    url: str | None = None
    duration: int | None = Field(default=None, description="Duration in minutes")


class ResourceListResponse(BaseModel):
    total: int
    items: list[Resource]


# --- Concept Schemas ---


class ConceptBase(BaseModel):
    name: str
    description: str | None = None
    difficulty: float = Field(default=1.0, ge=1.0, le=10.0)
    estimated_time: int = Field(default=30, ge=0)  # in minutes


class ConceptCreate(ConceptBase):
    pass


class Concept(ConceptBase):
    id: str
    resources: list[Resource] = []
    model_config = {"from_attributes": True}


class ConceptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    difficulty: float | None = Field(default=None, ge=1.0, le=10.0)
    estimated_time: int | None = Field(default=None, ge=0)


class ConceptListResponse(BaseModel):
    total: int
    items: list[Concept]


# --- Relationship & Path Schemas ---


class RelationshipCreate(BaseModel):
    start_concept_id: str
    end_concept_id: str
    rel_type: str = Field(default="PREREQUISITE", alias="type")


class RelationshipDelete(BaseModel):
    start_concept_id: str
    end_concept_id: str
    rel_type: str = "PREREQUISITE"


class ResourceLink(BaseModel):
    concept_id: str
    resource_id: str


class PathResponse(BaseModel):
    path: list[Concept]


class RecommendationRequest(BaseModel):
    known_concept_ids: list[str]
    limit: int = 5


class RecommendationResponse(BaseModel):
    recommendations: list[Concept]


# --- Quiz Schemas ---


class QuestionOption(BaseModel):
    text: str
    is_correct: bool


class QuestionCreate(BaseModel):
    text: str
    options: list[QuestionOption]
    difficulty: float = 1.0


class Question(BaseModel):
    id: str
    text: str
    options: list[QuestionOption]
    difficulty: float = 1.0
    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    questions: list[Question]


class BatchQuestionsRequest(BaseModel):
    concept_ids: list[str]
    min_difficulty: float | None = None
    max_difficulty: float | None = None
    limit_per_concept: int = 3


class ConceptQuestions(BaseModel):
    concept_id: str
    questions: list[Question]


class BatchQuestionsResponse(BaseModel):
    data: list[ConceptQuestions]


class PathCandidate(BaseModel):
    id: str  # internal ID for debugging
    concepts: list[Concept]
    total_difficulty: float
    total_time: int


class MultiPathResponse(BaseModel):
    candidates: list[PathCandidate]
