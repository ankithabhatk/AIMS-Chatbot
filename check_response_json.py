import requests
import json

API_URL = "http://127.0.0.1:8000/api/v1/chat"

session_id = "test-session-12345"
user_context = {
    "name": "Test User",
    "email": "test@example.com",
    "mobile": "9876543210",
    "course": "BCA"
}

query = "Tell me about BCA"

payload = {
    "query": query,
    "session_id": session_id,
    "user_context": user_context
}

response = requests.post(API_URL, json=payload, timeout=10)
print("Full JSON Response:")
print(json.dumps(response.json(), indent=2))
