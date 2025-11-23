from fastapi import FastAPI, HTTPException
from . import schemas
from .database import get_knowledge_state, get_all_student_knowledge
from .config import settings

app = FastAPI(title="ML Service API")


@app.post("/api/v1/predict", response_model=schemas.PredictionResponse)
def predict_knowledge(request: schemas.PredictionRequest):
    """
    Synchronous request to obtain the current level of knowledge.
    In a more complex version, there may be a real-time call to the DKT model here.
    Now we read the cached result from the database (which is updated by Worker).
    """
    try:
        state = get_knowledge_state(request.student_id, request.concept_id)
        return {
            "student_id": request.student_id,
            "concept_id": request.concept_id,
            "mastery_level": state["mastery_level"],
            "confidence": state["confidence"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/students/{student_id}/mastery", response_model=schemas.StudentMasteryResponse)
def get_student_mastery(student_id: str):
    """
    Повертає повну карту знань студента.
    """
    try:
        mastery_map = get_all_student_knowledge(student_id)
        return {
            "student_id": student_id,
            "mastery_map": mastery_map
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ML Service",
        "framework": "PyTorch",
        "device": "CPU"
    }
