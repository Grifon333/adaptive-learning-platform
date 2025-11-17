import httpx
import pytest
from neo4j import AsyncSession

pytestmark = pytest.mark.asyncio


async def test_health_check(client: httpx.AsyncClient):
    """Check that the service is up and running."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Knowledge Graph Service"}


async def test_create_concept(client: httpx.AsyncClient, db_session: AsyncSession):
    """
    Test 1: Successful concept creation.
    Check the API response and direct query to the database.
    """
    concept_data = {
        "name": "Test Concept",
        "description": "A test description",
        "difficulty": 5.0,
        "estimated_time": 45,
    }
    response = await client.post("/api/v1/concepts", json=concept_data)

    # 1. API response verification
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == concept_data["name"]
    assert data["difficulty"] == 5.0
    assert "id" in data

    concept_id = data["id"]

    # 2. Database verification
    result = await db_session.run(
        "MATCH (c:Concept {id: $id}) RETURN c.name AS name, c.difficulty AS difficulty",
        id=concept_id,
    )
    record = await result.single()
    assert record is not None
    assert record["name"] == "Test Concept"
    assert record["difficulty"] == 5.0


async def test_get_concept_details(client: httpx.AsyncClient):
    """Test 2: Obtaining details of the existing concept."""
    # First, create a concept
    create_response = await client.post(
        "/api/v1/concepts", json={"name": "Test Concept 2", "description": "Details"}
    )
    concept_id = create_response.json()["id"]

    # Now get it
    get_response = await client.get(f"/api/v1/concepts/{concept_id}")

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == concept_id
    assert data["name"] == "Test Concept 2"
    assert data["description"] == "Details"


async def test_get_concept_not_found(client: httpx.AsyncClient):
    """Test 3: Error 404 when receiving a non-existent concept."""
    response = await client.get("/api/v1/concepts/a-fake-uuid-12345")
    assert response.status_code == 404
    assert response.json()["detail"] == "Concept not found"


async def test_create_relationship(client: httpx.AsyncClient, db_session: AsyncSession):
    """Test 4: Successful creation of a PREREQUISITE relationship."""
    # Create two concepts
    response_a = await client.post("/api/v1/concepts", json={"name": "Concept A"})
    response_b = await client.post("/api/v1/concepts", json={"name": "Concept B"})
    id_a = response_a.json()["id"]
    id_b = response_b.json()["id"]

    # Create the relationship
    rel_data = {
        "start_concept_id": id_a,
        "end_concept_id": id_b,
        "type": "PREREQUISITE",
    }
    response_rel = await client.post("/api/v1/relationships", json=rel_data)
    assert response_rel.status_code == 201
    assert response_rel.json()["type"] == "PREREQUISITE"

    # Verify in the database that the relationship exists
    result = await db_session.run(
        "MATCH (a:Concept {id: $id_a})-[r:PREREQUISITE]->(b:Concept {id: $id_b}) RETURN r",
        id_a=id_a,
        id_b=id_b,
    )
    record = await result.single()
    assert record is not None
    assert record["r"] is not None


async def test_create_relationship_missing_node(client: httpx.AsyncClient):
    """Test 5: Error 404 when creating a relationship if a node is not found."""
    response_a = await client.post("/api/v1/concepts", json={"name": "Concept A"})
    id_a = response_a.json()["id"]

    rel_data = {
        "start_concept_id": id_a,
        "end_concept_id": "fake-id",
        "type": "PREREQUISITE",
    }
    response_rel = await client.post("/api/v1/relationships", json=rel_data)

    assert response_rel.status_code == 404
    assert response_rel.json()["detail"] == "One or both concepts not found"


async def test_get_shortest_path(client: httpx.AsyncClient):
    """Test 6: Finding the shortest path between A, B, C."""
    # 1. Створюємо A, B, C
    id_a = (await client.post("/api/v1/concepts", json={"name": "A"})).json()["id"]
    id_b = (await client.post("/api/v1/concepts", json={"name": "B"})).json()["id"]
    id_c = (await client.post("/api/v1/concepts", json={"name": "C"})).json()["id"]

    # 2. Create relationships: A -> B -> C
    await client.post(
        "/api/v1/relationships",
        json={"start_concept_id": id_a, "end_concept_id": id_b, "type": "PREREQUISITE"},
    )
    await client.post(
        "/api/v1/relationships",
        json={"start_concept_id": id_b, "end_concept_id": id_c, "type": "PREREQUISITE"},
    )

    # 3. Find path A -> C
    response = await client.get(f"/api/v1/path?start_id={id_a}&end_id={id_c}")
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    path_nodes = data["path"]

    # 4. Verify that the path is [A, B, C]
    assert len(path_nodes) == 3
    assert path_nodes[0]["name"] == "A"
    assert path_nodes[1]["name"] == "B"
    assert path_nodes[2]["name"] == "C"


async def test_get_shortest_path_no_path(client: httpx.AsyncClient):
    """Test 7: Getting an empty path if no relationship exists."""
    id_a = (await client.post("/api/v1/concepts", json={"name": "A"})).json()["id"]
    id_c = (await client.post("/api/v1/concepts", json={"name": "C"})).json()["id"]
    # Create a different relationship to verify it is not considered
    await client.post(
        "/api/v1/relationships",
        json={"start_concept_id": id_a, "end_concept_id": id_c, "type": "RELATED_TO"},
    )

    # Find path A -> C (which does not exist since we only consider :PREREQUISITE)
    response = await client.get(f"/api/v1/path?start_id={id_a}&end_id={id_c}")
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == []
