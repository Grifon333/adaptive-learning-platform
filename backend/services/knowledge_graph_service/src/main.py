import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from loguru import logger
from neo4j import AsyncSession
from neo4j.exceptions import Neo4jError

from . import schemas
from .database import close_driver, get_db_session, init_driver
from .logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Knowledge Graph Service initializing...")
    await init_driver()
    yield
    # Shutdown
    logger.info("Knowledge Graph Service shutting down...")
    await close_driver()


app = FastAPI(title="Knowledge Graph Service", lifespan=lifespan)


@app.post(
    "/api/v1/concepts",
    response_model=schemas.Concept,
    status_code=status.HTTP_201_CREATED,
)
async def create_concept(
    concept: schemas.ConceptCreate, db: AsyncSession = Depends(get_db_session)
):
    """
    Creates a new 'Concept' node in Neo4j.
    """
    concept_id = str(uuid.uuid4())
    query = (
        "CREATE (c:Concept { "
        "id: $id, "
        "name: $name, "
        "description: $description, "
        "difficulty: $difficulty, "
        "estimated_time: $estimated_time "
        "}) RETURN c"
    )

    try:
        result = await db.run(
            query,
            {
                "id": concept_id,
                "name": concept.name,
                "description": concept.description,
                "difficulty": concept.difficulty,
                "estimated_time": concept.estimated_time,
            },
        )
        record = await result.single()

        if record is None:
            logger.error("Failed to create concept node in Neo4j.")
            raise HTTPException(status_code=500, detail="Could not create concept")

        node = record[0]
        node_properties = dict(node)
        logger.success(f"Concept created with ID: {concept_id}")
        return schemas.Concept(**node_properties)

    except Neo4jError as e:
        logger.error(f"Neo4j error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/concepts/{concept_id}", response_model=schemas.Concept)
async def get_concept_details(
    concept_id: str, db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves concept details by its 'id'
    """
    query = "MATCH (c:Concept {id: $id}) RETURN c"

    try:
        result = await db.run(query, {"id": concept_id})
        record = await result.single()

        if record is None:
            logger.warning(f"Concept with ID {concept_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept not found",
            )

        node = record[0]
        node_properties = dict(node)
        return schemas.Concept(**node_properties)

    except Neo4jError as e:
        logger.error(f"Neo4j error getting concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/relationships", status_code=status.HTTP_201_CREATED)
async def create_relationship(
    rel: schemas.RelationshipCreate, db: AsyncSession = Depends(get_db_session)
):
    """
    Creates a relationship between two concepts.
    """
    query = (
        f"MATCH (a:Concept {{id: $start_id}}), (b:Concept {{id: $end_id}}) "
        f"CREATE (a)-[r:{rel.rel_type}]->(b) "
        f"RETURN type(r) AS rel_type"
    )

    try:
        result = await db.run(
            query,
            {
                "start_id": rel.start_concept_id,
                "end_id": rel.end_concept_id,
            },
        )
        record = await result.single()

        if record is None:
            logger.error(
                "Could not create relationship. One or both concepts not found."
            )
            raise HTTPException(
                status_code=404, detail="One or both concepts not found"
            )

        rel_type = record["rel_type"]
        logger.success(
            f"Created relationship '{rel_type}' from {rel.start_concept_id} to {rel.end_concept_id}"
        )
        return {"status": "created", "type": rel_type}

    except Neo4jError as e:
        logger.error(f"Neo4j error creating relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/path", response_model=schemas.PathResponse)
async def get_shortest_path(
    start_id: str, end_id: str, db: AsyncSession = Depends(get_db_session)
):
    """
    Finds the shortest prerequisite path between two concepts.
    """
    query = (
        "MATCH (start:Concept {id: $start_id}), (end:Concept {id: $end_id}), "
        "p = shortestPath((start)-[:PREREQUISITE*]->(end)) "
        "RETURN nodes(p) AS path_nodes"
    )
    try:
        result = await db.run(query, {"start_id": start_id, "end_id": end_id})
        record = await result.single()

        if record is None or record["path_nodes"] is None:
            logger.warning(f"No prerequisite path found from {start_id} to {end_id}")
            return schemas.PathResponse(path=[])

        # Convert the list of nodes into a list of Pydantic models
        path_nodes = [schemas.Concept(**dict(node)) for node in record["path_nodes"]]

        return schemas.PathResponse(path=path_nodes)

    except Neo4jError as e:
        logger.error(f"Neo4j error finding path: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Knowledge Graph Service"}
