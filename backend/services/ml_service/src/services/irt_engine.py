import numpy as np

# from loguru import logger


class IRTEngine:
    """
    Implements Item Response Theory (2PL Model) for Adaptive Testing.

    Mathematical Model:
    P(theta) = 1 / (1 + e^(-a * (theta - b)))

    Where:
    - theta: Student ability (standard normal scale, approx -3 to +3)
    - b: Item difficulty (standard normal scale)
    - a: Discrimination parameter (assumed 1.0 for this MVP)
    """

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def normalize_difficulty(self, kg_difficulty: float) -> float:
        """
        Maps KG difficulty (1.0 - 10.0) to Standard Normal (-3.0 to +3.0).
        Center (5.5) -> 0.0
        """
        # Linear transform: (val - mean) / scale
        # 1.0 -> -3.0, 10.0 -> +3.0
        return (kg_difficulty - 5.5) / 1.5

    def denormalize_difficulty(self, theta: float) -> float:
        """Maps Theta back to KG scale (1.0 - 10.0)."""
        val = (theta * 1.5) + 5.5
        return float(np.clip(val, 1.0, 10.0))

    def estimate_ability(self, history: list[dict]) -> float:
        """
        Estimates theta using a simplified iterative approach (Hill Climbing)
        maximizing the Likelihood function based on response history.

        history: [{"difficulty": 5.0, "correct": True}, ...]
        """
        if not history:
            return 0.0  # Start at average ability

        # Grid search for MVP (Robust and stateless)
        # Range -3 to +3 with step 0.1
        thetas = np.linspace(-3.0, 3.0, 61)
        log_likelihoods = np.zeros_like(thetas)

        for i, theta in enumerate(thetas):
            ll = 0.0
            for item in history:
                b = self.normalize_difficulty(item["difficulty"])
                prob = self.sigmoid(theta - b)  # a=1.0

                # Avoid log(0)
                prob = np.clip(prob, 1e-9, 1.0 - 1e-9)

                if item["correct"]:
                    ll += np.log(prob)
                else:
                    ll += np.log(1.0 - prob)
            log_likelihoods[i] = ll

        # Return theta with max likelihood
        best_idx = np.argmax(log_likelihoods)
        return float(thetas[best_idx])

    def get_next_target_difficulty(self, current_theta: float) -> float:
        """
        In CAT, we select the item that maximizes Information.
        For 1PL/Rasch, this is simply an item where b is closest to theta.
        """
        return self.denormalize_difficulty(current_theta)

    def calculate_mastery(self, theta: float) -> float:
        """Converts Theta to Mastery (0.0 - 1.0) using Sigmoid."""
        # Map -3..+3 to 0..1 roughly
        return float(self.sigmoid(theta))


irt_engine = IRTEngine()
