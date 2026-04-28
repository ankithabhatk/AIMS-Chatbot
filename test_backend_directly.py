import requests
import json

API_URL = "http://127.0.0.1:8000/api/v1/chat"

# Test with proper session and profile context
session_id = "test-session-12345"
user_context = {
    "name": "Test User",
    "email": "test@example.com",
    "mobile": "9876543210",
    "course": "BCA"
}

test_queries = [
    "Tell me about BCA",
    "What are the fees?",
    "admission process"
]

print("\n🔍 TESTING BACKEND API DIRECTLY\n")
print(f"Session ID: {session_id}")
print(f"User Context: {user_context}")
print(f"{'='*70}\n")

for i, query in enumerate(test_queries, 1):
    print(f"\n{'='*70}")
    print(f"TEST {i}: {query}")
    print(f"{'='*70}")
    
    payload = {
        "query": query,
        "session_id": session_id,
        "user_context": user_context
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Status: {response.status_code}")
            answer = data.get('answer', '') or data.get('response', '')
            print(f"\n📝 ANSWER:")
            print(f"{answer}")
            print(f"\n--- Metadata ---")
            print(f"  confidence: {data.get('confidence_score', 0)}")
            print(f"  is_fallback: {data.get('is_fallback', False)}")
            print(f"  suggestions: {data.get('suggestions', [])}")
        else:
            print(f"\n❌ Status: {response.status_code}")
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")


