#!/usr/bin/env python3
"""Test structured knowledge routing after fix"""

import requests
import json

API_URL = "http://localhost:8000/api/v1/chat"

test_queries = [
    "BCA fees",
    "MBA fees",
    "BBA admission",
    "MCA placements",
    "B.Com courses",
    "BHM eligibility"
]

def test_query(query, session_id):
    """Test a single query"""
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
        "used_structured": data.get("meta", {}).get("used_structured", False),
        "answer_preview": data.get("answer", "")[:100]
    }

def main():
    print("🧪 Testing Structured Knowledge Routing\n")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, query in enumerate(test_queries, 1):
        session_id = f"test-struct-{i}"
        print(f"\n{i}. Query: '{query}'")
        print(f"   Session: {session_id}")
        
        result = test_query(query, session_id)
        
        if "error" in result:
            print(f"   ❌ ERROR: {result['error']}")
            failed += 1
            continue
        
        mode = result["mode"]
        used_structured = result["used_structured"]
        
        if mode == "structured" and used_structured:
            print(f"   ✅ PASS - Mode: {mode}, Intent: {result['intent']}")
            print(f"   Answer: {result['answer_preview']}...")
            passed += 1
        else:
            print(f"   ❌ FAIL - Mode: {mode}, Used Structured: {used_structured}")
            print(f"   Answer: {result['answer_preview']}...")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"\n📊 Results: {passed}/{len(test_queries)} passed")
    
    if passed == len(test_queries):
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {failed} tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
