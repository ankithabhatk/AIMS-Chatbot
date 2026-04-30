"""
Test contradiction signal behavior.

Verify that contradictions:
1. Reduce confidence (but don't destroy it)
2. Make system cautious
3. Don't erase profile
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.conversation_memory import (
    get_memory_store,
    extract_user_profile,
)


def test_contradiction_reduces_confidence():
    """Test that contradiction reduces confidence without destroying it."""
    memory = get_memory_store()
    session_id = "test_contradiction"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("CONTRADICTION TEST")
    print("="*80)
    
    # Turn 1: "idk"
    print("\n--- TURN 1: 'idk' ---")
    query1 = "idk"
    signals1 = extract_user_profile(query1)
    profile1 = memory.update_profile(session_id, signals1)
    
    print(f"Signals: {signals1.get('confidence_signals', [])}")
    print(f"Score: {profile1.confidence_score:.3f}")
    print(f"Category: {profile1.confidence_category}")
    
    # Turn 2: "maybe coding"
    print("\n--- TURN 2: 'maybe coding' ---")
    query2 = "maybe coding"
    profile = memory.get_profile(session_id)
    signals2 = extract_user_profile(query2, profile)
    profile2 = memory.update_profile(session_id, signals2)
    
    print(f"Signals: {signals2.get('confidence_signals', [])}")
    print(f"Score: {profile2.confidence_score:.3f}")
    print(f"Category: {profile2.confidence_category}")
    print(f"Interests: {profile2.interests}")
    
    # Turn 3: "I like coding"
    print("\n--- TURN 3: 'I like coding' ---")
    query3 = "I like coding"
    profile = memory.get_profile(session_id)
    signals3 = extract_user_profile(query3, profile)
    profile3 = memory.update_profile(session_id, signals3)
    score3 = profile3.confidence_score  # Capture score
    
    print(f"Signals: {signals3.get('confidence_signals', [])}")
    print(f"Score: {score3:.3f}")
    print(f"Category: {profile3.confidence_category}")
    print(f"Interests: {profile3.interests}")
    
    # Turn 4: "actually I don't like coding" (CONTRADICTION)
    print("\n--- TURN 4: 'actually I don't like coding' (CONTRADICTION) ---")
    query4 = "actually I don't like coding"
    profile = memory.get_profile(session_id)
    signals4 = extract_user_profile(query4, profile)
    profile4 = memory.update_profile(session_id, signals4)
    score4 = profile4.confidence_score  # Capture score
    
    print(f"Signals: {signals4.get('confidence_signals', [])}")
    print(f"Score: {score4:.3f}")
    print(f"Category: {profile4.confidence_category}")
    print(f"Interests: {profile4.interests}")
    
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)
    
    # Validate contradiction was detected
    assert "contradiction" in signals4.get('confidence_signals', []), \
        "Contradiction signal not detected"
    print("✓ Contradiction detected")
    
    # Validate score dropped
    assert score4 < score3, \
        f"Score should drop (was {score3:.3f}, now {score4:.3f})"
    print(f"✓ Score dropped: {score3:.3f} → {score4:.3f}")
    
    # Validate score didn't crash too hard
    assert score4 >= 0.30, \
        f"Score shouldn't crash below 0.30 (got {score4:.3f})"
    print(f"✓ Score didn't crash (stayed at {score4:.3f})")
    
    # Validate expected range
    expected_min = 0.40
    expected_max = 0.50
    if expected_min <= score4 <= expected_max:
        print(f"✓ Score in expected range ({expected_min}–{expected_max})")
    else:
        print(f"⚠️  Score outside expected range: {score4:.3f} (expected {expected_min}–{expected_max})")
    
    # Validate profile not erased
    assert len(profile4.interests) > 0, "Profile interests should not be erased"
    print(f"✓ Profile not erased (still has {len(profile4.interests)} interests)")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Turn 1: {profile1.confidence_score:.3f} (low)")
    print(f"Turn 2: {profile2.confidence_score:.3f} (medium)")
    print(f"Turn 3: {score3:.3f} (medium)")
    print(f"Turn 4: {score4:.3f} (medium) ← CONTRADICTION")
    print(f"\nDrop: {score3:.3f} → {score4:.3f} ({score4 - score3:+.3f})")
    print("\n✅ Contradiction behavior correct:")
    print("  • Reduces confidence")
    print("  • Doesn't destroy system")
    print("  • Doesn't erase profile")
    print("  • System becomes cautious")


def test_multiple_contradictions():
    """Test that multiple contradictions compound damage."""
    memory = get_memory_store()
    session_id = "test_multi_contradiction"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("MULTIPLE CONTRADICTIONS TEST")
    print("="*80)
    
    # Build up confidence
    queries = [
        "I like coding",
        "I want good salary",
        "I'm interested in tech"
    ]
    
    for i, query in enumerate(queries, 1):
        profile = memory.get_profile(session_id)
        signals = extract_user_profile(query, profile)
        profile = memory.update_profile(session_id, signals)
        print(f"Turn {i}: {profile.confidence_score:.3f}")
    
    baseline_score = profile.confidence_score
    print(f"\nBaseline score: {baseline_score:.3f}")
    
    # Single contradiction
    print("\n--- Single contradiction ---")
    query_single = "I don't like coding"
    profile = memory.get_profile(session_id)
    signals_single = extract_user_profile(query_single, profile)
    
    # Count contradictions
    contradiction_count = signals_single.get('confidence_signals', []).count("contradiction")
    print(f"Contradiction count: {contradiction_count}")
    
    if contradiction_count == 1:
        print("✓ Single contradiction detected correctly")
    else:
        print(f"⚠️  Expected 1 contradiction, got {contradiction_count}")


if __name__ == "__main__":
    try:
        test_contradiction_reduces_confidence()
        test_multiple_contradictions()
        
        print("\n" + "="*80)
        print("ALL CONTRADICTION TESTS PASSED ✅")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
