#!/usr/bin/env python3
"""
Production Evaluation Harness

Runs 100+ queries and tracks:
- fallback rate (% answers that failed to retrieve)
- avg score (quality metric)
- slow responses (latency detection)
- weak answers (quality issues)
- routing distribution (structured vs RAG vs fallback)

This is what prevents silent regressions after deployment.
"""

import requests
import time
import json
from statistics import mean, stdev
from typing import List, Dict, Any
from collections import defaultdict

API_URL = "http://127.0.0.1:8000/api/v1/chat"

# ========== TEST DATASET (EDIT / EXPAND AS NEEDED) ==========

TEST_QUERIES = [
    # ✅ STRUCTURED (should be deterministic, no LLM)
    ("mba fees", "structured"),
    ("bca fees", "structured"),
    ("admission process", "structured"),
    ("courses offered", "structured"),
    ("documents required", "structured"),
    ("mba course fee", "structured"),
    ("bca eligibility", "structured"),
    
    # 📚 RAG (must use retrieval)
    ("placement record", "rag"),
    ("average salary", "rag"),
    ("campus facilities", "rag"),
    ("hostel details", "rag"),
    ("library and infrastructure", "rag"),
    ("alumni placements", "rag"),
    ("internship opportunities", "rag"),
    ("recruiter companies", "rag"),
    
    # 🔀 MESSY QUERIES (realistic)
    ("mba total cost including everything", "rag"),
    ("placements avg package pls", "rag"),
    ("hostel good or not", "rag"),
    ("fees overall mba how much", "structured"),
    ("campus big or small", "rag"),
    
    # 🔗 FOLLOW UPS (test context preservation)
    ("mba fees", "structured"),
    ("what about placements", "rag"),
    ("and hostel?", "rag"),
    ("fees for bca", "structured"),
    ("same for mba", "structured"),
    
    # 🎯 MIXED QUERIES
    ("mba fees and placement", "rag"),
    ("hostel and facilities and campus", "rag"),
    ("fees + placements + admission", "rag"),
    
    # ⚠️ EDGE CASES
    ("iit delhi placements", "fallback"),  # should reject (OOD)
    ("random nonsense xyz abc", "fallback"),  # should reject
    ("???????", "fallback"),  # should reject
    ("a", "fallback"),  # too short, should reject
    ("tell me everything", "fallback"),  # too vague, should reject
]

# Expand to ~100 queries by repeating
TEST_QUERIES = TEST_QUERIES * 4

# ========== RUNNER ==========

def run_query(query: str, session_id: str = "eval_session") -> Dict[str, Any]:
    """Execute single query and capture response + metadata"""
    start = time.time()
    try:
        response = requests.post(
            API_URL,
            json={
                "query": query,
                "context": {"session_id": session_id}
            },
            timeout=10
        )
        latency = time.time() - start
        
        if response.status_code != 200:
            return {
                "query": query,
                "error": f"HTTP {response.status_code}",
                "latency": latency
            }
        
        data = response.json()
        answer = data.get("answer", "")
        meta = data.get("meta", {})
        
        return {
            "query": query,
            "answer": answer,
            "latency": latency,
            "score": meta.get("score", 0),
            "source": meta.get("source"),
            "fallback": meta.get("fallback", False),
            "intent": meta.get("intent"),
            "used_rag": meta.get("used_rag", False),
            "used_structured": meta.get("used_structured", False),
            "length": len(answer),
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "latency": time.time() - start
        }

# ========== ANALYSIS ==========

def analyze_results(results: List[Dict]) -> Dict[str, Any]:
    """Compute metrics from results"""
    valid = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]
    
    if not valid:
        return {"error": "All queries failed"}
    
    total = len(valid)
    latencies = [r["latency"] for r in valid]
    scores = [r["score"] for r in valid]
    
    fallback_count = sum(1 for r in valid if r["fallback"])
    rag_count = sum(1 for r in valid if r["source"] == "rag")
    structured_count = sum(1 for r in valid if r["source"] == "structured")
    
    # Weak answers: low score OR too short
    weak_answers = [
        r for r in valid
        if r["score"] < 0.5 or r["length"] < 60
    ]
    
    # Slow responses
    slow_responses = [
        r for r in valid
        if r["latency"] > 3.0
    ]
    
    return {
        "total_queries": len(results),
        "successful": total,
        "errors": len(errors),
        "error_rate": len(errors) / len(results),
        
        # Routing metrics
        "fallback_rate": fallback_count / total,
        "fallback_count": fallback_count,
        "rag_rate": rag_count / total,
        "rag_count": rag_count,
        "structured_rate": structured_count / total,
        "structured_count": structured_count,
        
        # Quality metrics
        "avg_score": mean(scores) if scores else 0,
        "median_score": sorted(scores)[len(scores) // 2] if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "score_stdev": stdev(scores) if len(scores) > 1 else 0,
        
        # Latency metrics
        "avg_latency_ms": mean(latencies) * 1000 if latencies else 0,
        "median_latency_ms": sorted(latencies)[len(latencies) // 2] * 1000 if latencies else 0,
        "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] * 1000 if latencies else 0,
        "slow_response_count": len(slow_responses),
        "slow_response_pct": len(slow_responses) / total if total else 0,
        
        # Quality issues
        "weak_answer_count": len(weak_answers),
        "weak_answer_pct": len(weak_answers) / total if total else 0,
        
        # Sample issues
        "weak_samples": [
            {"query": r["query"], "score": r["score"], "length": r["length"]}
            for r in weak_answers[:5]
        ],
        "slow_samples": [
            {"query": r["query"], "latency_ms": r["latency"] * 1000}
            for r in slow_responses[:5]
        ],
    }

# ========== HEALTH CHECK ==========

def check_health(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate if system is healthy"""
    health = {
        "overall": "HEALTHY",
        "issues": [],
        "warnings": [],
    }
    
    # CRITICAL: Fallback rate too high
    if summary["fallback_rate"] > 0.15:
        health["overall"] = "DEGRADED"
        health["issues"].append(f"Fallback rate too high: {summary['fallback_rate']:.2%}")
    
    # CRITICAL: Average score too low
    if summary["avg_score"] < 0.6:
        health["overall"] = "DEGRADED"
        health["issues"].append(f"Average score too low: {summary['avg_score']:.2f}")
    
    # WARNING: Some slow responses
    if summary["slow_response_pct"] > 0.1:
        health["warnings"].append(f"Slow responses detected: {summary['slow_response_pct']:.2%}")
    
    # WARNING: Weak answers
    if summary["weak_answer_pct"] > 0.2:
        health["warnings"].append(f"Weak answers detected: {summary['weak_answer_pct']:.2%}")
    
    # WARNING: Error rate
    if summary["error_rate"] > 0.05:
        health["warnings"].append(f"Error rate: {summary['error_rate']:.2%}")
    
    return health

# ========== MAIN ==========

def run_evaluation():
    """Run full evaluation and save results"""
    print("\n" + "=" * 70)
    print("🚀 PRODUCTION EVALUATION HARNESS")
    print("=" * 70 + "\n")
    
    print(f"Running {len(TEST_QUERIES)} queries...\n")
    
    results = []
    for i, (query, expected_type) in enumerate(TEST_QUERIES):
        result = run_query(query)
        results.append(result)
        
        # Show progress
        has_error = "error" in result
        fallback = result.get("fallback", False)
        score = result.get("score", 0)
        
        if has_error:
            status = "❌"
        elif fallback:
            status = "⚠️ "
        elif score > 0.7:
            status = "✅"
        else:
            status = "⚠️ "
        
        print(f"{status} [{i+1:3d}] {query[:40]:40s} | score={score:.2f}")
        
        if (i + 1) % 20 == 0:
            print()
    
    # Analyze
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70 + "\n")
    
    summary = analyze_results(results)
    health = check_health(summary)
    
    # Print summary
    print(f"Total Queries:        {summary['total_queries']}")
    print(f"Successful:           {summary['successful']}")
    print(f"Errors:               {summary['errors']} ({summary['error_rate']:.2%})\n")
    
    print("ROUTING DISTRIBUTION:")
    print(f"  Structured:         {summary['structured_count']:3d} ({summary['structured_rate']:.2%})")
    print(f"  RAG:                {summary['rag_count']:3d} ({summary['rag_rate']:.2%})")
    print(f"  Fallback:           {summary['fallback_count']:3d} ({summary['fallback_rate']:.2%})\n")
    
    print("QUALITY METRICS:")
    print(f"  Avg Score:          {summary['avg_score']:.2f}")
    print(f"  Median Score:       {summary['median_score']:.2f}")
    print(f"  Score StDev:        {summary['score_stdev']:.2f}\n")
    
    print("LATENCY METRICS:")
    print(f"  Avg Latency:        {summary['avg_latency_ms']:.0f}ms")
    print(f"  Median Latency:     {summary['median_latency_ms']:.0f}ms")
    print(f"  P95 Latency:        {summary['p95_latency_ms']:.0f}ms")
    print(f"  Slow (>3s):         {summary['slow_response_count']} ({summary['slow_response_pct']:.2%})\n")
    
    print("QUALITY ISSUES:")
    print(f"  Weak Answers:       {summary['weak_answer_count']} ({summary['weak_answer_pct']:.2%})\n")
    
    print("SYSTEM HEALTH:")
    print(f"  Status:             {health['overall']}")
    if health["issues"]:
        for issue in health["issues"]:
            print(f"  ❌ {issue}")
    if health["warnings"]:
        for warning in health["warnings"]:
            print(f"  ⚠️  {warning}")
    
    # Save results
    with open("eval_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    with open("eval_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    with open("eval_health.json", "w") as f:
        json.dump(health, f, indent=2)
    
    print("\n" + "=" * 70)
    print("📁 FILES SAVED:")
    print("  - eval_results.json  (full query results)")
    print("  - eval_summary.json  (aggregated metrics)")
    print("  - eval_health.json   (health check)")
    print("=" * 70 + "\n")
    
    return summary, health

if __name__ == "__main__":
    run_evaluation()
