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

    model_config = {
        "from_attributes": True  # Allows mapping from objects (e.g., Neo4j nodes)
    }


# --- Relationship & Path Schemas ---


class RelationshipCreate(BaseModel):
    start_concept_id: str
    end_concept_id: str
    rel_type: str = Field(default="PREREQUISITE", alias="type")


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
