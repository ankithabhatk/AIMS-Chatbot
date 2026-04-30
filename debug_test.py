#!/usr/bin/env python3
"""
Truth Verification Harness - Proves Runtime Behavior Matches Logic

This script verifies that routing logic works correctly for critical queries.
"""

import requests
import json
from typing import Dict, List

API_URL = "http://127.0.0.1:8000/api/v1/chat"

# Critical queries that MUST route correctly
CRITICAL_QUERIES = [
    {
        "id": "Q4",
        "query": "I'm weak in math but like coding. Should I still take BCA?",
        "expected_route": "counselor",
        "expected_signals": {
            "constraint": ["weak in"],
            "interest": ["coding"],
        },
        "must_not_route_to": ["structured", "placements"],
    },
    {
        "id": "Q8",
        "query": "I like coding but I also want good salary and I'm not great at studies",
        "expected_route": "counselor",
        "expected_signals": {
            "constraint": ["not great at"],
            "interest": ["coding", "salary"],
        },
        "must_not_route_to": ["structured", "placements"],
    },
    {
        "id": "Q10",
        "query": "I got 92 percentile in JEE. Should I join AIMS or try NIT?",
        "expected_route": "boundary",
        "expected_signals": {
            "comparison": ["jee", "nit"],
            "percentile": ["92"],
        },
        "must_contain": ["NIT is the stronger path", "engineering", "software development"],
        "must_not_contain": ["I can only provide information about AIMS"],
    },
]


def test_query(query: str, query_id: str) -> Dict:
    """Send query to API and return response"""
    payload = {
        "query": query,
        "session_id": f"debug-test-{query_id}",
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def detect_route_from_intent(intent: str) -> str:
    """Detect which route was taken based on intent"""
    if "counselor" in intent:
        return "counselor"
    elif intent in ["placements", "fees", "courses", "admission"]:
        return "structured"
    elif "out_of_scope" in intent:
        return "boundary"
    elif intent == "multi-intent" or "+" in intent:
        return "multi-intent"
    elif intent == "fallback":
        return "rag_fallback"
    else:
        return "rag"


def verify_signals(query: str, expected_signals: Dict) -> Dict:
    """Verify that expected signals are present in query"""
    q = query.lower()
    results = {}
    
    for signal_type, signals in expected_signals.items():
        detected = []
        for signal in signals:
            if signal.lower() in q:
                detected.append(signal)
        results[signal_type] = {
            "expected": signals,
            "detected": detected,
            "all_found": len(detected) == len(signals),
        }
    
    return results


def verify_content(answer: str, must_contain: List[str] = None, must_not_contain: List[str] = None) -> Dict:
    """Verify answer contains/doesn't contain specific phrases"""
    results = {
        "contains_check": {},
        "not_contains_check": {},
    }
    
    answer_lower = answer.lower()
    
    if must_contain:
        for phrase in must_contain:
            found = phrase.lower() in answer_lower
            results["contains_check"][phrase] = found
    
    if must_not_contain:
        for phrase in must_not_contain:
            found = phrase.lower() in answer_lower
            results["not_contains_check"][phrase] = not found  # True if NOT found (good)
    
    return results


def run_verification():
    """Run verification harness on all critical queries"""
    print("\n" + "="*80)
    print("🔍 TRUTH VERIFICATION HARNESS")
    print("="*80)
    print("\nVerifying runtime behavior matches logic...\n")
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "details": [],
    }
    
    for test_case in CRITICAL_QUERIES:
        query_id = test_case["id"]
        query = test_case["query"]
        expected_route = test_case["expected_route"]
        
        print(f"\n{'='*80}")
        print(f"{query_id}: {query[:60]}...")
        print(f"{'='*80}")
        print(f"Expected Route: {expected_route}")
        print(f"{'-'*80}")
        
        # Send query
        response = test_query(query, query_id)
        results["total"] += 1
        
        if "error" in response:
            print(f"❌ ERROR: {response['error']}")
            results["failed"] += 1
            results["details"].append({
                "id": query_id,
                "status": "error",
                "error": response["error"],
            })
            continue
        
        # Extract response data
        intent = response.get("intent", "unknown")
        answer = response.get("answer", "")
        confidence = response.get("confidence", 0.0)
        
        # Detect actual route
        actual_route = detect_route_from_intent(intent)
        
        print(f"Actual Route: {actual_route}")
        print(f"Intent: {intent}")
        print(f"Confidence: {confidence:.2f}")
        print()
        
        # Verify routing
        route_correct = actual_route == expected_route
        print(f"Route Check: {'✅ PASS' if route_correct else '❌ FAIL'}")
        
        # Verify signals
        if "expected_signals" in test_case:
            print(f"\nSignal Detection:")
            signal_results = verify_signals(query, test_case["expected_signals"])
            for signal_type, result in signal_results.items():
                all_found = result["all_found"]
                status = "✅" if all_found else "❌"
                print(f"  {status} {signal_type}: {result['detected']} (expected: {result['expected']})")
        
        # Verify must_not_route_to
        if "must_not_route_to" in test_case:
            wrong_routes = test_case["must_not_route_to"]
            routed_wrong = actual_route in wrong_routes
            print(f"\nMust NOT route to {wrong_routes}: {'❌ FAIL (routed wrong!)' if routed_wrong else '✅ PASS'}")
        
        # Verify content
        if "must_contain" in test_case or "must_not_contain" in test_case:
            print(f"\nContent Verification:")
            content_results = verify_content(
                answer,
                test_case.get("must_contain"),
                test_case.get("must_not_contain")
            )
            
            if content_results["contains_check"]:
                print(f"  Must contain:")
                for phrase, found in content_results["contains_check"].items():
                    status = "✅" if found else "❌"
                    print(f"    {status} '{phrase[:50]}...'")
            
            if content_results["not_contains_check"]:
                print(f"  Must NOT contain:")
                for phrase, not_found in content_results["not_contains_check"].items():
                    status = "✅" if not_found else "❌"
                    print(f"    {status} '{phrase[:50]}...'")
        
        # Overall pass/fail
        passed = route_correct
        if "must_not_route_to" in test_case:
            passed = passed and not routed_wrong
        if "must_contain" in test_case:
            passed = passed and all(content_results["contains_check"].values())
        if "must_not_contain" in test_case:
            passed = passed and all(content_results["not_contains_check"].values())
        
        print(f"\n{'='*80}")
        print(f"Overall: {'✅ PASS' if passed else '❌ FAIL'}")
        print(f"{'='*80}")
        
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        
        results["details"].append({
            "id": query_id,
            "status": "pass" if passed else "fail",
            "expected_route": expected_route,
            "actual_route": actual_route,
            "intent": intent,
        })
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 VERIFICATION SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}/{results['total']} ({results['passed']/results['total']*100:.0f}%)")
    print(f"❌ Failed: {results['failed']}/{results['total']} ({results['failed']/results['total']*100:.0f}%)")
    
    print(f"\n{'='*80}")
    print("🎯 VERDICT")
    print(f"{'='*80}\n")
    
    if results["failed"] == 0:
        print("✅ ALL TESTS PASSED")
        print("Behavior matches logic. System is production-ready.")
    else:
        print("❌ TESTS FAILED")
        print("Behavior does NOT match logic. Fix routing before production.")
        print("\nFailed tests:")
        for detail in results["details"]:
            if detail["status"] == "fail":
                print(f"  - {detail['id']}: Expected {detail['expected_route']}, got {detail['actual_route']}")
    
    print(f"\n{'='*80}\n")
    
    return results


if __name__ == "__main__":
    results = run_verification()
    exit(0 if results["failed"] == 0 else 1)
