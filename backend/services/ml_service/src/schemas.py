from typing import Any
from uuid import UUID

from pydantic import BaseModel


class PredictionRequest(BaseModel):
    student_id: UUID
    concept_id: str


class BatchPredictionRequest(BaseModel):
    student_id: UUID
    concept_ids: list[str]


class PredictionResponse(BaseModel):
    student_id: UUID
    concept_id: str
    mastery_level: float
    confidence: float = 0.5


class BatchPredictionResponse(BaseModel):
    student_id: UUID
    mastery_map: dict[str, float]  # {concept_id: mastery_level}


class KnowledgeUpdateItem(BaseModel):
    concept_id: str
    mastery_level: float


class BatchKnowledgeUpdateRequest(BaseModel):
    student_id: UUID
    updates: list[KnowledgeUpdateItem]


class BatchKnowledgeUpdateResponse(BaseModel):
    student_id: UUID
    updated_count: int
    new_mastery_map: dict[str, float]


class BehavioralProfileUpdate(BaseModel):
    student_id: UUID
    procrastination_index: float
    gaming_score: float
    engagement_score: float


class BehavioralProfileResponse(BaseModel):
    student_id: UUID
    profile: dict[str, float]


class RLRecommendationRequest(BaseModel):
    student_id: UUID
    valid_concept_ids: list[str]
    student_profile: dict[str, Any]  # Contains cognitive & prefs


class RLRecommendationResponse(BaseModel):
    recommended_concept_id: str
    exploration_flag: bool = False


class RLRewardRequest(BaseModel):
    student_id: UUID
    prev_state_vector: list[float] | None = None  # Optional for stateless update
    action_concept_id: str
    reward_components: dict[str, float]  # mastery_delta, behavior_delta, etc.
