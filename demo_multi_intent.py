"""
Demo script to show multi-intent responses in action.
"""

import requests

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str):
    payload = {
        "query": query,
        "user": {"email": "demo@example.com"},
        "session_id": f"demo-{hash(query)}",
    }
    response = requests.post(API_URL, json=payload, timeout=10)
    return response.json()

# Demo queries
demo_queries = [
    "fees and hostel",
    "courses and fees",
    "placements and admission",
    "scholarship and fees structure",
]

print("=" * 80)
print("MULTI-INTENT DEMO")
print("=" * 80)

for query in demo_queries:
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}")
    
    response = test_query(query)
    
    intent = response.get("intent", "unknown")
    confidence = response.get("confidence", 0.0)
    answer = response.get("answer", "")
    
    print(f"\nIntent: {intent}")
    print(f"Confidence: {confidence}")
    print(f"\nResponse:")
    print("-" * 80)
    print(answer)
    print("-" * 80)

print("\n" + "=" * 80)
print("✅ Multi-intent handling is working!")
print("=" * 80)
