# TODO
# Mapping of Concept UUIDs to Integer Indices for the Embedding Layer
# Based on seed.py data
CONCEPT_TO_INDEX = {
    # Python Branch
    "ff9eecf7-81fc-489d-9e8e-2f6360595f02": 0,  # Python Basics
    "0b63688c-5068-4898-9831-7ead26d587b3": 1,  # Data Structures
    "674c74c6-8525-4a85-86ec-04ab12a032d2": 2,  # Algorithms
    "de53b2dd-b583-4d9c-a190-65e83b26c2b6": 3,  # Data Science Intro
    # Flutter Branch
    "21c3597d-b920-494f-b862-1f6da27da305": 4,  # Dart Language
    "45232220-1b22-4eba-a97f-e50606b2b5ef": 5,  # Flutter Widgets
    "9a4c9a78-eca9-4395-8798-3f0956f95fad": 6,  # Flutter Advanced
}


def get_concept_index(concept_id: str) -> int:
    return CONCEPT_TO_INDEX.get(concept_id, 0)
