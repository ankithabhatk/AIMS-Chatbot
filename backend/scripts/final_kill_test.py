import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/chat"

def run_kill_test():
    session_id = "test_kill_session_123"
    user_context = {
        "name": "Test User",
        "email": "test@example.com",
        "mobile": "9876543210",
        "course": "MBA"
    }

    results = {}

    # 1. First query
    print("🚀 Query 1: mba fees")
    r1 = requests.post(BASE_URL, json={
        "query": "mba fees",
        "context": {"session_id": session_id},
        "user": user_context
    })
    data1 = r1.json()
    results[1] = data1
    print(f"   Mode: {data1.get('mode')}, Intent: {data1.get('intent')}, Fallback: {data1.get('fallback')}")

    # 2. Repeat
    print("\n🚀 Query 2: mba fees (Repeat)")
    r2 = requests.post(BASE_URL, json={
        "query": "mba fees",
        "context": {"session_id": session_id},
        "user": user_context
    })
    data2 = r2.json()
    results[2] = data2
    print(f"   Matches Query 1: {data1.get('answer') == data2.get('answer')}")

    # 3. Multi-intent
    print("\n🚀 Query 3: mba fees and placement")
    r3 = requests.post(BASE_URL, json={
        "query": "mba fees and placement",
        "context": {"session_id": session_id},
        "user": user_context
    })
    data3 = r3.json()
    results[3] = data3
    print(f"   Mode: {data3.get('mode')}, Intent: {data3.get('intent')}")
    print(f"   Contains Fee: {'fee' in data3.get('answer').lower()}")
    print(f"   Contains Placement: {'placement' in data3.get('answer').lower()}")

    # 4. Out of scope
    print("\n🚀 Query 4: iit bombay fees")
    r4 = requests.post(BASE_URL, json={
        "query": "iit bombay fees",
        "context": {"session_id": session_id},
        "user": user_context
    })
    data4 = r4.json()
    results[4] = data4
    print(f"   Fallback: {data4.get('fallback')}")
    print(f"   Answer snippet: {data4.get('answer')[:50]}")

    # 7. Spam test (Logic check)
    print("\n🚀 Query 7: Spam test (5x)")
    for i in range(5):
        requests.post(BASE_URL, json={
            "query": "mba fees",
            "context": {"session_id": session_id},
            "user": user_context
        })
    print("   Sent 5 requests. Check logs for duplication.")

    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print(f"1 -> {'PASS' if not data1.get('fallback') and data1.get('mode') == 'structured' else 'FAIL'}")
    print(f"2 -> {'PASS' if data1.get('answer') == data2.get('answer') else 'FAIL'}")
    print(f"3 -> {'PASS' if 'fee' in data3.get('answer').lower() and 'placement' in data3.get('answer').lower() else 'FAIL'}")
    print(f"4 -> {'PASS' if data4.get('fallback') else 'FAIL'}")
    print("="*50)

if __name__ == "__main__":
    run_kill_test()
