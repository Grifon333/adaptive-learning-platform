import heapq
from typing import Any, cast

from loguru import logger
from neo4j import AsyncSession


class Pathfinder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_optimal_path(
        self, start_id: str | None, goal_id: str, knowledge: dict[str, float], prefs: dict[str, Any]
    ) -> tuple[list[dict], int, float]:
        """
        Implements A* Algorithm on the Concept Graph.
        Returns: (List of Concepts with embedded Resources, Total Time, Total Complexity)
        """

        start_id = await self._resolve_start_id(start_id, goal_id)

        # 1. Initialization
        # Priority Queue: (f_score, current_node_id)
        open_set: list[tuple[float, str]] = []
        heapq.heappush(open_set, (0.0, start_id))

        # Maps
        came_from: dict[str, str] = {}  # node_id -> parent_id
        g_score = {start_id: 0.0}  # Cost from start

        # Cache for node data to avoid repeated DB hits
        nodes_cache = {}

        # Pre-fetch goal info for heuristic
        goal_node = await self._get_node(goal_id)
        if not goal_node:
            raise ValueError(f"Goal node {goal_id} not found")
        nodes_cache[goal_id] = goal_node

        while open_set:
            _, current_id = heapq.heappop(open_set)

            if current_id == goal_id:
                return await self._reconstruct_path(came_from, current_id, nodes_cache, prefs)

            # Ensure current node is in cache
            if current_id not in nodes_cache:
                node = await self._get_node(current_id)
                if node is None:
                    raise ValueError(f"Node {current_id} not found")
                nodes_cache[current_id] = node

            # Fetch Neighbors (Prerequisites -> Next Steps)
            neighbors = await self._get_neighbors(current_id)

            for neighbor in neighbors:
                n_id = neighbor["id"]
                nodes_cache[n_id] = neighbor

                # --- COST CALCULATION ---
                # Cost(n) = Time * (1 + alpha * max(0, Difficulty - Mastery))
                mastery = knowledge.get(n_id, 0.0)
                difficulty = neighbor.get("difficulty", 1.0)
                est_time = neighbor.get("estimated_time", 30)

                # If mastered, cost is minimal (review time, e.g., 20%)
                if mastery > 0.8:
                    step_cost = est_time * 0.2
                else:
                    # Difficulty penalty: Harder concepts cost more "effort"
                    diff_penalty = max(0, difficulty - (mastery * 5.0 + 1.0))
                    step_cost = est_time * (1.0 + 1.5 * diff_penalty)

                tentative_g = g_score[current_id] + step_cost

                if tentative_g < g_score.get(n_id, float("inf")):
                    came_from[n_id] = current_id
                    g_score[n_id] = tentative_g

                    # --- HEURISTIC (h) ---
                    # Using 0.0 effectively makes this Dijkstra, which is safe/correct.
                    # A better heuristic requires graph distance pre-calculation.
                    h_score = 0.0

                    f_score = tentative_g + h_score
                    heapq.heappush(open_set, (f_score, n_id))

        # If queue empty and goal not reached
        raise ValueError(f"No path found from {start_id} to {goal_id}")

    async def _resolve_start_id(self, start_id: str | None, goal_id: str) -> str:
        if start_id:
            return start_id
        logger.info(f"No start_id provided. Finding root ancestor for goal {goal_id}...")
        root = await self._find_root_concept(goal_id)
        if root:
            return cast(str, root)
        logger.warning(f"No dependencies found. Setting start = goal ({goal_id})")
        return goal_id

    async def _find_root_concept(self, goal_id: str) -> str | None:
        """
        Finds the furthest ancestor (root) of the goal concept.
        This represents the absolute beginning of the learning tree.
        """
        # Search backwards (<-[:PREREQUISITE]) until we hit a node with no incoming prerequisites
        query = """
        MATCH (goal:Concept {id: $id})
        MATCH (root:Concept)-[:PREREQUISITE*0..]->(goal)
        WHERE NOT (root)<-[:PREREQUISITE]-()
        RETURN root.id as id LIMIT 1
        """
        try:
            result = await self.db.run(query, {"id": goal_id})
            record = await result.single()
            if record:
                return cast(str, record["id"])
            return None
        except Exception as e:
            logger.error(f"Error finding root concept: {e}")
            return None

    async def _get_node(self, concept_id: str) -> dict | None:
        query = """
        MATCH (c:Concept {id: $id})
        OPTIONAL MATCH (c)-[:HAS_RESOURCE]->(r:Resource)
        RETURN c, collect(r) as resources
        """
        result = await self.db.run(query, {"id": concept_id})
        record = await result.single()
        if not record:
            return None

        node = dict(record["c"])
        node["resources"] = [dict(r) for r in record["resources"] if r]
        return node

    async def _get_neighbors(self, concept_id: str) -> list[dict]:
        # Direction: We follow Prerequisite chains forward (Start -> Goal)
        query = """
        MATCH (current:Concept {id: $id})-[:PREREQUISITE]->(next:Concept)
        OPTIONAL MATCH (next)-[:HAS_RESOURCE]->(r:Resource)
        RETURN next, collect(r) as resources
        """
        result = await self.db.run(query, {"id": concept_id})
        neighbors = []
        async for record in result:
            node = dict(record["next"])
            node["resources"] = [dict(r) for r in record["resources"] if r]
            neighbors.append(node)
        return neighbors

    async def _reconstruct_path(self, came_from, current, nodes_cache, prefs) -> tuple[list[dict], int, float]:
        path = []
        total_time = 0
        total_complexity = 0.0

        while current in came_from:
            node_data = nodes_cache[current]
            best_resource = self._select_best_resource(node_data["resources"], prefs)
            if best_resource:
                node_data["resources"] = [best_resource]
            path.append(node_data)
            total_time += node_data.get("estimated_time", 0)
            total_complexity += node_data.get("difficulty", 0)
            current = came_from[current]

        if current in nodes_cache:
            start_node = nodes_cache[current]
            best_resource = self._select_best_resource(start_node["resources"], prefs)
            if best_resource:
                start_node["resources"] = [best_resource]
            path.append(start_node)

        path.reverse()
        return path, total_time, total_complexity

    def _select_best_resource(self, resources: list[dict], prefs: dict[str, Any]) -> dict | None:
        if not resources:
            return None

        def score(res):
            s = 0
            rtype = res.get("type", "").lower()
            if "video" in rtype:
                s += prefs.get("visual", 0)
            elif "text" in rtype or "article" in rtype:
                s += prefs.get("reading", 0)
            elif "quiz" in rtype:
                s += prefs.get("kinesthetic", 0)
            return s

        resources.sort(key=score, reverse=True)
        return resources[0]
