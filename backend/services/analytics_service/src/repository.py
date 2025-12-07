from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from . import schemas
from .database import get_mongo_events
from .math_engine import BehavioralMathEngine


class AnalyticsRepository:
    def __init__(self, pg_db: Session):
        self.pg_db = pg_db
        self.mongo_collection = get_mongo_events()

    def get_knowledge_stats(self, student_id: str):
        """
        Calculates the average knowledge and number of topics studied in Postgres.
        """
        # 1. Average Mastery & Count
        stats_query = text("""
            SELECT
                COALESCE(AVG(mastery_level), 0) as avg_mastery,
                COUNT(CASE WHEN mastery_level > 0.8 THEN 1 END) as learned_count
            FROM knowledge_states
            WHERE student_id = :uid
        """)
        result = self.pg_db.execute(stats_query, {"uid": student_id}).fetchone()

        # 2. Weakest Concepts (Bottom 3, but only if attempted)
        weakness_query = text("""
            SELECT concept_id, mastery_level
            FROM knowledge_states
            WHERE student_id = :uid AND mastery_level < 0.6 AND mastery_level > 0
            ORDER BY mastery_level ASC
            LIMIT 3
        """)
        weaknesses = self.pg_db.execute(weakness_query, {"uid": student_id}).fetchall()

        return {
            "avg": result[0],
            "learned": result[1],
            "weaknesses": [schemas.WeaknessItem(concept_id=row[0], mastery_level=row[1]) for row in weaknesses],
        }

    async def get_activity_stats(self, student_id: str) -> dict:
        """
        Counts strikes and activity over the last 7 days from MongoDB.
        """
        today = datetime.now(UTC).date()
        seven_days_ago = datetime.now(UTC) - timedelta(days=7)

        # 1. Activity Chart (Aggregation)
        pipeline = [
            {"$match": {"student_id": student_id, "timestamp": {"$gte": seven_days_ago.isoformat()}}},
            {
                "$project": {
                    "date_str": {"$substr": ["$timestamp", 0, 10]}  # Extract YYYY-MM-DD
                }
            },
            {"$group": {"_id": "$date_str", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]

        cursor = self.mongo_collection.aggregate(pipeline)
        activity_map = {doc["_id"]: doc["count"] async for doc in cursor}

        # Fill zeros for missing days
        activity_list = []
        for i in range(7):
            d = (seven_days_ago + timedelta(days=i + 1)).date().isoformat()
            activity_list.append(schemas.ActivityPoint(date=d, count=activity_map.get(d, 0)))

        # 2. Simple Streak Calculation (MVP)
        # Get unique days of activity for the last 30 days
        streak = 0
        check_date = today

        # This is simplified logic. In reality, this is done through more complex aggregation or Redis bitfields.
        # We check “yesterday,” “the day before yesterday,” etc.
        # For MVP, we will simply return the number of days of activity per week as a “streak trend.”
        current_week_activity = sum(a.count for a in activity_list)
        simulated_streak = min(current_week_activity, 7)  # Hack for demo

        return {"streak": simulated_streak, "chart": activity_list}

    async def compute_behavioral_profile(self, student_id: str) -> dict:
        """
        Fetches events and applies math engine.
        """
        # Fetch last 100 events for this student
        cursor = self.mongo_collection.find({"student_id": student_id}).sort("timestamp", -1).limit(100)
        events = [doc async for doc in cursor]

        # Calculate Vectors
        p_idx = BehavioralMathEngine.calculate_procrastination_index(events)
        g_score = BehavioralMathEngine.calculate_gaming_score(events)
        e_score = BehavioralMathEngine.calculate_engagement_score(events)
        h_rate = BehavioralMathEngine.calculate_hint_rate(events)
        err_rate = BehavioralMathEngine.calculate_recent_error_rate(events)

        return {
            "student_id": student_id,
            "procrastination_index": round(p_idx, 4),
            "gaming_score": round(g_score, 4),
            "engagement_score": round(e_score, 4),
            "hint_rate": round(h_rate, 4),
            "error_rate": round(err_rate, 4),
        }
