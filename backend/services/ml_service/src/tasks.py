from .celery_app import celery_app
from loguru import logger
import torch
from .models.dkt import get_model
from .config import settings
from .database import update_knowledge_state
from .utils import get_concept_index

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


    # 1. Prepare Data
    # In a full DKT, we would take the entire history. Now we are taking step 1.
    # history = db.get_user_history(student_id)
    # prediction = model(history)
    # TODO
    concept_idx = get_concept_index(concept_id)
    num_concepts = settings.INPUT_DIM # має бути 100 згідно конфігу

    # Generating an input token: id + (total * correctness)
    # If correctly: idx + 100. Якщо ні: idx.
    input_val = concept_idx + (num_concepts if is_correct else 0)

    # Tensor shape: (Batch=1, SeqLen=1)
    input_tensor = torch.tensor([[input_val]], dtype=torch.long)

    # 2. Model Inference
    with torch.no_grad():
        # Output shape: (1, 1, 100) -> [Batch, Seq, ConceptPredictions]
        output = model(input_tensor)

    # We are interested in predictions specifically for the CURRENT concept (as well as we know it NOW).
    # output[0, 0, concept_idx] -> scalar tensor
    predicted_mastery = output[0, 0, concept_idx].item()

    logger.info(f"DKT Raw Prediction for concept {concept_idx}: {predicted_mastery:.4f}")

    # 3. Post-processing (MVP Hack)
    # Since the model is untrained (weights are random), it will output something like 0.49-0.51.
    # This will not allow us to see progress in the UI (the threshold there is 0.8).
    # Therefore, we add heuristics on top of the model until we train it.
    # THIS IS ONLY TO DEMONSTRATE HOW THE PIPELINE WORKS!
    # TODO

    final_mastery = predicted_mastery
    if is_correct:
        final_mastery = 0.85 + (predicted_mastery * 0.1)
    else:
        final_mastery = predicted_mastery * 0.5

    final_mastery = min(1.0, max(0.0, final_mastery)) # Clip

    logger.success(f"Final Saved Mastery: {final_mastery:.4f}")

    # 4. Save to DB
    try:
        update_knowledge_state(student_id, concept_id, final_mastery)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        # self.retry() for Celery
        raise e

    return {
        "student_id": student_id,
        "concept_id": concept_id,
        "raw_prediction": predicted_mastery,
        "final_mastery": final_mastery,
        "status": "saved"
    }
