import torch
import os
from loguru import logger
from ..config import settings
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
        model_path = "model_weights.pth" # Local file for now
        if os.path.exists(model_path):
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                logger.info(f"Model weights loaded from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load model weights: {e}")
        else:
            logger.warning("No model weights found. Using random initialization (untrained).")

    def predict_mastery(self, concept_id: str, is_correct: bool) -> float:
        """
        Performs a forward pass for a SINGLE interaction.

        NOTE: A full DKT implementation requires the student's ENTIRE history sequence.
        Since we are currently processing events statelessly in this MVP worker,
        we use a simplified 'Online Update' approach or a Heuristic Fallback
        if the model is untrained.
        """

        # 1. Preprocessing
        concept_idx = get_concept_index(concept_id)
        input_dim = settings.INPUT_DIM

        # Input token: ConceptID + (TotalConcepts * Correctness)
        # Example: ID=5, Correct=True (1), Total=100 -> Input=105
        input_val = concept_idx + (input_dim if is_correct else 0)

        input_tensor = torch.tensor([[input_val]], dtype=torch.long).to(self.device)

        # 2. Inference
        with torch.no_grad():
            output = self.model(input_tensor)
            # output shape: [Batch=1, Seq=1, Concepts]

        # 3. Extract prediction for the *current* concept
        # (How well do I know this concept AFTER this interaction?)
        predicted_mastery = output[0, 0, concept_idx].item()

        return self._apply_business_rules(predicted_mastery, is_correct)

    def _apply_business_rules(self, raw_prediction: float, is_correct: bool) -> float:
        """
        Hybrid Logic: Model + Heuristics.
        If the model is random (untrained), raw_prediction will be ~0.5.
        We need to ensure the UI reacts to user actions even without a trained model.
        """
        # "Smoothing" the neural network output with explicit logic
        if is_correct:
            return max(raw_prediction, 0.75) + 0.1
        else:
            return min(raw_prediction, 0.4)


inference_service = InferenceService()
