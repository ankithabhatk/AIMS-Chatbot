#!/usr/bin/env python3
"""Test the reranker scoring directly"""

import sys
sys.path.insert(0, "/Users/maneeth/Desktop/Chat-Bot/backend")

from app.services.orchestration.engine import _rerank_chunks_by_topic
from app.services.retrieval.faiss_index import get_index

def test_reranker():
    """Test if reranker properly scores and reranks chunks"""
    
    index = get_index()
    if not index:
        print("❌ No FAISS index")
        return
    
    # Get placement chunks
    query = "Tell me about placements"
    chunks = index.keyword_search(query, k=10)
    
    print(f"Original FAISS order (top 5):")
    for i, chunk in enumerate(chunks[:5]):
        if isinstance(chunk, tuple):
            text = chunk[0][:80] if chunk[0] else ""
        else:
            text = chunk.get("text", chunk.get("content", ""))[:80]
        print(f"  [{i}] {text}...")
    
    print(f"\nAfter reranking (top 5):")
    reranked = _rerank_chunks_by_topic(chunks, query, max_chunks=5)
    for i, chunk in enumerate(reranked[:5]):
        if isinstance(chunk, tuple):
            text = chunk[0][:80] if chunk[0] else ""
        else:
            text = chunk.get("text", chunk.get("content", ""))[:80]
        print(f"  [{i}] {text}...")

if __name__ == "__main__":
    test_reranker()
