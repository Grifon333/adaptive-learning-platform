import json
import os
import shutil
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.staticfiles import StaticFiles
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

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# --- Concept Endpoints ---


@app.post(
    "/api/v1/concepts",
    response_model=schemas.Concept,
    status_code=status.HTTP_201_CREATED,
)
async def create_concept(concept: schemas.ConceptCreate, db: AsyncSession = Depends(get_db_session)):
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
        # Return an empty list of resources for the new concept
        return schemas.Concept(**dict(node), resources=[])

    except Exception as e:
        logger.error(f"Error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/concepts/{concept_id}", response_model=schemas.Concept)
async def get_concept_details(concept_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves concept details by its 'id'
    """
    query = (
        "MATCH (c:Concept {id: $id}) OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) RETURN c, collect(r) as resources"
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
async def create_resource(resource: schemas.ResourceCreate, db: AsyncSession = Depends(get_db_session)):
    """
    Creates a new learning resource node.
    """
    res_id = str(uuid.uuid4())
    query = "CREATE (r:Resource { id: $id, title: $title, type: $type, url: $url, duration: $duration }) RETURN r"

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
async def add_resource_to_concept(concept_id: str, resource_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Links an existing resource to a concept via HAS_RESOURCE relationship.
    """
    query = "MATCH (c:Concept {id: $cid}), (r:Resource {id: $rid}) MERGE (c)-[:HAS_RESOURCE]->(r) RETURN c, r"
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


@app.get("/api/v1/path", response_model=schemas.PathResponse)
async def get_shortest_path(end_id: str, start_id: str | None = None, db: AsyncSession = Depends(get_db_session)):
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
            "MATCH p = (start:Concept)-[:PREREQUISITE*0..]->(end) "
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
                logger.info(f"Main path query empty. Attempting fallback for single concept: {end_id}")
                # Try to simply return the target itself if it has no dependencies.
                fallback_query = (
                    "MATCH (c:Concept {id: $end_id}) "
                    "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
                    "RETURN c, collect(r) as resources"
                )
                result = await db.run(fallback_query, {"end_id": end_id})
                records = [record async for record in result]

            # Re-check records after fallback attempt
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


@app.post("/api/v1/recommendations", response_model=schemas.RecommendationResponse)
async def get_recommendations(req: schemas.RecommendationRequest, db: AsyncSession = Depends(get_db_session)):
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


@app.post("/api/v1/concepts/{concept_id}/questions", status_code=status.HTTP_201_CREATED)
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
    query = "MATCH (c:Concept {id: $cid})-[:HAS_QUESTION]->(q:Question) RETURN q"

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


@app.post("/api/v1/questions/batch", response_model=schemas.BatchQuestionsResponse)
async def get_questions_batch(req: schemas.BatchQuestionsRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Fetches questions for a list of concepts, optionally filtered by difficulty.
    Used by Learning Path Service to construct assessments.
    """
    if not req.concept_ids:
        return schemas.BatchQuestionsResponse(data=[])

    # Dynamic query building
    # We collect questions per concept, limited by the request
    query = "MATCH (c:Concept)-[:HAS_QUESTION]->(q:Question) WHERE c.id IN $concept_ids "

    if req.min_difficulty is not None:
        query += "AND q.difficulty >= $min_diff "

    if req.max_difficulty is not None:
        query += "AND q.difficulty <= $max_diff "

    query += (
        "WITH c, q "
        "ORDER BY q.difficulty ASC "  # Basic ordering
        "WITH c, collect(q)[..$limit] as questions "
        "RETURN c.id as concept_id, questions"
    )

    params = {
        "concept_ids": req.concept_ids,
        "limit": req.limit_per_concept,
        "min_diff": req.min_difficulty,
        "max_diff": req.max_difficulty,
    }

    try:
        result = await db.run(query, params)
        records = [record async for record in result]

        response_data = []
        for record in records:
            concept_id = record["concept_id"]
            q_nodes = record["questions"]

            parsed_questions = []
            for q in q_nodes:
                q_dict = dict(q)
                if isinstance(q_dict.get("options"), str):
                    q_dict["options"] = json.loads(q_dict["options"])

                # Ensure difficulty is present (handle legacy nodes if any)
                if "difficulty" not in q_dict:
                    q_dict["difficulty"] = 1.0

                parsed_questions.append(schemas.Question(**q_dict))

            response_data.append(schemas.ConceptQuestions(concept_id=concept_id, questions=parsed_questions))

        return schemas.BatchQuestionsResponse(data=response_data)

    except Exception as e:
        logger.error(f"Error fetching batch questions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/concepts", response_model=schemas.ConceptListResponse)
async def get_all_concepts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves a paginated list of concepts.
    """
    # 1. Count Total
    count_query = "MATCH (c:Concept) RETURN count(c) as total"
    count_result = await db.run(count_query)
    count = await count_result.single()
    if count is None:
        total = 0
    else:
        total = count["total"]

    # 2. Fetch Items
    query = "MATCH (c:Concept) RETURN c ORDER BY c.name SKIP $skip LIMIT $limit"
    result = await db.run(query, {"skip": skip, "limit": limit})
    records = [record async for record in result]

    concepts = [schemas.Concept(**dict(r["c"])) for r in records]

    return schemas.ConceptListResponse(total=total, items=concepts)


@app.put("/api/v1/concepts/{concept_id}", response_model=schemas.Concept)
async def update_concept(
    concept_id: str,
    update_data: schemas.ConceptUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Updates concept properties.
    """
    # Construct dynamic SET clause
    fields = update_data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = ", ".join([f"c.{key} = ${key}" for key in fields.keys()])

    query = f"MATCH (c:Concept {{id: $id}}) SET {set_clauses} RETURN c"

    params = {"id": concept_id, **fields}

    try:
        result = await db.run(query, params)
        record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="Concept not found")

        return schemas.Concept(**dict(record["c"]))
    except Exception as e:
        logger.error(f"Error updating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/concepts/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_concept(concept_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Deletes a concept and all its attached relationships.
    """
    # DETACH DELETE removes relationships first to prevent orphan errors
    query = "MATCH (c:Concept {id: $id}) DETACH DELETE c"

    try:
        # Check existence first (optional, but good for UX)
        check = await db.run("MATCH (c:Concept {id: $id}) RETURN c", {"id": concept_id})
        if not await check.single():
            raise HTTPException(status_code=404, detail="Concept not found")

        await db.run(query, {"id": concept_id})
        logger.info(f"Deleted concept {concept_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/relationships", status_code=status.HTTP_201_CREATED)
async def create_relationship(rel: schemas.RelationshipCreate, db: AsyncSession = Depends(get_db_session)):
    """
    Creates a relationship between two concepts with Cycle Detection.
    """
    if rel.start_concept_id == rel.end_concept_id:
        raise HTTPException(status_code=400, detail="Cannot link a concept to itself")

    # 1. Cycle Detection Logic
    # If we are adding A -> B, check if a path B -> ... -> A already exists.
    # If it does, adding A -> B closes the loop.
    cycle_check_query = (
        "MATCH path = (end:Concept {id: $end_id})-[:PREREQUISITE*]->(start:Concept {id: $start_id}) RETURN path LIMIT 1"
    )

    try:
        check_result = await db.run(
            cycle_check_query,
            {"start_id": rel.start_concept_id, "end_id": rel.end_concept_id},
        )
        if await check_result.single():
            raise HTTPException(
                status_code=400,
                detail="Cycle detected! Adding this relationship would create an infinite loop.",
            )

        # 2. Create Relationship (If safe)
        query = (
            f"MATCH (a:Concept {{id: $start_id}}), (b:Concept {{id: $end_id}}) "
            f"MERGE (a)-[r:{rel.rel_type}]->(b) "
            f"RETURN type(r) AS rel_type"
        )

        result = await db.run(
            query,
            {
                "start_id": rel.start_concept_id,
                "end_id": rel.end_concept_id,
            },
        )
        record = await result.single()

        if record is None:
            raise HTTPException(status_code=404, detail="One or both concepts not found")

        return {"status": "created", "type": record["rel_type"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/relationships", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(rel: schemas.RelationshipDelete, db: AsyncSession = Depends(get_db_session)):
    """
    Removes a specific relationship between two concepts.
    """
    query = f"MATCH (a:Concept {{id: $start_id}})-[r:{rel.rel_type}]->(b:Concept {{id: $end_id}}) DELETE r"

    try:
        await db.run(query, {"start_id": rel.start_concept_id, "end_id": rel.end_concept_id})
    except Exception as e:
        logger.error(f"Error deleting relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/resources", response_model=schemas.ResourceListResponse)
async def get_all_resources(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves a paginated list of all available resources.
    """
    # 1. Count Total
    count_query = "MATCH (r:Resource) RETURN count(r) as total"
    count_result = await db.run(count_query)
    count = await count_result.single()
    if count is None:
        total = 0
    else:
        total = count["total"]

    # 2. Fetch Items
    query = "MATCH (r:Resource) RETURN r ORDER BY r.title SKIP $skip LIMIT $limit"
    result = await db.run(query, {"skip": skip, "limit": limit})
    records = [record async for record in result]

    items = [schemas.Resource(**dict(r["r"])) for r in records]

    return schemas.ResourceListResponse(total=total, items=items)


@app.put("/api/v1/resources/{resource_id}", response_model=schemas.Resource)
async def update_resource(
    resource_id: str,
    update_data: schemas.ResourceUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Updates resource metadata.
    """
    fields = update_data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = ", ".join([f"r.{key} = ${key}" for key in fields.keys()])

    query = f"MATCH (r:Resource {{id: $id}}) SET {set_clauses} RETURN r"

    params = {"id": resource_id, **fields}

    try:
        result = await db.run(query, params)
        record = await result.single()

        if not record:
            raise HTTPException(status_code=404, detail="Resource not found")

        return schemas.Resource(**dict(record["r"]))
    except Exception as e:
        logger.error(f"Error updating resource: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(resource_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Deletes a resource node and all its links to concepts.
    """
    query = "MATCH (r:Resource {id: $id}) DETACH DELETE r"

    try:
        # Check existence
        check = await db.run("MATCH (r:Resource {id: $id}) RETURN r", {"id": resource_id})
        if not await check.single():
            raise HTTPException(status_code=404, detail="Resource not found")

        await db.run(query, {"id": resource_id})
        logger.info(f"Deleted resource {resource_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resource: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete(
    "/api/v1/concepts/{concept_id}/resources/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_resource_from_concept(concept_id: str, resource_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Removes the HAS_RESOURCE relationship between a specific concept and resource.
    Does NOT delete the resource itself.
    """
    query = "MATCH (c:Concept {id: $cid})-[rel:HAS_RESOURCE]->(r:Resource {id: $rid}) DELETE rel"

    try:
        # Check relationship existence
        check_query = "MATCH (c:Concept {id: $cid})-[rel:HAS_RESOURCE]->(r:Resource {id: $rid}) RETURN rel"
        check = await db.run(check_query, {"cid": concept_id, "rid": resource_id})
        if not await check.single():
            raise HTTPException(status_code=404, detail="Link between Concept and Resource not found")

        await db.run(query, {"cid": concept_id, "rid": resource_id})
        logger.info(f"Unlinked resource {resource_id} from concept {concept_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking resource: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/uploads", status_code=status.HTTP_201_CREATED)
async def upload_file(request: Request, file: UploadFile = File(...)):
    """
    Uploads a file to the server and returns a direct URL.
    """
    try:
        # 1. Generate unique filename to prevent overwrites
        filename = file.filename or ""
        if "." in filename:
            file_ext = filename.rsplit(".", 1)[-1]
        else:
            file_ext = "bin"

        unique_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        # 2. Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Construct Public URL
        # We use the request base URL to ensure it works for localhost/10.0.2.2/etc.
        # Note: request.base_url typically ends with a slash.
        base_url = str(request.base_url).rstrip("/")
        # We assume the service is exposed directly or via gateway on the same port for now.
        # For docker internal, this might return http://alp_kg_service:8000
        # But for the client (Flutter), we need the external URL.
        # Since we don't have a reverse proxy configured in code yet, we return a relative path
        # or rely on the client to know the domain.
        # Ideally, we return the full accessible URL.

        # Simple solution for MVP: Return the path relative to the service root
        file_url = f"{base_url}/static/{unique_name}"

        return {
            "filename": unique_name,
            "url": file_url,
            "content_type": file.content_type,
        }

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed") from e


@app.get("/api/v1/path/candidates", response_model=schemas.MultiPathResponse)
async def get_path_candidates(
    end_id: str,
    start_id: str | None = None,
    limit: int = 5,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Finds up to 'limit' distinct paths from Start to End.
    """
    # 1. Base Query Construction
    if not start_id:
        # Fallback for "Goal Only" mode: Find paths from any root to the goal
        base_match = (
            "MATCH (end:Concept {id: $end_id}) "
            "MATCH p = (start:Concept)-[:PREREQUISITE*]->(end) "
            "WHERE NOT (start)<-[:PREREQUISITE]-() "
        )
        params = {"end_id": end_id, "limit": limit}
    else:
        # Path from A to B (limiting length to prevent exponential explosion)
        base_match = (
            "MATCH (start:Concept {id: $start_id}), (end:Concept {id: $end_id}) "
            "MATCH p = (start)-[:PREREQUISITE*..15]->(end) "
        )
        params = {"start_id": start_id, "end_id": end_id, "limit": limit}

    # 2. Optimized Query with Resource Projection
    # We use UNWIND and collect() to fetch all concepts AND their resources in a single DB hit.
    query = (
        f"{base_match} "
        "WITH p, reduce(d=0.0, n in nodes(p) | d + n.difficulty) as diff, "
        "reduce(t=0, n in nodes(p) | t + n.estimated_time) as time "
        "ORDER BY length(p) ASC "
        "LIMIT $limit "
        "UNWIND nodes(p) as c "
        "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
        "WITH p, diff, time, c, collect(r) as resources "
        "WITH p, diff, time, collect({concept: c, resources: resources}) as full_path "
        "RETURN full_path, diff, time"
    )

    try:
        result = await db.run(query, params)
        records = [record async for record in result]

        candidates = []
        for record in records:
            # full_path is a list of objects: [{concept: Node, resources: [Node, Node]}, ...]
            full_path_data = record["full_path"]

            concepts_list = []
            for item in full_path_data:
                c_node = item["concept"]
                r_nodes = item["resources"]

                # Convert Resource Nodes to Pydantic Models
                res_objs = [schemas.Resource(**dict(r)) for r in r_nodes if r]

                # Convert Concept Node to Pydantic Model (attaching resources)
                concepts_list.append(schemas.Concept(**dict(c_node), resources=res_objs))

            candidates.append(
                schemas.PathCandidate(
                    id=str(uuid.uuid4()),  # Generate ephemeral ID for this candidate path
                    concepts=concepts_list,
                    total_difficulty=record["diff"],
                    total_time=record["time"],
                )
            )

        return schemas.MultiPathResponse(candidates=candidates)

    except Exception as e:
        logger.error(f"Error finding candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get(
    "/api/v1/concepts/{concept_id}/prerequisites",
    response_model=schemas.ConceptListResponse,
)
async def get_concept_prerequisites(concept_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Returns immediate prerequisites for a concept.
    Used by Adaptation Engine to find remedial content.
    """
    query = (
        "MATCH (c:Concept {id: $id})<-[:PREREQUISITE]-(p:Concept) "
        "OPTIONAL MATCH (p)-[:HAS_RESOURCE]->(r:Resource) "
        "RETURN p, collect(r) as resources"
    )

    try:
        result = await db.run(query, {"id": concept_id})
        records = [record async for record in result]

        concepts = []
        for record in records:
            c_node = record["p"]
            r_nodes = record["resources"]
            resources_list = [schemas.Resource(**dict(r)) for r in r_nodes if r]
            concepts.append(schemas.Concept(**dict(c_node), resources=resources_list))

        return schemas.ConceptListResponse(total=len(concepts), items=concepts)

    except Exception as e:
        logger.error(f"Error fetching prerequisites: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Knowledge Graph Service"}
