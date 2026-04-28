#!/usr/bin/env python3
"""Test course-aware responses with specific queries"""
import requests
import json

API_URL = "http://localhost:8000/api/v1/chat"

tests = [
    {
        "query": "Tell me about BCA",
        "description": "Generic course inquiry"
    },
    {
        "query": "What are the fees for BCA?",
        "description": "Fees inquiry (should use structured knowledge)"
    },
    {
        "query": "BCA admission process",
        "description": "Admission inquiry (should use structured knowledge)"
    },
]

for test in tests:
    payload = {
        "query": test["query"],
        "session_id": f"test-{test['query'][:10]}",
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
    print(f"TEST: {test['description']}")
    print(f"Query: {test['query']}")
    print(f"User Course: BCA")
    print("=" * 70)
    
    answer = data.get('answer', '')
    print(f"\nResponse: {answer[:150]}...")
    print(f"\nMetadata:")
    print(f"  Mode: {data.get('mode')}")
    print(f"  Intent: {data.get('intent')}")
    print(f"  Fallback: {data.get('fallback')}")
    print(f"  Confidence: {data.get('confidence')}")
    
    # Check if BCA is mentioned in response
    if 'bca' in answer.lower():
        print(f"✅ Response mentions BCA")
    else:
        print(f"⚠️ Response doesn't mention BCA")
    
    print()
