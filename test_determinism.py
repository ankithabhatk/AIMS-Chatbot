"""
Test determinism - same query should return identical response every time.
"""

import requests
import hashlib

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str, run_id: int):
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"test-determinism-{run_id}",
    }
    response = requests.post(API_URL, json=payload, timeout=10)
    return response.json()

def hash_response(response: dict) -> str:
    """Hash the answer and intent to check for consistency."""
    answer = response.get("answer", "")
    intent = response.get("intent", "")
    combined = f"{intent}|{answer}"
    return hashlib.md5(combined.encode()).hexdigest()

# Test query
query = "fees and hostel"

print("=" * 80)
print("DETERMINISM TEST")
print("=" * 80)
print(f"\nQuery: {query}")
print("Running 10 times...\n")

hashes = []
intents = []
answers = []

for i in range(1, 11):
    response = test_query(query, i)
    intent = response.get("intent", "unknown")
    answer = response.get("answer", "")
    response_hash = hash_response(response)
    
    hashes.append(response_hash)
    intents.append(intent)
    answers.append(answer[:100])  # First 100 chars for comparison
    
    print(f"Run {i:2d}: Intent={intent:20s} Hash={response_hash}")

print("\n" + "=" * 80)

# Check if all hashes are identical
unique_hashes = set(hashes)
unique_intents = set(intents)

if len(unique_hashes) == 1:
    print("✅ DETERMINISTIC - All responses identical")
    print(f"   Intent: {intents[0]}")
    print(f"   Hash: {hashes[0]}")
else:
    print(f"❌ NON-DETERMINISTIC - Found {len(unique_hashes)} different responses")
    print(f"   Unique hashes: {unique_hashes}")
    print(f"   Unique intents: {unique_intents}")

print("=" * 80)

exit(0 if len(unique_hashes) == 1 else 1)
