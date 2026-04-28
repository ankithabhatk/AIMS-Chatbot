#!/usr/bin/env python3
"""Test course awareness in backend - direct API call with user context"""

import requests
import json
import uuid

API_URL = "http://localhost:8000/api/v1/chat"
SESSION_ID = str(uuid.uuid4())

# Test with BCA course in user context
payload = {
    "query": "Tell me about BCA",
    "session_id": SESSION_ID,
    "user": {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "9876543210",
        "course": "BCA"  # User's course
    }
}

print("=" * 60)
print("TEST: Course-Aware Response")
print("=" * 60)
print(f"\nPayload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

response = requests.post(API_URL, json=payload)

if response.status_code == 200:
    data = response.json()
    print(f"\n✅ Response (200):")
    print(f"Answer: {data.get('answer', '')}")
    print(f"Intent: {data.get('intent', '')}")
    print(f"Fallback: {data.get('fallback', '')}")
    print(f"Confidence: {data.get('confidence', '')}")
    
    # Check if we got course-specific response
    answer = data.get('answer', '').lower()
    if 'bca' in answer or 'course' in answer or 'curriculum' in answer:
        print("\n✅ SUCCESS: Got course-aware response!")
    elif 'try asking' in answer or 'generic' in answer:
        print("\n❌ FAIL: Still getting generic fallback")
    else:
        print("\n⚠️ Got response but unclear if course-aware")
else:
    print(f"\n❌ Error: {response.status_code}")
    print(response.text)

# Test 2: Query about fees for user's course
print("\n\n" + "=" * 60)
print("TEST 2: Fees inquiry for user's course")
print("=" * 60)

payload2 = {
    "query": "What are the fees?",
    "session_id": str(uuid.uuid4()),
    "user": {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "9876543210",
        "course": "BCA"
    }
}

response2 = requests.post(API_URL, json=payload2)
if response2.status_code == 200:
    data2 = response2.json()
    print(f"\nAnswer: {data2.get('answer', '')}")
    answer = data2.get('answer', '').lower()
    if 'bca' in answer or 'fee' in answer and 'bca' in answer:
        print("✅ Got course-specific fees response")
    else:
        print("⚠️ Response received but may not be BCA-specific")
else:
    print(f"Error: {response2.status_code}")

# Test 3: Admission inquiry
print("\n\n" + "=" * 60)
print("TEST 3: Admission inquiry for user's course")
print("=" * 60)

payload3 = {
    "query": "How do I get admitted to BCA?",
    "session_id": str(uuid.uuid4()),
    "user": {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "9876543210",
        "course": "BCA"
    }
}

response3 = requests.post(API_URL, json=payload3)
if response3.status_code == 200:
    data3 = response3.json()
    print(f"\nAnswer: {data3.get('answer', '')}")
    print(f"Fallback: {data3.get('fallback', '')}")
else:
    print(f"Error: {response3.status_code}")

print("\n" + "=" * 60)
