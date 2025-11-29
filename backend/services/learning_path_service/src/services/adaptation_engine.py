from loguru import logger

from .. import schemas


class AdaptationEngine:
    """
    Encapsulates logic for constructing and modifying learning paths
    based on the student's Knowledge State (Mastery).
    """

    def generate_adaptive_steps(
        self, raw_path: list[schemas.KGSConcept], mastery_map: dict[str, float]
    ) -> tuple[list[schemas.USLearningStepCreate], int]:
        """
        Takes a raw graph path and transforms it into a personalized linear sequence.
        Returns: (List of Steps, Total Estimated Time)
        """
        us_steps = []
        total_time = 0
        current_step_num = 1

        for concept in raw_path:
            mastery_level = mastery_map.get(concept.id, 0.0)

            # Strategy 1: Skip if Mastered (Competence > 80%)
            if mastery_level > 0.8:
                logger.info(f"Skipping mastered concept: {concept.name}")
                us_steps.append(
                    self._create_step(concept, current_step_num, status="completed")
                )
                current_step_num += 1
                continue

            # Strategy 2: Remedial Support (Struggling: 0% < Competence < 60%)
            # If the student has tried before but failed (mastery > 0 but low)
            if 0.0 < mastery_level < 0.6:
                logger.info(f"Adding remedial content for: {concept.name}")

                # A. Remedial Step (Simplified / Review)
                remedial_step = self._create_step(
                    concept,
                    current_step_num,
                    status="pending",
                    is_remedial=True,
                    description=f"Detected difficulty in '{concept.name}'. Let's review the basics.",
                    time_modifier=0.5,
                    difficulty_modifier=0.7,
                )
                us_steps.append(remedial_step)
                total_time += remedial_step.estimated_time

                # Main step follows, but shares the same step number visually
                # (or handled by UI as a substep, currently just sequential)
                # We increment step_num only once per "Topic" usually,
                # but for this MVP linear list, we just append.

            # Strategy 3: Standard Learning
            step = self._create_step(concept, current_step_num, status="pending")
            us_steps.append(step)

            current_step_num += 1
            total_time += step.estimated_time

        return us_steps, total_time

    def _create_step(
        self,
        concept: schemas.KGSConcept,
        step_num: int,
        status: str,
        is_remedial: bool = False,
        description: str | None = None,
        time_modifier: float = 1.0,
        difficulty_modifier: float = 1.0,
    ) -> schemas.USLearningStepCreate:
        resources = [res.model_dump() for res in concept.resources]

        return schemas.USLearningStepCreate(
            step_number=step_num,
            concept_id=concept.id,
            resources=resources,
            estimated_time=int(concept.estimated_time * time_modifier),
            difficulty=concept.difficulty * difficulty_modifier,
            status=status,
            is_remedial=is_remedial,
            description=description or concept.description,
        )


# Singleton instance
adaptation_engine = AdaptationEngine()
