# experiments/effectiveness_verification/student_agent.py

import random
import math
from uuid import uuid4


class SimulatedStudent:
    def __init__(self, profile_type="average"):
        self.id = uuid4()
        self.profile_type = profile_type

        # Knowledge State (0.0 to 1.0)
        self.knowledge = {}

        if profile_type == "strong":
            self.learning_rate = 0.20
            self.fatigue_accrual = 0.05
            self.base_knowledge = 0.4
            self.resilience = 15
        elif profile_type == "struggling":
            self.learning_rate = 0.08
            self.fatigue_accrual = 0.08
            self.base_knowledge = 0.20
            self.resilience = 12
        else:  # average
            self.learning_rate = 0.12
            self.fatigue_accrual = 0.07
            self.base_knowledge = 0.25
            self.resilience = 8

        self.fatigue = 0.0
        self.consecutive_failures = 0
        self.dropped_out = False

    def learn(self, concept_id, difficulty, resource_quality=1.0, is_remedial=False):
        if self.dropped_out:
            return 0.0

        current_k = self.knowledge.get(concept_id, self.base_knowledge)

        # Zone of Proximal Development Logic
        gap = difficulty - current_k

        if gap > 0.4:
            gain = self.learning_rate * 0.2
        elif gap < -0.2:
            gain = self.learning_rate * 0.5
        else:
            gain = self.learning_rate * 1.5

        # CALIBRATION: Stronger Intervention
        # Remedial steps are now assumed to be "High Impact" (e.g., personalized tutoring)
        if is_remedial:
            gain *= 4.0

        # Fatigue penalty
        effective_fatigue = min(0.95, self.fatigue)
        gain *= 1.0 - effective_fatigue

        new_k = min(1.0, current_k + gain)
        self.knowledge[concept_id] = new_k

        # Accrue Fatigue
        self.fatigue = min(1.0, self.fatigue + self.fatigue_accrual)

        return gain

    def attempt_quiz(self, concept_id, difficulty):
        if self.dropped_out:
            return 0.0, False

        current_k = self.knowledge.get(concept_id, self.base_knowledge)

        # Scale difficulty to 0.1-1.0
        scaled_diff = difficulty * 0.1

        # Advantage
        advantage = current_k - scaled_diff

        # CALIBRATION: Softer Sigmoid (k=8 instead of 12)
        # This prevents the "probability cliff" where being slightly behind guarantees failure
        prob_success = 1 / (1 + math.exp(-8 * advantage))

        passed = random.random() < prob_success

        if passed:
            score = random.uniform(0.70, 1.0)
            self.consecutive_failures = 0
            # Success recovers fatigue
            self.fatigue = max(0.0, self.fatigue - 0.4)
        else:
            score = random.uniform(0.30, 0.69)
            self.consecutive_failures += 1
            self.fatigue = min(1.0, self.fatigue + 0.05)

        if self.consecutive_failures >= self.resilience:
            self.dropped_out = True

        return score, passed
