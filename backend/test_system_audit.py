"""
System Audit - Correctness Verification
No changes. Just testing.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_case(case_num, query, expected):
    """Test a single case and report pass/fail"""
    print(f"\n{'='*60}")
    print(f"CASE {case_num}: {query}")
    print(f"{'='*60}")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"query": query, "session_id": f"audit_case_{case_num}"}
    )
    
    result = response.json()
    answer = result.get("answer", "")
    mode = result.get("mode", "")
    
    print(f"\nResponse mode: {mode}")
    print(f"Answer preview: {answer[:200]}...")
    
    # Check expectations
    checks = {}
    for key, value in expected.items():
        if key == "lock":
            # Check if course is locked (look for "locked" in context or specific phrases)
            locked = "locked" in answer.lower() or "chosen" in answer.lower()
            checks[key] = "PASS" if locked == value else "FAIL"
        elif key == "course":
            # Check if specific course mentioned
            has_course = value.upper() in answer.upper() if value else True
            checks[key] = "PASS" if has_course else "FAIL"
        elif key == "no_fallback":
            # Check fallback didn't trigger
            is_fallback = "what would you like to explore" in answer.lower() or "you can ask me about" in answer.lower()
            checks[key] = "PASS" if not is_fallback else "FAIL"
        elif key == "stage":
            checks[key] = "PASS" if mode == value else "FAIL"
        elif key == "no_lock":
            locked = "locked" in answer.lower() or "chosen" in answer.lower()
            checks[key] = "PASS" if not locked else "FAIL"
        elif key == "no_course_mention":
            # Check no specific course mentioned (MCA, BCA, etc)
            courses = ["MCA", "BCA", "BBA", "MBA", "B.COM", "M.COM"]
            has_course = any(course in answer.upper() for course in courses)
            checks[key] = "PASS" if not has_course else "FAIL"
        elif key == "neutral":
            # Check for neutral guidance (not forced)
            is_neutral = mode in ["guidance", "structured"] and "locked" not in answer.lower()
            checks[key] = "PASS" if is_neutral else "FAIL"
    
    print(f"\nChecks:")
    for check, status in checks.items():
        print(f"  {check}: {status}")
    
    overall = "PASS" if all(s == "PASS" for s in checks.values()) else "FAIL"
    print(f"\nOverall: {overall}")
    
    return overall, answer, mode

def test_memory():
    """Test memory persistence"""
    print(f"\n{'='*60}")
    print(f"MEMORY TEST")
    print(f"{'='*60}")
    
    session_id = "audit_memory_test"
    
    # First query - lock BCA
    print("\nQuery 1: I want BCA")
    r1 = requests.post(f"{BASE_URL}/chat", json={"query": "I want BCA", "session_id": session_id})
    answer1 = r1.json().get("answer", "")
    print(f"Response: {answer1[:150]}...")
    
    # Second query - ask about fees
    print("\nQuery 2: fees?")
    r2 = requests.post(f"{BASE_URL}/chat", json={"query": "fees?", "session_id": session_id})
    answer2 = r2.json().get("answer", "")
    print(f"Response: {answer2[:150]}...")
    
    # Check if BCA is still mentioned
    has_bca = "BCA" in answer2.upper()
    no_switch = "MCA" not in answer2.upper() and "MBA" not in answer2.upper()
    
    result = "PASS" if has_bca and no_switch else "FAIL"
    print(f"\nBCA mentioned: {has_bca}")
    print(f"No course switch: {no_switch}")
    print(f"Memory: {result}")
    
    return result

def main():
    print("="*60)
    print("SYSTEM AUDIT - CORRECTNESS VERIFICATION")
    print("="*60)
    
    results = {}
    
    # Case 1: Explicit decision
    results["Case 1"], _, _ = test_case(
        1,
        "I want to do BCA",
        {"lock": True, "course": "BCA", "no_fallback": True}
    )
    
    # Case 2: Generic query (no course)
    results["Case 2"], _, _ = test_case(
        2,
        "Campus facilities",
        {"no_lock": True, "no_course_mention": True, "neutral": True}
    )
    
    # Case 3: Weak intent
    results["Case 3"], _, _ = test_case(
        3,
        "Maybe BCA",
        {"lock": True, "course": "BCA"}  # Acceptable for now
    )
    
    # Case 4: Action intent
    results["Case 4"], _, _ = test_case(
        4,
        "How to apply",
        {"stage": "apply"}
    )
    
    # Case 5: Conflicting intent
    results["Case 5"], _, _ = test_case(
        5,
        "I like coding but want MBA",
        {"no_lock": True}  # Should ask clarification
    )
    
    # Memory test
    results["Memory"] = test_memory()
    
    # Summary
    print(f"\n{'='*60}")
    print("AUDIT RESULT")
    print(f"{'='*60}")
    for case, result in results.items():
        print(f"{case}: {result}")
    
    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    print(f"\nScore: {passed}/{total}")

if __name__ == "__main__":
    main()
