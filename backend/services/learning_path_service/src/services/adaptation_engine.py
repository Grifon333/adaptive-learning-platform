from typing import Any

import httpx
from loguru import logger

from .. import config, schemas


class AdaptationEngine:
    """
    Encapsulates logic for constructing and modifying learning paths
    using Reinforcement Learning.
    """

    async def select_optimal_path(
        self,
        client: httpx.AsyncClient,
        student_id: str,
        candidates: list[schemas.KGSPathCandidate],
        profile: schemas.StudentProfile | None,
    ) -> list[schemas.KGSConcept]:
        """
        USAGE: Called by `create_learning_path` (Initial Path Generation).

        Logic:
        1. We have multiple full path options (candidates).
        2. To decide which path is "best" using an RL agent (which operates on concepts),
           we look at the *First Divergent Concept* of each path.
        3. We ask the RL Agent: "Which of these starting concepts is best for the student?"
        4. We select the path that starts with that recommended concept.
        """
        if not candidates:
            return []

        if len(candidates) == 1:
            return candidates[0].concepts

        # 1. Identify valid starting concepts
        # We create a map of {first_concept_id: candidate_object}
        candidate_map = {}
        valid_start_ids = []

        for cand in candidates:
            if not cand.concepts:
                continue
            first_id = cand.concepts[0].id
            candidate_map[first_id] = cand
            valid_start_ids.append(first_id)

        # Remove duplicates
        valid_start_ids = list(set(valid_start_ids))

        # 2. Ask RL Agent to pick the best start
        recommended_start_id = await self._query_rl_agent(client, student_id, valid_start_ids, profile)

        # 3. Return the path corresponding to the recommendation
        # If RL picks something we have, return it. Else default to first.
        selected_candidate = candidate_map.get(recommended_start_id, candidates[0])

        logger.info(f"RL Agent selected path starting with {recommended_start_id}")
        return selected_candidate.concepts

    async def select_optimal_path_concept(
        self,
        client: httpx.AsyncClient,
        student_id: str,
        candidates: list[schemas.KGSConcept],
        profile: schemas.StudentProfile | None,
    ) -> schemas.KGSConcept | None:
        """
        USAGE: Called by `get_student_recommendations` and `adapt_learning_path`.

        Logic:
        1. We have a list of possible single concepts (e.g., potential next steps).
        2. We ask the RL Agent to pick the best one.
        """
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        # 1. Extract IDs
        valid_ids = [c.id for c in candidates]

        # 2. Ask RL Agent
        recommended_id = await self._query_rl_agent(client, student_id, valid_ids, profile)

        # 3. Find object
        for c in candidates:
            if c.id == recommended_id:
                return c

        return candidates[0]

    async def _query_rl_agent(
        self,
        client: httpx.AsyncClient,
        student_id: str,
        valid_concept_ids: list[str],
        profile: schemas.StudentProfile | None,
    ) -> str:
        """
        Helper to send request to ML Service.
        """
        try:
            profile_dict = {}
            if profile:
                profile_dict = {
                    "cognitive_profile": profile.cognitive_profile,
                    "learning_preferences": profile.learning_preferences,
                }

            ml_url = f"{config.settings.ML_SERVICE_URL}/api/v1/rl/recommend"
            payload = {
                "student_id": student_id,
                "valid_concept_ids": valid_concept_ids,
                "student_profile": profile_dict,
            }

            resp = await client.post(ml_url, json=payload)
            resp.raise_for_status()

            return str(resp.json().get("recommended_concept_id"))
        except Exception as e:
            logger.error(f"RL Service unavailable: {e}")
            # Fallback: return the first one
            return valid_concept_ids[0] if valid_concept_ids else ""

    def generate_adaptive_steps(
        self,
        raw_path: list[schemas.KGSConcept],
        mastery_map: dict[str, float],
        profile: schemas.StudentProfile | None = None,
    ) -> tuple[list[schemas.USLearningStepCreate], int]:
        """
        Transforms raw graph path into personalized linear sequence.
        Returns: (List of Steps, Total Estimated Time)
        """
        us_steps = []
        total_time = 0
        current_step_num = 1

        # Extract factors if profile exists
        attention_score = 0.5
        preferences = {}

        if profile:
            attention_score = profile.cognitive_profile.get("attention", 0.5)
            preferences = profile.learning_preferences

        # Factor for time estimation
        time_modifier = 1.0
        if attention_score < 0.4:
            time_modifier = 1.2
        elif attention_score > 0.8:
            time_modifier = 0.9

        remedial_exist = False

        for concept in raw_path:
            mastery_level = mastery_map.get(concept.id, 0.0)

            # Strategy 1: Skip if Mastered
            if mastery_level > 0.8:
                # We record it as completed for history, but user doesn't "do" it now
                us_steps.append(
                    self._create_step(
                        concept,
                        current_step_num,
                        status="completed",
                        resources=concept.resources,
                    )
                )
                current_step_num += 1
                continue

            # Strategy 2: Resource Sorting based on Preferences
            sorted_resources = self._sort_resources(concept.resources, preferences)

            # Strategy 3: Remedial Support (Simplified)
            # In a full flow, we might call select_optimal_path_concept here to pick *which* remedial to use
            # if there are multiple options from KG.
            if 0.0 < mastery_level < 0.6 and not remedial_exist:
                remedial_step = self._create_step(
                    concept,
                    current_step_num,
                    status="pending",
                    is_remedial=True,
                    description=f"Review required for '{concept.name}'.",
                    time_modifier=0.5 * time_modifier,
                    difficulty_modifier=0.7,
                    resources=sorted_resources,
                )
                us_steps.append(remedial_step)
                total_time += remedial_step.estimated_time
                remedial_exist = True

            # Standard Learning Step
            step = self._create_step(
                concept,
                current_step_num,
                status="pending",
                time_modifier=time_modifier,
                resources=sorted_resources,
            )
            us_steps.append(step)

            current_step_num += 1
            total_time += step.estimated_time

        return us_steps, total_time

    def _sort_resources(self, resources: list[schemas.KGSResource], prefs: dict[str, Any]) -> list[schemas.KGSResource]:
        if not resources or not prefs:
            return resources

        def get_score(res: schemas.KGSResource) -> float:
            rtype = res.type.lower()
            if "video" in rtype:
                return float(prefs.get("visual", 0.0))
            if "article" in rtype or "text" in rtype:
                return float(prefs.get("reading", 0.0))
            if "audio" in rtype:
                return float(prefs.get("auditory", 0.0))
            if "quiz" in rtype or "exercise" in rtype:
                return float(prefs.get("kinesthetic", 0.0))
            return 0.0

        return sorted(resources, key=get_score, reverse=True)

    def _create_step(
        self,
        concept: schemas.KGSConcept,
        step_num: int,
        status: str,
        resources: list[schemas.KGSResource],
        is_remedial: bool = False,
        description: str | None = None,
        time_modifier: float = 1.0,
        difficulty_modifier: float = 1.0,
    ) -> schemas.USLearningStepCreate:
        resources_dicts = [res.model_dump() for res in resources]

        return schemas.USLearningStepCreate(
            step_number=step_num,
            concept_id=concept.id,
            resources=resources_dicts,
            estimated_time=int(concept.estimated_time * time_modifier),
            difficulty=concept.difficulty * difficulty_modifier,
            status=status,
            is_remedial=is_remedial,
            description=description or concept.description,
        )

    async def create_remediation_plan(
        self, client: httpx.AsyncClient, concept_id: str, current_step_number: int
    ) -> tuple[list[schemas.USLearningStepCreate], str]:
        """
        Creates a remedial step.
        """
        try:
            url = f"{config.settings.KG_SERVICE_URL}/api/v1/concepts/{concept_id}/prerequisites"
            resp = await client.get(url)
            resp.raise_for_status()
            prereqs_data = resp.json().get("items", [])
            # Convert dicts back to KGSConcept objects to use with select_optimal_path_concept
            prereqs = [schemas.KGSConcept(**p) for p in prereqs_data]
        except Exception as e:
            logger.error(f"Failed to fetch prereqs: {e}")
            return [], "Error fetching prerequisites"

        if not prereqs:
            return [], "No prerequisites found to review."

        # USE RL TO SELECT BEST REMEDIAL CONCEPT
        # We need student_id... this method signature needs updating or context passing.
        # For now, we take the first one to avoid breaking signature in this snippet,
        # or we assume simple logic.
        target = prereqs[0]

        remedial_step = schemas.USLearningStepCreate(
            step_number=current_step_number + 1,
            concept_id=target.id,
            resources=[r.model_dump() for r in target.resources],
            estimated_time=15,
            difficulty=target.difficulty * 0.8,
            status="pending",
            is_remedial=True,
            description=f"Remedial: Review '{target.name}' to improve understanding.",
        )

        return [remedial_step], "remedial_insertion"


adaptation_engine = AdaptationEngine()
