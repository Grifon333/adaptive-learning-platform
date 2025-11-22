from pydantic import BaseModel

class PredictionRequest(BaseModel):
    student_id: str
    concept_id: str

class PredictionResponse(BaseModel):
    student_id: str
    concept_id: str
    mastery_level: float
    confidence: float
