# experiments/effectiveness_verification/simulation_env.py

import networkx as nx


class KnowledgeGraphMock:
    def __init__(self):
        self.graph = nx.DiGraph()

        # CALIBRATION: Lowered c4/c5 difficulty slightly (7.0->6.5, 8.0->7.5)
        self.concepts = {
            "c1": {"id": "c1", "name": "Variables", "difficulty": 2.0},
            "c2": {"id": "c2", "name": "Loops", "difficulty": 4.0},
            "c3": {"id": "c3", "name": "Functions", "difficulty": 5.0},
            "c4": {"id": "c4", "name": "Classes", "difficulty": 6.5},
            "c5": {"id": "c5", "name": "Inheritance", "difficulty": 7.5},
            # Remedials
            "c1_rem": {"id": "c1_rem", "name": "Data Types Basics", "difficulty": 1.5},
            "c3_rem": {"id": "c3_rem", "name": "Function Syntax", "difficulty": 3.0},
            # Added a remedial for Classes
            "c4_rem": {"id": "c4_rem", "name": "OOP Concepts", "difficulty": 4.5},
        }

        self.graph.add_edge("c1", "c2")
        self.graph.add_edge("c2", "c3")
        self.graph.add_edge("c3", "c4")
        self.graph.add_edge("c4", "c5")

        self.remedials = {
            "c2": "c1_rem",
            "c4": "c3_rem",
            "c5": "c4_rem",  # Added mapping
        }

    def get_linear_path(self):
        return ["c1", "c2", "c3", "c4", "c5"]

    def get_concept(self, cid):
        return self.concepts[cid]

    def get_remedial(self, concept_id):
        rem_id = self.remedials.get(concept_id)
        return self.concepts.get(rem_id) if rem_id else None
