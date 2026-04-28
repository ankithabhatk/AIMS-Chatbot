import requests
import json

# Test API directly
url = "http://127.0.0.1:8000/api/v1/chat"
payload = {
    "query": "Fees structure",
    "context": {"session_id": "test-session"}
}

print("Testing API directly...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=5)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
