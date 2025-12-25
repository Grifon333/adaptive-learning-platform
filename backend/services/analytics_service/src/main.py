import httpx
from fastapi import Depends, FastAPI, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from . import schemas
from .config import settings
from .database import get_pg_session
from .repository import AnalyticsRepository

app = FastAPI(title="Analytics Service")


@app.get("/api/v1/analytics/dashboard/{student_id}", response_model=schemas.DashboardData)
async def get_student_dashboard(student_id: str, db: Session = Depends(get_pg_session)):
    logger.info(f"Generating dashboard for {student_id}")

    repo = AnalyticsRepository(db)

    try:
        # Synchronous query to Postgres
        pg_stats = repo.get_knowledge_stats(student_id)

        # Asynchronous request to Mongo
        mongo_stats = await repo.get_activity_stats(student_id)

        return schemas.DashboardData(
            student_id=student_id,
            average_mastery=pg_stats["avg"],
            total_concepts_learned=pg_stats["learned"],
            current_streak=mongo_stats["streak"],
            weakest_concepts=pg_stats["weaknesses"],
            activity_last_7_days=mongo_stats["chart"],
        )
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard") from e


@app.post("/api/v1/analytics/calculate-behavior/{student_id}")
async def calculate_and_push_behavior(student_id: str, db: Session = Depends(get_pg_session)):
    """
    Triggers the calculation of B_t and pushes it to ML Service.
    """
    repo = AnalyticsRepository(db)

    # 1. Compute
    behavior_data = await repo.compute_behavioral_profile(student_id)

    # 2. Push to ML Service
    ml_url = f"{settings.ML_SERVICE_URL}/api/v1/behavior/profiles"  # Ensure config has this URL

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(ml_url, json=behavior_data)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to sync with ML Service: {e}")
            raise HTTPException(status_code=500, detail="Sync failed") from e

    return {"status": "updated", "data": behavior_data}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Analytics Service"}
