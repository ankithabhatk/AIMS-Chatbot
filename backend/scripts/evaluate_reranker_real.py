# backend/scripts/evaluate_reranker_real.py

import sys
import os
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.query_rewriter import rewrite_query
from app.services.reranker import simple_rerank

def run_evaluation():
    queries = ["mba fees", "placements", "hostel"]
    index = get_index()
    
    print("\n" + "="*80)
    print("REAL PIPELINE EVALUATION: RERANKER IMPACT")
    print("="*80)
    
    for query in queries:
        print(f"\nQUERY: '{query}'")
        print("-" * 40)
        
        # 1. Rewrite
        rewritten = rewrite_query(query)
        print(f"Rewritten: '{rewritten}'")
        
        # 2. Embed & Search (Top 10 candidates)
        embedding = embed_text(rewritten)
        raw_results = index.search(embedding, k=10)
        
        # Format as candidates dicts
        candidates = [
            {"content": c[0], "score": c[1], "url": c[2], "heading": c[3]}
            for c in raw_results
        ]
        
        # DISPLAY BEFORE (Top 3)
        print("\n[BEFORE RERANK] (Top 3 raw semantic matches):")
        for i, c in enumerate(candidates[:3], 1):
            print(f" {i}. Score: {c['score']:.3f} | Heading: {c['heading']}")
            print(f"    Text: {c['content'][:150]}...\n")
            
        # 3. Rerank
        reranked = simple_rerank(rewritten, candidates, min_score=0.3)
        
        # DISPLAY AFTER (Top 3)
        print("[AFTER RERANK] (Top 3 keyword-boosted matches):")
        for i, c in enumerate(reranked, 1):
            # Calculate manual boosted score for logging
            q_words = set(rewritten.lower().split())
            c_words = set(c['content'].lower().split())
            overlap = len(q_words & c_words)
            boosted = c['score'] + (0.05 * overlap)
            
            print(f" {i}. Score: {boosted:.3f} (Base: {c['score']:.3f}, Overlap: {overlap}) | Heading: {c['heading']}")
            print(f"    Text: {c['content'][:150]}...\n")

    print("="*80 + "\n")

if __name__ == "__main__":
    run_evaluation()
