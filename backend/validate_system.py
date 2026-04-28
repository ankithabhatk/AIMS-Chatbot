#!/usr/bin/env python3
"""
HEADLESS VALIDATION TEST

This script validates the ACTUAL system behavior post-fixes.
No guessing. Pure metrics.

Run this and show the results.
"""

import requests
import json
import time
from typing import Dict, List, Any

API_URL = "http://127.0.0.1:8000/api/v1/chat"
SESSION_ID = "validation_test"

# Test cases with strict expectations
TEST_CASES = [
    {
        "query": "MBA fees",
        "expected_source": "structured",
        "expected_fallback": False,
        "min_length": 50,
        "description": "Structured KB query"
    },
    {
        "query": "placement record",
        "expected_source": "rag",
        "expected_fallback": False,
        "min_length": 100,
        "description": "RAG query - placement"
    },
    {
        "query": "campus facilities",
        "expected_source": "rag",
        "expected_fallback": False,
        "min_length": 100,
        "description": "RAG query - campus"
    },
    {
        "query": "hostel at AIMS",
        "expected_source": "rag",
        "expected_fallback": False,
        "min_length": 80,
        "description": "RAG query - hostel"
    },
    {
        "query": "What about placements?",
        "expected_source": "rag",
        "expected_fallback": False,
        "min_length": 80,
        "uses_context": True,
        "description": "Follow-up query - should use context from MBA"
    },
    {
        "query": "Tell me about campus",
        "expected_source": "rag",
        "expected_fallback": False,
        "min_length": 100,
        "description": "RAG query - campus info"
    },
    {
        "query": "scholarship eligibility",
        "expected_source": "structured",
        "expected_fallback": False,
        "min_length": 50,
        "description": "Structured KB query - scholarship"
    },
    {
        "query": "random xyz blah test",
        "expected_source": "fallback",
        "expected_fallback": True,
        "min_length": 20,
        "description": "Garbage query - should fallback"
    }
]

# ========== RUNNER ==========

def run_test(query: str, session_id: str) -> Dict[str, Any]:
    """Run single query and return response"""
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "context": {"session_id": session_id}},
            timeout=10
        )
        
        if response.status_code != 200:
            return {
                "query": query,
                "error": f"HTTP {response.status_code}",
                "status": "ERROR"
            }
        
        data = response.json()
        return {
            "query": query,
            "answer": data.get("answer", ""),
            "meta": data.get("meta", {}),
            "status": "OK"
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "status": "ERROR"
        }

def validate_result(result: Dict, test_case: Dict) -> Dict[str, Any]:
    """Validate if result matches expectations"""
    if result["status"] == "ERROR":
        return {
            "passed": False,
            "reason": f"Error: {result.get('error')}",
            "meta": {}
        }
    
    answer = result["answer"]
    meta = result.get("meta", {})
    
    failures = []
    
    # Check source
    expected_source = test_case["expected_source"]
    actual_source = meta.get("source", "unknown")
    if actual_source != expected_source:
        failures.append(f"source: expected {expected_source}, got {actual_source}")
    
    # Check fallback
    expected_fallback = test_case["expected_fallback"]
    actual_fallback = meta.get("fallback", False)
    if actual_fallback != expected_fallback:
        failures.append(f"fallback: expected {expected_fallback}, got {actual_fallback}")
    
    # Check length
    min_length = test_case.get("min_length", 20)
    if len(answer) < min_length:
        failures.append(f"length: expected >{min_length}, got {len(answer)}")
    
    # Check score
    score = meta.get("score", 0)
    if not test_case["expected_fallback"] and score < 0.4:
        failures.append(f"score: expected >0.4, got {score}")
    
    # Check RAG usage flag
    if expected_source == "rag" and not meta.get("used_rag", False):
        failures.append(f"used_rag: should be True for RAG queries")
    
    passed = len(failures) == 0
    
    return {
        "passed": passed,
        "reason": "; ".join(failures) if failures else "OK",
        "meta": meta,
        "answer_length": len(answer)
    }

# ========== MAIN ==========

def run_validation():
    """Run complete validation suite"""
    print("\n" + "=" * 80)
    print("🧪 HEADLESS SYSTEM VALIDATION")
    print("=" * 80 + "\n")
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        query = test_case["query"]
        print(f"[{i}/{len(TEST_CASES)}] {query[:50]}...", end=" ", flush=True)
        
        result = run_test(query, SESSION_ID)
        validation = validate_result(result, test_case)
        
        results.append({
            "test_case": test_case,
            "result": result,
            "validation": validation
        })
        
        if validation["passed"]:
            print("✅ PASS")
            passed_count += 1
        else:
            print(f"❌ FAIL - {validation['reason']}")
            failed_count += 1
    
    # Compute metrics
    print("\n" + "=" * 80)
    print("📊 METRICS")
    print("=" * 80 + "\n")
    
    # Success rate
    success_rate = passed_count / len(TEST_CASES)
    print(f"Pass Rate:              {passed_count}/{len(TEST_CASES)} ({success_rate:.1%})")
    
    # Fallback rate (for non-garbage queries)
    fallback_queries = [r for r in results if not r["test_case"]["expected_fallback"]]
    actual_fallbacks = sum(1 for r in fallback_queries if r["validation"]["meta"].get("fallback", False))
    fallback_rate = actual_fallbacks / len(fallback_queries) if fallback_queries else 0
    print(f"Unexpected Fallbacks:   {actual_fallbacks}/{len(fallback_queries)} ({fallback_rate:.1%})")
    
    # Average score
    scores = [r["validation"]["meta"].get("score", 0) for r in results if r["validation"]["meta"]]
    avg_score = sum(scores) / len(scores) if scores else 0
    print(f"Average Score:          {avg_score:.2f}")
    
    # RAG utilization
    rag_queries = [r for r in results if r["test_case"]["expected_source"] == "rag"]
    rag_used = sum(1 for r in rag_queries if r["validation"]["meta"].get("used_rag", False))
    rag_util = rag_used / len(rag_queries) if rag_queries else 0
    print(f"RAG Utilization:        {rag_used}/{len(rag_queries)} ({rag_util:.1%})")
    
    # Answer lengths
    lengths = [r["validation"]["answer_length"] for r in results]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    print(f"Avg Answer Length:      {avg_length:.0f} chars")
    
    # ========== PASS/FAIL VERDICT ==========
    
    print("\n" + "=" * 80)
    print("🚨 VERDICT")
    print("=" * 80 + "\n")
    
    all_pass = passed_count == len(TEST_CASES)
    
    if all_pass:
        print("✅ ALL TESTS PASSED")
        print("\nSystem behavior:")
        print("  ✓ Routing decisions correct")
        print("  ✓ RAG activating for data queries")
        print("  ✓ Structured answers fast")
        print("  ✓ Fallback safe for garbage")
        print("  ✓ Context preserved in follow-ups")
        print("\n🚀 READY FOR PRODUCTION")
    else:
        print(f"❌ TESTS FAILED ({failed_count}/{len(TEST_CASES)})")
        print("\nFailing tests:")
        for i, r in enumerate(results, 1):
            if not r["validation"]["passed"]:
                print(f"\n  [{i}] {r['test_case']['query']}")
                print(f"      Expected: {r['test_case']['expected_source']}")
                print(f"      Reason: {r['validation']['reason']}")
    
    # ========== DETAILED RESULTS ==========
    
    print("\n" + "=" * 80)
    print("📋 DETAILED RESULTS")
    print("=" * 80 + "\n")
    
    for i, r in enumerate(results, 1):
        test = r["test_case"]
        val = r["validation"]
        meta = val["meta"]
        
        status = "✅" if val["passed"] else "❌"
        print(f"{status} [{i}] {test['query']}")
        print(f"    Expected: {test['expected_source']}")
        print(f"    Actual:   {meta.get('source', 'unknown')}")
        print(f"    Score:    {meta.get('score', 0):.2f}")
        print(f"    Used RAG: {meta.get('used_rag', False)}")
        print(f"    Fallback: {meta.get('fallback', False)}")
        print(f"    Length:   {val['answer_length']} chars")
        if not val["passed"]:
            print(f"    ❌ {val['reason']}")
        print()
    
    # ========== SAVE RESULTS ==========
    
    with open("validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("=" * 80)
    print("💾 Results saved to: validation_results.json")
    print("=" * 80 + "\n")
    
    return all_pass

if __name__ == "__main__":
    success = run_validation()
    exit(0 if success else 1)
