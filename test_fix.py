#!/usr/bin/env python3
"""Test quality control patch with real API"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"

def test_query(query: str, description: str):
    """Test a single query"""
    print(f"\n📌 Query: '{query}'")
    print(f"   ({description})")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={"query": query, "session_id": "test-session"},
            timeout=15
        )
        latency = (time.time() - start) * 1000
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
            return
        
        data = response.json()
        answer = data.get("answer", "")
        mode = data.get("mode", "")
        is_fallback = data.get("fallback", False)
        
        chars = len(answer)
        lines = len(answer.split("\n")) if answer else 0
        bullets = answer.count("•") if answer else 0
        
        print(f"Latency: {latency:.0f}ms | Chars: {chars} | Lines: {lines} | Bullets: {bullets}")
        print(f"Mode: {mode} | Fallback: {is_fallback}")
        print(f"Answer preview: {answer[:150]}..." if len(answer) > 150 else f"Answer: {answer}")
        
        # Quality checks
        if is_fallback:
            print(f"⚠️  FALLBACK RESPONSE (regression?)")
        elif chars > 600:
            print(f"⚠️  TOO LONG ({chars} chars, should be <600)")
        elif chars < 50:
            print(f"⚠️  TOO SHORT ({chars} chars)")
        else:
            print(f"✅ Quality check passed")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    print("🧪 TESTING QUALITY CONTROL PATCH")
    print("=" * 60)
    
    # Give server time to start
    print("\n⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test 1: Structured query (MBA fees)
    test_query("MBA fees", "Structured query - should hit fast path")
    
    # Test 2: RAG query - placements (was broken before fix)
    test_query("Tell me about placements", "RAG query - placements (was regressed)")
    
    # Test 3: RAG query - another angle on placements
    test_query("What about placements?", "RAG query - placements variant")
    
    # Test 4: RAG query - facilities
    test_query("Tell me about campus facilities", "RAG query - campus info")
    
    # Test 5: RAG query - course comparison
    test_query("Is MBA worth it?", "RAG query - reasoning question")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")

if __name__ == "__main__":
    main()
