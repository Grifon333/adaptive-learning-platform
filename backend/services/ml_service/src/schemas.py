from uuid import UUID
from pydantic import BaseModel

class PredictionRequest(BaseModel):
    student_id: UUID
    concept_id: str

class BatchPredictionRequest(BaseModel):
    student_id: UUID
    concept_ids: list[str]

class PredictionResponse(BaseModel):
    student_id: UUID
    concept_id: str
    mastery_level: float
    confidence: float = 0.5

class BatchPredictionResponse(BaseModel):
    student_id: UUID
    mastery_map: dict[str, float] # {concept_id: mastery_level}
