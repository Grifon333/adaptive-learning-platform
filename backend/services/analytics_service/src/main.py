from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from .database import get_pg_session
from .repository import AnalyticsRepository
from . import schemas

app = FastAPI(title="Analytics Service")

@app.get(
    "/api/v1/analytics/dashboard/{student_id}",
    response_model=schemas.DashboardData
)
async def get_student_dashboard(
    student_id: str,
    db: Session = Depends(get_pg_session)
):
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
            activity_last_7_days=mongo_stats["chart"]
        )
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Analytics Service"}
