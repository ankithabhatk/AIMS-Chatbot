#!/usr/bin/env python3
"""Direct test of course-aware API"""
import requests
import json

API_URL = "http://localhost:8000/api/v1/chat"

payload = {
    "query": "Tell me about BCA",
    "session_id": "test-bca-001",
    "user": {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "9876543210",
        "course": "BCA"
    }
}

response = requests.post(API_URL, json=payload)
data = response.json()

print("=" * 70)
print("QUERY: Tell me about BCA")
print("USER COURSE: BCA")
print("=" * 70)
print("\nRESPONSE:")
print(data.get('answer', 'NO ANSWER'))
print("\nMETADATA:")
print(f"Intent: {data.get('intent')}")
print(f"Fallback: {data.get('fallback')}")
print(f"Mode: {data.get('mode')}")

# Check if response is course-specific
answer = data.get('answer', '').lower()
if 'bca' in answer or 'bachelor of computer' in answer or 'computer applications' in answer:
    print("\n✅ SUCCESS: Got course-specific response!")
else:
    print("\n❌ FAIL: Got generic response")
