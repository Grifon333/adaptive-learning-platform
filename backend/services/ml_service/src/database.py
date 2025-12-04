import json

from loguru import logger
from sqlalchemy import create_engine, text

from .config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=20, max_overflow=10)


def init_behavioral_table():
    """
    Creates the behavioral_profiles table if it doesn't exist.
    """
    query = text("""
        CREATE TABLE IF NOT EXISTS behavioral_profiles (
            student_id UUID PRIMARY KEY,
            procrastination_index FLOAT DEFAULT 0.0,
            gaming_score FLOAT DEFAULT 0.0,
            engagement_score FLOAT DEFAULT 0.0,
            hint_rate FLOAT DEFAULT 0.0,
            error_rate FLOAT DEFAULT 0.0,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    try:
        with engine.begin() as conn:
            conn.execute(query)
            logger.info("Initialized behavioral_profiles table.")
    except Exception as e:
        logger.error(f"Failed to init behavioral table: {e}")


def init_history_table():
    """
    Creates table to store DKT interaction sequences.
    """
    query = text("""
        CREATE TABLE IF NOT EXISTS interaction_histories (
            student_id UUID PRIMARY KEY,
            sequence JSONB DEFAULT '[]', -- List of {"concept_id": str, "correct": bool}
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    try:
        with engine.begin() as conn:
            conn.execute(query)
            logger.info("Initialized interaction_histories table.")
    except Exception as e:
        logger.error(f"Failed to init history table: {e}")


init_behavioral_table()
init_history_table()


def get_student_history(student_id: str) -> list[dict]:
    query = text("SELECT sequence FROM interaction_histories WHERE student_id = :uid")
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"uid": student_id}).fetchone()
            if result and result[0]:
                return result[0]
            return []
    except Exception as e:
        logger.error(f"DB Error fetch history: {e}")
        return []


def append_interaction(student_id: str, concept_id: str, is_correct: bool):
    """
    Appends a new interaction to the JSONB list.
    """
    new_item = json.dumps({"concept_id": concept_id, "correct": is_correct})

    # Postgres specific JSONB append
    query = text("""
        INSERT INTO interaction_histories (student_id, sequence, updated_at)
        VALUES (:uid, :item::jsonb, NOW())
        ON CONFLICT (student_id)
        DO UPDATE SET
            sequence = interaction_histories.sequence || :item_single::jsonb,
            updated_at = NOW();
    """)

    try:
        with engine.begin() as conn:
            # We pass the list for INSERT and single item for UPDATE concatenation
            # Note: Formatting JSON for SQL params can be tricky.
            # Ideally use a wrapper, but for this pure SQL approach:
            conn.execute(
                query,
                {
                    "uid": student_id,
                    "item": json.dumps([{"concept_id": concept_id, "correct": is_correct}]),
                    "item_single": new_item,
                },
            )
    except Exception as e:
        logger.error(f"DB Error append history: {e}")
        raise


def update_behavioral_profile(student_id: str, p_idx: float, g_score: float, e_score: float):
    """
    Updates the behavioral vector B_t^u for a student.
    """
    query = text("""
        INSERT INTO behavioral_profiles (student_id, procrastination_index, gaming_score, engagement_score, hint_rate, error_rate, updated_at)
        VALUES (:student_id, :p_idx, :g_score, :e_score, :h_rate, :err_rate, NOW())
        ON CONFLICT (student_id)
        DO UPDATE SET
            procrastination_index = EXCLUDED.procrastination_index,
            gaming_score = EXCLUDED.gaming_score,
            engagement_score = EXCLUDED.engagement_score,
            hint_rate = EXCLUDED.hint_rate,
            error_rate = EXCLUDED.error_rate,
            updated_at = NOW();
    """)

    try:
        with engine.begin() as conn:
            conn.execute(query, {"student_id": student_id, "p_idx": p_idx, "g_score": g_score, "e_score": e_score})
            logger.info(f"Updated behavioral profile for {student_id}")
    except Exception as e:
        logger.error(f"DB Error behavioral upsert: {e}")
        raise


def get_behavioral_profile(student_id: str) -> dict:
    query = text("""
        SELECT procrastination_index, gaming_score, engagement_score
        FROM behavioral_profiles
        WHERE student_id = :student_id
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(query, {"student_id": student_id}).fetchone()
            if row:
                return {"procrastination_index": row[0], "gaming_score": row[1], "engagement_score": row[2]}
            return {"procrastination_index": 0.0, "gaming_score": 0.0, "engagement_score": 0.0}
    except Exception as e:
        logger.error(f"DB Error fetch behavior: {e}")
        return {}


# Deprecate
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
            conn.execute(query, {"student_id": student_id, "concept_id": concept_id, "mastery": mastery_level})
            logger.info(f"Upserted mastery for {student_id}/{concept_id}")
    except Exception as e:
        logger.error(f"DB Error during upsert: {e}")
        raise


def update_knowledge_state_batch(updates: list[dict]):
    """
    Batch UPSERT for knowledge states.
    updates: list of dicts with keys {'student_id', 'concept_id', 'mastery_level'}
    """
    if not updates:
        return

    # Constructing a VALUES list for the query
    # Note: In a real high-load scenario, we might use postgres-specific unnest or copy,
    # but for <100 items, a loop with execute_many or a generated query is fine.
    # We will use explicit transaction for safety.

    query = text("""
        INSERT INTO knowledge_states (student_id, concept_id, mastery_level, updated_at, confidence)
        VALUES (:student_id, :concept_id, :mastery_level, NOW(), 0.9)
        ON CONFLICT (student_id, concept_id)
        DO UPDATE SET
            mastery_level = EXCLUDED.mastery_level,
            updated_at = NOW(),
            confidence = 0.9;
    """)

    try:
        with engine.begin() as conn:
            # SQLAlchemy execute with a list of dicts performs an executemany
            conn.execute(query, updates)
            logger.info(f"Batch upserted {len(updates)} knowledge states.")
    except Exception as e:
        logger.error(f"DB Error during batch upsert: {e}")
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
            result = conn.execute(query, {"student_id": student_id, "concept_ids": concept_ids}).fetchall()
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
