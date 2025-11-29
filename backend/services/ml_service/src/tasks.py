from .celery_app import celery_app
from loguru import logger
from .models.dkt import get_model
from .config import settings
from .database import update_knowledge_state
from .services.inference_service import inference_service

# Initialize the model when starting the worker
# In the future, weights will be loaded here: model.load_state_dict(torch.load(...))
model = get_model(settings)

@celery_app.task(name="process_student_interaction")
def process_student_interaction(student_id: str, concept_id: str, is_correct: bool):
    """
    Orchestrator task:
    1. Calculate new mastery level (ML + Heuristics).
    2. Persist to Database (Postgres).
    """
    logger.info(f"ML Worker: Processing {student_id} on {concept_id} (Correct: {is_correct})")

    try:
        # 1. Get Prediction
        final_mastery = inference_service.predict_mastery(concept_id, is_correct)

        # Clip results to [0, 1]
        final_mastery = min(1.0, max(0.0, final_mastery))

        logger.info(f"Calculated Mastery: {final_mastery:.4f}")

        # 2. Save to DB
        update_knowledge_state(student_id, concept_id, final_mastery)

        return {
            "student_id": student_id,
            "concept_id": concept_id,
            "new_mastery": final_mastery,
            "status": "updated"
        }

    except Exception as e:
        logger.error(f"Error in ML task: {e}")
        # celery_app.retry() could be added here
        raise e
