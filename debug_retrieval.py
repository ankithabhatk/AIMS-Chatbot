#!/usr/bin/env python3
"""Debug what chunks are being retrieved and scored"""

import sys
sys.path.insert(0, "/Users/maneeth/Desktop/Chat-Bot/backend")

from app.services.retrieval.faiss_index import get_index

def debug_retrieval():
    """See what FAISS returns for placements"""
    
    index = get_index()
    if not index:
        print("❌ No FAISS index")
        return
    
    queries = [
        ("Tell me about placements", ["placement", "salary", "lpa"]),
        ("Tell me about campus facilities", ["hostel", "facility", "library"]),
    ]
    
    for query, expected_kw in queries:
        print(f"\n{'='*70}")
        print(f"Query: '{query}'")
        print(f"Expected keywords: {expected_kw}")
        print('='*70)
        
        # Get raw FAISS results
        chunks = index.keyword_search(query, k=10)
        print(f"Retrieved {len(chunks)} chunks from FAISS")
        
        for i, chunk in enumerate(chunks[:5]):
            if isinstance(chunk, tuple):
                text = chunk[0][:150] if chunk[0] else ""
                score = chunk[1] if len(chunk) > 1 else 0
            else:
                text = chunk.get("text", chunk.get("content", ""))[:150]
                score = chunk.get("score", 0)
            
            # Check for keywords
            text_lower = text.lower()
            found = [kw for kw in expected_kw if kw in text_lower]
            
            print(f"\n  [{i}] Score: {score:.3f}")
            print(f"      Text: {text}...")
            print(f"      Keywords found: {found}")

if __name__ == "__main__":
    debug_retrieval()
