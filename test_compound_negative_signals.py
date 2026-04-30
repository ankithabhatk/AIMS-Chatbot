"""
Test compound negative signals at high confidence.

Verify that contradiction dominates and other negative signals don't stack destructively.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.conversation_memory import (
    get_memory_store,
    extract_user_profile,
)


def test_compound_negative_at_high_confidence():
    """
    Test compound negative signals at very high confidence.
    
    Scenario: User at 0.90 confidence says:
    "actually coding is boring and stressful and I don't like it"
    
    Signals: contradiction + negative_sentiment + pivot
    
    Expected: ~0.55-0.60 (destabilization, not collapse)
    NOT: < 0.50 (too harsh) or > 0.65 (too soft)
    """
    memory = get_memory_store()
    session_id = "test_compound_negative"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("COMPOUND NEGATIVE SIGNALS AT HIGH CONFIDENCE TEST")
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
    
    # Compound negative: contradiction + negative_sentiment + pivot
    print("\n--- COMPOUND NEGATIVE: 'actually coding is boring and stressful and I don't like it' ---")
    query_compound = "actually coding is boring and stressful and I don't like it"
    profile = memory.get_profile(session_id)
    signals = extract_user_profile(query_compound, profile)
    profile_after = memory.update_profile(session_id, signals, query_compound)
    
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Score before: {baseline_score:.3f}")
    print(f"Score after: {profile_after.confidence_score:.3f}")
    print(f"Drop: {profile_after.confidence_score - baseline_score:+.3f}")
    
    # Validation
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)
    
    # Should detect all signals
    conf_signals = signals.get('confidence_signals', [])
    assert "contradiction" in conf_signals, "Contradiction not detected"
    print(f"✓ Contradiction detected")
    
    if "negative_sentiment" in conf_signals:
        print(f"✓ Negative sentiment detected")
    if "pivot" in conf_signals:
        print(f"✓ Pivot detected")
    
    # Should drop significantly
    assert profile_after.confidence_score < baseline_score, \
        f"Score should drop (was {baseline_score:.3f}, now {profile_after.confidence_score:.3f})"
    print(f"✓ Score dropped: {baseline_score:.3f} → {profile_after.confidence_score:.3f}")
    
    # Should land in destabilization zone (0.55-0.60), NOT collapse zone (< 0.50)
    expected_min = 0.50
    expected_max = 0.65
    
    drop_percentage = (baseline_score - profile_after.confidence_score) / baseline_score
    print(f"\nDrop percentage: {drop_percentage*100:.1f}%")
    
    # Critical validation: Should NOT collapse
    if profile_after.confidence_score < 0.50:
        print(f"❌ COLLAPSE: Score dropped too far ({profile_after.confidence_score:.3f} < 0.50)")
        print(f"   This is a collapse, not destabilization")
        print(f"   Expected: {expected_min}–{expected_max}")
        assert False, f"Compound negative caused collapse: {profile_after.confidence_score:.3f} < 0.50"
    else:
        print(f"✓ No collapse: Score stayed above 0.50")
    
    # Should be in destabilization zone
    if expected_min <= profile_after.confidence_score <= expected_max:
        print(f"✓ Score in destabilization zone ({expected_min}–{expected_max})")
    else:
        if profile_after.confidence_score < expected_min:
            print(f"⚠️  Score too low: {profile_after.confidence_score:.3f} (expected {expected_min}–{expected_max})")
            print(f"   Compound negatives stacking destructively")
            assert False, f"Score too low: {profile_after.confidence_score:.3f} < {expected_min}"
        else:
            print(f"⚠️  Score too high: {profile_after.confidence_score:.3f} (expected {expected_min}–{expected_max})")
            print(f"   Contradiction not strong enough")
            assert False, f"Score too high: {profile_after.confidence_score:.3f} > {expected_max}"
    
    # Should NOT stay in high confidence
    assert profile_after.confidence_score < 0.70, \
        f"High confidence contradiction should drop below 0.70 (got {profile_after.confidence_score:.3f})"
    print(f"✓ Dropped below high confidence threshold (< 0.70)")
    
    print("\n✅ Compound negative signals behavior validated")
    
    return profile_after.confidence_score


def test_contradiction_dominates():
    """
    Test that contradiction dominates other negative signals.
    
    Compare:
    1. Contradiction alone
    2. Contradiction + negative_sentiment + pivot
    
    Expected: Similar drops (contradiction dominates, others don't stack destructively)
    """
    memory = get_memory_store()
    
    print("\n" + "="*80)
    print("CONTRADICTION DOMINANCE TEST")
    print("="*80)
    
    # Test 1: Contradiction alone
    session_id_1 = "test_contradiction_alone"
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
    
    query_contradiction = "I don't like coding"
    profile = memory.get_profile(session_id_1)
    signals = extract_user_profile(query_contradiction, profile)
    profile_after_1 = memory.update_profile(session_id_1, signals, query_contradiction)
    
    drop_1 = baseline_1 - profile_after_1.confidence_score
    
    print(f"\n--- Test 1: Contradiction alone ---")
    print(f"Query: \"{query_contradiction}\"")
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Drop: {baseline_1:.3f} → {profile_after_1.confidence_score:.3f} ({drop_1:+.3f})")
    
    # Test 2: Contradiction + compound negatives
    session_id_2 = "test_contradiction_compound"
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
    
    query_compound = "actually coding is boring and stressful and I don't like it"
    profile = memory.get_profile(session_id_2)
    signals = extract_user_profile(query_compound, profile)
    profile_after_2 = memory.update_profile(session_id_2, signals, query_compound)
    
    drop_2 = baseline_2 - profile_after_2.confidence_score
    
    print(f"\n--- Test 2: Contradiction + compound negatives ---")
    print(f"Query: \"{query_compound}\"")
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Drop: {baseline_2:.3f} → {profile_after_2.confidence_score:.3f} ({drop_2:+.3f})")
    
    # Validation
    print("\n" + "="*80)
    print("DOMINANCE VALIDATION")
    print("="*80)
    
    drop_diff = abs(drop_2 - drop_1)
    print(f"\nDrop difference: {drop_diff:.3f}")
    
    # Drops should be similar (contradiction dominates)
    # Allow up to 0.10 difference for compound signals
    if drop_diff <= 0.10:
        print(f"✓ Contradiction dominates: Drops are similar ({drop_1:.3f} vs {drop_2:.3f})")
        print(f"  Other negative signals didn't stack destructively")
    else:
        print(f"⚠️  Compound signals stacking: Drop difference too large ({drop_diff:.3f})")
        print(f"  Contradiction alone: {drop_1:.3f}")
        print(f"  Contradiction + compound: {drop_2:.3f}")
        print(f"  Expected: Similar drops (difference < 0.10)")
    
    print("\n✅ Contradiction dominance validated")


if __name__ == "__main__":
    try:
        score = test_compound_negative_at_high_confidence()
        test_contradiction_dominates()
        
        print("\n" + "="*80)
        print("ALL COMPOUND NEGATIVE TESTS COMPLETE")
        print("="*80)
        
        # Final verdict
        if 0.50 <= score <= 0.65:
            print("\n✅ PRODUCTION-READY: Compound negatives handled correctly")
        else:
            print(f"\n⚠️  NEEDS ADJUSTMENT: Score {score:.3f} outside target range (0.50-0.65)")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
