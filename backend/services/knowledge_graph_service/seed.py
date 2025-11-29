import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

from src.database import close_driver, get_driver, init_driver

# --- Nodes ---

CONCEPTS = [
    {
        "id": "ff9eecf7-81fc-489d-9e8e-2f6360595f02",
        "name": "Python Basics",
        "description": "Learn the basics of syntax, variables, and loops.",
        "difficulty": 1.0,
        "estimated_time": 60,
    },
    {
        "id": "0b63688c-5068-4898-9831-7ead26d587b3",
        "name": "Data Structures",
        "description": "Lists, Dictionaries, Sets.",
        "difficulty": 2.0,
        "estimated_time": 60,
    },
    {
        "id": "21c3597d-b920-494f-b862-1f6da27da305",
        "name": "Dart Language",
        "description": "Dart basics for Flutter.",
        "difficulty": 1.0,
        "estimated_time": 60,
    },
]

# Updated Resources (Skipped for brevity as they are unchanged from existing_code.txt)
RESOURCES = [
    {
        "id": "9f56514d-c297-4796-9a65-fd6c8646c616",
        "title": "Micro-SaaS Development",
        "type": "Text",
        "url": "https://medium.com/@theabhishek.040/solo-developer-micro-saas-60k-month-12-months-41455c786fad",
        "duration": 25,
    }
]

# UPDATED: Questions with Difficulty (1.0 = Easy, 2.0 = Medium, 3.0 = Hard)
QUESTIONS = [
    # Python Basics
    {
        "id": "139d67d0-bea0-41bc-a926-189180de9971",
        "text": "What is the correct file extension for Python files?",
        "difficulty": 1.0,
        "options": '[{"text": ".pyth", "is_correct": false}, {"text": ".pt", "is_correct": false}, {"text": ".py", "is_correct": true}]',
    },
    {
        "id": "777d67d0-bea0-41bc-a926-189180de9972",
        "text": "How do you create a variable with the numeric value 5?",
        "difficulty": 1.0,
        "options": '[{"text": "x = 5", "is_correct": true}, {"text": "x == 5", "is_correct": false}, {"text": "int x = 5", "is_correct": false}]',
    },
    # Dart
    {
        "id": "888d67d0-bea0-41bc-a926-189180de9973",
        "text": "Which function is the entry point of a Dart app?",
        "difficulty": 1.0,
        "options": '[{"text": "start()", "is_correct": false}, {"text": "main()", "is_correct": true}, {"text": "init()", "is_correct": false}]',
    },
]

PREREQUISITES = [
    ("ff9eecf7-81fc-489d-9e8e-2f6360595f02", "0b63688c-5068-4898-9831-7ead26d587b3"),
]

CONCEPT_RESOURCES = [
    ("ff9eecf7-81fc-489d-9e8e-2f6360595f02", "9f56514d-c297-4796-9a65-fd6c8646c616"),
]

# (Concept ID -> Question ID)
CONCEPT_QUESTIONS = [
    ("ff9eecf7-81fc-489d-9e8e-2f6360595f02", "139d67d0-bea0-41bc-a926-189180de9971"),
    ("ff9eecf7-81fc-489d-9e8e-2f6360595f02", "777d67d0-bea0-41bc-a926-189180de9972"),
    ("21c3597d-b920-494f-b862-1f6da27da305", "888d67d0-bea0-41bc-a926-189180de9973"),
]


async def seed():
    logger.info("Seeding Neo4j database...")
    await init_driver()
    driver = get_driver()

    async with driver.session() as session:
        # 1. Clear DB (Optional - create constraints in production instead)
        # await session.run("MATCH (n) DETACH DELETE n")

        # 2. Insert Concepts
        logger.info("Inserting Concepts...")
        for c in CONCEPTS:
            await session.run(
                """
                MERGE (c:Concept {id: $id})
                SET c.name = $name,
                    c.description = $description,
                    c.difficulty = $difficulty,
                    c.estimated_time = $estimated_time
            """,
                **c,
            )

        # 3. Insert Resources
        logger.info("Inserting Resources...")
        for r in RESOURCES:
            await session.run(
                """
                MERGE (r:Resource {id: $id})
                SET r.title = $title,
                    r.type = $type,
                    r.url = $url,
                    r.duration = $duration
            """,
                **r,
            )

        # 4. Insert Questions (Updated with difficulty)
        logger.info("Inserting Questions...")
        for q in QUESTIONS:
            await session.run(
                """
                MERGE (q:Question {id: $id})
                SET q.text = $text,
                    q.options = $options,
                    q.difficulty = $difficulty
            """,
                **q,
            )

        # 5-7. Linking (Prerequisites, Resources, Questions)
        logger.info("Linking Entities...")
        for start, end in PREREQUISITES:
            await session.run(
                "MATCH (a:Concept {id: $start}), (b:Concept {id: $end}) MERGE (a)-[:PREREQUISITE]->(b)",
                start=start,
                end=end,
            )

        for cid, rid in CONCEPT_RESOURCES:
            await session.run(
                "MATCH (c:Concept {id: $cid}), (r:Resource {id: $rid}) MERGE (c)-[:HAS_RESOURCE]->(r)",
                cid=cid,
                rid=rid,
            )

        for cid, qid in CONCEPT_QUESTIONS:
            await session.run(
                "MATCH (c:Concept {id: $cid}), (q:Question {id: $qid}) MERGE (c)-[:HAS_QUESTION]->(q)",
                cid=cid,
                qid=qid,
            )

    await close_driver()
    logger.success("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
