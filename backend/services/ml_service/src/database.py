from sqlalchemy import create_engine, text
from .config import settings
from loguru import logger

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

def update_knowledge_state(student_id: str, concept_id: str, mastery_level: float):
    """
    Updates or creates a record of the student's knowledge status.
    """
    query = text("""
        INSERT INTO knowledge_states (student_id, concept_id, mastery_level, updated_at, confidence)
        VALUES (:student_id, :concept_id, :mastery, NOW(), 0.5)
        ON CONFLICT (id) DO UPDATE
        SET mastery_level = :mastery,
            updated_at = NOW();
    """)

    # Note: We do not have a unique key (student_id, concept_id) in the knowledge_states table
    # in the current create script (there is id SERIAL PRIMARY KEY).
    # Therefore, we will first check if the record exists and update it, or create a new one.

    check_query = text("""
        SELECT id FROM knowledge_states
        WHERE student_id = :student_id AND concept_id = :concept_id
    """)

    update_query = text("""
        UPDATE knowledge_states
        SET mastery_level = :mastery, updated_at = NOW()
        WHERE id = :pk
    """)

    insert_query = text("""
        INSERT INTO knowledge_states (student_id, concept_id, mastery_level, updated_at, confidence)
        VALUES (:student_id, :concept_id, :mastery, NOW(), 0.5)
    """)

    try:
        with engine.begin() as conn: # begin() automatically commits
            result = conn.execute(check_query, {"student_id": student_id, "concept_id": concept_id}).fetchone()

            if result:
                conn.execute(update_query, {"mastery": mastery_level, "pk": result[0]})
                logger.info(f"Updated mastery for student {student_id}, concept {concept_id}")
            else:
                conn.execute(insert_query, {
                    "student_id": student_id,
                    "concept_id": concept_id,
                    "mastery": mastery_level
                })
                logger.info(f"Created mastery record for student {student_id}, concept {concept_id}")

    except Exception as e:
        logger.error(f"DB Error: {e}")
        raise


def get_knowledge_state(student_id: str, concept_id: str):
    """
    Receives the current state of knowledge from the database.
    """
    query = text("""
        SELECT mastery_level, confidence
        FROM knowledge_states
        WHERE student_id = :student_id AND concept_id = :concept_id
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"student_id": student_id, "concept_id": concept_id}).fetchone()
        if result:
            return {"mastery_level": result[0], "confidence": result[1]}
        else:
            return {"mastery_level": 0.0, "confidence": 0.0}


def get_all_student_knowledge(student_id: str):
    """
    Returns the dictionary {concept_id: mastery_level} for the student.
    """
    query = text("""
        SELECT concept_id, mastery_level
        FROM knowledge_states
        WHERE student_id = :student_id
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"student_id": student_id}).fetchall()
        return {row[0]: row[1] for row in result}
