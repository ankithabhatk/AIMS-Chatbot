"""
Test boundary handler for out-of-scope queries.
"""

import requests

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str):
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"boundary-test-{hash(query)}",
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Out-of-scope test cases
test_cases = [
    # External exams
    {
        "query": "Do I need JEE for BCA?",
        "category": "external_exam",
        "should_contain": ["AIMS", "do NOT require", "10+2 marks"],
    },
    {
        "query": "What is the NEET cutoff for MBBS?",
        "category": "external_exam",
        "should_contain": ["AIMS", "admission"],
    },
    {
        "query": "I scored 85% in boards, can I get admission?",
        "category": "in_scope",  # This should NOT trigger boundary
        "should_contain": ["admission", "eligibility"],
    },
    {
        "query": "What are the minimum required scores for MBA?",
        "category": "in_scope",  # This should NOT trigger boundary
        "should_contain": ["MBA", "50%"],
    },
    {
        "query": "Does the college require SAT or ACT?",
        "category": "external_exam",
        "should_contain": ["AIMS", "do NOT require"],
    },
    {
        "query": "AIMS vs Christ University which is better?",
        "category": "comparative",
        "should_contain": ["AIMS", "can't make comparisons"],
    },
    {
        "query": "What is the JEE Main cutoff for IIT?",
        "category": "external_cutoff",
        "should_contain": ["AIMS", "admission criteria"],
    },
    {
        "query": "Compare AIMS with other colleges in Bangalore",
        "category": "comparative",
        "should_contain": ["AIMS", "can't make comparisons"],
    },
]

print("=" * 80)
print("BOUNDARY HANDLER TEST")
print("=" * 80)

results = {"correct": 0, "incorrect": 0, "error": 0}

for i, test in enumerate(test_cases, 1):
    query = test["query"]
    category = test["category"]
    should_contain = test["should_contain"]
    
    print(f"\n[{i}/{len(test_cases)}] Category: {category}")
    print(f"Q: {query}")
    
    response = test_query(query)
    
    if "error" in response:
        print(f"❌ ERROR: {response['error']}")
        results["error"] += 1
        continue
    
    answer = response.get("answer", "").lower()
    intent = response.get("intent", "unknown")
    
    # Check if response contains expected keywords
    missing = []
    for keyword in should_contain:
        if keyword.lower() not in answer:
            missing.append(keyword)
    
    # Determine if boundary was correctly triggered
    is_boundary = "out_of_scope" in intent or response.get("meta", {}).get("boundary_handler", False) == True
    should_be_boundary = category != "in_scope"
    
    if missing:
        print(f"⚠️  PARTIAL | Intent: {intent} | Missing keywords: {missing}")
        results["incorrect"] += 1
    elif is_boundary == should_be_boundary:
        print(f"✅ CORRECT | Intent: {intent} | Boundary: {is_boundary}")
        results["correct"] += 1
    else:
        print(f"❌ WRONG ROUTING | Intent: {intent} | Expected boundary: {should_be_boundary}, Got: {is_boundary}")
        results["incorrect"] += 1
    
    # Show answer preview
    preview = answer[:150] + "..." if len(answer) > 150 else answer
    print(f"Answer: {preview}")

print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)
print(f"Correct: {results['correct']}/{len(test_cases)} ({results['correct']/len(test_cases)*100:.0f}%)")
print(f"Incorrect: {results['incorrect']}/{len(test_cases)}")
print(f"Error: {results['error']}/{len(test_cases)}")
print("=" * 80)

if results['correct'] == len(test_cases):
    print("✅ All boundary tests passed!")
else:
    print("⚠️  Some tests failed - review boundary detection logic")
