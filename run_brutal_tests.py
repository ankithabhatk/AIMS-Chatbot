"""
Run brutal test queries and analyze results.
"""

import requests
from brutal_test_queries import BRUTAL_QUERIES, CATEGORIES

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str):
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"brutal-{hash(query)}",
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

print("=" * 80)
print("BRUTAL TEST SUITE")
print("=" * 80)

results = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "errors": 0,
}

failed_queries = []

for i, query in enumerate(BRUTAL_QUERIES, 1):
    results["total"] += 1
    
    response = test_query(query)
    
    if "error" in response:
        print(f"❌ [{i:2d}] ERROR: {query}")
        print(f"    Error: {response['error']}")
        results["errors"] += 1
        failed_queries.append((query, "ERROR", response.get("error", "Unknown")))
    else:
        answer = response.get("answer", "")
        intent = response.get("intent", "unknown")
        confidence = response.get("confidence", 0.0)
        fallback = response.get("fallback", False)
        
        # Simple success criteria: got an answer, not a fallback
        if answer and not fallback:
            print(f"✅ [{i:2d}] {query[:50]:50s} | Intent: {intent:20s}")
            results["success"] += 1
        else:
            print(f"⚠️  [{i:2d}] {query[:50]:50s} | Intent: {intent:20s} | Fallback: {fallback}")
            results["failed"] += 1
            failed_queries.append((query, intent, "Fallback or empty answer"))

print("\n" + "=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)
print(f"Total queries: {results['total']}")
print(f"Success: {results['success']} ({results['success']/results['total']*100:.1f}%)")
print(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
print(f"Errors: {results['errors']} ({results['errors']/results['total']*100:.1f}%)")

if failed_queries:
    print("\n" + "=" * 80)
    print("FAILED QUERIES")
    print("=" * 80)
    for query, intent, reason in failed_queries:
        print(f"Query: {query}")
        print(f"Intent: {intent}")
        print(f"Reason: {reason}")
        print()

print("=" * 80)

exit(0 if results["success"] == results["total"] else 1)
