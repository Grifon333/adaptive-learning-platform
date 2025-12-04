from uuid import UUID

from pydantic import BaseModel


class WeaknessItem(BaseModel):
    concept_id: str
    mastery_level: float


class ActivityPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class DashboardData(BaseModel):
    student_id: str
    average_mastery: float
    total_concepts_learned: int  # mastery > 0.8
    current_streak: int
    weakest_concepts: list[WeaknessItem]
    activity_last_7_days: list[ActivityPoint]


class BehavioralUpdatePayload(BaseModel):
    student_id: UUID
    procrastination_index: float
    gaming_score: float
    engagement_score: float
