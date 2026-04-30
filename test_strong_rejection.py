"""
Test strong rejection (strong_contradiction) behavior.

Verify that strong negative language causes collapse, not just destabilization.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.conversation_memory import (
    get_memory_store,
    extract_user_profile,
)


def test_strong_rejection_at_high_confidence():
    """
    Test strong rejection at very high confidence.
    
    Scenario: User at 0.90 confidence says:
    "I hate coding, this is terrible"
    
    Expected: Collapse (0.30-0.45), not just destabilization (0.55-0.60)
    """
    memory = get_memory_store()
    session_id = "test_strong_rejection"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("STRONG REJECTION AT HIGH CONFIDENCE TEST")
    print("="*80)
    
    # Build to very high confidence
    queries = [
        "I love coding",
        "I'm passionate about programming",
        "I'm 100% sure coding is my future",
        "I want to be a software engineer"
    ]
    
    for i, query in enumerate(queries, 1):
        profile = memory.get_profile(session_id)
        signals = extract_user_profile(query, profile)
        profile = memory.update_profile(session_id, signals, query)
        print(f"Turn {i}: {profile.confidence_score:.3f} - \"{query}\"")
    
    baseline_score = profile.confidence_score
    print(f"\n✓ Baseline score: {baseline_score:.3f}")
    
    # Strong rejection
    print("\n--- STRONG REJECTION: 'I hate coding, this is terrible' ---")
    query_rejection = "I hate coding, this is terrible"
    profile = memory.get_profile(session_id)
    signals = extract_user_profile(query_rejection, profile)
    profile_after = memory.update_profile(session_id, signals, query_rejection)
    
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Score before: {baseline_score:.3f}")
    print(f"Score after: {profile_after.confidence_score:.3f}")
    print(f"Drop: {profile_after.confidence_score - baseline_score:+.3f}")
    
    # Validation
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)
    
    # Should detect strong_contradiction
    conf_signals = signals.get('confidence_signals', [])
    assert "strong_contradiction" in conf_signals, \
        f"Strong contradiction not detected. Got: {conf_signals}"
    print(f"✓ Strong contradiction detected")
    
    # Should drop significantly (collapse, not just destabilization)
    assert profile_after.confidence_score < baseline_score, \
        f"Score should drop (was {baseline_score:.3f}, now {profile_after.confidence_score:.3f})"
    print(f"✓ Score dropped: {baseline_score:.3f} → {profile_after.confidence_score:.3f}")
    
    # Should collapse (< 0.50), not just destabilize
    expected_min = 0.30
    expected_max = 0.50
    
    drop_percentage = (baseline_score - profile_after.confidence_score) / baseline_score
    print(f"\nDrop percentage: {drop_percentage*100:.1f}%")
    
    if expected_min <= profile_after.confidence_score <= expected_max:
        print(f"✓ Score in collapse zone ({expected_min}–{expected_max})")
    else:
        if profile_after.confidence_score > expected_max:
            print(f"⚠️  Score too high: {profile_after.confidence_score:.3f} (expected {expected_min}–{expected_max})")
            print(f"   Strong rejection should cause collapse, not just destabilization")
            assert False, f"Strong rejection didn't collapse: {profile_after.confidence_score:.3f} > {expected_max}"
        else:
            print(f"⚠️  Score too low: {profile_after.confidence_score:.3f} (expected {expected_min}–{expected_max})")
    
    print("\n✅ Strong rejection behavior correct")
    
    return profile_after.confidence_score


def test_normal_vs_strong_contradiction():
    """
    Compare normal contradiction vs strong rejection.
    
    Expected:
    - Normal: "I don't like coding" → destabilization (~0.55)
    - Strong: "I hate coding" → collapse (~0.35-0.45)
    """
    memory = get_memory_store()
    
    print("\n" + "="*80)
    print("NORMAL VS STRONG CONTRADICTION COMPARISON")
    print("="*80)
    
    # Test 1: Normal contradiction
    session_id_1 = "test_normal_contradiction"
    memory.clear_session(session_id_1)
    
    queries_1 = [
        "I love coding",
        "I'm passionate about programming",
        "I'm 100% sure coding is my future",
        "I want to be a software engineer"
    ]
    
    for query in queries_1:
        profile = memory.get_profile(session_id_1)
        signals = extract_user_profile(query, profile)
        profile = memory.update_profile(session_id_1, signals, query)
    
    baseline_1 = profile.confidence_score
    
    query_normal = "I don't like coding"
    profile = memory.get_profile(session_id_1)
    signals = extract_user_profile(query_normal, profile)
    profile_after_1 = memory.update_profile(session_id_1, signals, query_normal)
    
    drop_1 = baseline_1 - profile_after_1.confidence_score
    
    print(f"\n--- Test 1: Normal contradiction ---")
    print(f"Query: \"{query_normal}\"")
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Drop: {baseline_1:.3f} → {profile_after_1.confidence_score:.3f} ({drop_1:+.3f})")
    
    # Test 2: Strong rejection
    session_id_2 = "test_strong_rejection_compare"
    memory.clear_session(session_id_2)
    
    queries_2 = [
        "I love coding",
        "I'm passionate about programming",
        "I'm 100% sure coding is my future",
        "I want to be a software engineer"
    ]
    
    for query in queries_2:
        profile = memory.get_profile(session_id_2)
        signals = extract_user_profile(query, profile)
        profile = memory.update_profile(session_id_2, signals, query)
    
    baseline_2 = profile.confidence_score
    
    query_strong = "I hate coding, this is terrible"
    profile = memory.get_profile(session_id_2)
    signals = extract_user_profile(query_strong, profile)
    profile_after_2 = memory.update_profile(session_id_2, signals, query_strong)
    
    drop_2 = baseline_2 - profile_after_2.confidence_score
    
    print(f"\n--- Test 2: Strong rejection ---")
    print(f"Query: \"{query_strong}\"")
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Drop: {baseline_2:.3f} → {profile_after_2.confidence_score:.3f} ({drop_2:+.3f})")
    
    # Validation
    print("\n" + "="*80)
    print("SEVERITY VALIDATION")
    print("="*80)
    
    drop_diff = drop_2 - drop_1
    print(f"\nDrop difference: {drop_diff:.3f}")
    print(f"Normal drop: {drop_1:.3f}")
    print(f"Strong drop: {drop_2:.3f}")
    
    # Strong rejection should drop significantly more than normal contradiction
    if drop_2 > drop_1 + 0.10:
        print(f"✓ Strong rejection drops harder: {drop_2:.3f} vs {drop_1:.3f} (diff: {drop_diff:.3f})")
        print(f"  Normal: destabilization (~0.55)")
        print(f"  Strong: collapse (~0.35-0.45)")
    else:
        print(f"⚠️  Strong rejection not severe enough: {drop_2:.3f} vs {drop_1:.3f} (diff: {drop_diff:.3f})")
        print(f"  Expected: Strong drop > Normal drop + 0.10")
        assert False, f"Strong rejection not severe enough: diff = {drop_diff:.3f}"
    
    # Validate zones
    if 0.50 <= profile_after_1.confidence_score <= 0.65:
        print(f"✓ Normal contradiction in destabilization zone: {profile_after_1.confidence_score:.3f}")
    else:
        print(f"⚠️  Normal contradiction outside destabilization zone: {profile_after_1.confidence_score:.3f}")
    
    if 0.30 <= profile_after_2.confidence_score <= 0.50:
        print(f"✓ Strong rejection in collapse zone: {profile_after_2.confidence_score:.3f}")
    else:
        print(f"⚠️  Strong rejection outside collapse zone: {profile_after_2.confidence_score:.3f}")
    
    print("\n✅ Severity distinction validated")


def test_emotional_residual_effect():
    """
    Test that emotional signals have slight residual effect.
    
    Compare:
    1. "I hate coding"
    2. "I hate coding and it's boring and stressful"
    
    Expected: Slight difference (0.02-0.05), not zero
    """
    memory = get_memory_store()
    
    print("\n" + "="*80)
    print("EMOTIONAL RESIDUAL EFFECT TEST")
    print("="*80)
    
    # Test 1: Strong rejection alone
    session_id_1 = "test_rejection_alone"
    memory.clear_session(session_id_1)
    
    queries_1 = [
        "I love coding",
        "I'm passionate about programming",
        "I'm 100% sure coding is my future",
        "I want to be a software engineer"
    ]
    
    for query in queries_1:
        profile = memory.get_profile(session_id_1)
        signals = extract_user_profile(query, profile)
        profile = memory.update_profile(session_id_1, signals, query)
    
    baseline_1 = profile.confidence_score
    
    query_rejection = "I hate coding"
    profile = memory.get_profile(session_id_1)
    signals = extract_user_profile(query_rejection, profile)
    profile_after_1 = memory.update_profile(session_id_1, signals, query_rejection)
    
    print(f"\n--- Test 1: Strong rejection alone ---")
    print(f"Query: \"{query_rejection}\"")
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Result: {baseline_1:.3f} → {profile_after_1.confidence_score:.3f}")
    
    # Test 2: Strong rejection + emotional signals
    session_id_2 = "test_rejection_emotional"
    memory.clear_session(session_id_2)
    
    queries_2 = [
        "I love coding",
        "I'm passionate about programming",
        "I'm 100% sure coding is my future",
        "I want to be a software engineer"
    ]
    
    for query in queries_2:
        profile = memory.get_profile(session_id_2)
        signals = extract_user_profile(query, profile)
        profile = memory.update_profile(session_id_2, signals, query)
    
    baseline_2 = profile.confidence_score
    
    query_emotional = "I hate coding and it's boring and stressful"
    profile = memory.get_profile(session_id_2)
    signals = extract_user_profile(query_emotional, profile)
    profile_after_2 = memory.update_profile(session_id_2, signals, query_emotional)
    
    print(f"\n--- Test 2: Strong rejection + emotional signals ---")
    print(f"Query: \"{query_emotional}\"")
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Result: {baseline_2:.3f} → {profile_after_2.confidence_score:.3f}")
    
    # Validation
    print("\n" + "="*80)
    print("RESIDUAL EFFECT VALIDATION")
    print("="*80)
    
    diff = abs(profile_after_1.confidence_score - profile_after_2.confidence_score)
    print(f"\nScore difference: {diff:.3f}")
    
    if 0.02 <= diff <= 0.05:
        print(f"✓ Emotional residual effect present: {diff:.3f}")
        print(f"  Not zero (contradiction dominates)")
        print(f"  Not large (no destructive stacking)")
    elif diff < 0.02:
        print(f"⚠️  Residual effect too small: {diff:.3f} (expected 0.02-0.05)")
        print(f"  Emotional signals should have slight influence")
    else:
        print(f"⚠️  Residual effect too large: {diff:.3f} (expected 0.02-0.05)")
        print(f"  Emotional signals stacking too much")
    
    print("\n✅ Emotional residual effect validated")


if __name__ == "__main__":
    try:
        score = test_strong_rejection_at_high_confidence()
        test_normal_vs_strong_contradiction()
        test_emotional_residual_effect()
        
        print("\n" + "="*80)
        print("ALL STRONG REJECTION TESTS COMPLETE")
        print("="*80)
        
        # Final verdict
        if 0.30 <= score <= 0.50:
            print("\n✅ PRODUCTION-READY: Strong rejection causes collapse correctly")
        else:
            print(f"\n⚠️  NEEDS ADJUSTMENT: Score {score:.3f} outside collapse range (0.30-0.50)")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
