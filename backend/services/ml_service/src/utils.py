import json
import os

from loguru import logger

# Path to the mapping file
MAPPING_FILE = os.path.join(os.path.dirname(__file__), "concept_mapping.json")


def load_concept_mapping():
    """
    Loads the mapping from UUIDs to Model Indices.
    """
    if not os.path.exists(MAPPING_FILE):
        logger.warning(f"Mapping file not found at {MAPPING_FILE}. Using empty map.")
        return {}

    try:
        with open(MAPPING_FILE) as f:
            data = json.load(f)
            # Ensure keys are strings (UUIDs) and values are ints
            return {k: int(v) for k, v in data.items()}
    except Exception as e:
        logger.error(f"Failed to load concept mapping: {e}")
        return {}


# Load on module import (effectively a singleton)
CONCEPT_TO_INDEX = load_concept_mapping()

# Create reverse mapping for RL decoding
INDEX_TO_CONCEPT = {v: k for k, v in CONCEPT_TO_INDEX.items()}


def get_concept_index(concept_id: str) -> int:
    """
    Returns the integer index for a concept UUID.
    Returns 0 (default) if unknown, to prevent crashes.
    """
    return CONCEPT_TO_INDEX.get(concept_id, 0)


def get_concept_from_index(index: int) -> str | None:
    """
    Returns the UUID for a model integer index.
    """
    return INDEX_TO_CONCEPT.get(index)
