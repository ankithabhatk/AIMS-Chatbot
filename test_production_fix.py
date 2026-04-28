#!/usr/bin/env python3
"""
PRODUCTION FIX VERIFICATION TEST
=================================
Tests that RAG is now ALWAYS attempted, regardless of intent detection.

Previously failing queries that should now work:
- "campus facilities" → was fallback, should now be RAG ✅
- "placement record" → was fallback, should now be RAG ✅  
- Any query → should attempt RAG before fallback ✅
"""

import requests
import json
import time
from typing import Dict, Any

API_URL = "http://127.0.0.1:8000/api/v1/chat"
TIMEOUT = 10

TEST_QUERIES = [
    # These were returning fallback before - should now work via RAG
    "Does AIMS have campus facilities like hostel?",
    "What is the placement record at AIMS?",
    "Tell me about campus facilities",
    "What are placement statistics?",
    
    # These should still work via structured KB
    "What is the fee structure for MBA?",
    "What programs does AIMS offer?",
    "What is the admission process?",
]

def test_query(query: str, session_id: str = "test_session") -> Dict[str, Any]:
    """Send query to API and return response"""
    try:
        response = requests.post(
            API_URL,
            json={
                "query": query,
                "session_id": session_id,
                "retrieved_chunks": None,
                "intent": None
            },
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "status": "failed"}

def print_result(query: str, response: Dict[str, Any]) -> None:
    """Print formatted test result"""
    if "error" in response:
        print(f"❌ FAILED: {query}")
        print(f"   Error: {response['error']}\n")
        return
    
    mode = response.get("meta", {}).get("mode", "unknown")
    intent = response.get("meta", {}).get("intent", "unknown")
    fallback = response.get("meta", {}).get("fallback", False)
    confidence = response.get("meta", {}).get("confidence", 0)
    answer_len = len(response.get("answer", ""))
    
    status = "✅ PASS" if not fallback and answer_len > 50 else "⚠️ FALLBACK"
    
    print(f"{status}: {query}")
    print(f"   Mode: {mode} | Intent: {intent} | Confidence: {confidence:.2f}")
    print(f"   Answer length: {answer_len} chars")
    if fallback:
        print(f"   ⚠️ WARNING: Returned fallback mode")
    print()

def main():
    print("\n" + "="*80)
    print("PRODUCTION FIX VERIFICATION TEST")
    print("="*80 + "\n")
    
    print(f"Testing against: {API_URL}")
    print(f"Total queries to test: {len(TEST_QUERIES)}\n")
    
    # Test each query
    results = []
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] Testing...")
        response = test_query(query)
        results.append({
            "query": query,
            "response": response,
            "is_rag": response.get("meta", {}).get("mode") == "rag"
        })
        print_result(query, response)
        time.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    rag_count = sum(1 for r in results if r.get("is_rag"))
    fallback_count = sum(1 for r in results if r["response"].get("meta", {}).get("fallback"))
    failed_count = sum(1 for r in results if "error" in r["response"])
    
    print(f"✅ RAG mode used: {rag_count}/{len(TEST_QUERIES)}")
    print(f"⚠️  Fallback mode: {fallback_count}/{len(TEST_QUERIES)}")
    print(f"❌ Failed: {failed_count}/{len(TEST_QUERIES)}")
    print()
    
    # Key metric: RAG should be used more often
    if rag_count > fallback_count:
        print("✅ SUCCESS: RAG is now being used! (RAG > Fallback)")
    else:
        print("❌ ISSUE: Fallback still being used too much")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
