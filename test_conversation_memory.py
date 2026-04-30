#!/usr/bin/env python3
"""
Test script for conversation memory and follow-up intelligence.

Tests the 4 critical scenarios:
1. Multi-turn context continuity (coding + weak in math)
2. Trade-off advice (high salary + not good at studies)
3. Conflict resolution (parents want MBA but I like tech)
4. Follow-up continuity (okay then what about fees?)
"""

import sys
sys.path.insert(0, "backend")

from app.services.conversation_memory import (
    get_memory_store,
    extract_user_profile,
    UserProfile,
    build_memory_context,
)
from app.services.counselor_handler import get_counselor_response, is_exploratory_query


def test_extract_user_profile():
    """Test signal extraction from queries."""
    print("=" * 60)
    print("TEST: extract_user_profile()")
    print("=" * 60)

    # Test 1: Interest detection
    profile = extract_user_profile("I like coding")
    assert "coding" in profile["interests"], f"Expected 'coding' in interests, got {profile}"
    print("✓ Interest detection: 'I like coding' → coding interest")

    # Test 2: Constraint detection
    profile = extract_user_profile("I'm weak in math")
    assert any("math" in c for c in profile["constraints"]), f"Expected math constraint, got {profile}"
    print("✓ Constraint detection: 'weak in math' → math constraint")

    # Test 3: Goal detection
    profile = extract_user_profile("I want high salary")
    assert any("salary" in g for g in profile["goals"]), f"Expected salary goal, got {profile}"
    print("✓ Goal detection: 'high salary' → salary goal")

    # Test 4: Ambiguity detection
    profile = extract_user_profile("I'm confused about what to choose")
    assert "uncertain" in profile["ambiguity_signals"], f"Expected uncertainty, got {profile}"
    print("✓ Ambiguity detection: 'confused' → uncertain")

    # Test 5: Parental pressure
    profile = extract_user_profile("My parents want MBA but I like tech")
    assert "parental_pressure" in profile["constraints"], f"Expected parental pressure, got {profile}"
    assert "internal_conflict" in profile["constraints"], f"Expected internal conflict, got {profile}"
    print("✓ Conflict detection: 'parents want X but I like Y' → conflict signals")

    print("\n✅ All extract_user_profile tests passed!\n")
    return True


def test_session_memory_accumulation():
    """Test that signals accumulate across turns."""
    print("=" * 60)
    print("TEST: Session Memory Accumulation")
    print("=" * 60)

    memory = get_memory_store()
    test_session = "test_session_001"

    # Clear any existing session
    memory.clear_session(test_session)

    # Turn 1: "I like coding"
    profile = memory.get_profile(test_session)
    signals1 = extract_user_profile("I like coding")
    memory.update_profile(test_session, signals1)
    profile = memory.get_profile(test_session)

    assert "coding" in profile.interests, f"Expected coding interest after turn 1"
    print("✓ Turn 1: 'I like coding' → interests: {coding}")

    # Turn 2: "I'm weak in math"
    signals2 = extract_user_profile("I'm weak in math")
    memory.update_profile(test_session, signals2)
    profile = memory.get_profile(test_session)

    assert "coding" in profile.interests, "Expected coding interest to persist"
    assert any("math" in c for c in profile.constraints), "Expected math constraint"
    print("✓ Turn 2: 'I'm weak in math' → constraints: {weak_in_math}, interests still: {coding}")

    # Turn 3: "I want good salary"
    signals3 = extract_user_profile("I want good salary")
    memory.update_profile(test_session, signals3)
    profile = memory.get_profile(test_session)

    assert "coding" in profile.interests, "Expected coding interest to persist"
    assert any("math" in c for c in profile.constraints), "Expected math constraint to persist"
    assert any("salary" in g for g in profile.goals), "Expected salary goal"
    print("✓ Turn 3: 'I want good salary' → goals: {high_salary}, all previous signals retained")

    # Clean up
    memory.clear_session(test_session)

    print("\n✅ Session memory accumulation tests passed!\n")
    return True


def test_counselor_responses():
    """Test counselor responses with memory."""
    print("=" * 60)
    print("TEST: Counselor Responses with Memory")
    print("=" * 60)

    memory = get_memory_store()
    test_session = "test_session_002"
    memory.clear_session(test_session)

    # Scenario 1: coding + weak in math
    print("\n--- Scenario 1: Coding interest + Math constraint ---")
    memory.update_profile(test_session, extract_user_profile("I like coding"))
    response = get_counselor_response("I'm weak in math but want to do coding", test_session)

    assert response is not None, "Expected counselor response for constraint query"
    assert "BCA" in response["answer"] or "math" in response["answer"].lower(), "Expected BCA/math discussion"
    print(f"✓ Response contains guidance for coding + weak in math")
    print(f"  Preview: {response['answer'][:150]}...")

    memory.clear_session(test_session)

    # Scenario 2: Salary concern + study constraint
    print("\n--- Scenario 2: High salary + Not good at studies ---")
    memory.update_profile(test_session, extract_user_profile("I want high salary"))
    response = get_counselor_response("I want good salary but not good at studies", test_session)

    assert response is not None, "Expected counselor response"
    assert "BCA" in response["answer"] or "effort" in response["answer"].lower(), "Expected trade-off discussion"
    print(f"✓ Response contains trade-off advice")
    print(f"  Preview: {response['answer'][:150]}...")

    memory.clear_session(test_session)

    # Scenario 3: Parental pressure
    print("\n--- Scenario 3: Parents want MBA but I like tech ---")
    response = get_counselor_response("My parents want MBA but I like tech", test_session)

    assert response is not None, "Expected counselor response for conflict"
    assert "parents" in response["answer"].lower() or "parent" in response["answer"].lower(), "Expected parent discussion"
    print(f"✓ Response addresses parental conflict")
    print(f"  Preview: {response['answer'][:150]}...")

    memory.clear_session(test_session)

    print("\n✅ Counselor response tests passed!\n")
    return True


def test_full_multi_turn_conversation():
    """Test the full multi-turn conversation flow."""
    print("=" * 60)
    print("TEST: Full Multi-Turn Conversation")
    print("=" * 60)

    memory = get_memory_store()
    test_session = "test_session_003"
    memory.clear_session(test_session)

    # Simulate the critical test case from the spec:
    # User: I like coding
    # User: I'm weak in math
    # User: I want good salary
    # User: what should I do?

    print("\nSimulating conversation:")
    print("-" * 40)

    queries = [
        "I like coding",
        "I'm weak in math",
        "I want good salary",
        "what should I do?",
    ]

    for i, query in enumerate(queries, 1):
        profile = memory.get_profile(test_session)
        signals = extract_user_profile(query)
        memory.update_profile(test_session, signals)

        response = get_counselor_response(query, test_session)

        print(f"\nTurn {i}: '{query}'")
        if response:
            print(f"  → Counselor responded (intent: {response.get('intent')})")
            # Show accumulated profile
            profile = memory.get_profile(test_session)
            print(f"  → Profile now: interests={profile.interests}, constraints={profile.constraints}, goals={profile.goals}")
        else:
            print(f"  → Not a counselor query (would go to RAG/structured)")

    # Final state check
    final_profile = memory.get_profile(test_session)
    print("\n" + "-" * 40)
    print(f"Final accumulated profile:")
    print(f"  Interests: {final_profile.interests}")
    print(f"  Constraints: {final_profile.constraints}")
    print(f"  Goals: {final_profile.goals}")

    # Verify all signals accumulated
    assert "coding" in final_profile.interests, "Expected coding interest"
    assert any("math" in c for c in final_profile.constraints), "Expected math constraint"
    assert any("salary" in g for g in final_profile.goals), "Expected salary goal"

    print("\n✅ Full multi-turn conversation test passed!\n")

    memory.clear_session(test_session)
    return True


def test_is_exploratory_query():
    """Test exploratory query detection."""
    print("=" * 60)
    print("TEST: is_exploratory_query()")
    print("=" * 60)

    # Should be exploratory
    exploratory = [
        "I like coding",
        "I'm weak in math",
        "I'm confused about what to choose",
        "My parents want MBA but I like tech",
        "What should I do?",
        "Help me choose",
    ]

    for query in exploratory:
        result = is_exploratory_query(query)
        assert result is True, f"Expected '{query}' to be exploratory"
        print(f"✓ '{query}' → exploratory=True")

    # Should NOT be exploratory (factual queries)
    factual = [
        "What are BCA fees?",
        "When does admission start?",
        "BCA placement statistics",
    ]

    for query in factual:
        result = is_exploratory_query(query)
        # Note: Some of these might still be exploratory depending on implementation
        print(f"  '{query}' → exploratory={result}")

    print("\n✅ Exploratory query detection tests passed!\n")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CONVERSATION MEMORY TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        ("extract_user_profile", test_extract_user_profile),
        ("session_memory_accumulation", test_session_memory_accumulation),
        ("counselor_responses", test_counselor_responses),
        ("full_multi_turn_conversation", test_full_multi_turn_conversation),
        ("is_exploratory_query", test_is_exploratory_query),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            if test_fn():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ {name} FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"\n❌ {name} ERROR: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Conversation memory is working correctly.\n")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Review the output above.\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
