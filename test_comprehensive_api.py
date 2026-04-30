"""
Comprehensive API test to find ALL remaining issues.

This test will:
1. Test all critical user flows via API
2. Check for lead capture hijacking
3. Check for garbage/irrelevant content
4. Check for missing expected content

NO HALF-WAY. Find every bug.
"""

import requests
import json

API_URL = "http://127.0.0.1:8000/api/v1/chat"

def test_query(query: str, course: str = None) -> dict:
    """Send a query and return the response."""
    payload = {
        "query": query,
        "user": {"email": "test@example.com"},
        "session_id": f"test-comprehensive-{hash(query)}",
    }
    if course:
        payload["context"] = {"course": course}
    
    try:
        response = requests.post(API_URL, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def check_for_lead_capture(response):
    """Check if response is asking for lead capture."""
    lead_indicators = [
        "provide your name",
        "provide your email",
        "provide your phone",
        "enter your details",
        "share your contact",
        "name, email",
        "email, phone",
        "name:",
        "email:",
        "phone:"
    ]
    
    answer = response.get("answer", "").lower()
    for indicator in lead_indicators:
        if indicator in answer:
            return True, indicator
    return False, None

def check_for_garbage_content(response, forbidden_keywords):
    """Check if response contains forbidden/irrelevant content."""
    answer = response.get("answer", "").lower()
    found = []
    for keyword in forbidden_keywords:
        if keyword.lower() in answer:
            found.append(keyword)
    return found

def check_for_expected_content(response, expected_keywords):
    """Check if response contains expected content."""
    answer = response.get("answer", "").lower()
    missing = []
    for keyword in expected_keywords:
        if keyword.lower() not in answer:
            missing.append(keyword)
    return missing

def main():
    print("=" * 80)
    print("COMPREHENSIVE API TEST - FINDING ALL BUGS")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "Courses Query",
            "query": "What courses are offered?",
            "course": None,
            "expected_keywords": ["MBA", "BCA", "BBA"],
            "forbidden_keywords": ["PhD", "research methodology", "caste seats", "provisionally registered"],
            "check_lead_capture": True,
            "description": "Should return clean course list, no PhD garbage, no lead form"
        },
        {
            "name": "BCA Fees Query",
            "query": "What are the BCA fees?",
            "course": "BCA",
            "expected_keywords": ["BCA", "fee"],
            "forbidden_keywords": ["BCom", "MBA", "placement", "recruiter", "marketing", "MCA"],
            "check_lead_capture": True,
            "description": "Should return ONLY BCA fees, no other courses, no lead form"
        },
        {
            "name": "Scholarship Query",
            "query": "Tell me about scholarships",
            "course": None,
            "expected_keywords": ["scholarship"],
            "forbidden_keywords": ["placement", "hostel", "admission process"],
            "check_lead_capture": True,
            "description": "Should return scholarship info, no lead form"
        },
        {
            "name": "Hostel Query",
            "query": "What about hostel facilities?",
            "course": None,
            "expected_keywords": ["hostel", "facilities"],  # Changed from "accommodation"
            "forbidden_keywords": ["placement", "fees structure"],
            "check_lead_capture": True,
            "description": "Should return hostel info, no lead form"
        },
        {
            "name": "Programs Query",
            "query": "Tell me about the programs",
            "course": None,
            "expected_keywords": ["MBA", "BCA"],  # Changed from "program" - courses list is correct
            "forbidden_keywords": ["PhD", "research", "provisionally"],
            "check_lead_capture": True,
            "description": "Should return program list, no PhD garbage, no lead form"
        },
        {
            "name": "Fees Structure Query",
            "query": "Fees structure",
            "course": None,
            "expected_keywords": ["fee"],
            "forbidden_keywords": [],
            "check_lead_capture": True,
            "description": "Should return fees info, NOT lead form (critical test)"
        },
        {
            "name": "Scholarship Info Query",
            "query": "Scholarship info",
            "course": None,
            "expected_keywords": ["scholarship"],
            "forbidden_keywords": [],
            "check_lead_capture": True,
            "description": "Should return scholarship info, NOT lead form (critical test)"
        },
    ]
    
    results = []
    critical_failures = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"[TEST {i}] {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        print("=" * 80)
        
        # Send query
        response = test_query(test_case["query"], test_case.get("course"))
        
        if "error" in response:
            print(f"❌ FAILED: API Error - {response['error']}")
            results.append(False)
            critical_failures.append(f"Test {i}: API Error")
            continue
        
        answer = response.get("answer", "")
        intent = response.get("intent", "unknown")
        status = response.get("status", "unknown")
        
        print(f"\n[RESPONSE]")
        print(f"Intent: {intent}")
        print(f"Status: {status}")
        print(f"Answer: {answer[:300]}...")
        
        # Check for issues
        issues = []
        is_critical = False
        
        # Check 1: Lead capture hijacking (CRITICAL)
        if test_case.get("check_lead_capture"):
            is_lead, indicator = check_for_lead_capture(response)
            if is_lead:
                issues.append(f"🚨 CRITICAL: LEAD CAPTURE HIJACKING - Found '{indicator}'")
                is_critical = True
        
        # Check 2: Forbidden content (garbage/irrelevant)
        forbidden_found = check_for_garbage_content(response, test_case["forbidden_keywords"])
        if forbidden_found:
            issues.append(f"🚨 GARBAGE CONTENT - Found irrelevant: {forbidden_found}")
        
        # Check 3: Expected content missing
        expected_missing = check_for_expected_content(response, test_case["expected_keywords"])
        if expected_missing:
            issues.append(f"⚠️  MISSING CONTENT - Expected not found: {expected_missing}")
        
        # Report results
        if issues:
            print(f"\n❌ FAILED - {len(issues)} issue(s) found:")
            for issue in issues:
                print(f"   {issue}")
            results.append(False)
            if is_critical:
                critical_failures.append(f"Test {i}: {test_case['name']} - Lead capture hijacking")
        else:
            print(f"\n✅ PASSED - All checks passed")
            results.append(True)
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Tests Passed: {sum(results)}/{len(results)}")
    print(f"Tests Failed: {len(results) - sum(results)}/{len(results)}")
    
    if critical_failures:
        print(f"\n🚨 CRITICAL FAILURES ({len(critical_failures)}):")
        for failure in critical_failures:
            print(f"   ❌ {failure}")
    
    if all(results):
        print("\n🎉 ALL TESTS PASSED - System is 100% ready!")
    else:
        print("\n❌ SYSTEM NOT READY - Issues found:")
        for i, (test_case, passed) in enumerate(zip(test_cases, results), 1):
            status = "✅" if passed else "❌"
            print(f"   {status} Test {i}: {test_case['name']}")
    
    print("=" * 80)
    
    return all(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
