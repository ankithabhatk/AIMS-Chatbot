"""
TEST 2: API vs UI COMPARISON
Direct API call vs UI interaction - do they match?
"""

import requests
import json
from datetime import datetime
import time

def test_api_vs_ui():
    print("\n" + "="*80)
    print("🧪 TEST 2: API vs UI COMPARISON")
    print("="*80)
    
    query = "What programs does AIMS offer?"
    
    # TEST 2a: Direct API call
    print(f"\n📡 Direct API Call")
    print("-" * 80)
    
    api_url = "http://localhost:8000/api/v1/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": query,
        "session_id": "test_session_123"
    }
    
    api_response = None
    api_latency = 0
    
    try:
        start = time.time()
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        api_latency = (time.time() - start) * 1000  # ms
        
        if response.status_code == 200:
            api_response = response.json()
            print(f"✅ API Status:          {response.status_code} OK")
            print(f"✅ Response received:   {len(json.dumps(api_response))} bytes")
            print(f"✅ Latency:             {api_latency:.2f}ms")
            print(f"\n📋 API Response:")
            print(json.dumps(api_response, indent=2)[:500] + "...")
        else:
            print(f"❌ API Status:          {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API Error: {e}")
    
    # TEST 2b: Browser UI interaction
    print(f"\n🌐 Browser UI Interaction")
    print("-" * 80)
    
    # This would be captured from the visible browser test
    print("ℹ️  Run TEST 1 first to see UI response")
    print("Then compare the responses below")
    
    # TEST 2c: Comparison
    print(f"\n📊 Comparison Results")
    print("-" * 80)
    
    if api_response:
        confidence = api_response.get('confidence', 0)
        answer = api_response.get('answer') or api_response.get('message', '')
        sources = api_response.get('sources', [])
        suggestions = api_response.get('suggestions', [])
        fallback = api_response.get('fallback', False)
        
        print(f"✅ Fallback Used:       {fallback}")
        print(f"✅ API Answer:          {answer[:100]}..." if len(answer) > 100 else f"✅ API Answer:          {answer}")
        print(f"✅ Confidence Score:    {confidence:.2%}")
        print(f"✅ Sources Found:       {len(sources)} documents")
        print(f"✅ Suggestions:         {len(suggestions)} follow-ups")
        print(f"✅ Response Latency:    {api_latency:.2f}ms")
        
        print(f"\n🔍 Detailed API Response:")
        print(json.dumps(api_response, indent=2))
    
    # TEST 2d: Summary
    print("\n" + "="*80)
    print("📊 TEST 2 SUMMARY")
    print("="*80)
    print(f"✅ API Endpoint:        {api_url}")
    print(f"✅ Query:               '{query}'")
    print(f"✅ API Response:        {'RECEIVED' if api_response else 'FAILED'}")
    if api_response:
        print(f"✅ Status:              {'PASSED ✅' if api_response.get('confidence', 0) > 0 else 'NO ANSWER'}")
    print("="*80)
    print("\n💡 Compare with TEST 1 screenshot to verify UI matches API response")

if __name__ == "__main__":
    test_api_vs_ui()
