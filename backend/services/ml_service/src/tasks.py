from .celery_app import celery_app
from loguru import logger
import torch
from .models.dkt import get_model
from .config import settings

# Ініціалізуємо модель при старті воркера
# У майбутньому тут буде завантаження ваг: model.load_state_dict(torch.load(...))
model = get_model(settings)

@celery_app.task(name="process_student_interaction")
def process_student_interaction(student_id: str, concept_id: str, is_correct: bool):
    """
    Задача, яка приймає результат тесту та оновлює стан знань студента.
    """
    logger.info(f"ML Worker: Processing interaction for student {student_id}")
    logger.info(f"   Concept: {concept_id}, Correct: {is_correct}")

    # --- 1. ЕМУЛЯЦІЯ DKT ПРОГНОЗУ ---
    # У реальній системі тут ми б зробили запит до БД за історією студента

    # Створюємо фейковий вхідний тензор (batch_size=1, seq_len=1)
    # Просто щоб перевірити, що PyTorch працює
    dummy_input = torch.tensor([[1]])

    with torch.no_grad():
        prediction = model(dummy_input)

    # Отримуємо "передбачення" (просто число від 0 до 1)
    predicted_mastery = prediction[0, 0, 0].item()

    logger.success(f"🧠 DKT Prediction: New mastery for concept {concept_id} -> {predicted_mastery:.4f}")

    # --- 2. ТУТ БУДЕ ОНОВЛЕННЯ POSTGRES (у наступних кроках) ---
    # Ми викличемо User Service або запишемо в БД напряму

    return {
        "student_id": student_id,
        "concept_id": concept_id,
        "new_mastery": predicted_mastery,
        "status": "processed"
    }
