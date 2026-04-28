#!/usr/bin/env python3
"""
Stress Test: 15 Real-User Compound Queries
Tests multi-intent, weak intent, and interest+info combinations
"""

import requests
import json
from datetime import datetime

# 15 stress test queries from system review
STRESS_QUERIES = [
    # Multi-intent (Core Stress)
    "What is AIMS and fees for BCA and hostel?",
    "Tell me about MBA placements and admission process",
    "BCA fees, placements and duration?",
    "What courses are there and which is best for coding?",
    "Hostel and campus facilities and fees?",

    # Weak Intent + Decision Confusion
    "I like coding, maybe BCA or MCA what do you suggest?",
    "I'm not sure but maybe MBA, what are the options?",
    "I think business is good, should I take BBA?",
    "Maybe computer science, what courses are there?",
    "I'm confused between BCA and BBA, which is better?",

    # Interest + Info Combo (High Risk)
    "I like coding, what are fees and placements?",
    "I want business, what is BBA and hostel facility?",
    "Interested in IT, how is MCA and placements?",
    "I like computers, what courses and fees?",
    "Passion for business, what does AIMS offer?",
]

API_URL = "http://localhost:8000/api/v1/chat"

def run_stress_test():
    print("=" * 80)
    print("STRESS TEST: 15 Compound Queries")
    print("=" * 80)
    print(f"API: {API_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    results = []

    for i, query in enumerate(STRESS_QUERIES, 1):
        category = "Multi-intent" if i <= 5 else ("Weak Intent" if i <= 10 else "Interest+Info")

        try:
            start = datetime.now()
            response = requests.post(API_URL, json={"query": query}, timeout=15)
            elapsed = (datetime.now() - start).total_seconds()

            if response.status_code == 200:
                data = response.json()
                result = {
                    "id": i,
                    "category": category,
                    "query": query,
                    "status": "ok",
                    "answer": data.get("answer", ""),
                    "confidence": data.get("confidence", 0),
                    "fallback": data.get("fallback", False),
                    "mode": data.get("mode"),
                    "intents": data.get("intents", []),
                    "response_time_sec": elapsed
                }
            else:
                result = {
                    "id": i,
                    "category": category,
                    "query": query,
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "answer": "",
                    "confidence": 0,
                    "fallback": True,
                    "response_time_sec": elapsed
                }
        except Exception as e:
            result = {
                "id": i,
                "category": category,
                "query": query,
                "status": "exception",
                "error": str(e),
                "answer": "",
                "confidence": 0,
                "fallback": True,
                "response_time_sec": 0
            }

        results.append(result)

        # Print status
        status = "OK" if result["status"] == "ok" and not result["fallback"] else "FALLBACK" if result["fallback"] else "ERROR"
        status_icon = "✓" if status == "OK" else "F" if status == "FALLBACK" else "X"
        print(f"[{i:2d}] [{category:15s}] {status_icon} {query[:55]}")
        if result.get("confidence"):
            print(f"       confidence={result['confidence']:.2f}, fallback={result['fallback']}, mode={result.get('mode')}")
        if result.get("intents"):
            print(f"       intents={result['intents']}")

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = len(results)
    ok = sum(1 for r in results if r["status"] == "ok" and not r["fallback"])
    fallback = sum(1 for r in results if r["fallback"])
    error = sum(1 for r in results if r["status"] in ("error", "exception"))

    print(f"Total: {total} | OK: {ok} ({ok/total*100:.0f}%) | Fallback: {fallback} | Error: {error}")
    print()

    # By category
    for cat in ["Multi-intent", "Weak Intent", "Interest+Info"]:
        cat_results = [r for r in results if r["category"] == cat]
        cat_ok = sum(1 for r in cat_results if r["status"] == "ok" and not r["fallback"])
        print(f"{cat:15s}: {cat_ok}/{len(cat_results)} OK")

    # Identify worst failures
    print()
    print("=" * 80)
    print("WORST FAILURES (fallbacks + errors)")
    print("=" * 80)
    failures = [r for r in results if r["fallback"] or r["status"] != "ok"]
    for f in failures[:5]:
        print(f"  [{f['id']:2d}] [{f['category']:15s}] {f['query'][:60]}")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "ok": ok,
            "fallback": fallback,
            "error": error,
            "ok_rate": f"{ok/total*100:.1f}%"
        },
        "by_category": {
            "multi_intent": sum(1 for r in results if r["category"] == "Multi-intent" and r["status"] == "ok" and not r["fallback"]),
            "weak_intent": sum(1 for r in results if r["category"] == "Weak Intent" and r["status"] == "ok" and not r["fallback"]),
            "interest_info": sum(1 for r in results if r["category"] == "Interest+Info" and r["status"] == "ok" and not r["fallback"]),
        },
        "results": results
    }

    output_file = "/tmp/stress_test_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print()
    print(f"Results saved to: {output_file}")

    return output

if __name__ == "__main__":
    run_stress_test()
