from fastapi import FastAPI, status
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="Learning Path Service")


class LearningPathRequest(BaseModel):
    goal_concepts: List[str]


class LearningPathResponse(BaseModel):
    path_id: str
    student_id: str
    goal_concepts: List[str]
    steps: List[Dict[str, Any]]
    estimated_total_time: int
    average_difficulty: float


@app.post(
    "/api/v1/students/{student_id}/learning-paths",
    response_model=LearningPathResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_learning_path(student_id: str, request: LearningPathRequest):
    fake_path = {
        "path_id": "fake-path-uuid-123",
        "student_id": student_id,
        "goal_concepts": request.goal_concepts,
        "steps": [
            {
                "step_number": 1,
                "concept_id": "c1",
                "concept_name": "Linear Algebra Basics",
                "resources": [
                    {"resource_id": "r1", "type": "video", "title": "Intro to Vectors"}
                ],
            },
            {
                "step_number": 2,
                "concept_id": "c2",
                "concept_name": "Python Basics",
                "resources": [
                    {"resource_id": "r3", "type": "text", "title": "Python Data Types"}
                ],
            },
        ],
        "estimated_total_time": 120,
        "average_difficulty": 3.00,
    }
    return fake_path


@app.get("/health")
def health_check():
    return {"status": "ok"}
