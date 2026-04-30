"""
Test to verify RAG retrieval failure is fixed.

BEFORE FIX:
- User asks "courses offered" → Bot returns PhD garbage ❌
- User asks "BCA fees" → Bot returns placements + BCom + marketing ❌
- User asks "scholarship" → Bot returns unrelated content ❌

AFTER FIX:
- User asks "courses offered" → Bot returns clean course list ✅
- User asks "BCA fees" → Bot returns ONLY BCA fees ✅
- User asks "scholarship" → Bot returns scholarship info ✅

Root cause: RAG retrieval was pulling wrong chunks because structured
knowledge override was not being called in the main chat endpoint.
"""

import requests
import json

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str, course: str = None) -> dict:
    """Send a query and return the response."""
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"test-rag-fix-{hash(query)}",
    }
    if course:
        payload["context"] = {"course": course}
    
    response = requests.post(API_URL, json=payload)
    return response.json()

def main():
    print("=" * 80)
    print("TESTING: RAG Retrieval Failure Fix")
    print("=" * 80)
    
    test_cases = [
        {
            "query": "What courses are offered?",
            "course": None,
            "expected_keywords": ["MBA", "BCA", "BBA", "MCA"],
            "forbidden_keywords": ["PhD", "research methodology", "caste seats"],
            "description": "Courses query should return course list, not PhD garbage"
        },
        {
            "query": "Tell me about the programs",
            "course": None,
            "expected_keywords": ["MBA", "BCA", "BBA"],
            "forbidden_keywords": ["PhD", "research"],
            "description": "Programs query should return course list"
        },
        {
            "query": "What are the BCA fees?",
            "course": "BCA",
            "expected_keywords": ["BCA", "₹", "fee"],
            "forbidden_keywords": ["BCom", "placement", "marketing", "MBA"],
            "description": "BCA fees query should return ONLY BCA fees"
        },
        {
            "query": "Tell me about scholarships",
            "course": None,
            "expected_keywords": ["scholarship", "merit", "financial"],
            "forbidden_keywords": ["placement", "hostel", "admission"],
            "description": "Scholarship query should return scholarship info"
        },
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        course = test_case["course"]
        expected = test_case["expected_keywords"]
        forbidden = test_case["forbidden_keywords"]
        description = test_case["description"]
        
        print(f"\n[Test {i}] {description}")
        print(f"Query: {query}")
        
        response = test_query(query, course)
        answer = response.get("answer", "").lower()
        intent = response.get("intent", "unknown")
        
        # Check for expected keywords
        expected_found = [kw for kw in expected if kw.lower() in answer]
        expected_missing = [kw for kw in expected if kw.lower() not in answer]
        
        # Check for forbidden keywords
        forbidden_found = [kw for kw in forbidden if kw.lower() in answer]
        
        # Determine pass/fail
        passed = len(expected_found) > 0 and len(forbidden_found) == 0
        
        if passed:
            print(f"✅ PASSED")
            print(f"   Intent: {intent}")
            print(f"   Expected keywords found: {expected_found}")
            print(f"   Answer preview: {answer[:150]}...")
            results.append(True)
        else:
            print(f"❌ FAILED")
            print(f"   Intent: {intent}")
            if expected_missing:
                print(f"   Missing expected keywords: {expected_missing}")
            if forbidden_found:
                print(f"   Found forbidden keywords: {forbidden_found}")
            print(f"   Answer preview: {answer[:150]}...")
            results.append(False)
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 80)
    
    if all(results):
        print("✅ RAG retrieval failure is FIXED!")
        print("Structured knowledge override is working correctly.")
    else:
        print("❌ Some tests failed. RAG may still be returning wrong chunks.")
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    exit(main())
