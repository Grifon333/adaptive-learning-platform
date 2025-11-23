import json
import uuid
from contextlib import asynccontextmanager
from typing import Any

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

    except HTTPException:
        raise
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/path", response_model=schemas.PathResponse)
async def get_shortest_path(
    end_id: str, start_id: str | None = None, db: AsyncSession = Depends(get_db_session)
):
    """
    Finds path and returns concepts populated with their resources.
    """
    # 1. Find the path (nodes)
    # 2. UNWIND the list of nodes to process each one individually
    # 3. For each node (Concept), we search for associated resources
    # 4. Collect everything back into a list

    if start_id:
        # 1. Classic search from A to B
        query = (
            "MATCH (start:Concept {id: $start_id}), (end:Concept {id: $end_id}), "
            "p = shortestPath((start)-[:PREREQUISITE*]->(end)) "
            "WITH nodes(p) AS path_nodes "
            "UNWIND path_nodes AS c "
            "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
            "RETURN c, collect(r) as resources"
        )
        params = {"start_id": start_id, "end_id": end_id}
    else:
        # 2. Search for the "root" (a node with no incoming links from which you can reach the goal)
        # Logic: Find a path p to end_node where the first node has no incoming links PREREQUISITE
        query = (
            "MATCH (end:Concept {id: $end_id}) "
            "MATCH p = (start:Concept)-[:PREREQUISITE*]->(end) "
            "WHERE NOT (start)<-[:PREREQUISITE]-() "
            "WITH p, length(p) as len ORDER BY len DESC LIMIT 1 "  # Take the longest path from the root
            "WITH nodes(p) AS path_nodes "
            "UNWIND path_nodes AS c "
            "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
            "RETURN c, collect(r) as resources"
        )
        params = {"end_id": end_id}

    try:
        result = await db.run(query, params)
        records = [record async for record in result]

        if not records:
            if not start_id:
                # Try to simply return the target itself if it has no dependencies.
                fallback_query = (
                    "MATCH (c:Concept {id: $end_id}) "
                    "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
                    "RETURN c, collect(r) as resources"
                )
                result = await db.run(fallback_query, {"end_id": end_id})
                records = [record async for record in result]
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


@app.post("/api/v1/recommendations", response_model=schemas.RecommendationResponse)
async def get_recommendations(
    req: schemas.RecommendationRequest, db: AsyncSession = Depends(get_db_session)
):
    """
    Finds concepts that are the next steps for those already studied.
    1. Find all nodes from the known_concept_ids list.
    2. Find their outgoing links (PREREQUISITE) to other nodes.
    3. Filter out those that are already in known_concept_ids.
    4. Return unique results.
    """
    # If the student knows nothing, we recommend "initial" nodes (without incoming links).)
    if not req.known_concept_ids:
        query = (
            "MATCH (c:Concept) "
            "WHERE NOT (c)<-[:PREREQUISITE]-(:Concept) "
            "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
            "RETURN c, collect(r) as resources LIMIT $limit"
        )
        params: dict[str, Any] = {"limit": req.limit}
    else:
        query = (
            "MATCH (known:Concept)-[:PREREQUISITE]->(next:Concept) "
            "WHERE known.id IN $known_ids "
            "AND NOT next.id IN $known_ids "
            "OPTIONAL MATCH (next)-[:HAS_RESOURCE]->(r:Resource) "
            "RETURN DISTINCT next as c, collect(r) as resources "
            "LIMIT $limit"
        )
        params = {
            "known_ids": req.known_concept_ids,
            "limit": req.limit,
        }

    try:
        result = await db.run(query, params)
        # records = await result.fetch(req.limit)
        records = [record async for record in result]

        recommendations = []
        for record in records:
            c_node = record["c"]
            r_nodes = record["resources"]
            resources_list = [schemas.Resource(**dict(r)) for r in r_nodes if r]
            concept_obj = schemas.Concept(**dict(c_node), resources=resources_list)
            recommendations.append(concept_obj)

        return schemas.RecommendationResponse(recommendations=recommendations)

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Quiz Endpoints ---


@app.post(
    "/api/v1/concepts/{concept_id}/questions", status_code=status.HTTP_201_CREATED
)
async def add_question_to_concept(
    concept_id: str,
    question: schemas.QuestionCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Creates a question and links it to a concept.
    """
    q_id = str(uuid.uuid4())
    options_json = json.dumps([opt.model_dump() for opt in question.options])
    query = (
        "MATCH (c:Concept {id: $cid}) "
        "CREATE (q:Question {id: $qid, text: $text, options: $options}) "
        "CREATE (c)-[:HAS_QUESTION]->(q) "
        "RETURN q"
    )

    try:
        result = await db.run(
            query,
            {
                "cid": concept_id,
                "qid": q_id,
                "text": question.text,
                "options": options_json,
            },
        )
        record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="Concept not found")

        return {"status": "created", "question_id": q_id}
    except Exception as e:
        logger.error(f"Error creating question: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/concepts/{concept_id}/quiz", response_model=schemas.QuizResponse)
async def get_concept_quiz(concept_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Returns all questions for the concept.
    """
    query = "MATCH (c:Concept {id: $cid})-[:HAS_QUESTION]->(q:Question) " "RETURN q"

    try:
        result = await db.run(query, {"cid": concept_id})
        records = [record async for record in result]

        questions = []
        for record in records:
            node = dict(record["q"])
            node["options"] = json.loads(node["options"])
            questions.append(schemas.Question(**node))

        return schemas.QuizResponse(questions=questions)

    except Exception as e:
        logger.error(f"Error fetching quiz: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Knowledge Graph Service"}
