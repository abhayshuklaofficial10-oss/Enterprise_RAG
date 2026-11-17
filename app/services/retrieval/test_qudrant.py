
from app.services.retrieval.qdrant_service import (
    search_enterprise_knowledge
)

print("Testing Qdrant retrieval...")

results = search_enterprise_knowledge(
    "What is Kubernetes?",
    limit=5
)

print("Retrieved documents:", len(results))

for i, doc in enumerate(results, 1):

    print(f"\nDocument {i}")
    print("Source:", doc["source"])
    print("Score:", doc["score"])
    print("Content:", doc["content"][:300])
