#!/usr/bin/env python3
"""
Test the reranker - Does it fix topic accuracy?
Focus: placements, facilities, hostel
"""

import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_query(query: str, expected_keywords: list):
    """Test a single query"""
    print(f"\n{'='*70}")
    print(f"Query: '{query}'")
    print('='*70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={"query": query, "session_id": "rerank-test"},
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}")
            return False
        
        data = response.json()
        answer = data.get("answer", "")
        mode = data.get("mode", "")
        fallback = data.get("fallback", False)
        
        print(f"Mode: {mode} | Fallback: {fallback}")
        print(f"Answer ({len(answer)} chars):")
        print(f"---")
        print(answer)
        print(f"---")
        
        # Check for expected keywords
        answer_lower = answer.lower()
        found = [kw for kw in expected_keywords if kw in answer_lower]
        missing = [kw for kw in expected_keywords if kw not in answer_lower]
        
        print(f"\n✅ Found keywords: {found}")
        if missing:
            print(f"❌ Missing keywords: {missing}")
        else:
            print(f"✅ ALL keywords found - CORRECT TOPIC!")
        
        return len(missing) == 0
        
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🔥 RERANKER TEST - Topic Accuracy")
    print("="*70)
    
    # Wait for server
    print("\n⏳ Waiting for server...")
    time.sleep(3)
    
    # Test 1: Placements (should have LPA, salary, recruiters)
    print("\n" + "🎯 TEST 1: Placements Query".center(70))
    test1 = test_query(
        "Tell me about placements",
        ["placement", "salary", "lpa", "recruiter"]  # OR just need one
    )
    
    time.sleep(1)
    
    # Test 2: Facilities (should have hostel, campus, library)
    print("\n" + "🎯 TEST 2: Facilities Query".center(70))
    test2 = test_query(
        "Tell me about campus facilities",
        ["hostel", "campus", "library", "facility"]  # OR just need one
    )
    
    time.sleep(1)
    
    # Test 3: Placements variant
    print("\n" + "🎯 TEST 3: Placements Variant".center(70))
    test3 = test_query(
        "What about placements?",
        ["placement", "salary", "recruiter"]
    )
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Placements (main): {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Facilities: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Placements (variant): {'✅ PASS' if test3 else '❌ FAIL'}")
    
    if test1 and test2 and test3:
        print("\n🎉 RERANKER WORKING - ALL TOPICS CORRECT!")
    else:
        print("\n⚠️  Still some topic drift - may need adjustment")

if __name__ == "__main__":
    main()
