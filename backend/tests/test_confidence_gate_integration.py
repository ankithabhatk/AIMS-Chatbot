"""
Integration Test: Confidence Gate Behavior

Tests the real-world behavior of context-aware interruption logic.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.counselor.confidence_gate import should_interrupt_for_confirmation


def test_real_user_scenarios():
    """Test real user conversation scenarios"""
    
    print("\n" + "=" * 70)
    print("REAL USER SCENARIO TESTS")
    print("=" * 70)
    
    scenarios = [
        {
            "name": "User says 'yeah' after recommendation",
            "query": "yeah",
            "confidence": 0.75,
            "expected_behavior": "ASK CONFIRMATION",
            "expected_interrupt": True,
            "reason": "Short idle reply - user might be thinking"
        },
        {
            "name": "User says 'yeah tell me fees'",
            "query": "yeah tell me fees",
            "confidence": 0.75,
            "expected_behavior": "LOCK AND ANSWER",
            "expected_interrupt": False,
            "reason": "User has action intent - wants information"
        },
        {
            "name": "User says 'ok what about placement'",
            "query": "ok what about placement",
            "confidence": 0.70,
            "expected_behavior": "LOCK AND ANSWER",
            "expected_interrupt": False,
            "reason": "Multi-intent - answer everything first"
        },
        {
            "name": "User says 'fine how to apply'",
            "query": "fine how to apply",
            "confidence": 0.72,
            "expected_behavior": "LOCK AND PROCEED",
            "expected_interrupt": False,
            "reason": "User wants to apply - don't interrupt"
        },
        {
            "name": "User says 'BCA sounds good but what about salary'",
            "query": "BCA sounds good but what about salary",
            "confidence": 0.80,
            "expected_behavior": "LOCK AND ANSWER SALARY",
            "expected_interrupt": False,
            "reason": "Multi-intent - answer secondary question first"
        },
        {
            "name": "User says 'hmm maybe' (neutral)",
            "query": "hmm maybe",
            "confidence": 0.70,
            "expected_behavior": "DON'T LOCK",
            "expected_interrupt": False,
            "reason": "Neutral reply - not a decision (handled by decision_detector)"
        },
    ]
    
    passed = 0
    failed = 0
    
    for scenario in scenarios:
        should_interrupt, reason = should_interrupt_for_confirmation(
            scenario["query"], 
            scenario["confidence"]
        )
        
        behavior = "ASK CONFIRMATION" if should_interrupt else "LOCK AND CONTINUE"
        
        if should_interrupt == scenario["expected_interrupt"]:
            status = "✅"
            passed += 1
        else:
            status = "❌"
            failed += 1
        
        print(f"\n{status} {scenario['name']}")
        print(f"   Query: '{scenario['query']}'")
        print(f"   Confidence: {scenario['confidence']:.2f}")
        print(f"   Expected: {scenario['expected_behavior']}")
        print(f"   Actual: {behavior}")
        print(f"   Reason: {scenario['reason']}")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return passed, failed


def test_edge_cases():
    """Test edge cases"""
    
    print("\n" + "=" * 70)
    print("EDGE CASE TESTS")
    print("=" * 70)
    
    edge_cases = [
        ("", 0.75, False, "Empty query"),
        ("   ", 0.75, False, "Whitespace only"),
        ("yeah yeah yeah", 0.75, True, "Repeated word (still short positive)"),
        ("ok cool", 0.75, True, "Two short words"),
        ("yeah but", 0.75, False, "Short + conjunction"),
    ]
    
    passed = 0
    failed = 0
    
    for query, confidence, expected, description in edge_cases:
        should_interrupt, reason = should_interrupt_for_confirmation(query, confidence)
        
        if should_interrupt == expected:
            print(f"✅ {description}: '{query}' → {should_interrupt}")
            passed += 1
        else:
            print(f"❌ {description}: '{query}' → {should_interrupt} (expected: {expected})")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return passed, failed


if __name__ == "__main__":
    scenario_passed, scenario_failed = test_real_user_scenarios()
    edge_passed, edge_failed = test_edge_cases()
    
    total_passed = scenario_passed + edge_passed
    total_failed = scenario_failed + edge_failed
    
    print("\n" + "=" * 70)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")
    print("=" * 70)
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED - Confidence gate is production ready!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_failed} tests failed - needs attention")
        sys.exit(1)
