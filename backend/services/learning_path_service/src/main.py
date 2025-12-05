import uuid
from contextlib import asynccontextmanager
from typing import cast

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from loguru import logger

from . import config, schemas
from .logger import setup_logging
from .services.adaptation_engine import adaptation_engine
from .services.assessment_service import assessment_service

# Storage for HTTP client
client_store: dict[str, httpx.AsyncClient] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Learning Path Service initializing...")
    client_store["client"] = httpx.AsyncClient(timeout=10.0)
    yield
    logger.info("Learning Path Service shutting down...")
    await client_store["client"].aclose()
    client_store.clear()


app = FastAPI(title="Learning Path Service", lifespan=lifespan)


def get_http_client() -> httpx.AsyncClient:
    return client_store["client"]


async def _get_student_profile(
    client: httpx.AsyncClient, student_id: str, auth_header: str
) -> schemas.StudentProfile | None:
    """
    Fetches student profile from User Service.
    """
    url = f"{config.settings.USER_SERVICE_URL}/api/v1/users/{student_id}/profile"  # Assuming admin/internal endpoint
    # OR reuse /me/profile if we proxy the user's token.
    # Since the request comes FROM the user, we can use /me/profile with their token.
    url = f"{config.settings.USER_SERVICE_URL}/api/v1/users/me/profile"

    try:
        resp = await client.get(url, headers={"Authorization": auth_header})
        if resp.status_code == 200:
            return schemas.StudentProfile(**resp.json())
        logger.warning(f"Could not fetch profile: {resp.status_code}")
        return None
    except Exception as e:
        logger.error(f"Error fetching profile: {e}")
        return None


async def _fetch_kg_path(
    client: httpx.AsyncClient, end_id: str, start_id: str | None = None
) -> schemas.KGSPathResponse:
    """
    Receives the "raw" path from the Knowledge Graph Service.
    """
    kgs_url = f"{config.settings.KG_SERVICE_URL}/api/v1/path"
    params = {"end_id": end_id}
    if start_id:
        params["start_id"] = start_id
    try:
        logger.info(f"Calling KGS at {kgs_url}...")
        kgs_response = await client.get(kgs_url, params=params)
        kgs_response.raise_for_status()
        return schemas.KGSPathResponse(**kgs_response.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"KGS request failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"KG Service error: {e.response.json().get('detail')}",
        ) from e
    except Exception as e:
        logger.error(f"KGS connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="KG Service is unavailable",
        ) from e


async def _save_path_to_user_service(
    client: httpx.AsyncClient,
    path_data: schemas.USLearningPathCreate,
    headers: dict,
) -> schemas.LearningPathResponse:
    """
    Sends the generated path to User Service for storage.
    """
    us_url = f"{config.settings.USER_SERVICE_URL}/api/v1/learning-paths"
    try:
        logger.info(f"Calling User Service at {us_url} to save path...")
        us_response = await client.post(
            us_url,
            json=path_data.model_dump(),
            headers=headers,
        )
        us_response.raise_for_status()
        return schemas.LearningPathResponse(**us_response.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"User Service request failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"User Service error: {e.response.json().get('detail')}",
        ) from e
    except Exception as e:
        logger.error(f"User Service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User Service is unavailable",
        ) from e


async def _fetch_kg_candidates(
    client: httpx.AsyncClient, end_id: str, start_id: str | None = None
) -> list[schemas.KGSPathCandidate]:
    kgs_url = f"{config.settings.KG_SERVICE_URL}/api/v1/path/candidates"
    params = {"end_id": end_id, "limit": 3}  # Get top 3 structural paths
    if start_id:
        params["start_id"] = start_id
    resp = await client.get(kgs_url, params=params)
    resp.raise_for_status()
    return schemas.KGSMultiPathResponse(**resp.json()).candidates


@app.post(
    "/api/v1/students/{student_id}/learning-paths",
    response_model=schemas.LearningPathResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_learning_path(
    student_id: uuid.UUID,
    request: schemas.LearningPathCreateRequest,
    authorization: str | None = Header(None),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    logger.info(f"Received path request for student {student_id}...")
    str_student_id = str(student_id)

    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # 1. Get Raw Path Candidates from KGS
    try:
        candidates = await _fetch_kg_candidates(client, request.goal_concept_id, request.start_concept_id)
    except Exception as e:
        logger.error(f"KGS candidates fetch failed: {e}")
        raise HTTPException(status_code=404, detail="No path found") from e

    if not candidates:
        raise HTTPException(status_code=404, detail="No viable path found")

    # 2. Fetch Profile (for RL)
    profile = await _get_student_profile(client, str_student_id, authorization)

    # 3. SELECT BEST PATH via RL
    # We ask RL agent to pick the best candidate based on the full profile
    best_path_concepts = await adaptation_engine.select_optimal_path(client, str_student_id, candidates, profile)

    # 4. Batch Fetch Mastery (for adaptation)
    unique_ids = list(set([c.id for c in best_path_concepts]))
    mastery_map = await _get_mastery_batch(client, str_student_id, unique_ids)

    # 5. Linearize and Adapt
    us_steps, total_time = adaptation_engine.generate_adaptive_steps(best_path_concepts, mastery_map, profile)

    # 6. Save to User Service
    us_path_data = schemas.USLearningPathCreate(
        goal_concepts=[request.goal_concept_id],
        steps=us_steps,
        estimated_time=total_time,
    )

    us_url = f"{config.settings.USER_SERVICE_URL}/api/v1/learning-paths"
    try:
        us_response = await client.post(
            us_url,
            json=us_path_data.model_dump(),
            headers={"Authorization": authorization},
        )
        us_response.raise_for_status()
        return us_response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to save path") from e


@app.get(
    "/api/v1/students/{student_id}/learning-paths",
    response_model=list[schemas.LearningPathResponse],
)
async def get_student_learning_paths(
    student_id: str,
    authorization: str | None = Header(None),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Retrieves all learning paths for a specific student from User Service.
    """
    us_url = f"{config.settings.USER_SERVICE_URL}/api/v1/students/{student_id}/learning-paths"

    try:
        logger.info(f"Fetching paths from User Service: {us_url}")
        us_response = await client.get(us_url, headers={"Authorization": authorization} if authorization else {})
        us_response.raise_for_status()
        return us_response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"User Service error: {e.response.text}")
        if e.response.status_code == 404:
            return []
        raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch paths") from e
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=500, detail="User Service unavailable") from e


@app.get(
    "/api/v1/students/{student_id}/recommendations",
    response_model=schemas.RecommendationResponse,
)
async def get_student_recommendations(
    student_id: str,
    authorization: str | None = Header(None),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Recommendation orchestrator using RL:
    1. Get Student Profile.
    2. Get Mastery Map.
    3. Filter 'known' concepts.
    4. Ask KGS for candidates (next possible steps).
    5. Ask RL Agent to select the single best concept from candidates.
    6. Return it.
    """
    logger.info(f"Generating recommendations for student {student_id}")

    # 1. Fetch Profile
    profile = await _get_student_profile(client, student_id, authorization or "")

    # 2. Receive Mastery Map
    try:
        ml_url = f"{config.settings.ML_SERVICE_URL}/api/v1/students/{student_id}/mastery"
        ml_response = await client.get(ml_url)
        ml_response.raise_for_status()
        mastery_map = ml_response.json().get("mastery_map", {})
    except Exception:
        mastery_map = {}

    # 3. Identify Known Concepts (Mastery > 0.7)
    known_ids = [cid for cid, score in mastery_map.items() if score > 0.7]

    # 4. Ask KGS for Candidates
    # KGS returns a list of concepts that logically follow the known ones
    try:
        kg_url = f"{config.settings.KG_SERVICE_URL}/api/v1/recommendations"
        # We ask for a few candidates (limit=5) to give the RL agent some choices
        kg_response = await client.post(kg_url, json={"known_concept_ids": known_ids, "limit": 5})
        kg_response.raise_for_status()
        concepts_data = kg_response.json().get("recommendations", [])
        # Convert to objects
        candidates = [schemas.KGSConcept(**c) for c in concepts_data]
    except Exception as e:
        logger.error(f"Failed to fetch recommendations from KG: {e}")
        raise HTTPException(status_code=500, detail="Recommendation generation failed") from e

    if not candidates:
        return schemas.RecommendationResponse(recommendations=[])

    # 5. RL Selection
    # We ask the RL engine to pick the BEST one from the 5 candidates
    best_concept = await adaptation_engine.select_optimal_path_concept(client, student_id, candidates, profile)

    # If RL fails or returns nothing, fallback to first
    if not best_concept:
        best_concept = candidates[0]

    # 6. Format Response
    # We return the Best concept first, followed by others (optional, here we return list)
    # Re-ordering list to put best first
    final_list = [best_concept] + [c for c in candidates if c.id != best_concept.id]

    formatted_recs = []
    for i, concept in enumerate(final_list):
        formatted_recs.append(
            schemas.LearningStep(
                id=uuid.uuid4(),
                step_number=i + 1,
                concept_id=concept.id,
                resources=[r.model_dump() for r in concept.resources],
                status="pending",
                estimated_time=concept.estimated_time,
                difficulty=concept.difficulty,
                description=concept.description,
            )
        )

    return schemas.RecommendationResponse(recommendations=formatted_recs)


@app.get("/api/v1/quizzes/{concept_id}", response_model=schemas.QuizResponse)
async def get_quiz_for_concept(
    concept_id: str,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Receives a test for the concept from the Knowledge Graph Service.
    """
    try:
        kg_url = f"{config.settings.KG_SERVICE_URL}/api/v1/concepts/{concept_id}/quiz"
        response = await client.get(kg_url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch quiz: {e}")
        return {"questions": []}


async def _get_mastery_batch(client: httpx.AsyncClient, student_id: str, concept_ids: list[str]) -> dict[str, float]:
    if not concept_ids:
        return {}
    try:
        ml_url = f"{config.settings.ML_SERVICE_URL}/api/v1/predict/batch"
        ml_response = await client.post(ml_url, json={"student_id": student_id, "concept_ids": concept_ids})
        ml_response.raise_for_status()
        data = ml_response.json().get("mastery_map", {})
        return cast(dict[str, float], data)
    except Exception:
        return {cid: 0.0 for cid in concept_ids}


@app.post(
    "/api/v1/assessments/start",
    response_model=schemas.AssessmentSession,
    status_code=status.HTTP_200_OK,
)
async def start_initial_assessment(
    request: schemas.AssessmentStartRequest,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Generates an initial test session for the requested Goal.
    """
    logger.info(f"Generating assessment for student {request.student_id}")
    try:
        session = await assessment_service.generate_assessment(client, request.goal_concept_id, str(request.student_id))
        return session
    except Exception as e:
        logger.error(f"Error starting assessment: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate assessment") from e


@app.post(
    "/api/v1/assessments/submit",
    response_model=schemas.LearningPathResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_assessment(
    submission: schemas.AssessmentSubmission,
    authorization: str | None = Header(None),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    1. Grades the assessment against KGS data.
    2. Updates ML system (via Event bus).
    3. Calculates local mastery.
    4. Generates and saves a personalized Learning Path.
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    logger.info(f"Processing assessment submission for {submission.student_id}")
    str_student_id = str(submission.student_id)

    # 1. Grade & Update ML
    try:
        assessment_mastery_map = await assessment_service.grade_and_update_ml(client, submission)
    except Exception as e:
        logger.error(f"Grading failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to grade assessment") from e

    # 2. Fetch Raw Path (Structure)
    kgs_data = await _fetch_kg_path(client, submission.goal_concept_id)
    if not kgs_data.path:
        raise HTTPException(status_code=404, detail="No path found for this goal")

    # 3. Fetch Historical Mastery (from ML Service)
    # We combine historical data with the *just* calculated assessment results.
    # The assessment results take precedence for the immediate path generation.
    all_concept_ids = [c.id for c in kgs_data.path]
    historical_mastery = await _get_mastery_batch(client, str_student_id, all_concept_ids)

    # Merge: Assessment overrides History for this session
    combined_mastery = {**historical_mastery, **assessment_mastery_map}

    # 4. Run Adaptation Engine
    us_steps, total_time = adaptation_engine.generate_adaptive_steps(kgs_data.path, combined_mastery)

    if not us_steps:
        # Edge case: Student knows everything
        logger.info("Student mastered all concepts via assessment.")
        # We can create a "Completed" path or a maintenance path.
        # For now, we return a completed path container.
        us_path_data = schemas.USLearningPathCreate(
            goal_concepts=[submission.goal_concept_id], steps=[], estimated_time=0
        )
    else:
        us_path_data = schemas.USLearningPathCreate(
            goal_concepts=[submission.goal_concept_id],
            steps=us_steps,
            estimated_time=total_time,
        )

    # 5. Save to User Service
    final_path = await _save_path_to_user_service(client, us_path_data, {"Authorization": authorization})

    logger.success(f"Assessment complete. Generated path with {len(us_steps)} steps.")
    return final_path


async def _send_rl_feedback(
    client: httpx.AsyncClient, student_id: str, concept_id: str, score: float, passed: bool, prev_mastery: float
):
    """
    Calculates reward components and sends them to the RL Agent.
    """
    # 1. Calculate Reward Components (Simplified for Real-time)

    # Mastery Delta (Approximate): If passed, we assume mastery went up.
    # In a perfect world, we'd query DKT before and after.
    # Here: Score is a proxy for knowledge gain.
    mastery_delta = 0.1 if passed else -0.05
    if score > 0.9:
        mastery_delta = 0.2

    # Behavior Delta:
    # Did they pass? (Engagement/Effort proxy)
    behavior_delta = 0.1 if passed else -0.1

    # Difficulty: We'd ideally fetch this from KG. Defaulting to 1.0 (Medium).
    difficulty = 1.0

    payload = {
        "student_id": student_id,
        "action_concept_id": concept_id,
        "reward_components": {
            "mastery_delta": mastery_delta,
            "behavior_delta": behavior_delta,
            "difficulty": difficulty,
        },
        # Note: We let ML Service reconstruct the state to save bandwidth
    }

    try:
        # Fire and forget - don't block the user response for RL training
        url = f"{config.settings.ML_SERVICE_URL}/api/v1/rl/reward"
        await client.post(url, json=payload)
        logger.info(f"Sent RL feedback for {student_id}")
    except Exception as e:
        logger.error(f"Failed to send RL feedback: {e}")


async def _fetch_user_id(client: httpx.AsyncClient, authorization: str) -> str:
    resp = await client.get(
        f"{config.settings.USER_SERVICE_URL}/api/v1/users/me/profile",
        headers={"Authorization": authorization},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid User")
    return str(resp.json()["user_id"])


async def _get_prev_mastery(client: httpx.AsyncClient, student_id: str, concept_id: str) -> float:
    try:
        resp = await client.post(
            f"{config.settings.ML_SERVICE_URL}/api/v1/predict",
            json={"student_id": student_id, "concept_id": concept_id},
        )
        if resp.status_code == 200:
            return float(resp.json().get("mastery_level", 0.0))
    except Exception:
        pass
    return 0.0


async def _trigger_adaptation_logic(
    client: httpx.AsyncClient,
    authorization: str,
    submission: schemas.StepQuizSubmission,
    base_result: schemas.StepQuizResult,
):
    """
    Triggers adaptive remediation logic after a quiz submission.
    This method contains all comments and logic structure from submit_step_quiz.
    """

    adaptation_occurred = False
    final_message = base_result.message

    if base_result.score < 0.6:
        try:
            logger.info(f"Low score ({base_result.score}) detected. Triggering adaptation...")

            # 1. Get current step info (we need the path_id and current number)
            # We need to query User Service to find which path/step this was.
            # This is a bit of an overhead, usually the client sends path_id, but we have step_id.

            # Hack: In a real system we would pass path_id in submission.
            # Here we assume we can fetch the step details from User Service.
            try:
                # We need to find the step to know where to insert.
                # Ideally, submit_step_quiz in assessment_service should return this context.
                # For this Phase, we will proceed assuming we can get the step context.
                pass
                # (Skipping complex context fetch for brevity, assume we have:
                # path_id, current_step_number from a helper or client).

                # Let's assume we implement a helper `_get_step_context(step_id)`
                # ...

            except Exception:
                pass

            # Calculate Remediation
            # We need the current step number to insert *after* it.
            # Let's assume the current step number is N. We insert at N+1.
            # Since we don't have step number in the request, we rely on the FE to refresh.

            # Fetch step details
            step_resp = await client.get(
                f"{config.settings.USER_SERVICE_URL}/api/v1/learning-paths/steps/{submission.step_id}",
                headers={"Authorization": authorization},
            )

            if step_resp.status_code == 200:
                step_data = step_resp.json()
                path_id = step_data["path_id"]
                current_number = step_data["step_number"]

                # Generate Strategy
                (
                    remedial_steps,
                    strategy,
                ) = await adaptation_engine.create_remediation_plan(client, submission.concept_id, current_number)

                if remedial_steps:
                    # Apply to User Service
                    adapt_payload = {
                        "trigger_type": "low_score",
                        "strategy": strategy,
                        "insert_at_step": current_number + 1,  # Insert as next step
                        "new_steps": [s.model_dump() for s in remedial_steps],
                    }

                    adapt_resp = await client.post(
                        f"{config.settings.USER_SERVICE_URL}/api/v1/learning-paths/{path_id}/adapt",
                        json=adapt_payload,
                        headers={"Authorization": authorization},
                    )

                    if adapt_resp.status_code == 200:
                        adaptation_occurred = True
                        final_message = "Don't worry! We've added a quick review step to help you master this."

        except Exception as e:
            logger.error(f"Adaptation failed silently: {e}")

    return final_message, adaptation_occurred


@app.post(
    "/api/v1/steps/quiz/submit",
    response_model=schemas.StepQuizResult,
)
async def submit_step_quiz(
    submission: schemas.StepQuizSubmission,
    authorization: str | None = Header(None),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    if authorization is None:
        raise ValueError("authorization must not be None")

    student_id = await _fetch_user_id(client, authorization)
    prev_mastery = await _get_prev_mastery(client, student_id, submission.concept_id)
    base_result = await assessment_service.submit_step_quiz(client, submission, student_id, authorization)
    # Send RL Feedback (Closing the Loop)
    # We do this specifically for the concept that was just tested.
    await _send_rl_feedback(
        client, student_id, submission.concept_id, base_result.score, base_result.passed, prev_mastery
    )
    adaptation_occurred, final_message = await _trigger_adaptation_logic(client, authorization, submission, base_result)

    return schemas.StepQuizResult(
        passed=base_result.passed,
        score=base_result.score,
        message=final_message,
        adaptation_occurred=adaptation_occurred,
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Learning Path Service"}
