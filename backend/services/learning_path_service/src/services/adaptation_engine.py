from typing import Any

from loguru import logger

from .. import schemas


class AdaptationEngine:
    """
    Encapsulates logic for constructing and modifying learning paths
    based on Knowledge State (Mastery) AND Student Profile (Preferences).
    """

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

        # Factor for time estimation: Low attention -> More time needed
        # If attention < 0.4, add 20% buffer. If attention > 0.8, reduce by 10%.
        time_modifier = 1.0
        if attention_score < 0.4:
            time_modifier = 1.2
        elif attention_score > 0.8:
            time_modifier = 0.9

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
            # We sort the available resources for this concept before creating the step
            sorted_resources = self._sort_resources(concept.resources, preferences)

            # Strategy 3: Remedial Support
            if 0.0 < mastery_level < 0.6:
                # Remedial Step
                remedial_step = self._create_step(
                    concept,
                    current_step_num,
                    status="pending",
                    is_remedial=True,
                    description=f"Review required for '{concept.name}'.",
                    time_modifier=0.5
                    * time_modifier,  # Remedial is shorter but affected by attention
                    difficulty_modifier=0.7,
                    resources=sorted_resources,
                )
                us_steps.append(remedial_step)
                total_time += remedial_step.estimated_time
                # Note: We don't increment step_num here to keep them grouped in UI if needed,
                # or we increment to show distinct items. Let's increment for linear clarity.
                # current_step_num += 1

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

    def _sort_resources(
        self, resources: list[schemas.KGSResource], prefs: dict[str, Any]
    ) -> list[schemas.KGSResource]:
        """
        Sorts resources based on VARK scores.
        """
        if not resources or not prefs:
            return resources

        # Mapping Resource Type -> VARK Key
        # Types: 'Video', 'Article', 'Text', 'Book'
        # VARK: 'visual', 'reading', 'auditory', 'kinesthetic'

        def get_score(res: schemas.KGSResource) -> float:
            rtype = res.type.lower()
            if "video" in rtype:
                return float(prefs.get("visual", 0.0))
            if (
                "article" in rtype
                or "text" in rtype
                or "book" in rtype
                or "markdown" in rtype
            ):
                return float(prefs.get("reading", 0.0))
            if "audio" in rtype:
                return float(prefs.get("auditory", 0.0))
            if "quiz" in rtype or "exercise" in rtype:
                return float(prefs.get("kinesthetic", 0.0))
            return 0.0

        # Sort descending by score
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
        # Serialize resources
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

    def select_optimal_path(
        self,
        candidates: list[schemas.KGSPathCandidate],
        profile: schemas.StudentProfile | None,
        mastery_map: dict[str, float],
    ) -> list[schemas.KGSConcept]:
        """
        Evaluates multiple path candidates and returns the best one for the user.
        """
        if not candidates:
            return []

        if not profile:
            # Default: Shortest / First
            return candidates[0].concepts

        best_score = float("inf")
        best_candidate = candidates[0]

        # Weights
        # 1. Knowledge Gap (Avoid stuff we don't know? No, we want to learn.
        #    Actually, we favor paths where we might already know some prerequisites to speed up.)
        w_mastery = -10.0  # Negative because high mastery sum is GOOD (lowers score)

        # 2. Cognitive Load (Difficulty vs Attention)
        #    If attention is low, high difficulty is VERY bad.
        w_difficulty = 5.0
        attention = profile.cognitive_profile.get("attention", 0.5)
        if attention < 0.4:
            w_difficulty = 15.0  # Penalize difficulty heavily

        # 3. Preference Match (Resource Types)
        w_preference = -2.0  # Bonus for matching resources

        logger.info(f"Scoring {len(candidates)} candidates for user...")

        for cand in candidates:
            score = 0.0

            # Factor A: Total Difficulty vs Attention
            score += cand.total_difficulty * w_difficulty

            # Factor B: Mastery Bonus
            path_mastery_sum = sum(mastery_map.get(c.id, 0.0) for c in cand.concepts)
            score += path_mastery_sum * w_mastery

            # Factor C: Learning Style Match
            visual_pref = profile.learning_preferences.get("visual", 0.0)
            reading_pref = profile.learning_preferences.get("reading", 0.0)

            for c in cand.concepts:
                for r in c.resources:
                    if "video" in r.type.lower():
                        score += visual_pref * w_preference
                    elif "text" in r.type.lower() or "article" in r.type.lower():
                        score += reading_pref * w_preference

            logger.info(f"Candidate {cand.id} Score: {score}")

            if score < best_score:
                best_score = score
                best_candidate = cand

        return best_candidate.concepts


adaptation_engine = AdaptationEngine()
