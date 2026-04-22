# backend/scripts/evaluate_reliability_matrix.py

import sys
import os
import asyncio

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.query_rewriter import rewrite_query
from app.services.reranker import simple_rerank
from app.services.response.confidence import calculate_confidence
from app.services.llm.answer_generator import get_answer_generator

async def run_reliability_test():
    queries = [
        "What is AIMS Institutes?",       # Expected: High Confidence / Confident Answer
        "placements at aims",              # Expected: Medium Confidence / Disclaimer
        "mba fees",                        # Expected: Low Confidence / Smart Fallback
        "hostel facilities"                # Expected: Low Confidence / Smart Fallback
    ]
    
    index = get_index()
    answer_gen = get_answer_generator()
    
    FALLBACK_THRESHOLD = 0.55
    CONFIDENCE_THRESHOLD = 0.75
    
    print("\n" + "="*90)
    print("FINAL RELIABILITY MATRIX EVALUATION")
    print("="*90)
    
    for query in queries:
        print(f"\nQUERY: '{query}'")
        print("-" * 40)
        
        # 1. Rewrite
        rewritten = rewrite_query(query)
        
        # 2. Search & Rerank
        embedding = embed_text(rewritten)
        raw_results = index.search(embedding, k=10)
        candidates = [
            {"content": r[0], "score": r[1], "url": r[2], "heading": r[3]}
            for r in raw_results
        ]
        reranked = simple_rerank(rewritten, candidates, min_score=0.3)
        
        # 3. Confidence Factor
        confidence = calculate_confidence(rewritten, reranked)
        print(f"Confidence Score: {confidence:.2f}")
        
        # 4. DECISION BRANCHING
        if confidence < FALLBACK_THRESHOLD:
            print("BRANCH: [LOW CONFIDENCE] -> Smart Fallback Triggered")
            final_answer = (
                f"I couldn't find exact details about '{query}' right now. "
                "For the most accurate information, I recommend contacting admissions office."
            )
        else:
            final_answer = answer_gen.synthesize(query, [
                (r["content"], r["score"], r["url"], r["heading"]) for r in reranked
            ])
            
            if confidence < CONFIDENCE_THRESHOLD:
                 print("BRANCH: [MEDIUM CONFIDENCE] -> Answer + Disclaimer Triggered")
                 final_answer += "\n\nFor more specific details, please contact the admissions office."
            else:
                 print("BRANCH: [HIGH CONFIDENCE] -> Confident Structured Answer")
                 
        print(f"\nFINAL RESPONSE:\n{final_answer}")
        print("\n" + "."*60)

    print("="*90 + "\n")

if __name__ == "__main__":
    asyncio.run(run_reliability_test())
