"""
Test placement handling in multi-intent queries.
"""

import requests

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str):
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"test-placement-{hash(query)}",
    }
    response = requests.post(API_URL, json=payload, timeout=10)
    return response.json()

# Test cases for placement handling
test_cases = [
    {
        "query": "fees and placements",
        "must_contain": ["fee", "placement"],
        "description": "Must return BOTH fees AND placements"
    },
    {
        "query": "fees and hostel and placements",
        "must_contain": ["fee", "hostel"],  # Only top 2 intents
        "description": "Must return fees AND hostel (top 2 intents)"
    },
    {
        "query": "placements",
        "must_contain": ["placement"],
        "description": "Must return placement info"
    },
]

print("=" * 80)
print("PLACEMENT MULTI-INTENT TEST")
print("=" * 80)

results = []
for i, test in enumerate(test_cases, 1):
    print(f"\n[TEST {i}] {test['query']}")
    print(f"Expected: {test['description']}")
    
    response = test_query(test["query"])
    answer = response.get("answer", "").lower()
    intent = response.get("intent", "unknown")
    
    # Check if all required keywords are present
    missing = []
    for keyword in test["must_contain"]:
        if keyword.lower() not in answer:
            missing.append(keyword)
    
    if missing:
        print(f"❌ FAILED - Missing: {missing}")
        print(f"Intent: {intent}")
        print(f"Answer preview: {answer[:200]}...")
        results.append(False)
    else:
        print(f"✅ PASSED - All topics covered")
        print(f"Intent: {intent}")
        results.append(True)

print("\n" + "=" * 80)
print(f"RESULTS: {sum(results)}/{len(results)} passed")
print("=" * 80)

if all(results):
    print("✅ Placement handling is WORKING!")
else:
    print("❌ Some placement queries still failing")

exit(0 if all(results) else 1)
