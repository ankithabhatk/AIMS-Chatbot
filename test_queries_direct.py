"""Quick test of 5 queries directly against FAISS + retrieval"""
import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index

QUERIES = [
    "What is the admission process?",
    "What are the hostel facilities?",
    "What is the placement record?",
    "What programs does AIMS offer?",
    "What are the MBA fees?"
]

print("=" * 70)
print("TESTING 5 QUERIES")
print("=" * 70)

index = get_index()
stats = index.get_stats()
print(f"\n✓ FAISS Index loaded: {stats['document_count']} documents\n")

for i, query in enumerate(QUERIES, 1):
    print(f"\n{'='*70}")
    print(f"QUERY {i}: {query}")
    print(f"{'='*70}")
    
    try:
        # Embed query
        query_embedding = embed_text(query)
        
        # Retrieve top 5
        results = index.search(query_embedding, k=5)
        
        if not results:
            print("❌ NO RESULTS")
            continue
        
        print(f"\n✓ Retrieved {len(results)} chunks\n")
        
        for j, (content, score, url, heading, doc_id) in enumerate(results, 1):
            print(f"--- Result {j} (similarity: {score:.3f}) ---")
            print(f"Source: {url}")
            if heading:
                print(f"Heading: {heading}")
            print(f"Content: {content[:200]}...")
            print()
    
    except Exception as e:
        print(f"❌ ERROR: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
