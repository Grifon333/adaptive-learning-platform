import uuid
from typing import Any

import httpx
from fastapi import HTTPException
from loguru import logger

from .. import config, schemas


class AssessmentService:
    """
    Manages the Initial Assessment flow: generation, grading, and ML synchronization.
    """

    async def generate_assessment(
        self, client: httpx.AsyncClient, goal_concept_id: str, student_id: str
    ) -> schemas.AssessmentSession:
        """
        Generates a test based on the goal path.
        """
        # 1. Fetch the Target Path to know which concepts to test
        kg_path_url = f"{config.settings.KG_SERVICE_URL}/api/v1/path"
        try:
            path_resp = await client.get(
                kg_path_url, params={"end_id": goal_concept_id}
            )
            path_resp.raise_for_status()
            path_data = path_resp.json()  # Raw dict
            concepts = path_data.get("path", [])
        except Exception as e:
            logger.error(f"Failed to fetch path for assessment generation: {e}")
            raise

        if not concepts:
            return schemas.AssessmentSession(
                session_id=str(uuid.uuid4()), total_questions=0, questions=[]
            )

        concept_ids = [c["id"] for c in concepts]

        # 2. Fetch Questions from KGS
        # We request "Medium" difficulty (1.0 - 2.0) for placement testing.
        kg_batch_url = f"{config.settings.KG_SERVICE_URL}/api/v1/questions/batch"
        try:
            questions_resp = await client.post(
                kg_batch_url,
                json={
                    "concept_ids": concept_ids,
                    "limit_per_concept": 2,
                    "min_difficulty": 1.0,
                    "max_difficulty": 2.0,
                },
            )
            questions_resp.raise_for_status()
            questions_data = questions_resp.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch questions from KGS: {e}")
            raise

        # 3. Transform and Sanitize (Remove 'is_correct' for security)
        final_questions = []
        for item in questions_data:
            c_id = item["concept_id"]
            for q in item["questions"]:
                # Sanitize options for client
                sanitized_options = [{"text": opt["text"]} for opt in q["options"]]

                final_questions.append(
                    schemas.AssessmentQuestion(
                        id=q["id"],
                        text=q["text"],
                        options=sanitized_options,
                        difficulty=q.get("difficulty", 1.0),
                        concept_id=c_id,
                    )
                )

        return schemas.AssessmentSession(
            session_id=str(uuid.uuid4()),
            total_questions=len(final_questions),
            questions=final_questions,
        )

    async def _fetch_concept_path(
        self, client: httpx.AsyncClient, goal_id: str
    ) -> list[str]:
        url = f"{config.settings.KG_SERVICE_URL}/api/v1/path"
        resp = await client.get(url, params={"end_id": goal_id})
        data = resp.json()
        return [c["id"] for c in data.get("path", [])]

    async def _fetch_truth_data(
        self, client: httpx.AsyncClient, concept_ids: list[str]
    ) -> list[dict]:
        url = f"{config.settings.KG_SERVICE_URL}/api/v1/questions/batch"
        resp = await client.post(
            url,
            json={"concept_ids": concept_ids, "limit_per_concept": 10},
        )
        data = resp.json().get("data", [])
        if not isinstance(data, list):
            return []
        return data

    def _build_question_map(self, truth_data: list[dict]) -> dict[str, Any]:
        question_map = {}

        for item in truth_data:
            c_id = item["concept_id"]
            for q in item["questions"]:
                correct_idx = next(
                    (
                        idx
                        for idx, opt in enumerate(q["options"])
                        if opt.get("is_correct")
                    ),
                    -1,
                )

                question_map[q["id"]] = {
                    "c_id": c_id,
                    "correct_idx": correct_idx,
                    "difficulty": q.get("difficulty", 1.0),
                }
        return question_map

    def _calculate_mastery_updates(
        self,
        concept_ids: list[str],
        question_map: dict[str, Any],
        answers: dict[str, int],
    ) -> list[dict]:
        concept_stats = {cid: {"earned": 0.0, "total": 0.0} for cid in concept_ids}

        for q_id, selected_idx in answers.items():
            if q_id not in question_map:
                continue

            q = question_map[q_id]
            c_id = q["c_id"]

            difficulty = q["difficulty"]
            correct_idx = q["correct_idx"]

            concept_stats[c_id]["total"] += difficulty
            if selected_idx == correct_idx:
                concept_stats[c_id]["earned"] += difficulty

        updates = []
        for c_id, stats in concept_stats.items():
            if stats["total"] > 0:
                mastery = round(stats["earned"] / stats["total"], 2)
                updates.append({"concept_id": c_id, "mastery_level": mastery})

        return updates

    async def grade_and_update_ml(
        self, client: httpx.AsyncClient, submission: schemas.AssessmentSubmission
    ) -> dict[str, float]:
        concept_ids = await self._fetch_concept_path(client, submission.goal_concept_id)
        truth_data = await self._fetch_truth_data(client, concept_ids)
        question_map = self._build_question_map(truth_data)

        ml_updates = self._calculate_mastery_updates(
            concept_ids, question_map, submission.answers
        )

        if not ml_updates:
            return {}

        ml_url = f"{config.settings.ML_SERVICE_URL}/api/v1/knowledge/batch-update"

        try:
            resp = await client.post(
                ml_url,
                json={"student_id": str(submission.student_id), "updates": ml_updates},
            )
            resp.raise_for_status()

            data = resp.json().get("new_mastery_map", {})
            if not isinstance(data, dict):
                data = {}
            return {str(k): float(v) for k, v in data.items()}

        except Exception as e:
            logger.error(f"Failed to update ML service: {e}")
            raise HTTPException(status_code=503, detail="ML Service unavailable") from e

    async def submit_step_quiz(
        self,
        client: httpx.AsyncClient,
        submission: schemas.StepQuizSubmission,
        student_id: str,
        auth_header: str,
    ) -> schemas.StepQuizResult:
        """
        Grades a step quiz, updates ML, and persists to User Service.
        """
        # 1. Fetch Truth Data (Correct Answers) from KG
        # We reuse _fetch_truth_data but for a single concept
        truth_data = await self._fetch_truth_data(client, [submission.concept_id])
        question_map = self._build_question_map(truth_data)

        # 2. Calculate Score
        total_questions = len(question_map)
        if total_questions == 0:
            # Fallback if no questions found (shouldn't happen in valid flow)
            return schemas.StepQuizResult(
                passed=True, score=1.0, message="No questions to grade."
            )

        correct_count = 0
        for q_id, selected_idx in submission.answers.items():
            if q_id in question_map:
                if question_map[q_id]["correct_idx"] == selected_idx:
                    correct_count += 1

        score = round(correct_count / total_questions, 2)
        passed = score >= 0.6  # 60% threshold

        # 3. Update ML Service (Mastery)
        # We assume if passed, mastery is high. If failed, it decreases or stays same.
        # Ideally, ML calculates this based on specific question difficulty.
        # Here we send a raw update.
        try:
            # Construct ML updates
            ml_updates = self._calculate_mastery_updates(
                [submission.concept_id], question_map, submission.answers
            )
            if ml_updates:
                await client.post(
                    f"{config.settings.ML_SERVICE_URL}/api/v1/knowledge/batch-update",
                    json={"student_id": student_id, "updates": ml_updates},
                )
        except Exception as e:
            logger.error(f"Failed to update ML on quiz submit: {e}")
            # Non-blocking error

        # 4. Update User Service (Persistence)
        us_url = f"{config.settings.USER_SERVICE_URL}/api/v1/learning-paths/steps/{submission.step_id}/quiz-result"

        try:
            resp = await client.post(
                us_url,
                json={"score": score, "passed": passed},
                headers={"Authorization": auth_header},
            )
            resp.raise_for_status()
            # If passed, User Service returns the updated path status info.
            # We might want to fetch the full path to return to UI or just the status.
            # Let's assume we might need to refresh the path on client.
        except Exception as e:
            logger.error(f"Failed to save quiz result to User Service: {e}")
            raise HTTPException(status_code=500, detail="Failed to save results") from e

        message = (
            "Quiz Passed!" if passed else "Quiz Failed. Try reviewing the material."
        )

        return schemas.StepQuizResult(passed=passed, score=score, message=message)


assessment_service = AssessmentService()
