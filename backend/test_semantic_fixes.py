#!/usr/bin/env python3
"""
Test script to validate semantic routing fixes
Tests intent detection, routing, and fallback behavior
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import (
    extract_intents,
    extract_entities,
    route_to_mode,
    parse_query,
    execute_orchestration
)

# Test cases with expected outcomes
TEST_CASES = [
    # ORIGINAL FAILURES
    {
        "query": "What is the scholarship eligibility?",
        "expected_intent": "scholarship",
        "expected_mode": "structured",
        "description": "Scholarship eligibility detection"
    },
    {
        "query": "What is the average salary?",
        "expected_intent": "placement",
        "expected_mode": "rag",
        "description": "Average salary routing"
    },
    {
        "query": "fees structure",
        "expected_intent": "fees",
        "expected_mode": "structured",
        "description": "Fees structure keyword variation"
    },
    {
        "query": "mba",
        "expected_intent": "courses",
        "expected_mode": "structured",
        "description": "Single-word course query"
    },
    
    # SYNONYM TESTS
    {
        "query": "What's the cost of MBA?",
        "expected_intent": "fees",
        "expected_mode": "structured",
        "description": "Cost synonym for fees"
    },
    {
        "query": "How to apply for BCA?",
        "expected_intent": "admission",
        "expected_mode": "structured",
        "description": "Apply keyword for admission"
    },
    {
        "query": "Hostel accommodations and facilities",
        "expected_intent": "campus",
        "expected_mode": "rag",
        "description": "Accommodation keyword for campus"
    },
    {
        "query": "Placement record and average package",
        "expected_intent": "placement",
        "expected_mode": "rag",
        "description": "Package synonym for salary"
    },
    
    # MULTI-INTENT
    {
        "query": "What are fees and placements for MBA?",
        "expected_intent": "fees",  # First detected
        "description": "Multi-intent query"
    },
    
    # TYPO/VARIATION HANDLING
    {
        "query": "fee for mba",
        "expected_intent": "fees",
        "expected_mode": "structured",
        "description": "Typo handling (fee vs fees)"
    },
]

def test_intent_detection():
    """Test intent extraction"""
    print("\n" + "="*70)
    print("TESTING INTENT DETECTION")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for test_case in TEST_CASES:
        query = test_case["query"]
        expected_intent = test_case["expected_intent"]
        
        intents = extract_intents(query)
        detected_intent = intents[0] if intents else "general"
        
        is_pass = detected_intent == expected_intent
        passed += is_pass
        failed += not is_pass
        
        status = "✅ PASS" if is_pass else "❌ FAIL"
        print(f"\n{status} | {test_case['description']}")
        print(f"  Query: '{query}'")
        print(f"  Expected: {expected_intent}, Got: {detected_intent}")
        if not is_pass:
            print(f"  All intents: {intents}")
    
    return passed, failed

def test_routing():
    """Test mode routing"""
    print("\n" + "="*70)
    print("TESTING ROUTING LOGIC")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for test_case in TEST_CASES:
        if "expected_mode" not in test_case:
            continue
            
        query = test_case["query"]
        expected_mode = test_case["expected_mode"]
        
        parsed = parse_query(query)
        intents = parsed.intents
        entities = parsed.entities
        mode = route_to_mode(intents, entities)
        
        is_pass = mode == expected_mode
        passed += is_pass
        failed += not is_pass
        
        status = "✅ PASS" if is_pass else "❌ FAIL"
        print(f"\n{status} | {test_case['description']}")
        print(f"  Query: '{query}'")
        print(f"  Expected: {expected_mode}, Got: {mode}")
        print(f"  Intents: {intents}, Entities: {entities}")
    
    return passed, failed

def test_orchestration():
    """Test full orchestration with structured/RAG answers"""
    print("\n" + "="*70)
    print("TESTING FULL ORCHESTRATION")
    print("="*70)
    
    test_queries = [
        ("mba fees", "Should return MBA fee structure"),
        ("bca admission", "Should return BCA admission process"),
        ("scholarship eligibility", "Should clarify scholarship"),
        ("mba", "Should ask clarification"),
        ("placement record", "Should use RAG mode"),
        ("average salary", "Should handle salary query"),
    ]
    
    for query, description in test_queries:
        print(f"\n📝 Query: '{query}'")
        print(f"   Expected: {description}")
        
        try:
            result = execute_orchestration(query, retrieved_chunks=None)
            
            print(f"   ✅ Intent: {result.intent}")
            print(f"   ✅ Mode: {result.mode}")
            print(f"   ✅ Confidence: {result.confidence}")
            print(f"   ✅ Fallback: {result.fallback}")
            print(f"   📄 Answer: {result.answer[:100]}...")
            
            # Check for good indicators
            if result.mode == "structured" and result.confidence >= 0.7:
                print(f"   ✅ HIGH CONFIDENCE STRUCTURED - Good!")
            elif result.mode == "rag" and result.confidence >= 0.5:
                print(f"   ✅ RAG MODE - Good!")
            elif query == "mba" and not result.fallback:
                print(f"   ✅ SINGLE WORD HANDLED - Good!")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    print("\n" + "🧪 " * 20)
    print("SEMANTIC ROUTING FIX VALIDATION TEST SUITE")
    print("🧪 " * 20)
    
    # Run tests
    intent_passed, intent_failed = test_intent_detection()
    route_passed, route_failed = test_routing()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Intent Detection: {intent_passed} passed, {intent_failed} failed")
    print(f"Routing Logic:    {route_passed} passed, {route_failed} failed")
    
    total_passed = intent_passed + route_passed
    total_failed = intent_failed + route_failed
    
    print(f"\nTotal: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("\n✅ ALL CORE TESTS PASSED!")
        print("\n🎯 Semantic routing improvements are working correctly")
    else:
        print(f"\n⚠️  {total_failed} tests failed - review intent keywords")
    
    # Run orchestration test
    test_orchestration()
    
    print("\n" + "="*70)
    print("END OF TEST SUITE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
