import os

import torch
from loguru import logger

from ..config import settings
from ..database import get_student_history
from ..models.dkt import get_model
from ..utils import get_concept_index


class InferenceService:
    def __init__(self):
        self.model = get_model(settings)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self._load_weights()

    def _load_weights(self):
        """
        Loads trained weights if they exist.
        In a real production scenario, this would load from S3 or a Model Registry.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "..", "models", "data", "dkt_model.pth")
        if os.path.exists(model_path):
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.eval()
                logger.info(f"Model weights loaded from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load model weights: {e}")
        else:
            logger.warning("No model weights found. Using random initialization (untrained).")

    def predict_next_state(self, student_id: str, current_concept: str, current_correct: bool) -> dict[str, float]:
        """
        1. Loads history.
        2. Appends current interaction.
        3. Runs DKT.
        4. Returns map of {concept_id: probability} for ALL concepts.
        """
        # 1. Fetch History
        history = get_student_history(student_id)

        # 2. Prepare Sequence
        # Add the current one conceptually to see the *result* state
        history.append({"concept_id": current_concept, "correct": current_correct})

        # Limit sequence length for performance (e.g., last 50 interactions)
        max_seq_len = 50
        if len(history) > max_seq_len:
            history = history[-max_seq_len:]

        # 3. Vectorize
        input_seq = []
        input_dim = settings.INPUT_DIM_DKT

        for item in history:
            c_idx = get_concept_index(item["concept_id"])
            # x = concept_index + (TotalConcepts * Correctness)
            val = c_idx + (input_dim if item["correct"] else 0)
            input_seq.append(val)

        if not input_seq:
            return {}

        # Shape: (Batch=1, SeqLen)
        input_tensor = torch.tensor([input_seq], dtype=torch.long).to(self.device)

        # 4. Inference
        self.model.eval()
        with torch.no_grad():
            # Output Shape: (1, SeqLen, OutputDim)
            output = self.model(input_tensor)

        # We are interested in the prediction AFTER the last step
        # shape: (OutputDim,)
        last_step_prediction = output[0, -1, :]

        # 5. Decode to Concept IDs
        # We need the reverse mapping or just iterate indices
        mastery_map = {}
        # Assuming utils has CONCEPT_TO_INDEX. We iterate it to map back.
        # Ideally we'd have INDEX_TO_CONCEPT.
        from ..utils import CONCEPT_TO_INDEX

        for c_id, idx in CONCEPT_TO_INDEX.items():
            if idx < len(last_step_prediction):
                mastery_map[c_id] = float(last_step_prediction[idx].item())

        return mastery_map


inference_service = InferenceService()
