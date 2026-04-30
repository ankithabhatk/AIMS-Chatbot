"""
Test to verify lead-gate hijacking is fixed.

BEFORE FIX:
- User asks "fees" → System forces lead capture form ❌
- User asks "scholarship" → System forces lead capture form ❌
- User asks "hostel" → System forces lead capture form ❌

AFTER FIX:
- User asks "fees" → System returns actual fees information ✅
- User asks "scholarship" → System returns scholarship information ✅
- User asks "hostel" → System returns hostel information ✅

Lead capture should ONLY trigger on explicit application intent like:
- "I want to apply"
- "I want to join"
- "Contact me"
"""

import requests
import json

API_URL = "http://127.0.0.1:8000/api/v1/chat"
SESSION_ID = "test-lead-gate-fix"

def test_query(query: str, course: str = None) -> dict:
    """Send a query and return the response."""
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": SESSION_ID,
    }
    if course:
        payload["context"] = {"course": course}
    
    response = requests.post(API_URL, json=payload)
    return response.json()

def main():
    print("=" * 80)
    print("TESTING: Lead-Gate Hijacking Fix")
    print("=" * 80)
    
    test_cases = [
        ("What are the BCA fees?", "BCA", "fees"),
        ("Tell me about scholarships", None, "scholarship"),
        ("What about hostel facilities?", None, "hostel"),
        ("How do I apply?", None, "admission"),
    ]
    
    results = []
    for i, (query, course, expected_topic) in enumerate(test_cases, 1):
        print(f"\n[Test {i}] Query: {query}")
        print(f"Expected: Information about {expected_topic}")
        
        response = test_query(query, course)
        status = response.get("status", "unknown")
        intent = response.get("intent", "unknown")
        answer = response.get("answer", "")
        
        # Check if it's a lead capture response
        is_lead_capture = (
            status == "lock" or
            intent == "Lead Capture" or
            "provide" in answer.lower() and "email" in answer.lower()
        )
        
        if is_lead_capture:
            print(f"❌ FAILED: Got lead capture form instead of information")
            print(f"   Status: {status}, Intent: {intent}")
            results.append(False)
        else:
            print(f"✅ PASSED: Got information response")
            print(f"   Status: {status}, Intent: {intent}")
            print(f"   Answer preview: {answer[:150]}...")
            results.append(True)
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 80)
    
    if all(results):
        print("✅ Lead-gate hijacking is FIXED!")
        print("Users now get INFORMATION for info queries, not forms.")
    else:
        print("❌ Some tests failed. Lead-gate may still be active.")
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    exit(main())
