from pydantic import BaseModel, Field


class ConceptBase(BaseModel):
    name: str
    description: str | None = None
    difficulty: float = Field(default=1.0, ge=1.0, le=10.0)
    estimated_time: int = Field(default=30, ge=0)  # in minutes


class ConceptCreate(ConceptBase):
    pass


class Concept(ConceptBase):
    id: str  # unique UUID

    model_config = {
        "from_attributes": True  # Allows mapping from objects (e.g., Neo4j nodes)
    }


class RelationshipCreate(BaseModel):
    start_concept_id: str
    end_concept_id: str
    rel_type: str = Field(default="PREREQUISITE", alias="type")


class PathResponse(BaseModel):
    path: list[Concept]
