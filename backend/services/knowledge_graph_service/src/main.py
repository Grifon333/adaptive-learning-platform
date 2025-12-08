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
    setup_logging()
    logger.info("Knowledge Graph Service initializing...")
    await init_driver()
    yield
    logger.info("Knowledge Graph Service shutting down...")
    await close_driver()


app = FastAPI(title="Knowledge Graph Service", lifespan=lifespan)

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")


# --- Concept Endpoints ---


@app.post("/api/v1/concepts", response_model=schemas.Concept, status_code=status.HTTP_201_CREATED)
async def create_concept(concept: schemas.ConceptCreate, db: AsyncSession = Depends(get_db_session)):
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
        if not record:
            raise HTTPException(status_code=500, detail="Could not create concept")
        return schemas.Concept(**dict(record[0]), resources=[])
    except Exception as e:
        logger.error(f"Error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/concepts", response_model=schemas.ConceptListResponse)
async def get_all_concepts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    count = await (await db.run("MATCH (c:Concept) RETURN count(c) as total")).single()
    total = count["total"] if count else 0

    result = await db.run(
        "MATCH (c:Concept) RETURN c ORDER BY c.name SKIP $skip LIMIT $limit", {"skip": skip, "limit": limit}
    )
    items = [schemas.Concept(**dict(r["c"])) async for r in result]
    return schemas.ConceptListResponse(total=total, items=items)


@app.get("/api/v1/concepts/{concept_id}", response_model=schemas.Concept)
async def get_concept_details(concept_id: str, db: AsyncSession = Depends(get_db_session)):
    query = (
        "MATCH (c:Concept {id: $id}) OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) RETURN c, collect(r) as resources"
    )
    try:
        result = await db.run(query, {"id": concept_id})
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Concept not found")

        concept_node = record["c"]
        resource_nodes = record["resources"]
        resources_data = [schemas.Resource(**dict(r)) for r in resource_nodes if r]

        return schemas.Concept(**dict(concept_node), resources=resources_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting concept: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.put("/api/v1/concepts/{concept_id}", response_model=schemas.Concept)
async def update_concept(
    concept_id: str, update_data: schemas.ConceptUpdate, db: AsyncSession = Depends(get_db_session)
):
    fields = update_data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields")
    set_clauses = ", ".join([f"c.{k} = ${k}" for k in fields.keys()])
    query = f"MATCH (c:Concept {{id: $id}}) SET {set_clauses} RETURN c"
    try:
        result = await db.run(query, {"id": concept_id, **fields})
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Not found")
        return schemas.Concept(**dict(record["c"]))
    except Exception as e:
        logger.error(f"Update error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/concepts/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_concept(concept_id: str, db: AsyncSession = Depends(get_db_session)):
    try:
        if not await (await db.run("MATCH (c:Concept {id: $id}) RETURN c", {"id": concept_id})).single():
            raise HTTPException(status_code=404, detail="Not found")
        await db.run("MATCH (c:Concept {id: $id}) DETACH DELETE c", {"id": concept_id})
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/relationships", status_code=status.HTTP_201_CREATED)
async def create_relationship(rel: schemas.RelationshipCreate, db: AsyncSession = Depends(get_db_session)):
    """
    Creates a relationship with Weight and Cycle Detection.
    - PREREQUISITE (Ep): Directed, Acyclic.
    - RELATED_TO (Es): Bidirectional (Undirected logic).
    """
    if rel.start_concept_id == rel.end_concept_id:
        raise HTTPException(status_code=400, detail="Cannot link a concept to itself")

    # 1. Cycle Detection (Strict for PREREQUISITE)
    if rel.rel_type == "PREREQUISITE":
        cycle_query = (
            "MATCH path = (end:Concept {id: $end_id})-[:PREREQUISITE*]->(start:Concept {id: $start_id}) "
            "RETURN path LIMIT 1"
        )
        try:
            check = await db.run(cycle_query, {"start_id": rel.start_concept_id, "end_id": rel.end_concept_id})
            if await check.single():
                raise HTTPException(status_code=400, detail="Cycle detected! PREREQUISITE violation.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Cycle check error: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    # 2. Create Relationship(s)
    allowed = ["PREREQUISITE", "RELATED_TO"]
    if rel.rel_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid type. Allowed: {allowed}")

    if rel.rel_type == "RELATED_TO":
        # Create Bidirectional for Semantic Similarity (Es)
        query = (
            f"MATCH (a:Concept {{id: $start_id}}), (b:Concept {{id: $end_id}}) "
            f"MERGE (a)-[r1:{rel.rel_type}]->(b) SET r1.weight = $weight "
            f"MERGE (b)-[r2:{rel.rel_type}]->(a) SET r2.weight = $weight "
            f"RETURN type(r1) AS rel_type, r1.weight as weight"
        )
    else:
        # Create Directed for Prerequisite (Ep)
        query = (
            f"MATCH (a:Concept {{id: $start_id}}), (b:Concept {{id: $end_id}}) "
            f"MERGE (a)-[r:{rel.rel_type}]->(b) SET r.weight = $weight "
            f"RETURN type(r) AS rel_type, r.weight as weight"
        )

    try:
        result = await db.run(
            query, {"start_id": rel.start_concept_id, "end_id": rel.end_concept_id, "weight": rel.weight}
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Concepts not found")
        return {"status": "created", "type": record["rel_type"], "weight": record["weight"]}
    except Exception as e:
        logger.error(f"Rel creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/concepts/{concept_id}/prerequisites", response_model=schemas.ConceptListResponse)
async def get_concept_prerequisites(concept_id: str, db: AsyncSession = Depends(get_db_session)):
    query = (
        "MATCH (c:Concept {id: $id})<-[:PREREQUISITE]-(p:Concept) "
        "OPTIONAL MATCH (p)-[:HAS_RESOURCE]->(r:Resource) "
        "RETURN p, collect(r) as resources"
    )
    try:
        result = await db.run(query, {"id": concept_id})
        items = []
        async for record in result:
            res_objs = [schemas.Resource(**dict(r)) for r in record["resources"] if r]
            items.append(schemas.Concept(**dict(record["p"]), resources=res_objs))
        return schemas.ConceptListResponse(total=len(items), items=items)
    except Exception as e:
        logger.error(f"Prereq error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/relationships", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship(rel: schemas.RelationshipDelete, db: AsyncSession = Depends(get_db_session)):
    """Deletes relationships. Handles bidirectional cleanup for RELATED_TO."""
    if rel.rel_type == "RELATED_TO":
        query = f"MATCH (a:Concept {{id: $s}})-[r:{rel.rel_type}]-(b:Concept {{id: $e}}) DELETE r"
    else:
        query = f"MATCH (a:Concept {{id: $s}})-[r:{rel.rel_type}]->(b:Concept {{id: $e}}) DELETE r"

    try:
        await db.run(query, {"s": rel.start_concept_id, "e": rel.end_concept_id})
    except Exception as e:
        logger.error(f"Delete rel error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Resource Endpoints ---


@app.post("/api/v1/resources", response_model=schemas.Resource, status_code=status.HTTP_201_CREATED)
async def create_resource(resource: schemas.ResourceCreate, db: AsyncSession = Depends(get_db_session)):
    """Creates a new learning resource node."""
    res_id = str(uuid.uuid4())
    query = (
        "CREATE (r:Resource { "
        "id: $id, title: $title, type: $type, url: $url, "
        "duration: $duration, difficulty: $difficulty "
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
                "difficulty": resource.difficulty,
            },
        )
        record = await result.single()
        if not record:
            raise HTTPException(status_code=500, detail="Failed to create resource")
        return schemas.Resource(**dict(record["r"]))
    except Exception as e:
        logger.error(f"Error creating resource: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/uploads", status_code=status.HTTP_201_CREATED)
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Uploads a file to the server and returns a direct URL."""
    try:
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        unique_name = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_DIR, unique_name)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        base_url = str(request.base_url).rstrip("/")
        return {"filename": unique_name, "url": f"{base_url}/static/{unique_name}", "content_type": file.content_type}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed") from e


@app.get("/api/v1/resources", response_model=schemas.ResourceListResponse)
async def get_all_resources(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db_session)):
    count = await (await db.run("MATCH (r:Resource) RETURN count(r) as total")).single()
    total = count["total"] if count else 0
    result = await db.run(
        "MATCH (r:Resource) RETURN r ORDER BY r.title SKIP $skip LIMIT $limit", {"skip": skip, "limit": limit}
    )
    items = [schemas.Resource(**dict(r["r"])) async for r in result]
    return schemas.ResourceListResponse(total=total, items=items)


@app.put("/api/v1/resources/{resource_id}", response_model=schemas.Resource)
async def update_resource(
    resource_id: str, update_data: schemas.ResourceUpdate, db: AsyncSession = Depends(get_db_session)
):
    fields = update_data.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields")
    set_clauses = ", ".join([f"r.{k} = ${k}" for k in fields.keys()])
    query = f"MATCH (r:Resource {{id: $id}}) SET {set_clauses} RETURN r"
    try:
        result = await db.run(query, {"id": resource_id, **fields})
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Not found")
        return schemas.Resource(**dict(record["r"]))
    except Exception as e:
        logger.error(f"Res update error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(resource_id: str, db: AsyncSession = Depends(get_db_session)):
    try:
        if not await (await db.run("MATCH (r:Resource {id: $id}) RETURN r", {"id": resource_id})).single():
            raise HTTPException(status_code=404, detail="Not found")
        await db.run("MATCH (r:Resource {id: $id}) DETACH DELETE r", {"id": resource_id})
    except Exception as e:
        logger.error(f"Res delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/concepts/{concept_id}/resources", status_code=status.HTTP_200_OK)
async def add_resource_to_concept(concept_id: str, resource_id: str, db: AsyncSession = Depends(get_db_session)):
    query = "MATCH (c:Concept {id: $cid}), (r:Resource {id: $rid}) MERGE (c)-[:HAS_RESOURCE]->(r) RETURN c"
    try:
        result = await db.run(query, {"cid": concept_id, "rid": resource_id})
        if not await result.single():
            raise HTTPException(status_code=404, detail="Concept or Resource not found")
        return {"message": "Resource linked successfully"}
    except Exception as e:
        logger.error(f"Error linking resource: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/v1/concepts/{concept_id}/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_resource_from_concept(concept_id: str, resource_id: str, db: AsyncSession = Depends(get_db_session)):
    query = "MATCH (c:Concept {id: $cid})-[rel:HAS_RESOURCE]->(r:Resource {id: $rid}) DELETE rel"
    try:
        check = await db.run(
            "MATCH (c:Concept {id: $cid})-[rel:HAS_RESOURCE]->(r:Resource {id: $rid}) RETURN rel",
            {"cid": concept_id, "rid": resource_id},
        )
        if not await check.single():
            raise HTTPException(status_code=404, detail="Link not found")
        await db.run(query, {"cid": concept_id, "rid": resource_id})
    except Exception as e:
        logger.error(f"Unlink error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Path Endpoints ---


@app.get("/api/v1/path", response_model=schemas.PathResponse)
async def get_shortest_path(end_id: str, start_id: str | None = None, db: AsyncSession = Depends(get_db_session)):
    if start_id:
        query = (
            "MATCH (start:Concept {id: $start_id}), (end:Concept {id: $end_id}), "
            "p = shortestPath((start)-[:PREREQUISITE*]->(end)) "
            "WITH nodes(p) AS path_nodes UNWIND path_nodes AS c "
            "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
            "RETURN c, collect(r) as resources"
        )
        params = {"start_id": start_id, "end_id": end_id}
    else:
        query = (
            "MATCH (end:Concept {id: $end_id}) "
            "MATCH p = (start:Concept)-[:PREREQUISITE*0..]->(end) "
            "WHERE NOT (start)<-[:PREREQUISITE]-() "
            "WITH p, length(p) as len ORDER BY len DESC LIMIT 1 "
            "WITH nodes(p) AS path_nodes UNWIND path_nodes AS c "
            "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
            "RETURN c, collect(r) as resources"
        )
        params = {"end_id": end_id}

    try:
        result = await db.run(query, params)
        records = [record async for record in result]

        if not records and not start_id:
            # Fallback for single node
            fallback = (
                "MATCH (c:Concept {id: $end_id}) "
                "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
                "RETURN c, collect(r) as resources"
            )
            result = await db.run(fallback, {"end_id": end_id})
            records = [record async for record in result]

        path_concepts = []
        for record in records:
            c_node = record["c"]
            resources_list = [schemas.Resource(**dict(r)) for r in record["resources"] if r]
            path_concepts.append(schemas.Concept(**dict(c_node), resources=resources_list))

        return schemas.PathResponse(path=path_concepts)
    except Exception as e:
        logger.error(f"Pathfinding error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/path/candidates", response_model=schemas.MultiPathResponse)
async def get_path_candidates(
    end_id: str, start_id: str | None = None, limit: int = 5, db: AsyncSession = Depends(get_db_session)
):
    if not start_id:
        base_match = (
            "MATCH (end:Concept {id: $end_id}) "
            "MATCH p = (start:Concept)-[:PREREQUISITE*]->(end) "
            "WHERE NOT (start)<-[:PREREQUISITE]-() "
        )
        params = {"end_id": end_id, "limit": limit}
    else:
        base_match = (
            "MATCH (start:Concept {id: $start_id}), (end:Concept {id: $end_id}) "
            "MATCH p = (start)-[:PREREQUISITE*..15]->(end) "
        )
        params = {"start_id": start_id, "end_id": end_id, "limit": limit}

    query = (
        f"{base_match} "
        "WITH p, reduce(d=0.0, n in nodes(p) | d + n.difficulty) as diff, "
        "reduce(t=0, n in nodes(p) | t + n.estimated_time) as time "
        "ORDER BY length(p) ASC LIMIT $limit "
        "UNWIND nodes(p) as c "
        "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
        "WITH p, diff, time, c, collect(r) as resources "
        "WITH p, diff, time, collect({concept: c, resources: resources}) as full_path "
        "RETURN full_path, diff, time"
    )

    try:
        result = await db.run(query, params)
        candidates = []
        async for record in result:
            full_path_data = record["full_path"]
            concepts_list = []
            for item in full_path_data:
                res_objs = [schemas.Resource(**dict(r)) for r in item["resources"] if r]
                concepts_list.append(schemas.Concept(**dict(item["concept"]), resources=res_objs))

            candidates.append(
                schemas.PathCandidate(
                    id=str(uuid.uuid4()),
                    concepts=concepts_list,
                    total_difficulty=record["diff"],
                    total_time=record["time"],
                )
            )
        return schemas.MultiPathResponse(candidates=candidates)
    except Exception as e:
        logger.error(f"Candidate search error: {e}")
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
    if not req.known_concept_ids:
        query = (
            "MATCH (c:Concept) WHERE NOT (c)<-[:PREREQUISITE]-(:Concept) "
            "OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource) "
            "RETURN c, collect(r) as resources LIMIT $limit"
        )
        params: dict[str, Any] = {"limit": req.limit}
    else:
        query = (
            "MATCH (known:Concept)-[:PREREQUISITE]->(next:Concept) "
            "WHERE known.id IN $known_ids AND NOT next.id IN $known_ids "
            "OPTIONAL MATCH (next)-[:HAS_RESOURCE]->(r:Resource) "
            "RETURN DISTINCT next as c, collect(r) as resources LIMIT $limit"
        )
        params = {"known_ids": req.known_concept_ids, "limit": req.limit}

    try:
        result = await db.run(query, params)
        recommendations = []
        async for record in result:
            res_objs = [schemas.Resource(**dict(r)) for r in record["resources"] if r]
            recommendations.append(schemas.Concept(**dict(record["c"]), resources=res_objs))
        return schemas.RecommendationResponse(recommendations=recommendations)
    except Exception as e:
        logger.error(f"Recs error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Quiz Endpoints ---


@app.post("/api/v1/concepts/{concept_id}/questions", status_code=status.HTTP_201_CREATED)
async def add_question_to_concept(
    concept_id: str, question: schemas.QuestionCreate, db: AsyncSession = Depends(get_db_session)
):
    q_id = str(uuid.uuid4())
    options_json = json.dumps([opt.model_dump() for opt in question.options])
    query = (
        "MATCH (c:Concept {id: $cid}) "
        "CREATE (q:Question {id: $qid, text: $text, options: $options, difficulty: $diff}) "
        "CREATE (c)-[:HAS_QUESTION]->(q) RETURN q"
    )
    try:
        result = await db.run(
            query,
            {
                "cid": concept_id,
                "qid": q_id,
                "text": question.text,
                "options": options_json,
                "diff": question.difficulty,
            },
        )
        if not await result.single():
            raise HTTPException(status_code=404, detail="Concept not found")
        return {"status": "created", "question_id": q_id}
    except Exception as e:
        logger.error(f"Add question error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/concepts/{concept_id}/quiz", response_model=schemas.QuizResponse)
async def get_concept_quiz(concept_id: str, db: AsyncSession = Depends(get_db_session)):
    query = "MATCH (c:Concept {id: $cid})-[:HAS_QUESTION]->(q:Question) RETURN q"
    try:
        result = await db.run(query, {"cid": concept_id})
        questions = []
        async for record in result:
            node = dict(record["q"])
            node["options"] = json.loads(node["options"])
            questions.append(schemas.Question(**node))
        return schemas.QuizResponse(questions=questions)
    except Exception as e:
        logger.error(f"Get quiz error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/questions/batch", response_model=schemas.BatchQuestionsResponse)
async def get_questions_batch(req: schemas.BatchQuestionsRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Fetches questions for a list of concepts, optionally filtered by difficulty.
    Used by Learning Path Service to construct assessments.
    """
    if not req.concept_ids:
        return schemas.BatchQuestionsResponse(data=[])

    query = "MATCH (c:Concept)-[:HAS_QUESTION]->(q:Question) WHERE c.id IN $concept_ids "
    if req.min_difficulty is not None:
        query += "AND q.difficulty >= $min_diff "
    if req.max_difficulty is not None:
        query += "AND q.difficulty <= $max_diff "

    query += (
        "WITH c, q ORDER BY q.difficulty ASC "
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
        data = []
        async for record in result:
            qs = []
            for q in record["questions"]:
                q_dict = dict(q)
                if isinstance(q_dict.get("options"), str):
                    q_dict["options"] = json.loads(q_dict["options"])
                if "difficulty" not in q_dict:
                    q_dict["difficulty"] = 1.0
                qs.append(schemas.Question(**q_dict))
            data.append(schemas.ConceptQuestions(concept_id=record["concept_id"], questions=qs))
        return schemas.BatchQuestionsResponse(data=data)
    except Exception as e:
        logger.error(f"Batch Q error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/questions/adaptive", response_model=schemas.AdaptiveQuestionResponse | None)
async def get_adaptive_question(req: schemas.AdaptiveQuestionRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Finds a single question closest to the target difficulty.
    Returns the question AND its concept_id.
    """
    query = (
        "MATCH (c:Concept)-[:HAS_QUESTION]->(q:Question) "
        "WHERE c.id IN $concept_ids "
        "AND NOT q.id IN $exclude_ids "
        "WITH q, c, abs(q.difficulty - $target) as diff_delta "
        "ORDER BY diff_delta ASC "
        "LIMIT 1 "
        "RETURN q, c.id as concept_id"
    )

    params = {"concept_ids": req.concept_ids, "exclude_ids": req.exclude_question_ids, "target": req.target_difficulty}

    try:
        result = await db.run(query, params)
        record = await result.single()

        if not record:
            return None

        q_data = dict(record["q"])

        # Handle JSON options if stored as string in Neo4j
        if isinstance(q_data.get("options"), str):
            q_data["options"] = json.loads(q_data["options"])

        # 2. Inject concept_id from the graph relationship
        q_data["concept_id"] = record["concept_id"]

        # 3. Return using the NEW schema
        return schemas.AdaptiveQuestionResponse(**q_data)

    except Exception as e:
        logger.error(f"Adaptive Q fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Knowledge Graph Service"}
