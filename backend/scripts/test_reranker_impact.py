# backend/scripts/test_reranker_impact.py

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.reranker import simple_rerank

def test_reranker_logic():
    # Mock FAISS results for query "mba fees"
    # Note: Chunks might be semantically similar but lack exact keywords
    results = [
        {"content": "AIMS college offers various management programs like MBA and BBA.", "score": 0.65},
        {"content": "The hostel fees for the academic year 2024 is listed on our portal.", "score": 0.60},
        {"content": "MBA fees at AIMS is 5 Lakhs per year inclusive of tuition and lab.", "score": 0.55}, # Keywords: MBA, fees
        {"content": "Student life at the college is vibrant with many clubs.", "score": 0.40},
    ]
    
    query = "mba fees aims college"
    
    print("\n" + "="*70)
    print("TESTING RERANKER LOGIC: Query = 'mba fees aims college'")
    print("="*70)
    
    print("BEFORE RERANKING:")
    for i, r in enumerate(results, 1):
        print(f"{i}. Score: {r['score']:.3f} | Text: {r['content'][:50]}...")
        
    reranked = simple_rerank(query, results)
    
    print("\nAFTER RERANKING (Top 3):")
    for i, r in enumerate(reranked, 1):
        # Calculate what the score should be for logging
        q_words = set(query.lower().split())
        c_words = set(r['content'].lower().split())
        overlap = len(q_words & c_words)
        boosted_score = r['score'] + (0.05 * overlap)
        
        print(f"{i}. Boosted Score: {boosted_score:.3f} (Base: {r['score']:.3f}, Overlap: {overlap})")
        print(f"   Text: {r['content'][:80]}...")
        
    # Check if the MBA fees chunk moved up
    if reranked[0]['content'].startswith("MBA fees"):
        print("\n✅ SUCCESS: Keyword-relevant chunk moved to rank 1!")
    else:
        print("\n❌ FAILURE: Keyword-relevant chunk did not reach rank 1.")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_reranker_logic()
