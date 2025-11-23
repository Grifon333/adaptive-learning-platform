from pydantic import BaseModel

class PredictionRequest(BaseModel):
    student_id: str
    concept_id: str

class PredictionResponse(BaseModel):
    student_id: str
    concept_id: str
    mastery_level: float
    confidence: float


class StudentMasteryResponse(BaseModel):
    student_id: str
    mastery_map: dict[str, float] # {concept_id: mastery_level}
