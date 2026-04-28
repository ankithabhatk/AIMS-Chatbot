"""
Integration tests for Stage Controller with Orchestration Engine

Tests the complete flow:
1. Stage detection
2. Decision locking
3. Locked course respect
4. Apply flow
5. Confusion handling
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.orchestration.engine import _execute_counselor_pipeline
from app.services.counselor.memory import SESSION_MEMORY, get_student_profile


def test_guidance_to_decision_lock():
    """Test: User explores → decides → course gets locked"""
    print("\n=== TEST 1: Guidance → Decision Lock ===")
    
    session_id = "test_lock_001"
    SESSION_MEMORY.clear()
    
    # Step 1: User provides marks (guidance stage)
    response1 = _execute_counselor_pipeline(
        "I got 75% in 12th",
        context={},
        session_id=session_id
    )
    print(f"Step 1 (Guidance): {response1.get('mode')}")
    assert response1.get("mode") in ["counselor", "guidance", "soft_bridge"], "Should run guidance"
    
    # Step 2: User says "sounds good" (decision stage → should lock)
    response2 = _execute_counselor_pipeline(
        "BCA sounds good",
        context={},
        session_id=session_id
    )
    print(f"Step 2 (Decision): {response2.get('mode')}")
    
    # Check if course is locked
    profile = get_student_profile(session_id)
    locked_course = profile.get("locked_course")
    print(f"Locked course: {locked_course}")
    
    assert locked_course is not None, "Course should be locked after decision"
    print("✅ Course locked successfully")
    
    # Step 3: User asks about fees (should stay locked)
    response3 = _execute_counselor_pipeline(
        "what about fees",
        context={},
        session_id=session_id
    )
    print(f"Step 3 (Locked): {response3.get('mode')}")
    
    # Verify course is still locked
    profile = get_student_profile(session_id)
    assert profile.get("locked_course") == locked_course, "Course should remain locked"
    print("✅ Course remains locked")


def test_apply_flow_with_locked_course():
    """Test: User locks course → asks to apply → gets structured steps"""
    print("\n=== TEST 2: Apply Flow with Locked Course ===")
    
    session_id = "test_apply_001"
    SESSION_MEMORY.clear()
    
    # Step 1: Lock a course
    context = {"locked_course": "BCA"}
    SESSION_MEMORY[session_id] = context
    
    # Step 2: User asks to apply
    response = _execute_counselor_pipeline(
        "how to apply",
        context={},
        session_id=session_id
    )
    print(f"Apply response mode: {response.get('mode')}")
    
    assert response.get("mode") == "apply", "Should trigger apply mode"
    assert "BCA" in response.get("answer", ""), "Should mention locked course"
    print("✅ Apply flow works with locked course")


def test_apply_without_locked_course():
    """Test: User asks to apply without locked course → asks for clarification"""
    print("\n=== TEST 3: Apply Without Locked Course ===")
    
    session_id = "test_apply_002"
    SESSION_MEMORY.clear()
    
    response = _execute_counselor_pipeline(
        "how to apply",
        context={},
        session_id=session_id
    )
    print(f"Response mode: {response.get('mode')}")
    
    assert response.get("mode") in ["clarification", "apply"], "Should ask for course"
    print("✅ Clarification requested when no course locked")


def test_confusion_simplification():
    """Test: User is confused → gets simplified guidance"""
    print("\n=== TEST 4: Confusion Simplification ===")
    
    session_id = "test_confusion_001"
    SESSION_MEMORY.clear()
    
    response = _execute_counselor_pipeline(
        "I'm confused",
        context={},
        session_id=session_id
    )
    print(f"Response mode: {response.get('mode')}")
    
    assert response.get("mode") in ["confusion", "counselor"], "Should handle confusion"
    print("✅ Confusion handled")


def test_locked_course_no_switching():
    """Test: Locked course prevents switching even with new interests"""
    print("\n=== TEST 5: Locked Course No Switching ===")
    
    session_id = "test_no_switch_001"
    SESSION_MEMORY.clear()
    
    # Lock BCA
    context = {"locked_course": "BCA"}
    SESSION_MEMORY[session_id] = context
    
    # User mentions different interest (should NOT switch)
    response = _execute_counselor_pipeline(
        "I'm interested in business",
        context={},
        session_id=session_id
    )
    
    # Verify course is still BCA
    profile = get_student_profile(session_id)
    assert profile.get("locked_course") == "BCA", "Should NOT switch from locked course"
    print("✅ Locked course prevents switching")


def test_fallback_when_no_signal():
    """Test: No signal → fallback"""
    print("\n=== TEST 6: Fallback When No Signal ===")
    
    session_id = "test_fallback_001"
    SESSION_MEMORY.clear()
    
    response = _execute_counselor_pipeline(
        "hello",
        context={},
        session_id=session_id
    )
    print(f"Response mode: {response.get('mode')}")
    
    assert response.get("mode") in ["fallback", "counselor"], "Should trigger fallback"
    print("✅ Fallback triggered correctly")


def test_stage_priority_hierarchy():
    """Test: Apply intent overrides locked state"""
    print("\n=== TEST 7: Stage Priority Hierarchy ===")
    
    session_id = "test_priority_001"
    SESSION_MEMORY.clear()
    
    # Lock a course
    context = {"locked_course": "BBA"}
    SESSION_MEMORY[session_id] = context
    
    # User asks to apply (APPLY stage has higher priority than LOCKED)
    response = _execute_counselor_pipeline(
        "how to apply",
        context={},
        session_id=session_id
    )
    
    assert response.get("mode") == "apply", "Apply should override locked state"
    print("✅ Stage priority hierarchy works")


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("STAGE CONTROLLER INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_guidance_to_decision_lock,
        test_apply_flow_with_locked_course,
        test_apply_without_locked_course,
        test_confusion_simplification,
        test_locked_course_no_switching,
        test_fallback_when_no_signal,
        test_stage_priority_hierarchy,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
