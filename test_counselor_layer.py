"""
Test counselor layer for exploratory queries.
"""

import requests
import time

API_URL = "http://127.0.0.1:8000/api/v1/chat"

# Exploratory test queries
EXPLORATORY_QUERIES = [
    # Interest-based
    "I like coding, what should I choose?",
    "I'm interested in business, which course is best?",
    "I love technology and want to build apps",
    "I want to start my own company",
    "I'm good at math and finance",
    
    # Uncertainty
    "I'm not sure what to study",
    "I don't know which course to choose",
    "Help me choose the right program",
    "I'm confused between BCA and BBA",
    
    # Program comparisons
    "BCA or BBA which is better?",
    "What's the difference between BCA and BBA?",
    "Should I do MBA or MCA after graduation?",
    "Which course has better placements?",
    
    # Career exploration
    "What career options do I have after BCA?",
    "I want a high-paying job, what should I study?",
    "Which course is best for future?",
]

def test_query(query: str) -> dict:
    """Send query to chatbot API"""
    payload = {
        "query": query,
        "session_id": f"counselor-test-{hash(query)}",
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def check_counselor_quality(answer: str, intent: str) -> dict:
    """Check if response is conversational and guidance-oriented"""
    
    # Counselor indicators
    conversational_signals = [
        "nice", "great", "let me ask", "tell me",
        "which one", "what do you", "are you",
        "👨‍💻", "🚀", "📊", "🎯", "🎓", "🏨", "💼",
    ]
    
    guidance_signals = [
        "you have", "main paths", "good for",
        "career", "placements", "learn:",
        "quick decision", "sounds more like you",
    ]
    
    info_dump_signals = [
        "duration:", "eligibility:", "fee structure",
        "admission process:", "documents required",
    ]
    
    is_conversational = any(signal in answer.lower() for signal in conversational_signals)
    is_guidance = any(signal in answer.lower() for signal in guidance_signals)
    is_info_dump = any(signal in answer.lower() for signal in info_dump_signals)
    is_counselor_intent = "counselor" in intent.lower()
    
    # Good counselor response: conversational + guidance, NOT info dump
    if is_conversational and is_guidance and not is_info_dump and is_counselor_intent:
        quality = "excellent"
    elif is_counselor_intent and (is_conversational or is_guidance):
        quality = "good"
    elif is_counselor_intent:
        quality = "detected_but_weak"
    else:
        quality = "not_counselor"
    
    return {
        "is_conversational": is_conversational,
        "is_guidance": is_guidance,
        "is_info_dump": is_info_dump,
        "is_counselor_intent": is_counselor_intent,
        "quality": quality,
    }

def main():
    print("\n" + "="*80)
    print("COUNSELOR LAYER TEST - EXPLORATORY QUERIES")
    print("="*80 + "\n")
    
    results = {
        "total": 0,
        "counselor_detected": 0,
        "excellent": 0,
        "good": 0,
        "detected_but_weak": 0,
        "not_counselor": 0,
        "errors": 0,
    }
    
    for i, query in enumerate(EXPLORATORY_QUERIES, 1):
        print(f"[{i}/{len(EXPLORATORY_QUERIES)}] Testing: {query}")
        
        response = test_query(query)
        results["total"] += 1
        
        if "error" in response:
            print(f"  ❌ ERROR: {response['error']}\n")
            results["errors"] += 1
            continue
        
        intent = response.get("intent", "")
        confidence = response.get("confidence", 0.0)
        answer = response.get("answer", "")
        fallback = response.get("fallback", False)
        
        # Check counselor quality
        quality = check_counselor_quality(answer, intent)
        
        if quality["is_counselor_intent"]:
            results["counselor_detected"] += 1
        
        results[quality["quality"]] += 1
        
        # Status emoji
        if quality["quality"] == "excellent":
            status = "✅ EXCELLENT"
        elif quality["quality"] == "good":
            status = "✅ GOOD"
        elif quality["quality"] == "detected_but_weak":
            status = "⚠️  WEAK"
        else:
            status = "❌ NOT COUNSELOR"
        
        print(f"  {status}")
        print(f"  Intent: {intent} | Confidence: {confidence:.2f} | Fallback: {fallback}")
        print(f"  Quality breakdown:")
        print(f"    - Conversational: {'✓' if quality['is_conversational'] else '✗'}")
        print(f"    - Guidance-oriented: {'✓' if quality['is_guidance'] else '✗'}")
        print(f"    - Info dump: {'✓' if quality['is_info_dump'] else '✗'}")
        print(f"    - Counselor intent: {'✓' if quality['is_counselor_intent'] else '✗'}")
        
        # Show first 200 chars of answer
        preview = answer[:200] + "..." if len(answer) > 200 else answer
        print(f"  💬 Preview: {preview}")
        print()
        
        time.sleep(0.3)
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total queries: {results['total']}")
    print(f"Errors: {results['errors']}")
    print(f"Counselor detected: {results['counselor_detected']}/{results['total']} ({results['counselor_detected']/results['total']*100:.1f}%)")
    print(f"\nQuality breakdown:")
    print(f"  ✅ Excellent: {results['excellent']}/{results['total']} ({results['excellent']/results['total']*100:.1f}%)")
    print(f"  ✅ Good: {results['good']}/{results['total']} ({results['good']/results['total']*100:.1f}%)")
    print(f"  ⚠️  Detected but weak: {results['detected_but_weak']}/{results['total']} ({results['detected_but_weak']/results['total']*100:.1f}%)")
    print(f"  ❌ Not counselor: {results['not_counselor']}/{results['total']} ({results['not_counselor']/results['total']*100:.1f}%)")
    
    # Success rate
    success_rate = (results['excellent'] + results['good']) / results['total'] * 100
    print(f"\n🎯 Success rate (excellent + good): {success_rate:.1f}%")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
