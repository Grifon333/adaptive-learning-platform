from fastapi import FastAPI, HTTPException
from . import schemas
from .database import get_all_student_knowledge, get_knowledge_states_batch, update_knowledge_state_batch
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
        mastery_map = get_knowledge_states_batch(request.student_id, [request.concept_id])
        mastery = mastery_map.get(request.concept_id, 0.0)
        return {
            "student_id": request.student_id,
            "concept_id": request.concept_id,
            "mastery_level": mastery,
            "confidence": 0.5 # Placeholder, no uncertainty model yet
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predict/batch", response_model=schemas.BatchPredictionResponse)
def predict_knowledge_batch(request: schemas.BatchPredictionRequest):
    """
    Batch request to get mastery levels.
    Optimized to minimize DB hits.
    """
    try:
        mastery_map = get_knowledge_states_batch(request.student_id, request.concept_ids)
        return {
            "student_id": request.student_id,
            "mastery_map": mastery_map
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/students/{student_id}/mastery", response_model=schemas.BatchPredictionResponse)
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


@app.post("/api/v1/knowledge/batch-update", response_model=schemas.BatchKnowledgeUpdateResponse)
def update_knowledge_batch(request: schemas.BatchKnowledgeUpdateRequest):
    """
    Synchronously updates mastery levels for a student.
    Used by Assessment Service to persist test results immediately.
    """
    # 1. Prepare Data
    db_updates = []
    concept_ids = []

    for item in request.updates:
        db_updates.append({
            "student_id": str(request.student_id),
            "concept_id": item.concept_id,
            "mastery_level": item.mastery_level
        })
        concept_ids.append(item.concept_id)

    # 2. Update DB
    try:
        update_knowledge_state_batch(db_updates)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database update failed: {str(e)}")

    # 3. Fetch confirmed states to return
    # This ensures LPS gets the persisted state (Source of Truth)
    new_map = get_knowledge_states_batch(str(request.student_id), concept_ids)

    return {
        "student_id": request.student_id,
        "updated_count": len(db_updates),
        "new_mastery_map": new_map
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ML Service",
        "framework": "PyTorch",
        "device": "CPU"
    }
