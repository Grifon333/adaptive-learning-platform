from loguru import logger

from .celery_app import celery_app
from .config import settings
from .database import append_interaction, update_knowledge_state_batch
from .models.dkt import get_model
from .services.inference_service import inference_service

# Initialize the model when starting the worker
# In the future, weights will be loaded here: model.load_state_dict(torch.load(...))
model = get_model(settings)


@celery_app.task(name="process_student_interaction")
def process_student_interaction(student_id: str, concept_id: str, is_correct: bool):
    """
    Full DKT Pipeline:
    1. Append to History (Sequence Store).
    2. Run LSTM Inference on new sequence.
    3. Update Knowledge State (Snapshot Store).
    """
    logger.info(f"ML Worker: Processing {student_id} on {concept_id} (Correct: {is_correct})")

    try:
        # 1. Persist the Interaction Event into Sequence History
        append_interaction(student_id, concept_id, is_correct)

        # 2. Run DKT Model
        # This returns the mastery prob for ALL concepts based on the updated history
        full_mastery_map = inference_service.predict_next_state(student_id, concept_id, is_correct)

        logger.info(f"DKT Update: Calculated mastery for {len(full_mastery_map)} concepts.")

        # 3. Update Snapshot DB (Postgres knowledge_states)
        # We perform a batch update because DKT updates probabilities for ALL concepts,
        # not just the one practiced.
        db_updates = []
        for c_id, mastery in full_mastery_map.items():
            db_updates.append({"student_id": student_id, "concept_id": c_id, "mastery_level": mastery})

        if db_updates:
            update_knowledge_state_batch(db_updates)

        return {"student_id": student_id, "status": "synchronized", "concepts_updated": len(db_updates)}

    except Exception as e:
        logger.error(f"Error in ML task: {e}")
        raise e
