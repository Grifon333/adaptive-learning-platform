from contextlib import asynccontextmanager

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


@app.post(
    "/api/v1/students/{student_id}/learning-paths",
    response_model=schemas.LearningPathResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_learning_path(
    student_id: str,
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

    if authorization is None:
        logger.warning("Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    headers = {"Authorization": authorization}

    # Step 1 & 2: Call Knowledge Graph Service
    kgs_url = f"{config.settings.KG_SERVICE_URL}/api/v1/path"
    try:
        logger.info(f"Calling KGS at {kgs_url}...")
        kgs_response = await client.get(
            kgs_url,
            params={
                "start_id": request.start_concept_id,
                "end_id": request.goal_concept_id,
            },
        )
        kgs_response.raise_for_status()  # Check for 4xx/5xx
        kgs_data = schemas.KGSPathResponse(**kgs_response.json())

    except httpx.HTTPStatusError as e:
        logger.error(f"KGS request failed: {e.response.status_code} {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Knowledge Graph Service error: {e.response.json().get('detail')}",
        ) from e
    except Exception as e:
        logger.error(f"KGS connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge Graph Service is unavailable",
        ) from e

    if not kgs_data.path:
        logger.warning("KGS returned an empty path.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No path found between the specified concepts",
        )

    logger.info(f"KGS returned path with {len(kgs_data.path)} steps.")

    # Step 3: Transform data for User Service
    us_steps = []
    total_time = 0
    for i, concept in enumerate(kgs_data.path):
        us_steps.append(
            schemas.USLearningStepCreate(
                step_number=i + 1,
                concept_id=concept.id,
                resource_ids=["fake-res-1", "fake-res-2"],  # TODO: Get real resources
                estimated_time=concept.estimated_time,
                difficulty=concept.difficulty,
            )
        )
        total_time += concept.estimated_time

    us_path_data = schemas.USLearningPathCreate(
        goal_concepts=[request.goal_concept_id],
        steps=us_steps,
        estimated_time=total_time,
    )

    # Step 4 & 5: Call User Service to save the path
    us_url = f"{config.settings.USER_SERVICE_URL}/api/v1/learning-paths"
    try:
        logger.info(f"Calling User Service at {us_url} to save path...")
        us_response = await client.post(
            us_url,
            json=us_path_data.model_dump(),
            headers=headers,  # Passing the user token!
        )
        us_response.raise_for_status()

        # Return the final result
        final_path = schemas.LearningPathResponse(**us_response.json())
        logger.success(f"Successfully created and saved path {final_path.id}")
        return final_path

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


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Learning Path Service"}
