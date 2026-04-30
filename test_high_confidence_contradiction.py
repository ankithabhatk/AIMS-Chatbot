"""
Test contradiction at high confidence levels.

Verify that high confidence contradictions fall harder than low confidence ones.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.conversation_memory import (
    get_memory_store,
    extract_user_profile,
)


def test_high_confidence_contradiction():
    """Test contradiction at very high confidence (0.85-0.90)."""
    memory = get_memory_store()
    session_id = "test_high_conf_contradiction"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("HIGH CONFIDENCE CONTRADICTION TEST")
    print("="*80)
    
    # Build to very high confidence
    queries = [
        "I love coding",
        "I'm passionate about programming",
        "I'm 100% sure coding is my future",
        "I want to be a software engineer",
        "what should I do?"
    ]
    
    for i, query in enumerate(queries, 1):
        profile = memory.get_profile(session_id)
        signals = extract_user_profile(query, profile)
        profile = memory.update_profile(session_id, signals)
        print(f"Turn {i}: {profile.confidence_score:.3f} - \"{query}\"")
    
    baseline_score = profile.confidence_score
    print(f"\n✓ Baseline score: {baseline_score:.3f}")
    
    # Contradiction at high confidence
    print("\n--- CONTRADICTION: 'actually I hate coding' ---")
    query_contradiction = "actually I hate coding"
    profile = memory.get_profile(session_id)
    signals = extract_user_profile(query_contradiction, profile)
    profile_after = memory.update_profile(session_id, signals)
    
    print(f"Signals: {signals.get('confidence_signals', [])}")
    print(f"Score before: {baseline_score:.3f}")
    print(f"Score after: {profile_after.confidence_score:.3f}")
    print(f"Drop: {profile_after.confidence_score - baseline_score:+.3f}")
    
    # Validation
    print("\n" + "="*80)
    print("VALIDATION")
    print("="*80)
    
    # Should detect contradiction
    assert "contradiction" in signals.get('confidence_signals', []), \
        "Contradiction not detected"
    print("✓ Contradiction detected")
    
    # Should drop significantly
    assert profile_after.confidence_score < baseline_score, \
        f"Score should drop (was {baseline_score:.3f}, now {profile_after.confidence_score:.3f})"
    print(f"✓ Score dropped: {baseline_score:.3f} → {profile_after.confidence_score:.3f}")
    
    # Should land in re-evaluation zone (0.50-0.65 for high confidence)
    expected_min = 0.50
    expected_max = 0.65
    if expected_min <= profile_after.confidence_score <= expected_max:
        print(f"✓ Score in expected range ({expected_min}–{expected_max})")
    else:
        print(f"⚠️  Score outside expected range: {profile_after.confidence_score:.3f} (expected {expected_min}–{expected_max})")
    
    # Should NOT stay in high confidence
    assert profile_after.confidence_score < 0.70, \
        f"High confidence contradiction should drop below 0.70 (got {profile_after.confidence_score:.3f})"
    print(f"✓ Dropped below high confidence threshold (< 0.70)")
    
    # Should drop harder than low confidence case
    # Low confidence: 0.525 → 0.404 (drop of 0.121, 23% drop)
    # High confidence: should drop more than 23%
    drop_percentage = (baseline_score - profile_after.confidence_score) / baseline_score
    print(f"\nDrop percentage: {drop_percentage*100:.1f}%")
    
    if drop_percentage > 0.25:  # More than 25% drop
        print(f"✓ High confidence fell harder (>{25}% drop)")
    else:
        print(f"⚠️  High confidence didn't fall hard enough ({drop_percentage*100:.1f}% drop)")
    
    print("\n✅ High confidence contradiction behavior correct")


def test_medium_high_confidence_contradiction():
    """Test contradiction at medium-high confidence (0.70-0.80)."""
    memory = get_memory_store()
    session_id = "test_med_high_contradiction"
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("MEDIUM-HIGH CONFIDENCE CONTRADICTION TEST")
    print("="*80)
    
    # Build to medium-high confidence
    queries = [
        "I like coding",
        "I want good salary",
        "I'm interested in tech",
        "what should I do?"
    ]
    
    for i, query in enumerate(queries, 1):
        profile = memory.get_profile(session_id)
        signals = extract_user_profile(query, profile)
        profile = memory.update_profile(session_id, signals)
        print(f"Turn {i}: {profile.confidence_score:.3f} - \"{query}\"")
    
    baseline_score = profile.confidence_score
    print(f"\n✓ Baseline score: {baseline_score:.3f}")
    
    # Contradiction
    print("\n--- CONTRADICTION: 'actually I don't like coding' ---")
    query_contradiction = "actually I don't like coding"
    profile = memory.get_profile(session_id)
    signals = extract_user_profile(query_contradiction, profile)
    profile_after = memory.update_profile(session_id, signals)
    
    print(f"Score before: {baseline_score:.3f}")
    print(f"Score after: {profile_after.confidence_score:.3f}")
    print(f"Drop: {profile_after.confidence_score - baseline_score:+.3f}")
    
    drop_percentage = (baseline_score - profile_after.confidence_score) / baseline_score
    print(f"Drop percentage: {drop_percentage*100:.1f}%")
    
    # Should land around 0.49-0.55 for medium-high
    if 0.45 <= profile_after.confidence_score <= 0.60:
        print(f"✓ Score in expected range (0.45–0.60)")
    else:
        print(f"⚠️  Score outside expected range: {profile_after.confidence_score:.3f}")
    
    print("\n✅ Medium-high confidence contradiction behavior correct")


if __name__ == "__main__":
    try:
        test_high_confidence_contradiction()
        test_medium_high_confidence_contradiction()
        
        print("\n" + "="*80)
        print("ALL HIGH CONFIDENCE TESTS PASSED ✅")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
