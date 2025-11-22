from .celery_app import celery_app
from loguru import logger
import torch
from .models.dkt import get_model
from .config import settings

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

    # --- 1. EMULATE DKT PREDICTION ---
    # In a real system, here we would query the database for the student's history

    # Create a fake input tensor (batch_size=1, seq_len=1)
    # Just to verify that PyTorch is functioning
    dummy_input = torch.tensor([[1]])

    with torch.no_grad():
        prediction = model(dummy_input)

    # Get the "prediction" (just a number between 0 and 1)
    predicted_mastery = prediction[0, 0, 0].item()

    logger.success(f"🧠 DKT Prediction: New mastery for concept {concept_id} -> {predicted_mastery:.4f}")

    # --- 2. HERE WILL BE POSTGRES UPDATE (in the next steps) ---
    # We will call the User Service or write directly to the database

    return {
        "student_id": student_id,
        "concept_id": concept_id,
        "new_mastery": predicted_mastery,
        "status": "processed"
    }
