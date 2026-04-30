"""
Quick test of 10 sample questions from different categories
"""

import requests
import time
from student_questions_100 import STUDENT_QUESTIONS

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str):
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"quick-test-{hash(query)}",
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Sample 2 questions from each category
sample_questions = [
    # Admission
    ("admission", "What documents are required for admission?"),
    ("admission", "What is the eligibility criteria for MBA?"),
    
    # Fees
    ("fees", "What are the fees for BCA?"),
    ("fees", "Are scholarships available for merit students?"),
    
    # Courses
    ("courses", "What courses are offered at AIMS?"),
    ("courses", "What specializations are available in MBA?"),
    
    # Placements
    ("placements", "What is the placement record?"),
    ("placements", "Which companies come for campus recruitment?"),
    
    # Exploratory
    ("exploratory", "I like coding, what should I choose?"),
    ("exploratory", "I'm not sure what to study, can you help?"),
]

print("=" * 80)
print("QUICK SAMPLE TEST - 10 QUESTIONS")
print("=" * 80)

results = {"good": 0, "fallback": 0, "error": 0}

for i, (category, query) in enumerate(sample_questions, 1):
    print(f"\n[{i}/10] Category: {category}")
    print(f"Q: {query}")
    
    response = test_query(query)
    
    if "error" in response:
        print(f"❌ ERROR: {response['error']}")
        results["error"] += 1
    else:
        intent = response.get("intent", "unknown")
        confidence = response.get("confidence", 0.0)
        fallback = response.get("fallback", False)
        answer = response.get("answer", "")
        
        if fallback:
            print(f"⚠️  FALLBACK | Intent: {intent} | Confidence: {confidence:.2f}")
            results["fallback"] += 1
        else:
            print(f"✅ SUCCESS | Intent: {intent} | Confidence: {confidence:.2f}")
            results["good"] += 1
        
        # Show first 150 chars of answer
        preview = answer[:150] + "..." if len(answer) > 150 else answer
        print(f"Answer: {preview}")
    
    time.sleep(0.3)

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)
print(f"Good: {results['good']}/10 ({results['good']/10*100:.0f}%)")
print(f"Fallback: {results['fallback']}/10 ({results['fallback']/10*100:.0f}%)")
print(f"Error: {results['error']}/10")
print("=" * 80)
