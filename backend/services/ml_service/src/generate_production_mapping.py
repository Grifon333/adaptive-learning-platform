import json

# 1. These are the UUIDs from your seed.py / Knowledge Graph
# (I extracted these from your knowledge_graph_service.txt seed.py logic)
# In a real scenario, you'd fetch these from DB.
ALP_CONCEPTS = [
    # Concepts from your seed.py
    "fea73b7d-9755-55a8-9b1f-ee89c1fe7c05",  # Python Syntax & Variables
    "f904d9df-edf4-5f24-8607-9206af8c1e9b",  # Control Flow
    "8f7fbd8b-78d0-5cef-8aa1-28d1d3f36893",  # Functions
    "d9121dcd-d6e3-5691-8a57-b21cd690ce6b",  # Data Structures
    "77bea151-fe78-5e8b-99a6-1446a27d32f6",  # Object-Oriented Programming
    "5d5da634-2b94-539b-8972-04e76e2fa128",  # Error Handling
]

# 2. Map your UUIDs to the indices the model knows (0, 1, 2, 3...)
# The model you trained has roughly 123 input slots. We will use the first N slots.
production_mapping = {}

for index, uuid_str in enumerate(ALP_CONCEPTS):
    production_mapping[uuid_str] = index

# 3. Save this file to be used by ML Service
print("Generated Mapping:")
print(json.dumps(production_mapping, indent=2))

with open("concept_mapping.json", "w") as f:
    json.dump(production_mapping, f)

print("\n[SUCCESS] Saved to 'concept_mapping.json'. Upload this to ml_service/src/")
