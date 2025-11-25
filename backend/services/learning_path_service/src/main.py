import uuid
from contextlib import asynccontextmanager
from typing import cast

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, status
from loguru import logger

from . import config, schemas
from .logger import setup_logging

# Storage for HTTP client
client_store: dict[str, httpx.AsyncClient] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialization at startup
    setup_logging()
    logger.info("Learning Path Service initializing...")
    client_store["client"] = httpx.AsyncClient(timeout=10.0)
    yield
    # Cleanup at shutdown
    logger.info("Learning Path Service shutting down...")
    await client_store["client"].aclose()
    client_store.clear()


app = FastAPI(title="Learning Path Service", lifespan=lifespan)


def get_http_client() -> httpx.AsyncClient:
    """FastAPI dependency to provide the HTTP client."""
    return client_store["client"]


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


async def _get_mastery_batch(
    client: httpx.AsyncClient, student_id: str, concept_ids: list[str]
) -> dict[str, float]:
    """
    Fetches mastery levels for multiple concepts in ONE request.
    Returns: {concept_id: mastery_level}
    """
    if not concept_ids:
        return {}

    try:
        ml_url = f"{config.settings.ML_SERVICE_URL}/api/v1/predict/batch"
        ml_response = await client.post(
            ml_url, json={"student_id": student_id, "concept_ids": concept_ids}
        )
        ml_response.raise_for_status()
        data = ml_response.json().get("mastery_map", {})
        return cast(dict[str, float], data)
    except Exception as e:
        logger.error(f"Failed to query ML service batch: {e}")
        # Fallback: assume zero knowledge on error to allow path generation
        return {cid: 0.0 for cid in concept_ids}


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
        logger.error(
            f"User Service request failed: {e.response.status_code} {e.response.text}"
        )
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
    """
    Main orchestration endpoint.
    1. Receives a request from the client (Flutter).
    2. Calls the Knowledge Graph Service (KGS) to obtain the route.
    3. Transforms the data.
    4. Calls the User Service (US) to save the route.
    5. Returns the saved route to the client.
    """
    logger.info(f"Received path request for student {student_id}...")
    str_student_id = str(student_id)

    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # 1. Get Raw Path from KGS
    kgs_data = await _fetch_kg_path(
        client, request.goal_concept_id, request.start_concept_id
    )

    if not kgs_data.path:
        raise HTTPException(status_code=404, detail="No path found")

    # 2. Apply Adaptive Logic (Transform Loop)
    logger.info("Applying adaptive filtering based on ML predictions...")

    all_concept_ids = [c.id for c in kgs_data.path]
    mastery_map = await _get_mastery_batch(client, str_student_id, all_concept_ids)

    us_steps = []
    total_time = 0
    current_step_num = 1

    for concept in kgs_data.path:
        # 2.1 Ask the ML service about the student's level of knowledge of this concept.
        mastery_level = mastery_map.get(concept.id, 0.0)
        logger.info(
            f"Concept {concept.name} ({concept.id[:8]}...): Mastery {mastery_level:.2f}"
        )

        resources_payload = [res.model_dump() for res in concept.resources]

        # --- LOGIC BRANCHING ---

        # A. High level of knowledge -> Auto-complete
        if mastery_level > 0.8:
            us_steps.append(
                schemas.USLearningStepCreate(
                    step_number=current_step_num,
                    concept_id=concept.id,
                    resources=resources_payload,
                    estimated_time=concept.estimated_time,
                    difficulty=concept.difficulty,
                    status="completed",
                )
            )
            current_step_num += 1
            total_time += concept.estimated_time
            continue

        # B. Remedial Logic (Struggling: 0.0 < Mastery < 0.6)
        if 0.0 < mastery_level < 0.6:
            logger.warning(
                f"Struggle detected on {concept.name}. Generating Remedial Step."
            )

            # --- 1. REMEDIAL STEP (Additional step) ---

            # AI TODO: Here, we will refer to Gemini in the future:
            # reason = await ai_service.analyze_error(student_id, concept.id)
            ai_instruction = (
                f"Review the material on '{concept.name}' again. Focus on the basics."
            )

            us_steps.append(
                schemas.USLearningStepCreate(
                    step_number=current_step_num,  # The number is the same as the main one (hide it visually)
                    concept_id=concept.id,
                    resources=resources_payload,  # Maybe only give part of the resources or others
                    estimated_time=int(concept.estimated_time * 0.5),
                    difficulty=concept.difficulty * 0.7,
                    status="pending",
                    is_remedial=True,  # Flag for visualization
                    description=ai_instruction,  # Reason
                )
            )
            total_time += int(concept.estimated_time * 0.5)

            # --- 2. MAIN STEP (Main step) ---
            # He follows suit, but he is blocked (pending) until we pass remedial.

            us_steps.append(
                schemas.USLearningStepCreate(
                    step_number=current_step_num,
                    concept_id=concept.id,
                    resources=resources_payload,
                    estimated_time=concept.estimated_time,
                    difficulty=concept.difficulty,
                    status="pending",  # Awaiting remedial
                    is_remedial=False,
                    description=concept.description,
                )
            )
            current_step_num += 1
            total_time += concept.estimated_time
            continue

        # C. Regular step (or the one following Remedial)
        us_steps.append(
            schemas.USLearningStepCreate(
                step_number=current_step_num,
                concept_id=concept.id,
                resources=resources_payload,
                estimated_time=concept.estimated_time,
                difficulty=concept.difficulty,
                status="pending",
            )
        )
        current_step_num += 1
        total_time += concept.estimated_time

    if not us_steps:
        # If the student knows EVERYTHING, we return a special answer or create an empty path.
        logger.info("Student already knows the entire path!")
        # In reality, maybe return a message about the completion of the course here.

    # 3. Prepare Payload
    us_path_data = schemas.USLearningPathCreate(
        goal_concepts=[request.goal_concept_id],
        steps=us_steps,
        estimated_time=total_time,
    )

    # 4. Save to User Service
    final_path = await _save_path_to_user_service(
        client, us_path_data, {"Authorization": authorization}
    )

    logger.success(f"Path adapted and saved. Total steps: {len(us_steps)}")
    return final_path


@app.get(
    "/api/v1/students/{student_id}/recommendations",
    response_model=schemas.RecommendationResponse,
)
async def get_student_recommendations(
    student_id: str,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Recommendation orchestrator:
    1. Get a knowledge map from ML Service.
    2. Filter out concepts that the student knows well (mastery > 0.7).
    3. Send the list of “known” IDs to KG Service.
    4. Get a list of recommended concepts.
    5. Format for the client.
    """
    logger.info(f"Generating recommendations for student {student_id}")

    # 1. Recieve Mastery Map
    try:
        ml_url = (
            f"{config.settings.ML_SERVICE_URL}/api/v1/students/{student_id}/mastery"
        )
        ml_response = await client.get(ml_url)
        ml_response.raise_for_status()
        mastery_map = ml_response.json().get("mastery_map", {})
    except Exception as e:
        logger.error(f"Failed to fetch mastery: {e}")
        mastery_map = {}

    # 2. Formatting a list of known concepts
    # Consider a concept to be known if the confidence level is > 70%
    known_ids = [cid for cid, score in mastery_map.items() if score > 0.7]

    # 3. Ask Knowledge Graph
    try:
        kg_url = f"{config.settings.KG_SERVICE_URL}/api/v1/recommendations"
        kg_response = await client.post(
            kg_url, json={"known_concept_ids": known_ids, "limit": 5}
        )
        kg_response.raise_for_status()
        concepts_data = kg_response.json().get("recommendations", [])
    except Exception as e:
        logger.error(f"Failed to fetch recommendations from KG: {e}")
        raise HTTPException(
            status_code=500, detail="Recommendation generation failed"
        ) from e

    # 4. Formatting the response
    formatted_recs = []
    for i, concept in enumerate(concepts_data):
        # Convert KG format to LearningStep format for front-end unification
        formatted_recs.append(
            schemas.LearningStep(
                id=uuid.uuid4(),  # Generate a temporary ID for the UI
                step_number=i + 1,
                concept_id=concept["id"],
                resources=concept.get("resources", []),
                status="pending",
                estimated_time=concept.get("estimated_time"),
                difficulty=concept.get("difficulty"),
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


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Learning Path Service"}
