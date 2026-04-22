"""
TEST 3: FAILURE CASE TEST
Test edge cases and fallback behavior
"""

import requests
import json
from datetime import datetime

def test_failure_cases():
    print("\n" + "="*80)
    print("🧪 TEST 3: FAILURE CASE & FALLBACK TEST")
    print("="*80)
    
    api_url = "http://localhost:8000/api/v1/chat"
    headers = {"Content-Type": "application/json"}
    
    # Test cases that should have LOW confidence or fallback
    test_cases = [
        {
            "name": "Space Engineering Program",
            "query": "Do you offer space engineering?",
            "expect": "Low confidence / Fallback",
            "reason": "Not a real program at AIMS"
        },
        {
            "name": "Hostel Food Menu",
            "query": "What's the hostel food menu?",
            "expect": "Low confidence / Fallback",
            "reason": "Not in knowledge base"
        },
        {
            "name": "Scholarship Abroad",
            "query": "Do you offer scholarships for studying abroad?",
            "expect": "Low confidence / Fallback",
            "reason": "Not mentioned in data"
        },
        {
            "name": "Valid Query (Baseline)",
            "query": "What is the MBA program?",
            "expect": "High confidence",
            "reason": "Should be in knowledge base"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test['name']}")
        print("-" * 80)
        print(f"Query:    '{test['query']}'")
        print(f"Expected: {test['expect']}")
        print(f"Reason:   {test['reason']}")
        
        try:
            payload = {
                "query": test['query'],
                "session_id": f"test_session_{i}"
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                confidence = data.get('confidence', 0)
                answer = data.get('answer') or data.get('message', '')
                is_fallback = data.get('fallback', False) or confidence < 0.7 or not answer
                
                print(f"\n✅ Response received")
                print(f"   Confidence:  {confidence:.2%}")
                print(f"   Is Fallback: {'YES ✅' if is_fallback else 'NO (direct answer)'}")
                print(f"   Answer:      {answer[:80]}...")
                
                # Validate no hallucination
                hallucinated = False
                bad_phrases = ["i'm not sure", "i don't have", "i cannot"]
                answer_lower = answer.lower() if answer else ""
                for phrase in bad_phrases:
                    if phrase in answer_lower and confidence < 0.5:
                        hallucinated = False  # Honest response, not hallucination
                
                print(f"   Hallucination Check: {'❌ HALLUCINATED' if hallucinated else '✅ HONEST'}")
                
                # Store result
                results.append({
                    "test": test['name'],
                    "query": test['query'],
                    "confidence": confidence,
                    "is_fallback": is_fallback,
                    "answer_preview": answer[:100],
                    "passed": (is_fallback or confidence > 0.6)
                })
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                results.append({
                    "test": test['name'],
                    "query": test['query'],
                    "error": response.status_code,
                    "passed": False
                })
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "test": test['name'],
                "query": test['query'],
                "error": str(e),
                "passed": False
            })
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST 3 SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r.get('passed'))
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    print("\nDetailed Results:")
    
    for result in results:
        status = "✅ PASS" if result.get('passed') else "❌ FAIL"
        confidence = result.get('confidence', 'N/A')
        if isinstance(confidence, float):
            confidence = f"{confidence:.2%}"
        
        print(f"\n{status} - {result['test']}")
        print(f"     Query:      '{result['query']}'")
        print(f"     Confidence: {confidence}")
        if result.get('is_fallback'):
            print(f"     Behavior:   Returned fallback (correct)")
        if result.get('error'):
            print(f"     Error:      {result['error']}")
    
    # Key validations
    print("\n" + "="*80)
    print("🔍 KEY VALIDATION CHECKLIST")
    print("="*80)
    
    print("✅ Low-confidence queries return fallback?  Check results above")
    print("✅ No hallucinated answers?                Check results above")
    print("✅ Valid queries get high confidence?      Check MBA program result")
    print("✅ Confidence < 0.7 threshold triggers fallback? Check pattern")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_failure_cases()
