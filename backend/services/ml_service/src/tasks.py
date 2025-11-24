from .celery_app import celery_app
from loguru import logger
import torch
from .models.dkt import get_model
from .config import settings
from .database import update_knowledge_state

# Initialize the model when starting the worker
# In the future, weights will be loaded here: model.load_state_dict(torch.load(...))
model = get_model(settings)

@celery_app.task(name="process_student_interaction")
def process_student_interaction(student_id: str, concept_id: str, is_correct: bool):
    """
    Task that receives a test result and updates the student's knowledge state.
    """
    logger.info(f"ML Worker: Processing interaction for student {student_id}")
    logger.info(f"   Concept: {concept_id}, Correct: {is_correct}")

    # --- 1. Simplified logic (Heuristic DKT) ---
    # In a real system, there will be:
    # history = db.get_user_history(student_id)
    # prediction = model(history)
    if is_correct:
        final_mastery = 0.95
        confidence = 0.8
    else:
        final_mastery = 0.3
        confidence = 0.5

    logger.success(f"Updated State: Concept {concept_id} -> Mastery {final_mastery}")

    # --- 2. Збереження в PostgreSQL ---
    try:
        # Ця функція вже реалізована в src/database.py і робить UPSERT
        update_knowledge_state(student_id, concept_id, final_mastery)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        # self.retry() for Celery
        raise e

    return {
        "student_id": student_id,
        "concept_id": concept_id,
        "new_mastery": final_mastery,
        "status": "saved"
    }
