#!/usr/bin/env python3
"""
End-to-End Test: Chat Endpoint with Integrated Pipeline

Tests:
1. Good query (should return synthesized answer)
2. Bad query (should return fallback)
3. Shows before/after output comparison
"""

import sys
import os
import json
import asyncio
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.response.filter import filter_results_by_relevance
from app.services.response.confidence import calculate_confidence, get_confidence_label
from app.services.llm.answer_generator import get_answer_generator


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_result(label: str, value: Any, indent: int = 2):
    """Print formatted result"""
    indent_str = " " * indent
    if isinstance(value, (int, float)):
        print(f"{indent_str}{label}: {value}")
    elif isinstance(value, list):
        print(f"{indent_str}{label}:")
        for item in value:
            print(f"{indent_str}  - {item}")
    else:
        print(f"{indent_str}{label}: {value}")


def test_query(query: str, query_type: str) -> Dict[str, Any]:
    """
    Test a single query through the entire pipeline
    
    Returns dict with results at each stage
    """
    print_section(f"{query_type.upper()} QUERY: '{query}'")
    
    results = {"query": query, "type": query_type}
    
    # Step 1: Embed query
    print("STEP 1: Embedding query...")
    query_embedding = embed_text(query)
    print(f"  ✓ Embedded to vector of size {len(query_embedding)}")
    results["embedding_size"] = len(query_embedding)
    
    # Step 2: Search FAISS
    print("\nSTEP 2: Searching FAISS index...")
    index = get_index()
    retrieved_chunks = index.search(query_embedding, k=5)
    print(f"  ✓ Retrieved {len(retrieved_chunks)} chunks")
    
    if retrieved_chunks:
        for i, chunk in enumerate(retrieved_chunks[:3], 1):
            text = chunk[0][:80] if isinstance(chunk[0], str) else str(chunk[0])[:80]
            score = chunk[1] if len(chunk) > 1 else 0
            print(f"    {i}. Score: {score:.3f}, Text: {text}...")
    results["raw_chunks_retrieved"] = len(retrieved_chunks)
    results["top_scores"] = [chunk[1] for chunk in retrieved_chunks[:3]] if retrieved_chunks else []
    
    # Step 3: Filter by relevance
    print("\nSTEP 3: Filtering by relevance (min_score=0.3)...")
    filtered_chunks = filter_results_by_relevance(retrieved_chunks, min_score=0.3)
    print(f"  ✓ Filtered to {len(filtered_chunks)} chunks")
    results["filtered_chunks"] = len(filtered_chunks)
    
    if not filtered_chunks:
        print("  ⚠ No chunks passed filter - fallback expected")
        results["confidence"] = 0.0
        results["confidence_label"] = "very_low"
        results["is_fallback"] = True
        results["answer"] = (
            "I don't have information about that in my knowledge base. "
            "Please contact admissions@theaims.ac.in for more details."
        )
        return results
    
    # Step 4: Calculate confidence
    print("\nSTEP 4: Calculating confidence score...")
    confidence = calculate_confidence(filtered_chunks)
    confidence_label = get_confidence_label(confidence)
    print(f"  ✓ Confidence: {confidence:.2f} ({confidence_label})")
    results["confidence"] = confidence
    results["confidence_label"] = confidence_label
    
    # Step 5: Check fallback threshold
    fallback_threshold = 0.4
    is_fallback = confidence < fallback_threshold
    print(f"\nSTEP 5: Checking fallback threshold (threshold={fallback_threshold})...")
    if is_fallback:
        print(f"  ⚠ FALLBACK: Confidence {confidence:.2f} < {fallback_threshold}")
        results["is_fallback"] = True
        results["answer"] = (
            "I don't have information about that in my knowledge base. "
            "Please contact admissions@theaims.ac.in for more details."
        )
        return results
    else:
        print(f"  ✓ Confidence {confidence:.2f} >= {fallback_threshold}, proceeding to synthesis")
        results["is_fallback"] = False
    
    # Step 6: Generate synthesized answer
    print("\nSTEP 6: Generating synthesized answer...")
    answer_gen = get_answer_generator()
    synthesized_answer = answer_gen.synthesize(query, filtered_chunks)
    print(f"  ✓ Generated answer ({len(synthesized_answer)} chars):")
    print(f"    \"{synthesized_answer}\"")
    results["answer"] = synthesized_answer
    results["answer_length"] = len(synthesized_answer)
    
    return results


def compare_results(good_result: Dict, bad_result: Dict):
    """
    Compare before/after for good and bad queries
    """
    print_section("BEFORE vs AFTER COMPARISON")
    
    print("Metric                          | Good Query        | Bad Query")
    print("-" * 70)
    
    metrics = [
        ("Raw chunks retrieved", "raw_chunks_retrieved"),
        ("Filtered chunks", "filtered_chunks"),
        ("Confidence score", "confidence"),
        ("Confidence label", "confidence_label"),
        ("Is fallback", "is_fallback"),
        ("Answer length", "answer_length"),
    ]
    
    for label, key in metrics:
        good_val = good_result.get(key, "N/A")
        bad_val = bad_result.get(key, "N/A")
        
        if isinstance(good_val, float):
            good_str = f"{good_val:.2f}"
            bad_str = f"{bad_val:.2f}" if isinstance(bad_val, (int, float)) else str(bad_val)
        else:
            good_str = str(good_val)
            bad_str = str(bad_val)
        
        print(f"{label:30} | {good_str:17} | {bad_str}")
    
    print("\n" + "="*70)
    print("GOOD QUERY OUTPUT (Admission process):")
    print("-"*70)
    print(f"Answer: {good_result.get('answer', 'N/A')}")
    print(f"Confidence: {good_result.get('confidence', 0):.2f}")
    print(f"Is Fallback: {good_result.get('is_fallback', False)}")
    
    print("\n" + "="*70)
    print("BAD QUERY OUTPUT (Space engineering):")
    print("-"*70)
    print(f"Answer: {bad_result.get('answer', 'N/A')}")
    print(f"Confidence: {bad_result.get('confidence', 0):.2f}")
    print(f"Is Fallback: {bad_result.get('is_fallback', False)}")


def main():
    """Run end-to-end tests"""
    print("\n" + "="*70)
    print("  PHASE 3: VALIDATION - Answer Synthesis Pipeline")
    print("="*70)
    
    try:
        # Test 1: Good query
        good_result = test_query("What is the admission process?", "GOOD")
        
        # Test 2: Bad query  
        bad_result = test_query("Do you offer space engineering?", "BAD")
        
        # Compare
        compare_results(good_result, bad_result)
        
        # Validation summary
        print_section("VALIDATION SUMMARY")
        
        validations = [
            ("Good query returns high confidence", good_result.get("confidence", 0) > 0.5),
            ("Good query is not fallback", not good_result.get("is_fallback", True)),
            ("Good query returns synthesized answer", len(good_result.get("answer", "")) > 50),
            ("Bad query returns fallback", bad_result.get("is_fallback", False)),
            ("Bad query returns low confidence", bad_result.get("confidence", 0) < 0.4),
        ]
        
        passed = 0
        for check, result in validations:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {check}")
            if result:
                passed += 1
        
        print(f"\n{passed}/{len(validations)} checks passed")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
