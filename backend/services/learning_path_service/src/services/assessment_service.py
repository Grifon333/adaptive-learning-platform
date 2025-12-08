import uuid
from datetime import UTC, datetime
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
            path_resp = await client.get(kg_path_url, params={"end_id": goal_concept_id})
            path_resp.raise_for_status()
            path_data = path_resp.json()  # Raw dict
            concepts = path_data.get("path", [])
        except Exception as e:
            logger.error(f"Failed to fetch path for assessment generation: {e}")
            raise

        if not concepts:
            return schemas.AssessmentSession(session_id=str(uuid.uuid4()), total_questions=0, questions=[])

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

    async def _fetch_concept_path(self, client: httpx.AsyncClient, goal_id: str) -> list[str]:
        url = f"{config.settings.KG_SERVICE_URL}/api/v1/path"
        resp = await client.get(url, params={"end_id": goal_id})
        data = resp.json()
        return [c["id"] for c in data.get("path", [])]

    async def _fetch_truth_data(self, client: httpx.AsyncClient, concept_ids: list[str], limit: int = 10) -> list[dict]:
        """
        Fetches truth data for grading.
        """
        url = f"{config.settings.KG_SERVICE_URL}/api/v1/questions/batch"
        resp = await client.post(url, json={"concept_ids": concept_ids, "limit_per_concept": limit})
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
                    (idx for idx, opt in enumerate(q["options"]) if opt.get("is_correct")),
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

        ml_updates = self._calculate_mastery_updates(concept_ids, question_map, submission.answers)

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
        truth_data = await self._fetch_truth_data(client, [submission.concept_id], limit=20)
        question_map = self._build_question_map(truth_data)

        # 2. Calculate Score
        total_questions = len(question_map)
        if total_questions == 0:
            # Fallback if no questions found (shouldn't happen in valid flow)
            return schemas.StepQuizResult(passed=True, score=1.0, message="No questions to grade.")

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
            ml_updates = self._calculate_mastery_updates([submission.concept_id], question_map, submission.answers)
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

        message = "Quiz Passed!" if passed else "Quiz Failed. Try reviewing the material."

        return schemas.StepQuizResult(passed=passed, score=score, message=message)

    async def start_adaptive_assessment(
        self, client: httpx.AsyncClient, student_id: str, goal_concept_id: str
    ) -> schemas.AdaptiveResponse:
        # 1. Initialize State
        state = schemas.AdaptiveSessionState(
            student_id=uuid.UUID(student_id),
            goal_concept_id=goal_concept_id,
            start_time=datetime.now(UTC).isoformat(),
            history=[],
        )

        # 2. Get Initial Question (Target Difficulty 5.0 - Average)
        return await self._fetch_next_adaptive_step(client, state, target_diff=5.0)

    async def submit_adaptive_answer(
        self, client: httpx.AsyncClient, req: schemas.AdaptiveSubmitRequest, auth_header: str
    ) -> schemas.AdaptiveResponse:
        state = req.session_state
        last_q = state.current_question

        if not last_q:
            raise HTTPException(status_code=400, detail="No active question in state")

        # 1. Grade the Answer
        # In a secure implementation, we'd verify against KG.
        # For MVP, assuming the client sent back the state containing the options we gave them.
        # We need to re-fetch truth or trust the options if we embed 'is_correct' (We sanitized it earlier).
        # Let's fetch the truth briefly to be safe.
        truth_data = await self._fetch_truth_data(client, [last_q.concept_id], limit=100)
        q_truth = next((q for item in truth_data for q in item["questions"] if q["id"] == last_q.id), None)

        if not q_truth:
            logger.error(f"Verification failed. QID: {last_q.id} not found in {len(truth_data)} concepts.")
            raise HTTPException(status_code=500, detail="Question verification failed")

        correct_idx = next((i for i, o in enumerate(q_truth["options"]) if o.get("is_correct")), -1)
        is_correct = req.answer_index == correct_idx

        logger.info(
            f"Grading Q={last_q.id}: StudentIdx={req.answer_index}, CorrectIdx={correct_idx}, "
            f"IsCorrect={is_correct}. Options={q_truth['options']}"
        )

        # 2. Update History
        state.history.append({"question_id": last_q.id, "difficulty": last_q.difficulty, "correct": is_correct})

        # 3. Call ML Service (IRT Engine)
        ml_url = f"{config.settings.ML_SERVICE_URL}/api/v1/irt/evaluate"
        ml_resp = await client.post(ml_url, json={"history": state.history})
        ml_resp.raise_for_status()
        irt_data = ml_resp.json()

        # 4. Check Stop Condition
        if irt_data["stop_test"] or len(state.history) >= 15:
            # FINISH
            final_mastery = irt_data["current_mastery"]

            # Save to ML Service (Batch Update)
            # We credit all concepts in the goal path with this estimated mastery
            path_concepts = await self._fetch_concept_path(client, state.goal_concept_id)
            updates = [{"concept_id": c, "mastery_level": final_mastery} for c in path_concepts]

            await client.post(
                f"{config.settings.ML_SERVICE_URL}/api/v1/knowledge/batch-update",
                json={"student_id": str(state.student_id), "updates": updates},
            )

            logger.info(f"Adaptive test complete. Mastery: {final_mastery}. Generating path...")

            # Fetch Raw Path from KG
            from .adaptation_engine import adaptation_engine  # Local import to avoid circular dependency

            kg_path_url = f"{config.settings.KG_SERVICE_URL}/api/v1/path"
            path_resp = await client.get(kg_path_url, params={"end_id": state.goal_concept_id})
            kgs_path_data = path_resp.json().get("path", [])
            kgs_concepts = [schemas.KGSConcept(**c) for c in kgs_path_data]

            # Construct Mastery Map (All concepts get the estimated mastery)
            mastery_map = {c.id: final_mastery for c in kgs_concepts}

            # Generate Personalized Steps
            # We pass 'None' for profile as we might not have it cached, or fetch it if needed.
            # For now, standard adaptation is fine.
            us_steps, total_time = adaptation_engine.generate_adaptive_steps(kgs_concepts, mastery_map)

            # Prepare payload for User Service
            us_path_data = schemas.USLearningPathCreate(
                goal_concepts=[state.goal_concept_id],
                steps=us_steps,
                estimated_time=total_time,
            )

            # Save to User Service
            us_url = f"{config.settings.USER_SERVICE_URL}/api/v1/learning-paths"
            us_response = await client.post(
                us_url,
                json=us_path_data.model_dump(),
                headers={"Authorization": auth_header},  # Need auth header passed through
            )
            us_response.raise_for_status()
            created_path = schemas.LearningPathResponse(**us_response.json())

            return schemas.AdaptiveResponse(
                session_state=state,
                completed=True,
                final_mastery=final_mastery,
                message="Assessment Complete",
                created_learning_path=created_path,  # Return the path
            )

        # 5. Fetch Next Question
        return await self._fetch_next_adaptive_step(client, state, irt_data["next_difficulty_target"])

    async def _fetch_next_adaptive_step(
        self, client: httpx.AsyncClient, state: schemas.AdaptiveSessionState, target_diff: float
    ) -> schemas.AdaptiveResponse:
        path_concepts = await self._fetch_concept_path(client, state.goal_concept_id)
        used_ids = [h["question_id"] for h in state.history]

        kg_url = f"{config.settings.KG_SERVICE_URL}/api/v1/questions/adaptive"
        kg_resp = await client.post(
            kg_url,
            json={"concept_ids": path_concepts, "target_difficulty": target_diff, "exclude_question_ids": used_ids},
        )

        if kg_resp.status_code != 200 or not kg_resp.json():
            # Graceful exit if no questions remain
            return schemas.AdaptiveResponse(
                session_state=state, completed=True, message="No more suitable questions found."
            )

        q_raw = kg_resp.json()

        # Sanitize options for client
        options = [{"text": o["text"], "id": i} for i, o in enumerate(q_raw["options"])]

        assigned_concept_id = q_raw.get("concept_id")
        if not assigned_concept_id:
            logger.warning(f"KG Service did not return concept_id for question {q_raw.get('id')}. using fallback.")
            assigned_concept_id = path_concepts[0]

        next_q = schemas.AssessmentQuestion(
            id=q_raw["id"],
            text=q_raw["text"],
            options=options,
            concept_id=assigned_concept_id,
            difficulty=q_raw.get("difficulty", target_diff),
        )

        state.current_question = next_q
        return schemas.AdaptiveResponse(session_state=state)


assessment_service = AssessmentService()
