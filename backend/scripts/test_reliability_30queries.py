#!/usr/bin/env python3
"""
Comprehensive Reliability Test
30+ real queries across different categories
Logs all details for manual evaluation
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.response.filter import filter_results_by_relevance
from app.services.response.confidence import calculate_confidence, get_confidence_label
from app.services.llm.answer_generator import get_answer_generator


# Real queries from different categories
QUERIES = [
    # ADMISSIONS (8 queries)
    {
        "query": "What is the admission process?",
        "category": "admissions",
        "expected": "answer"  # Should return meaningful answer
    },
    {
        "query": "What documents do I need to apply?",
        "category": "admissions",
        "expected": "answer"
    },
    {
        "query": "What are the eligibility criteria?",
        "category": "admissions",
        "expected": "answer"
    },
    {
        "query": "What is the application deadline?",
        "category": "admissions",
        "expected": "answer"
    },
    {
        "query": "Do you accept international students?",
        "category": "admissions",
        "expected": "answer"
    },
    {
        "query": "What is the fee structure?",
        "category": "admissions",
        "expected": "answer"
    },
    {
        "query": "How long does the admission process take?",
        "category": "admissions",
        "expected": "answer"
    },
    {
        "query": "Can I apply online?",
        "category": "admissions",
        "expected": "answer"
    },
    
    # COURSES/PROGRAMS (8 queries)
    {
        "query": "What programs does AIMS offer?",
        "category": "courses",
        "expected": "answer"
    },
    {
        "query": "Tell me about the BBA program",
        "category": "courses",
        "expected": "answer"
    },
    {
        "query": "What is the MBA specialization?",
        "category": "courses",
        "expected": "answer"
    },
    {
        "query": "How long is the MBA program?",
        "category": "courses",
        "expected": "answer"
    },
    {
        "query": "Does AIMS offer engineering programs?",
        "category": "courses",
        "expected": "answer"
    },
    {
        "query": "Are there any online courses?",
        "category": "courses",
        "expected": "answer"
    },
    {
        "query": "What is the curriculum like?",
        "category": "courses",
        "expected": "answer"
    },
    {
        "query": "Can I pursue dual degrees?",
        "category": "courses",
        "expected": "answer"
    },
    
    # PLACEMENTS/CAREERS (6 queries)
    {
        "query": "What is the placement rate?",
        "category": "placements",
        "expected": "answer"
    },
    {
        "query": "Which companies recruit from AIMS?",
        "category": "placements",
        "expected": "answer"
    },
    {
        "query": "What is the average salary?",
        "category": "placements",
        "expected": "answer"
    },
    {
        "query": "Are there internship opportunities?",
        "category": "placements",
        "expected": "answer"
    },
    {
        "query": "What is the career support like?",
        "category": "placements",
        "expected": "answer"
    },
    {
        "query": "Do you have alumni network?",
        "category": "placements",
        "expected": "answer"
    },
    
    # CAMPUS/FACILITIES (4 queries)
    {
        "query": "Does AIMS have hostel facilities?",
        "category": "campus",
        "expected": "answer"
    },
    {
        "query": "What are the library facilities?",
        "category": "campus",
        "expected": "answer"
    },
    {
        "query": "Is there a gym or sports complex?",
        "category": "campus",
        "expected": "answer"
    },
    {
        "query": "What is the location of the campus?",
        "category": "campus",
        "expected": "answer"
    },
    
    # VAGUE/EDGE CASES (4 queries)
    {
        "query": "fees",
        "category": "vague",
        "expected": "answer_or_fallback"  # Might answer or fallback
    },
    {
        "query": "hostel",
        "category": "vague",
        "expected": "answer_or_fallback"
    },
    {
        "query": "How much does it cost?",
        "category": "vague",
        "expected": "answer_or_fallback"
    },
    {
        "query": "Tell me everything about AIMS",
        "category": "vague",
        "expected": "answer_or_fallback"
    },
    
    # WRONG QUERIES (should trigger fallback)
    {
        "query": "Does AIMS have a space engineering program?",
        "category": "wrong",
        "expected": "fallback"
    },
    {
        "query": "What is your underwater basket weaving program?",
        "category": "wrong",
        "expected": "fallback"
    },
    {
        "query": "When does the robotics competition happen?",
        "category": "wrong",
        "expected": "fallback"
    },
    {
        "query": "What are your nuclear physics research centers?",
        "category": "wrong",
        "expected": "fallback"
    },
]


def run_query(query: str, index, answer_gen):
    """Run a single query through the pipeline"""
    
    # 1. Embed
    embedding = embed_text(query)
    
    # 2. Search FAISS
    chunks = index.search(embedding, k=5)
    
    # 3. Filter
    filtered = filter_results_by_relevance(chunks, min_score=0.3)
    
    # 4. Confidence
    confidence = calculate_confidence(filtered) if filtered else 0.0
    conf_label = get_confidence_label(confidence)
    
    # 5. Check fallback
    fallback_threshold = 0.4
    should_fallback = confidence < fallback_threshold or not filtered
    
    # 6. Generate answer
    if should_fallback:
        answer = (
            "I don't have information about that in my knowledge base. "
            "Please contact admissions@theaims.ac.in for more details."
        )
        is_fallback = True
    else:
        answer = answer_gen.synthesize(query, filtered)
        is_fallback = False
    
    return {
        "query": query,
        "chunks_retrieved": len(chunks),
        "chunks_filtered": len(filtered),
        "top_scores": [round(c[1], 3) for c in chunks[:3]],
        "confidence": round(confidence, 2),
        "confidence_label": conf_label,
        "is_fallback": is_fallback,
        "answer": answer,
        "answer_length": len(answer)
    }


def main():
    print("\n" + "="*80)
    print("  COMPREHENSIVE RELIABILITY TEST - 30+ QUERIES")
    print("="*80 + "\n")
    
    # Load system
    print("Loading system...")
    index = get_index()
    answer_gen = get_answer_generator()
    print(f"✓ Index loaded ({index.get_stats()['document_count']} documents)\n")
    
    # Run queries
    results = []
    by_category = {}
    
    print("Running queries...\n")
    
    for i, query_data in enumerate(QUERIES, 1):
        query = query_data["query"]
        category = query_data["category"]
        
        print(f"[{i:2d}/{len(QUERIES)}] {category:12} | {query[:50]:50} ", end="", flush=True)
        
        try:
            result = run_query(query, index, answer_gen)
            result["category"] = category
            result["expected"] = query_data["expected"]
            results.append(result)
            
            # Track by category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(result)
            
            status = "FALLBACK" if result["is_fallback"] else f"CONF:{result['confidence']:.2f}"
            print(f"→ {status}")
        
        except Exception as e:
            print(f"→ ERROR: {str(e)[:40]}")
            results.append({
                "query": query,
                "category": category,
                "error": str(e)
            })
    
    # Save detailed results
    output_file = "/tmp/reliability_test_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(results),
            "results": results
        }, f, indent=2)
    
    print(f"\n✓ Detailed results saved to {output_file}\n")
    
    # Print summary
    print("="*80)
    print("  SUMMARY BY CATEGORY")
    print("="*80 + "\n")
    
    for category in sorted(by_category.keys()):
        cat_results = by_category[category]
        total = len(cat_results)
        fallbacks = sum(1 for r in cat_results if r.get("is_fallback"))
        avg_conf = sum(r.get("confidence", 0) for r in cat_results) / total if total > 0 else 0
        
        print(f"{category:15} | Count: {total:2d} | Fallbacks: {fallbacks:2d} | Avg Confidence: {avg_conf:.2f}")
    
    print("\n" + "="*80)
    print("  DETAILED RESULTS")
    print("="*80 + "\n")
    
    for i, result in enumerate(results, 1):
        if "error" in result:
            print(f"[{i:2d}] QUERY: {result['query']}")
            print(f"     ERROR: {result['error']}\n")
            continue
        
        print(f"[{i:2d}] QUERY: {result['query']}")
        print(f"     Category: {result['category']} | Expected: {result['expected']}")
        print(f"     Chunks: {result['chunks_retrieved']} retrieved, {result['chunks_filtered']} filtered")
        print(f"     Top scores: {result['top_scores']}")
        print(f"     Confidence: {result['confidence']} ({result['confidence_label']})")
        print(f"     Fallback: {result['is_fallback']}")
        print(f"     Answer ({result['answer_length']} chars):")
        print(f"       \"{result['answer'][:120]}{'...' if len(result['answer']) > 120 else ''}\"")
        print()
    
    # Print evaluation template
    print("="*80)
    print("  MANUAL EVALUATION TEMPLATE")
    print("="*80 + "\n")
    
    print("For each query, evaluate:")
    print("  ✅ CORRECT: Answer is accurate, helpful, complete")
    print("  ⚠️  PARTIAL: Answer is relevant but incomplete or slightly off")
    print("  ❌ WRONG: Answer is incorrect or misleading")
    print("  ⚠️  FALLBACK OK: Fallback was appropriate (for wrong queries)")
    print("  ❌ FALLBACK WRONG: Should have answered or vice versa\n")
    
    print("Results file:")
    print(f"  {output_file}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
