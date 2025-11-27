from pydantic import BaseModel
from typing import List, Dict
from datetime import date

class WeaknessItem(BaseModel):
    concept_id: str
    mastery_level: float

class ActivityPoint(BaseModel):
    date: str # YYYY-MM-DD
    count: int

class DashboardData(BaseModel):
    student_id: str
    average_mastery: float
    total_concepts_learned: int # mastery > 0.8
    current_streak: int
    weakest_concepts: List[WeaknessItem]
    activity_last_7_days: List[ActivityPoint]
