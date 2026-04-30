"""
Test improved boundary handler with real-world context.
"""

import requests
import time

API_URL = "http://127.0.0.1:8000/api/v1/chat"

# Boundary test queries
BOUNDARY_QUERIES = [
    # External exams
    "Do I need JEE for BCA?",
    "What is the NEET cutoff for AIMS?",
    "Does AIMS accept SAT scores?",
    "Is CAT required for MBA at AIMS?",
    "What is the KCET rank required?",
    
    # Comparative queries
    "Is AIMS better than Christ University?",
    "AIMS vs PES University which is better?",
    "Compare AIMS with Jain University",
    
    # External cutoffs
    "What is the cutoff for BCA?",
    "What rank do I need for admission?",
    
    # Generic out-of-scope
    "Tell me about IIT admissions",
    "What are the top engineering colleges in Bangalore?",
]

def test_query(query: str) -> dict:
    """Send query to chatbot API"""
    payload = {
        "query": query,
        "session_id": f"boundary-test-{hash(query)}",
    }
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def check_context_quality(answer: str) -> dict:
    """Check if response includes real-world context"""
    
    # Context indicators
    context_phrases = [
        "about",
        "used for",
        "depends on",
        "vary by",
        "national-level",
        "state-level",
        "standardized test",
        "entrance exam",
        "admission to",
    ]
    
    has_context = any(phrase in answer.lower() for phrase in context_phrases)
    has_aims_info = "aims" in answer.lower()
    has_redirect = any(word in answer.lower() for word in ["would you like", "can help", "recommend"])
    
    return {
        "has_context": has_context,
        "has_aims_info": has_aims_info,
        "has_redirect": has_redirect,
        "quality": "good" if (has_context and has_aims_info and has_redirect) else "needs_improvement"
    }

def main():
    print("\n" + "="*80)
    print("BOUNDARY HANDLER TEST - IMPROVED WITH CONTEXT")
    print("="*80 + "\n")
    
    results = {
        "total": 0,
        "success": 0,
        "good_quality": 0,
        "has_context": 0,
        "has_aims_info": 0,
        "has_redirect": 0,
    }
    
    for i, query in enumerate(BOUNDARY_QUERIES, 1):
        print(f"[{i}/{len(BOUNDARY_QUERIES)}] Testing: {query}")
        
        response = test_query(query)
        results["total"] += 1
        
        if "error" in response:
            print(f"  ❌ ERROR: {response['error']}\n")
            continue
        
        intent = response.get("intent", "")
        confidence = response.get("confidence", 0.0)
        answer = response.get("answer", "")
        
        # Check if boundary handler was triggered
        if "out_of_scope" in intent:
            results["success"] += 1
            
            # Check context quality
            quality = check_context_quality(answer)
            
            if quality["has_context"]:
                results["has_context"] += 1
            if quality["has_aims_info"]:
                results["has_aims_info"] += 1
            if quality["has_redirect"]:
                results["has_redirect"] += 1
            if quality["quality"] == "good":
                results["good_quality"] += 1
            
            print(f"  ✅ Boundary detected: {intent}")
            print(f"  📊 Quality: {quality['quality']}")
            print(f"     - Has context: {'✓' if quality['has_context'] else '✗'}")
            print(f"     - Has AIMS info: {'✓' if quality['has_aims_info'] else '✗'}")
            print(f"     - Has redirect: {'✓' if quality['has_redirect'] else '✗'}")
            
            # Show first 150 chars of answer
            preview = answer[:150] + "..." if len(answer) > 150 else answer
            print(f"  💬 Preview: {preview}")
        else:
            print(f"  ⚠️  Not detected as boundary (intent: {intent})")
        
        print()
        time.sleep(0.3)
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total queries: {results['total']}")
    print(f"Boundary detected: {results['success']}/{results['total']} ({results['success']/results['total']*100:.1f}%)")
    print(f"Good quality: {results['good_quality']}/{results['success']} ({results['good_quality']/results['success']*100:.1f}% of detected)")
    print(f"\nQuality breakdown:")
    print(f"  - Has real-world context: {results['has_context']}/{results['success']} ({results['has_context']/results['success']*100:.1f}%)")
    print(f"  - Has AIMS info: {results['has_aims_info']}/{results['success']} ({results['has_aims_info']/results['success']*100:.1f}%)")
    print(f"  - Has helpful redirect: {results['has_redirect']}/{results['success']} ({results['has_redirect']/results['success']*100:.1f}%)")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
