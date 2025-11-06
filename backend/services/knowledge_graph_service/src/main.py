from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Knowledge Graph Service")


class Concept(BaseModel):
    id: str
    name: str
    description: str
    difficulty: float
    estimated_time: int  # in minutes


FAKE_DB = {
    "c1": Concept(
        id="c1",
        name="Linear Algebra Basics",
        description="Intro to vectors",
        difficulty=3.5,
        estimated_time=120,
    ),
    "c2": Concept(
        id="c2",
        name="Python Basics",
        description="Data types and loops",
        difficulty=2.0,
        estimated_time=90,
    ),
}


@app.get("/api/v1/concepts/{concept_id}", response_model=Concept)
def get_concept_details(concept_id: str):
    if concept_id not in FAKE_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found"
        )
    return FAKE_DB[concept_id]


@app.get("/health")
def health_check():
    return {"status": "ok"}
