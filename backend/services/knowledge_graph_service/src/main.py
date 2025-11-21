import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from loguru import logger
from neo4j import AsyncSession

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


# --- Concept Endpoints ---


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
            raise HTTPException(status_code=500, detail="Could not create concept")

        node = record[0]
        # Повертаємо пустий список ресурсів для нової концепції
        return schemas.Concept(**dict(node), resources=[])

    except Exception as e:
        logger.error(f"Error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/concepts/{concept_id}", response_model=schemas.Concept)
async def get_concept_details(
    concept_id: str, db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves concept details by its 'id'
    """
    query = (
        "MATCH (c:Concept {id: $id}) "
        "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
        "RETURN c, collect(r) as resources"
    )

    try:
        result = await db.run(query, {"id": concept_id})
        record = await result.single()

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept not found",
            )

        concept_node = record["c"]
        resource_nodes = record["resources"]

        resources_data = [schemas.Resource(**dict(r)) for r in resource_nodes if r]

        return schemas.Concept(**dict(concept_node), resources=resources_data)

    except Exception as e:
        logger.error(f"Error getting concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Resource Endpoints (NEW) ---


@app.post(
    "/api/v1/resources",
    response_model=schemas.Resource,
    status_code=status.HTTP_201_CREATED,
)
async def create_resource(
    resource: schemas.ResourceCreate, db: AsyncSession = Depends(get_db_session)
):
    """
    Creates a new learning resource node.
    """
    res_id = str(uuid.uuid4())
    query = (
        "CREATE (r:Resource { "
        "id: $id, "
        "title: $title, "
        "type: $type, "
        "url: $url, "
        "duration: $duration "
        "}) RETURN r"
    )

    try:
        result = await db.run(
            query,
            {
                "id": res_id,
                "title": resource.title,
                "type": resource.type,
                "url": resource.url,
                "duration": resource.duration,
            },
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=500, detail="Failed to create resource")

        return schemas.Resource(**dict(record["r"]))
    except Exception as e:
        logger.error(f"Error creating resource: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/concepts/{concept_id}/resources", status_code=status.HTTP_200_OK)
async def add_resource_to_concept(
    concept_id: str, resource_id: str, db: AsyncSession = Depends(get_db_session)
):
    """
    Links an existing resource to a concept via HAS_RESOURCE relationship.
    """
    query = (
        "MATCH (c:Concept {id: $cid}), (r:Resource {id: $rid}) "
        "MERGE (c)-[:HAS_RESOURCE]->(r) "
        "RETURN c, r"
    )
    try:
        result = await db.run(query, {"cid": concept_id, "rid": resource_id})
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Concept or Resource not found")

        return {"message": "Resource linked successfully"}
    except Exception as e:
        logger.error(f"Error linking resource: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Relationship & Path Endpoints ---


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
            raise HTTPException(
                status_code=404, detail="One or both concepts not found"
            )

        return {"status": "created", "type": record["rel_type"]}
    except Exception as e:
        logger.error(f"Error creating relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/path", response_model=schemas.PathResponse)
async def get_shortest_path(
    start_id: str, end_id: str, db: AsyncSession = Depends(get_db_session)
):
    """
    Finds path and returns concepts populated with their resources.
    """
    # 1. Find the path (nodes)
    # 2. UNWIND the list of nodes to process each one individually
    # 3. For each node (Concept), we search for associated resources
    # 4. Collect everything back into a list
    query = (
        "MATCH (start:Concept {id: $start_id}), (end:Concept {id: $end_id}), "
        "p = shortestPath((start)-[:PREREQUISITE*]->(end)) "
        "WITH nodes(p) AS path_nodes "
        "UNWIND path_nodes AS c "
        "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
        "RETURN c, collect(r) as resources"
    )

    try:
        result = await db.run(query, {"start_id": start_id, "end_id": end_id})
        records = [record async for record in result]

        if not records:
            logger.warning(f"No path found from {start_id} to {end_id}")
            return schemas.PathResponse(path=[])

        path_concepts = []
        for record in records:
            c_node = record["c"]
            r_nodes = record["resources"]

            # Converting resources into Pydantic models
            resources_list = [schemas.Resource(**dict(r)) for r in r_nodes if r]

            # Creating concept with resources
            concept_obj = schemas.Concept(**dict(c_node), resources=resources_list)
            path_concepts.append(concept_obj)

        return schemas.PathResponse(path=path_concepts)

    except Exception as e:
        logger.error(f"Neo4j error finding path: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Knowledge Graph Service"}
