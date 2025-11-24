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
        "id": "674c74c6-8525-4a85-86ec-04ab12a032d2",
        "name": "Algorithms",
        "description": "Sorting and Searching.",
        "difficulty": 3.0,
        "estimated_time": 60,
    },
    {
        "id": "de53b2dd-b583-4d9c-a190-65e83b26c2b6",
        "name": "Data Science Intro",
        "description": "Pandas and NumPy basics.",
        "difficulty": 4.0,
        "estimated_time": 60,
    },
    {
        "id": "21c3597d-b920-494f-b862-1f6da27da305",
        "name": "Dart Language",
        "description": "Dart basics for Flutter.",
        "difficulty": 1.0,
        "estimated_time": 60,
    },
    {
        "id": "45232220-1b22-4eba-a97f-e50606b2b5ef",
        "name": "Flutter Widgets",
        "description": "Stateless and Stateful widgets.",
        "difficulty": 2.0,
        "estimated_time": 60,
    },
    {
        "id": "9a4c9a78-eca9-4395-8798-3f0956f95fad",
        "name": "Flutter Advanced",
        "description": "State Management and Architecture.",
        "difficulty": 5.0,
        "estimated_time": 60,
    },
]

RESOURCES = [
    {
        "id": "cafa0c6c-d53b-4a1a-8219-2b1b2abf5d97",
        "title": "Use Git Like a Senior Engineer",
        "type": "Text",
        "url": "https://medium.com/the-software-journal/use-git-like-a-senior-engineer-42548aee6374",
        "duration": 15,
    },
    {
        "id": "71d54180-c55d-43c5-93b8-86ca67067c61",
        "title": "Why Flutter 3.38 Is the Biggest Upgrade",
        "type": "Text",
        "url": "https://medium.com/@flutter-app/why-flutter-3-38-is-the-biggest-performance-upgrade-since-flutter-3-7-f2597d6cc231",
        "duration": 10,
    },
    {
        "id": "f60dbda7-2871-433e-a917-843443a76ae5",
        "title": "10 Flutter Hacks",
        "type": "Text",
        "url": "https://medium.com/@avula.koti.realpage/10-flutter-hacks-every-senior-developer-should-know-428f6cf9f70c",
        "duration": 20,
    },
    {
        "id": "9f56514d-c297-4796-9a65-fd6c8646c616",
        "title": "Micro-SaaS Development",
        "type": "Text",
        "url": "https://medium.com/@theabhishek.040/solo-developer-micro-saas-60k-month-12-months-41455c786fad",
        "duration": 25,
    },
    {
        "id": "aa0ca8eb-f27f-414a-b3c0-a7a847c14e3f",
        "title": "How To Take Notes as a Programmer",
        "type": "Video",
        "url": "https://www.youtube.com/watch?v=fVMlUd9orf4",
        "duration": 12,
    },
    {
        "id": "b1aca6bb-7aea-48c9-91ec-b409b620a936",
        "title": "How to progress faster in tech",
        "type": "Video",
        "url": "https://www.youtube.com/watch?v=c5BIA5RpSpo",
        "duration": 18,
    },
]

QUESTIONS = [
    {
        "id": "139d67d0-bea0-41bc-a926-189180de9971",
        "text": "What is the main advantage of Flutter?",
        "options": '[{"text": "He uses Python", "is_correct": false}, {"text": "Single code base for iOS and Android", "is_correct": true}, {"text": "It is compiled in Java.", "is_correct": false}]',
    }
]

# (Start ID -> End ID)
PREREQUISITES = [
    ("ff9eecf7-81fc-489d-9e8e-2f6360595f02", "0b63688c-5068-4898-9831-7ead26d587b3"),
    ("0b63688c-5068-4898-9831-7ead26d587b3", "674c74c6-8525-4a85-86ec-04ab12a032d2"),
    ("674c74c6-8525-4a85-86ec-04ab12a032d2", "de53b2dd-b583-4d9c-a190-65e83b26c2b6"),
    ("21c3597d-b920-494f-b862-1f6da27da305", "45232220-1b22-4eba-a97f-e50606b2b5ef"),
    ("45232220-1b22-4eba-a97f-e50606b2b5ef", "9a4c9a78-eca9-4395-8798-3f0956f95fad"),
]

# (Concept ID -> Resource ID)
CONCEPT_RESOURCES = [
    ("ff9eecf7-81fc-489d-9e8e-2f6360595f02", "9f56514d-c297-4796-9a65-fd6c8646c616"),
    ("674c74c6-8525-4a85-86ec-04ab12a032d2", "f60dbda7-2871-433e-a917-843443a76ae5"),
    ("674c74c6-8525-4a85-86ec-04ab12a032d2", "aa0ca8eb-f27f-414a-b3c0-a7a847c14e3f"),
    ("de53b2dd-b583-4d9c-a190-65e83b26c2b6", "b1aca6bb-7aea-48c9-91ec-b409b620a936"),
    ("45232220-1b22-4eba-a97f-e50606b2b5ef", "cafa0c6c-d53b-4a1a-8219-2b1b2abf5d97"),
    ("9a4c9a78-eca9-4395-8798-3f0956f95fad", "71d54180-c55d-43c5-93b8-86ca67067c61"),
]

# (Concept ID -> Question ID)
CONCEPT_QUESTIONS = [
    ("ff9eecf7-81fc-489d-9e8e-2f6360595f02", "139d67d0-bea0-41bc-a926-189180de9971")
]


async def seed():
    logger.info("Seeding Neo4j database...")
    await init_driver()
    driver = get_driver()

    async with driver.session() as session:
        # 1. Clear DB (Optional)
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

        # 4. Insert Questions
        logger.info("Inserting Questions...")
        for q in QUESTIONS:
            await session.run(
                """
                MERGE (q:Question {id: $id})
                SET q.text = $text,
                    q.options = $options
            """,
                **q,
            )

        # 5. Create PREREQUISITE Relationships
        logger.info("Linking Prerequisites...")
        for start, end in PREREQUISITES:
            await session.run(
                """
                MATCH (a:Concept {id: $start}), (b:Concept {id: $end})
                MERGE (a)-[:PREREQUISITE]->(b)
            """,
                start=start,
                end=end,
            )

        # 6. Create HAS_RESOURCE Relationships
        logger.info("Linking Resources...")
        for cid, rid in CONCEPT_RESOURCES:
            await session.run(
                """
                MATCH (c:Concept {id: $cid}), (r:Resource {id: $rid})
                MERGE (c)-[:HAS_RESOURCE]->(r)
            """,
                cid=cid,
                rid=rid,
            )

        # 7. Create HAS_QUESTION Relationships
        logger.info("Linking Questions...")
        for cid, qid in CONCEPT_QUESTIONS:
            await session.run(
                """
                MATCH (c:Concept {id: $cid}), (q:Question {id: $qid})
                MERGE (c)-[:HAS_QUESTION]->(q)
            """,
                cid=cid,
                qid=qid,
            )

    await close_driver()
    logger.success("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
