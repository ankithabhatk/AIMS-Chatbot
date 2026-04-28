from app.services.counselor.entity_extractor import extract_entities

query = "I want to do BCA"
entities = extract_entities(query)
print(f"Query: {query}")
print(f"Entities: {entities}")
