import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.retrieval.faiss_index import FAISSIndex
from app.services.retrieval.faiss_index import FAISSIndex
from app.services.embeddings.embedding_service import embed_text

def check_gaps():
    print("Loading FAISS index...")
    index = FAISSIndex()
    
    queries = [
        "PhD programs offered",
        "BA Journalism and Psychology",
        "B.Sc Microbiology",
        "PGDM vs MBA",
        "Master of Social Work MSW",
        "Master of Fine Arts MFA",
        "Diploma in Hospitality"
    ]
    
    results = {}
    for query in queries:
        print(f"\nChecking: {query}")
        embedding = embed_text(query)
        hits = index.search(embedding, k=3)
        
        results[query] = []
        for hit in hits:
            # results[query].append((full_text, similarity, url, heading, doc_id, source, priority, course, topic, importance))
            text, similarity, url, heading = hit[0], hit[1], hit[2], hit[3]
            results[query].append({
                "similarity": similarity,
                "url": url,
                "heading": heading,
                "text_snippet": text[:200]
            })
            print(f"  [{similarity:.4f}] {heading} ({url})")

    with open("retrieval_gaps_audit.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    check_gaps()
