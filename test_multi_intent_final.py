"""
Final test for multi-intent handling.

Verifies that queries like "fees and hostel" return BOTH topics.
"""

import requests

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str):
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"test-final-{hash(query)}",
    }
    response = requests.post(API_URL, json=payload, timeout=10)
    return response.json()

# Critical multi-intent test cases
test_cases = [
    {
        "query": "fees and hostel",
        "must_contain": ["fee", "hostel"],
        "description": "Must return BOTH fees AND hostel"
    },
    {
        "query": "courses and fees",
        "must_contain": ["course", "fee"],
        "description": "Must return BOTH courses AND fees"
    },
    {
        "query": "what about bca fees and hostel",
        "must_contain": ["bca", "fee", "hostel"],
        "description": "Must return BCA fees AND hostel"
    },
    {
        "query": "scholarship and fees",
        "must_contain": ["scholarship", "fee"],
        "description": "Must return BOTH scholarship AND fees"
    },
]

print("=" * 80)
print("MULTI-INTENT FINAL TEST")
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
    print("✅ Multi-intent handling is WORKING!")
else:
    print("❌ Some multi-intent queries still failing")

exit(0 if all(results) else 1)
