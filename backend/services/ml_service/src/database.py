from sqlalchemy import create_engine, text
from .config import settings
from loguru import logger

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=20, max_overflow=10)

def update_knowledge_state(student_id: str, concept_id: str, mastery_level: float):
    """
    Thread-safe UPSERT using PostgreSQL ON CONFLICT.
    """
    # Using parameterized SQL for security
    query = text("""
        INSERT INTO knowledge_states (student_id, concept_id, mastery_level, updated_at, confidence)
        VALUES (:student_id, :concept_id, :mastery, NOW(), 0.5)
        ON CONFLICT (student_id, concept_id)
        DO UPDATE SET
            mastery_level = EXCLUDED.mastery_level,
            updated_at = NOW();
    """)

    try:
        with engine.begin() as conn:
            conn.execute(query, {
                "student_id": student_id,
                "concept_id": concept_id,
                "mastery": mastery_level
            })
            logger.info(f"Upserted mastery for {student_id}/{concept_id}")
    except Exception as e:
        logger.error(f"DB Error during upsert: {e}")
        raise

def get_knowledge_states_batch(student_id: str, concept_ids: list[str]) -> dict[str, float]:
    """
    Batch retrieval of mastery levels. Returns dict {concept_id: mastery}.
    """
    if not concept_ids:
        return {}

    query = text("""
        SELECT concept_id, mastery_level
        FROM knowledge_states
        WHERE student_id = :student_id AND concept_id = ANY(:concept_ids)
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {
                "student_id": student_id,
                "concept_ids": concept_ids
            }).fetchall()
            found_states = {row[0]: row[1] for row in result}
            return {cid: found_states.get(cid, 0.0) for cid in concept_ids}
    except Exception as e:
        logger.error(f"DB Error batch fetch: {e}")
        return {cid: 0.0 for cid in concept_ids}


def get_all_student_knowledge(student_id: str):
    """
    Returns the dictionary {concept_id: mastery_level} for the student.
    """
    query = text("""
        SELECT concept_id, mastery_level
        FROM knowledge_states
        WHERE student_id = :student_id
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"student_id": student_id}).fetchall()
            return {row[0]: row[1] for row in result}
    except Exception as e:
        logger.error(f"DB Error fetch all: {e}")
        return {}
