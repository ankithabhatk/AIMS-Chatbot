#!/usr/bin/env python3
"""Test apply intent routing - single pattern validation"""

import requests

API_URL = "http://localhost:8000/api/v1/chat"

# Test scenarios: apply intent should route to apply mode
test_cases = [
    "how to apply",
    "application process",
    "how do I apply for BCA",
    "what is the admission procedure",
    "tell me the application steps",
    "I want to apply",
    "show me how to join",
    "what documents do I need to apply",
    "application form",
    "admission process for MBA"
]

def test_query(query, session_id):
    response = requests.post(
        API_URL,
        json={"query": query, "session_id": session_id},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        return {"error": f"HTTP {response.status_code}"}
    
    data = response.json()
    return {
        "mode": data.get("mode"),
        "intent": data.get("intent"),
        "answer_preview": data.get("answer", "")[:80]
    }

def main():
    print("🧪 Testing Apply Intent Routing\n")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, query in enumerate(test_cases, 1):
        session_id = f"test-apply-{i}"
        print(f"\n{i}. Query: '{query}'")
        
        result = test_query(query, session_id)
        
        if "error" in result:
            print(f"   ❌ ERROR: {result['error']}")
            failed += 1
            continue
        
        mode = result["mode"]
        intent = result["intent"]
        
        # Check if routed to apply mode
        if mode == "apply" or intent == "apply" or mode == "conversion":
            print(f"   ✅ PASS - Mode: {mode}, Intent: {intent}")
            passed += 1
        else:
            print(f"   ❌ FAIL - Mode: {mode}, Intent: {intent}")
            print(f"   Answer: {result['answer_preview']}...")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"\n📊 Results: {passed}/{len(test_cases)} passed")
    
    routing_success = passed / len(test_cases) * 100
    print(f"🎯 Routing Success Rate: {routing_success:.0f}%")
    
    if passed == len(test_cases):
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {failed} tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
