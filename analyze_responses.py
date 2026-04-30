"""
Analyze responses for subtle issues that automated tests miss.

Looking for:
1. Multi-intent handling - Does it answer ALL parts?
2. Response bloat - Too much irrelevant info?
3. Wrong routing - Correct intent but wrong response?
4. Missing context - Should use course context but doesn't?
"""

import requests
import json

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def query_system(query: str, course: str = None):
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"analyze-{hash(query)}",
    }
    if course:
        payload["context"] = {"course": course}
    
    response = requests.post(API_URL, json=payload, timeout=10)
    return response.json()

# Critical test cases to analyze manually
CRITICAL_TESTS = [
    {
        "query": "fees and hostel and placements",
        "expected": "Should answer ALL THREE topics",
        "check": "Does it mention fees AND hostel AND placements?"
    },
    {
        "query": "what about bca fees and hostel",
        "expected": "Should answer BOTH BCA fees AND hostel",
        "check": "Does it mention BCA fees AND hostel facilities?"
    },
    {
        "query": "tell me courses and fees",
        "expected": "Should list courses AND show fees",
        "check": "Does it show course list AND fee structure?"
    },
    {
        "query": "tell everything about bca",
        "expected": "Comprehensive BCA info (duration, eligibility, fees, etc.)",
        "check": "Does it cover multiple aspects of BCA?"
    },
    {
        "query": "i want something in computers what can i take",
        "expected": "Suggest BCA/MCA courses",
        "check": "Does it suggest computer-related courses?"
    },
    {
        "query": "how much money for bca",
        "expected": "BCA fees only",
        "check": "Does it show BCA fees without other courses?"
    },
]

print("=" * 80)
print("MANUAL RESPONSE ANALYSIS")
print("=" * 80)

for i, test in enumerate(CRITICAL_TESTS, 1):
    print(f"\n[TEST {i}] {test['query']}")
    print(f"Expected: {test['expected']}")
    print(f"Check: {test['check']}")
    print("-" * 80)
    
    response = query_system(test["query"])
    answer = response.get("answer", "")
    intent = response.get("intent", "unknown")
    
    print(f"Intent: {intent}")
    print(f"\nResponse:\n{answer}\n")
    print("=" * 80)
    
    # Wait for manual review
    input("Press Enter to continue...")
