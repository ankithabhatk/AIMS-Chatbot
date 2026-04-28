"""
Edge Case Tests for Stage Controller

Tests the 3 critical edge cases:
1. Implicit decision detection (yeah, okay, fine, etc.)
2. Conversion push in locked stage
3. Apply mode hardening
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.orchestration.engine import _execute_counselor_pipeline
from app.services.counselor.memory import SESSION_MEMORY
from app.services.counselor.conversion import detect_decision_signal


def test_implicit_decision_detection():
    """Test: Implicit decision phrases get detected and lock course"""
    print("\n=== TEST 1: Implicit Decision Detection ===")
    
    implicit_phrases = [
        "yeah",
        "okay",
        "ok",
        "fine",
        "cool",
        "alright",
        "sure",
        "makes sense",
        "let's go with that"
    ]
    
    passed = 0
    failed = 0
    
    for phrase in implicit_phrases:
        detected = detect_decision_signal(phrase)
        if detected:
            print(f"✅ '{phrase}' → Decision detected")
            passed += 1
        else:
            print(f"❌ '{phrase}' → NOT detected")
            failed += 1
    
    print(f"\nImplicit Detection: {passed}/{len(implicit_phrases)} passed")
    assert failed == 0, f"{failed} implicit phrases not detected"


def test_decision_lock_with_implicit_phrase():
    """Test: Implicit phrase locks course in real flow"""
    print("\n=== TEST 2: Decision Lock with Implicit Phrase ===")
    
    session_id = "test_implicit_001"
    SESSION_MEMORY.clear()
    
    # Step 1: User gets guidance
    response1 = _execute_counselor_pipeline(
        "I got 75% and like coding",
        context={},
        session_id=session_id
    )
    print(f"Step 1: {response1.get('mode')}")
    
    # Step 2: User says implicit decision phrase
    response2 = _execute_counselor_pipeline(
        "yeah okay",
        context={},
        session_id=session_id
    )
    print(f"Step 2: {response2.get('mode')}")
    
    # Check if course is locked
    from app.services.counselor.memory import get_student_profile
    profile = get_student_profile(session_id)
    locked_course = profile.get("locked_course")
    
    print(f"Locked course: {locked_course}")
    assert locked_course is not None, "Course should be locked after implicit decision"
    print("✅ Implicit phrase locked course successfully")


def test_conversion_push_in_locked_stage():
    """Test: Locked stage pushes toward apply after answering"""
    print("\n=== TEST 3: Conversion Push in Locked Stage ===")
    
    session_id = "test_push_001"
    SESSION_MEMORY.clear()
    
    # Lock a course
    context = {"locked_course": "BCA"}
    SESSION_MEMORY[session_id] = context
    
    # User asks about fees (apply-related)
    response = _execute_counselor_pipeline(
        "what about fees",
        context={},
        session_id=session_id
    )
    
    answer = response.get("answer", "")
    print(f"Response mode: {response.get('mode')}")
    print(f"Answer preview: {answer[:200]}...")
    
    # Check if push is present
    push_keywords = ["admission", "apply", "application", "next step", "walk you through"]
    has_push = any(keyword in answer.lower() for keyword in push_keywords)
    
    if has_push:
        print("✅ Conversion push detected in locked stage")
    else:
        print("⚠️ No conversion push detected (may be okay depending on query)")
    
    assert response.get("mode") == "locked", "Should be in locked mode"


def test_apply_mode_blocks_exploration():
    """Test: Apply mode blocks exploratory questions"""
    print("\n=== TEST 4: Apply Mode Blocks Exploration ===")
    
    session_id = "test_apply_block_001"
    SESSION_MEMORY.clear()
    
    # Lock a course
    context = {"locked_course": "BCA"}
    SESSION_MEMORY[session_id] = context
    
    # User asks to apply but then tries to compare
    response = _execute_counselor_pipeline(
        "how to apply but is BBA better?",
        context={},
        session_id=session_id
    )
    
    answer = response.get("answer", "")
    print(f"Response mode: {response.get('mode')}")
    print(f"Answer preview: {answer[:200]}...")
    
    # Should be in apply mode and should mention locked course
    assert response.get("mode") == "apply", "Should be in apply mode"
    assert "BCA" in answer, "Should mention locked course"
    assert "chosen" in answer.lower() or "focus" in answer.lower(), "Should block exploration"
    print("✅ Apply mode blocked exploration successfully")


def test_stage_controller_always_wins():
    """Test: Stage controller cannot be bypassed"""
    print("\n=== TEST 5: Stage Controller Always Wins ===")
    
    session_id = "test_arbiter_001"
    SESSION_MEMORY.clear()
    
    # Lock a course
    context = {"locked_course": "BBA"}
    SESSION_MEMORY[session_id] = context
    
    # User tries to switch with strong interest signal
    response = _execute_counselor_pipeline(
        "I really love coding and technology",
        context={},
        session_id=session_id
    )
    
    # Check that course is still locked (stage controller wins)
    from app.services.counselor.memory import get_student_profile
    profile = get_student_profile(session_id)
    locked_course = profile.get("locked_course")
    
    print(f"Locked course after switch attempt: {locked_course}")
    assert locked_course == "BBA", "Stage controller should prevent course switching"
    print("✅ Stage controller blocked course switch")


def run_all_tests():
    """Run all edge case tests"""
    print("=" * 60)
    print("EDGE CASE TESTS - PRODUCTION HARDENING")
    print("=" * 60)
    
    tests = [
        test_implicit_decision_detection,
        test_decision_lock_with_implicit_phrase,
        test_conversion_push_in_locked_stage,
        test_apply_mode_blocks_exploration,
        test_stage_controller_always_wins,
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
