# import numpy as np
# import torch
from loguru import logger

from ..config import settings
from ..database import get_all_student_knowledge, get_behavioral_profile
from ..models.rl import RLAgent
from ..utils import CONCEPT_TO_INDEX, get_concept_index

# Global Agent Instance
# Input: 100 (Concepts) + 5 (Behavior) + 6 (Cognitive) = 111
# Output: 100 (Concepts)
# TODO: Get exact counts dynamically. For now, using hardcoded sizing from Seed/Config.
INPUT_DIM = settings.INPUT_DIM + 5 + 6
OUTPUT_DIM = settings.OUTPUT_DIM

rl_agent = RLAgent(INPUT_DIM, OUTPUT_DIM)


class RLEngine:
    """
    Orchestrates the RL process:
    1. Aggregates State S_t
    2. Calculates Reward R_t
    3. Interfaces with the Agent
    """

    async def get_recommendation(self, student_id: str, profile_data: dict, valid_concept_ids: list[str]) -> str:
        """
        Constructs state S_t and queries the agent.
        """
        # 1. Fetch State Components
        # K_t: Knowledge State (from local DB)
        knowledge_map = get_all_student_knowledge(student_id)  # {cid: mastery}

        # B_t: Behavioral Profile (from local DB - synced via events)
        behavior_profile = get_behavioral_profile(student_id)

        # psi: Cognitive Profile (passed from request to avoid circular dependency)
        cognitive_profile = profile_data.get("cognitive_profile", {})
        preferences = profile_data.get("learning_preferences", {})

        # 2. Vectorize State S_t
        # This must match the model's expected input structure strictly.
        state_vector = self._vectorize_state(knowledge_map, behavior_profile, cognitive_profile, preferences)

        # 3. Determine Valid Actions (Concepts)
        # We map UUIDs to Indices [0..99]
        valid_indices = [get_concept_index(cid) for cid in valid_concept_ids if cid in CONCEPT_TO_INDEX]

        if not valid_indices:
            # Fallback: if no valid concepts mapped, allow all (exploration)
            valid_indices = list(range(OUTPUT_DIM))

        # 4. Select Action
        action_idx = rl_agent.select_action(state_vector, valid_indices)

        # 5. Decode Action -> Concept ID
        # Invert the mapping. Ideally, utils has INDEX_TO_CONCEPT.
        # Doing a linear search for now (MVP).
        selected_concept_id = None
        for cid, idx in CONCEPT_TO_INDEX.items():
            if idx == action_idx:
                selected_concept_id = cid
                break

        return selected_concept_id or valid_concept_ids[0]

    async def process_feedback(
        self,
        student_id: str,
        action_concept_id: str,
        reward_components: dict,
        prev_state_vector: list[float] | None = None,
    ):
        """
        1. Reconstructs S_t (if not provided).
        2. Calculates Reward R_t.
        3. Fetches S_{t+1}.
        4. Stores transition in Agent Memory.
        5. Triggers training.
        """
        # 1. State S_t (Previous)
        # In a stateless API, we might need to reconstruct it or have the client pass it back.
        # If client passed it (ideal), use it. Else, approximate using current state (noisy).
        if prev_state_vector:
            state = prev_state_vector
        else:
            # Approximation (Not ideal for RL, but functional for MVP)
            # We assume state hasn't changed drastically *except* for the component we just updated.
            # Real implementation would cache S_t in Redis with a session_id.
            state = self._build_current_state_vector(student_id, {})

        # 2. Calculate Reward
        # reward_components: { "mastery_delta": 0.2, "behavior_delta": -0.1, "difficulty": 0.5 }
        reward = self.calculate_reward(
            mastery_delta=reward_components.get("mastery_delta", 0.0),
            behavior_delta=reward_components.get("behavior_delta", 0.0),
            concept_difficulty=reward_components.get("difficulty", 0.5),
            # Ideally we calculate student ability from K_t avg
            student_ability=0.5,
        )

        # 3. State S_{t+1} (Next)
        next_state = self._build_current_state_vector(student_id, {})

        # 4. Action Index
        action_idx = get_concept_index(action_concept_id)

        # 5. Store & Train
        # Done = False (Continuous learning)
        rl_agent.store_transition(state, action_idx, reward, next_state, False)
        rl_agent.train_step()
        rl_agent.save_checkpoint()
        logger.info(f"RL Agent trained on feedback from {student_id}. Reward: {reward}")

    def calculate_reward(
        self, mastery_delta: float, behavior_delta: float, concept_difficulty: float, student_ability: float
    ) -> float:
        w1, w2, w3 = 1.0, 0.5, 0.2

        # R_knowledge
        r_know = mastery_delta

        # R_engagement (negative delta in procrastination is good)
        r_engage = -behavior_delta

        # R_load
        load_diff = max(0, concept_difficulty - student_ability)
        r_load = load_diff * load_diff

        total_reward = (w1 * r_know) + (w2 * r_engage) - (w3 * r_load)
        return float(total_reward)

    def _build_current_state_vector(self, student_id: str, profile_override: dict) -> list[float]:
        # Helper to fetch fresh data and vectorize
        k_map = get_all_student_knowledge(student_id)
        b_prof = get_behavioral_profile(student_id)
        # We might miss static profile data here if not passed, defaulting to 0.5
        return self._vectorize_state(k_map, b_prof, {}, {})

    def _vectorize_state(self, k_map, b_prof, c_prof, prefs) -> list[float]:
        """
        Flattens all dictionaries into a single fixed-size list.
        Order: [Knowledge... | Behavior... | Cognitive... | Prefs...]
        """
        # 1. Knowledge (Sorted by Index)
        k_vec = [0.0] * settings.INPUT_DIM
        for cid, mastery in k_map.items():
            idx = get_concept_index(cid)
            if 0 <= idx < settings.INPUT_DIM:
                k_vec[idx] = mastery

        # 2. Behavior (Fixed order: procrastination, gaming, engagement, hint, error)
        b_vec = [
            b_prof.get("procrastination_index", 0.0),
            b_prof.get("gaming_score", 0.0),
            b_prof.get("engagement_score", 0.0),
            b_prof.get("hint_rate", 0.0),
            b_prof.get("error_rate", 0.0),
        ]

        # 3. Cognitive (memory, attention)
        c_vec = [c_prof.get("memory", 0.5), c_prof.get("attention", 0.5)]

        # 4. Preferences (visual, auditory, kinesthetic, reading)
        p_vec = [
            prefs.get("visual", 0.25),
            prefs.get("auditory", 0.25),
            prefs.get("kinesthetic", 0.25),
            prefs.get("reading", 0.25),
        ]

        return k_vec + b_vec + c_vec + p_vec


rl_engine = RLEngine()
