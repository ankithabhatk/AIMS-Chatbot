#!/usr/bin/env python3
"""
Direct test of intent detection without relying on response text parsing.
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot')
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

import json
from app.services.orchestration.engine import detect_multiple_intents, compute_intent_scores

def test_intent_detection():
    """Test intent detection directly."""
    
    test_cases = [
        {
            "query": "What is AIMS and fees for BCA",
            "expected": ["about_aims", "fees"],
            "description": "Institution + course fees"
        },
        {
            "query": "Tell me about AIMS, placement for MBA, and hostel facilities",
            "expected": ["about_aims", "placements", "hostel", "aims_features"],
            "description": "Institution + placement + hostel + facilities"
        },
        {
            "query": "BCA fees and admission process",
            "expected": ["fees", "admission"],
            "description": "Course fees + admission"
        },
        {
            "query": "Why AIMS and what courses are available",
            "expected": ["why_aims", "courses"],
            "description": "Why AIMS + courses"
        },
        {
            "query": "Fees, placements, and scholarships",
            "expected": ["fees", "placements", "scholarship"],
            "description": "Multiple course-related intents"
        },
    ]
    
    print("\n" + "="*100)
    print("DIRECT INTENT DETECTION TEST")
    print("="*100)
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        query = test["query"]
        expected = test["expected"]
        description = test["description"]
        
        print(f"\n{'='*100}")
        print(f"Test {i}: {description}")
        print(f"{'='*100}")
        print(f"Query: '{query}'")
        print(f"Expected intents: {expected}")
        
        # Get scores
        scores = compute_intent_scores(query)
        print(f"\nIntent scores (all):")
        for intent, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0:
                print(f"  {intent}: {score:.2f}")
        
        # Get detected intents
        detected = detect_multiple_intents(query)
        detected_names = [intent for intent, score in detected]
        
        print(f"\nDetected intents (score >= 0.4): {detected_names}")
        print(f"Detected with scores: {[(intent, f'{score:.2f}') for intent, score in detected]}")
        
        # Check if all expected intents are detected
        all_detected = all(exp in detected_names for exp in expected)
        print(f"All expected detected: {'✅ YES' if all_detected else '❌ NO'}")
        
        if not all_detected:
            missing = [e for e in expected if e not in detected_names]
            print(f"  Missing: {missing}")
        
        # Check order
        order_correct = detected_names == expected
        print(f"Order correct: {'✅ YES' if order_correct else '❌ NO'}")
        
        if not order_correct:
            print(f"  Expected order: {expected}")
            print(f"  Detected order: {detected_names}")
        
        results.append({
            "query": query,
            "expected": expected,
            "detected": detected_names,
            "all_detected": all_detected,
            "order_correct": order_correct,
        })
    
    # Summary
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    
    print(f"\n{'Query':<50} | {'Expected':<30} | {'Detected':<30} | {'All?':<5} | {'Order?':<7}")
    print("-" * 130)
    
    for result in results:
        query_short = result["query"][:47] + "..." if len(result["query"]) > 50 else result["query"]
        expected_str = ",".join(result["expected"][:2])
        detected_str = ",".join(result["detected"][:2])
        all_detected = "✅" if result["all_detected"] else "❌"
        order_correct = "✅" if result["order_correct"] else "❌"
        
        print(f"{query_short:<50} | {expected_str:<30} | {detected_str:<30} | {all_detected:<5} | {order_correct:<7}")
    
    # Statistics
    print("\n" + "="*100)
    print("STATISTICS")
    print("="*100)
    
    total = len(results)
    all_detected_count = sum(1 for r in results if r["all_detected"])
    order_correct_count = sum(1 for r in results if r["order_correct"])
    
    print(f"\nTotal tests: {total}")
    print(f"All expected intents detected: {all_detected_count}/{total} ({all_detected_count*100//total}%)")
    print(f"Order correct: {order_correct_count}/{total} ({order_correct_count*100//total}%)")
    
    # Detailed results
    print("\n" + "="*100)
    print("DETAILED RESULTS")
    print("="*100)
    
    for i, result in enumerate(results, 1):
        print(f"\nTest {i}:")
        print(f"  Query: {result['query']}")
        print(f"  Expected: {result['expected']}")
        print(f"  Detected: {result['detected']}")
        print(f"  All detected: {'✅ YES' if result['all_detected'] else '❌ NO'}")
        print(f"  Order correct: {'✅ YES' if result['order_correct'] else '❌ NO'}")


if __name__ == "__main__":
    try:
        test_intent_detection()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
