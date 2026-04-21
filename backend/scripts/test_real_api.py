#!/usr/bin/env python3
"""
End-to-End API Test: Real Chat Queries

Tests actual pipeline without mocks:
1. Good query: "What is the admission process?"
2. Bad query: "Do you offer space engineering?"
"""

import sys
import os
import asyncio
import json

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.response.filter import filter_results_by_relevance
from app.services.response.confidence import calculate_confidence, get_confidence_label
from app.services.llm.answer_generator import get_answer_generator


def print_section(title: str):
    """Print formatted section"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_real_query(query: str, test_name: str):
    """Test a real query through the full pipeline"""
    print_section(f"{test_name}: '{query}'")
    
    # 1. Embed
    print("▸ Step 1: Embedding query...")
    query_embedding = embed_text(query)
    print(f"  ✓ Vector size: {len(query_embedding)}")
    
    # 2. Check index
    print("\n▸ Step 2: Checking FAISS index...")
    index = get_index()
    stats = index.get_stats()
    print(f"  ✓ Index has {stats['document_count']} documents")
    
    if not index.validate_integrity():
        print("  ❌ Index corruption detected!")
        return None
    
    # 3. Search FAISS
    print("\n▸ Step 3: Searching FAISS...")
    retrieved_chunks = index.search(query_embedding, k=5)
    print(f"  ✓ Retrieved {len(retrieved_chunks)} chunks")
    
    if retrieved_chunks:
        for i, chunk in enumerate(retrieved_chunks[:3], 1):
            text = chunk[0][:60] if isinstance(chunk[0], str) else str(chunk[0])[:60]
            score = chunk[1] if len(chunk) > 1 else 0
            print(f"    {i}. Score: {score:.3f} | {text}...")
    
    # 4. Filter
    print("\n▸ Step 4: Filtering by relevance...")
    filtered_chunks = filter_results_by_relevance(retrieved_chunks, min_score=0.3)
    print(f"  ✓ After filtering: {len(filtered_chunks)} chunks")
    
    # 5. Confidence
    print("\n▸ Step 5: Calculating confidence...")
    confidence = calculate_confidence(filtered_chunks) if filtered_chunks else 0.0
    conf_label = get_confidence_label(confidence)
    print(f"  ✓ Confidence: {confidence:.2f} ({conf_label})")
    
    # 6. Check fallback
    print("\n▸ Step 6: Checking fallback threshold...")
    fallback_threshold = 0.4
    should_fallback = confidence < fallback_threshold or not filtered_chunks
    print(f"  Threshold: {fallback_threshold}")
    print(f"  Should fallback: {should_fallback}")
    
    if should_fallback:
        answer = (
            "I don't have information about that in my knowledge base. "
            "Please contact admissions@theaims.ac.in for more details."
        )
        is_fallback = True
    else:
        # 7. Synthesize answer
        print("\n▸ Step 7: Synthesizing answer...")
        answer_gen = get_answer_generator()
        answer = answer_gen.synthesize(query, filtered_chunks)
        is_fallback = False
        print(f"  ✓ Generated {len(answer)} character answer")
    
    # Results
    print(f"\n{'─'*70}")
    print("RESULT:")
    print(f"{'─'*70}")
    print(f"\nAnswer ({len(answer)} chars):")
    print(f'  "{answer}"')
    print(f"\nConfidence: {confidence:.2f}")
    print(f"Is Fallback: {is_fallback}")
    
    return {
        "query": query,
        "answer": answer,
        "confidence": confidence,
        "is_fallback": is_fallback,
        "num_chunks": len(filtered_chunks)
    }


def main():
    """Run end-to-end tests"""
    print("\n" + "="*70)
    print("  PHASE 3: REAL SYSTEM VALIDATION")
    print("  (Using live FAISS index and real query processing)")
    print("="*70)
    
    results = []
    
    # Test 1: Good query
    result1 = test_real_query(
        "What is the admission process?",
        "TEST 1 (GOOD QUERY)"
    )
    if result1:
        results.append(result1)
    
    # Test 2: Bad query
    result2 = test_real_query(
        "Do you offer space engineering?",
        "TEST 2 (BAD QUERY)"
    )
    if result2:
        results.append(result2)
    
    # Test 3: Edge case
    result3 = test_real_query(
        "What are the fees?",
        "TEST 3 (EDGE CASE)"
    )
    if result3:
        results.append(result3)
    
    # Summary
    print_section("SUMMARY")
    
    if len(results) >= 2:
        good = results[0]
        bad = results[1]
        
        print("✅ Good Query Results:")
        print(f"  Confidence: {good['confidence']:.2f}")
        print(f"  Is Fallback: {good['is_fallback']}")
        print(f"  Chunks Used: {good['num_chunks']}")
        
        print("\n✅ Bad Query Results:")
        print(f"  Confidence: {bad['confidence']:.2f}")
        print(f"  Is Fallback: {bad['is_fallback']}")
        print(f"  Chunks Used: {bad['num_chunks']}")
        
        # Validation
        print("\n" + "="*70)
        print("VALIDATION:")
        print("="*70)
        
        checks = [
            ("Good query is NOT fallback", not good['is_fallback']),
            ("Good query has high confidence", good['confidence'] > 0.5),
            ("Bad query IS fallback", bad['is_fallback']),
            ("Bad query has low confidence", bad['confidence'] < 0.4),
            ("Good query answer is meaningful", len(good['answer']) > 50),
            ("Bad query shows fallback message", "admissions@theaims.ac.in" in bad['answer']),
        ]
        
        passed = 0
        for check, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check}")
            if result:
                passed += 1
        
        print(f"\n{passed}/{len(checks)} checks passed")
        
        if passed == len(checks):
            print("\n🎉 SYSTEM IS WORKING!")
        
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
