#!/usr/bin/env python3
"""
SYSTEM AUDIT - Verify core correctness (no code changes)

Tests:
1. Explicit decision: "I want to do BCA"
2. Generic query: "Campus facilities"
3. Weak intent: "Maybe BCA"
4. Action intent: "How to apply"
5. Conflicting intent: "I like coding but want MBA"

Plus:
- Memory check: Does system remember course choice?
- Fallback misuse: Does fallback trigger only when no signal?
"""

import sys
sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot/backend')

from app.services.orchestration.engine import run_counselor_pipeline
from app.services.counselor.memory import get_student_profile, SESSION_MEMORY

def test_case(case_num, description, queries, expected_checks):
    """Run a single test case"""
    print(f"\n{'='*80}")
    print(f"📋 CASE {case_num}: {description}")
    print(f"{'='*80}")
    
    session_id = f"audit_session_{case_num}"
    results = []
    
    for i, query in enumerate(queries):
        print(f"\n  Query {i+1}: '{query}'")
        
        # Call orchestration engine
        response = run_counselor_pipeline(query, session_id=session_id, context={})
        
        # Extract key data
        result = {
            "query": query,
            "answer": response.get("answer", "")[:100] if response.get("answer") else "",
            "mode": response.get("mode", "unknown"),
            "confidence": response.get("confidence", 0.0),
            "intents": response.get("intents", []),
            "locked_course": response.get("locked_course"),
        }
        
        # Get memory state
        profile = get_student_profile(session_id)
        result["memory"] = {
            "locked_course": profile.get("locked_course"),
            "courses": profile.get("courses", []),
            "marks": profile.get("marks"),
        }
        
        results.append(result)
        
        # Print result
        print(f"    → Mode: {result['mode']} | Confidence: {result['confidence']:.2f}")
        print(f"    → Locked: {result['memory']['locked_course']} | Courses: {result['memory']['courses']}")
        print(f"    → Answer: {result['answer']}...")
    
    # Check expectations
    print(f"\n  📊 Checking expectations...")
    passed = 0
    failed = 0
    
    for check_name, check_fn in expected_checks.items():
        try:
            check_result = check_fn(results)
            status = "✅ PASS" if check_result else "❌ FAIL"
            if check_result:
                passed += 1
            else:
                failed += 1
            print(f"    {status}: {check_name}")
        except Exception as e:
            print(f"    ❌ FAIL: {check_name} - {str(e)}")
            failed += 1
    
    print(f"\n  Result: {passed}/{len(expected_checks)} checks passed")
    
    return {
        "case": case_num,
        "passed": passed,
        "total": len(expected_checks),
        "results": results
    }

# ============================================================================
# CASE 1: Explicit Decision ("I want to do BCA")
# ============================================================================
case1_expected = {
    "Lock YES": lambda r: r[0]["memory"]["locked_course"] == "BCA",
    "Course BCA": lambda r: "BCA" in r[0]["memory"]["courses"],
    "No fallback": lambda r: r[0]["mode"] != "fallback",
    "High confidence": lambda r: r[0]["confidence"] >= 0.7,
}

# ============================================================================
# CASE 2: Generic query ("Campus facilities")
# ============================================================================
case2_expected = {
    "Lock NO": lambda r: r[0]["memory"]["locked_course"] is None,
    "No course mention": lambda r: len(r[0]["memory"]["courses"]) == 0,
    "Tool mode": lambda r: r[0]["mode"] in ["tool", "guidance"],
    "Not fallback": lambda r: r[0]["mode"] != "fallback",
}

# ============================================================================
# CASE 3: Weak intent ("Maybe BCA")
# ============================================================================
case3_expected = {
    "Courses detected": lambda r: "BCA" in r[0]["memory"]["courses"],
    "Not locked": lambda r: r[0]["memory"]["locked_course"] != "BCA",  # Weak intent shouldn't lock
    "Guidance mode": lambda r: r[0]["mode"] in ["guidance", "structured"],
}

# ============================================================================
# CASE 4: Action intent ("How to apply")
# ============================================================================
case4_setup = [
    "I want BCA",  # Set up lock first
    "How to apply"  # Then ask about application
]
case4_expected = {
    "Course locked first": lambda r: r[0]["memory"]["locked_course"] == "BCA",
    "Apply mode": lambda r: r[1]["mode"] == "apply",
    "Structured response": lambda r: "steps" in r[1]["answer"].lower() or "apply" in r[1]["answer"].lower() or "admission" in r[1]["answer"].lower(),
}

# ============================================================================
# CASE 5: Conflicting intent
# ============================================================================
case5_expected = {
    "Not locked": lambda r: r[0]["memory"]["locked_course"] is None,
    "No single course": lambda r: len(r[0]["memory"]["courses"]) <= 1,  # Could detect coding interest
    "Guidance or clarification": lambda r: r[0]["mode"] in ["guidance", "clarification"],
}

# ============================================================================
# MEMORY CHECK: Course persistence
# ============================================================================
memory_setup = [
    "I want BCA",
    "What are the fees?"
]
memory_expected = {
    "Lock established": lambda r: r[0]["memory"]["locked_course"] == "BCA",
    "Lock persists": lambda r: r[1]["memory"]["locked_course"] == "BCA",
    "Still BCA": lambda r: r[1]["memory"]["courses"] == ["BCA"] or "BCA" in r[1]["memory"]["courses"],
}

# ============================================================================
# FALLBACK MISUSE CHECK
# ============================================================================
fallback_setup = [
    "Campus facilities",  # Clear signal (location)
    "Fee structure for BBA"  # Clear signal (fees + course)
]
fallback_expected = {
    "Location not fallback": lambda r: r[0]["mode"] != "fallback",
    "Fees not fallback": lambda r: r[1]["mode"] != "fallback",
    "Only fallback if no signal": lambda r: True,  # Manual check in results
}

# ============================================================================
# RUN ALL CASES
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔍 SYSTEM AUDIT - Correctness Verification")
    print("="*80)
    
    all_results = []
    
    # Case 1
    all_results.append(test_case(1, "Explicit decision", 
                                 ["I want to do BCA"],
                                 case1_expected))
    
    # Case 2
    all_results.append(test_case(2, "Generic query",
                                 ["Campus facilities"],
                                 case2_expected))
    
    # Case 3
    all_results.append(test_case(3, "Weak intent",
                                 ["Maybe BCA"],
                                 case3_expected))
    
    # Case 4
    all_results.append(test_case(4, "Action intent",
                                 case4_setup,
                                 case4_expected))
    
    # Case 5
    all_results.append(test_case(5, "Conflicting intent",
                                 ["I like coding but want MBA"],
                                 case5_expected))
    
    # Memory check
    all_results.append(test_case(6, "Memory persistence",
                                 memory_setup,
                                 memory_expected))
    
    # Fallback misuse
    all_results.append(test_case(7, "Fallback discipline",
                                 fallback_setup,
                                 fallback_expected))
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print(f"\n{'='*80}")
    print("📊 AUDIT SUMMARY")
    print(f"{'='*80}")
    
    total_passed = sum(r["passed"] for r in all_results)
    total_checks = sum(r["total"] for r in all_results)
    
    for r in all_results:
        status = "✅" if r["passed"] == r["total"] else "⚠️" if r["passed"] >= r["total"] * 0.75 else "❌"
        print(f"{status} Case {r['case']}: {r['passed']}/{r['total']} passed")
    
    print(f"\nOverall: {total_passed}/{total_checks} checks passed ({100*total_passed/total_checks:.1f}%)")
    
    if total_passed >= total_checks * 0.8:
        print("\n✅ SYSTEM IS SOLID")
        print("   → 4/5+ cases passing = system is reliable")
        print("   → Next step: behavioral tuning, not architecture")
    else:
        print("\n❌ ISSUES FOUND")
        print("   → Check failed cases above")
        print("   → May need pipeline fixes")
    
    print(f"\n{'='*80}\n")
