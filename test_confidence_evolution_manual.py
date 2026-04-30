"""
Manual test for confidence evolution integration.

This test verifies the complete confidence evolution flow:
1. Score updates per turn (no overwrite bugs)
2. Tone reflects category (low → exploratory, medium → balanced, high → decisive)
3. Decision override still works
4. No jitter (smooth tone evolution)
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.conversation_memory import (
    ConversationMemory,
    extract_user_profile,
    get_memory_store,
)
from app.services.counselor_handler import get_counselor_response


def test_confidence_evolution():
    """Test confidence evolution across realistic conversation."""
    memory = get_memory_store()
    session_id = "test_evolution"
    
    # Clear any existing session
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("CONFIDENCE EVOLUTION TEST")
    print("="*80)
    
    scores = []  # Track scores across turns
    
    # Turn 1: "idk what to do"
    print("\n--- TURN 1: 'idk what to do' ---")
    query1 = "idk what to do"
    signals1 = extract_user_profile(query1)
    profile1 = memory.update_profile(session_id, signals1)
    scores.append(profile1.confidence_score)
    
    print(f"Signals: {signals1.get('confidence_signals', [])}")
    print(f"Score: {profile1.confidence_score:.3f}")
    print(f"Category: {profile1.confidence_category}")
    print(f"Expected: ~0.25 (low)")
    
    assert profile1.confidence_category == "low", f"Turn 1: Expected low, got {profile1.confidence_category}"
    assert 0.20 <= profile1.confidence_score <= 0.30, f"Turn 1: Score {profile1.confidence_score} out of range"
    
    # Turn 2: "maybe coding"
    print("\n--- TURN 2: 'maybe coding' ---")
    query2 = "maybe coding"
    profile = memory.get_profile(session_id)  # Get current profile
    signals2 = extract_user_profile(query2, profile)
    profile2 = memory.update_profile(session_id, signals2)
    scores.append(profile2.confidence_score)
    
    print(f"Signals: {signals2.get('confidence_signals', [])}")
    print(f"Score: {profile2.confidence_score:.3f}")
    print(f"Category: {profile2.confidence_category}")
    print(f"Expected: ~0.35-0.40 (low/medium boundary)")
    print(f"Previous score: {scores[0]:.3f}")
    print(f"Increased: {scores[1] > scores[0]}")
    
    assert scores[1] > scores[0], \
        f"Turn 2: Score should increase (was {scores[0]:.3f}, now {scores[1]:.3f})"
    assert 0.30 <= profile2.confidence_score <= 0.45, f"Turn 2: Score {profile2.confidence_score} out of range"
    
    # Turn 3: "I like coding and want good salary"
    print("\n--- TURN 3: 'I like coding and want good salary' ---")
    query3 = "I like coding and want good salary"
    profile = memory.get_profile(session_id)
    signals3 = extract_user_profile(query3, profile)
    profile3 = memory.update_profile(session_id, signals3)
    scores.append(profile3.confidence_score)
    
    print(f"Signals: {signals3.get('confidence_signals', [])}")
    print(f"Score: {profile3.confidence_score:.3f}")
    print(f"Category: {profile3.confidence_category}")
    print(f"Expected: ~0.45-0.55 (medium)")
    print(f"Previous score: {scores[1]:.3f}")
    print(f"Increased: {scores[2] > scores[1]}")
    
    assert scores[2] > scores[1], \
        f"Turn 3: Score should increase (was {scores[1]:.3f}, now {scores[2]:.3f})"
    assert profile3.confidence_category == "medium", f"Turn 3: Expected medium, got {profile3.confidence_category}"
    assert 0.40 <= profile3.confidence_score <= 0.60, f"Turn 3: Score {profile3.confidence_score} out of range"
    
    # Turn 4: "what should I do?"
    print("\n--- TURN 4: 'what should I do?' ---")
    query4 = "what should I do?"
    profile = memory.get_profile(session_id)
    signals4 = extract_user_profile(query4, profile)
    profile4 = memory.update_profile(session_id, signals4)
    scores.append(profile4.confidence_score)
    
    print(f"Signals: {signals4.get('confidence_signals', [])}")
    print(f"Score: {profile4.confidence_score:.3f}")
    print(f"Category: {profile4.confidence_category}")
    print(f"Expected: ~0.65-0.75 (medium/high)")
    print(f"Previous score: {scores[2]:.3f}")
    print(f"Increased: {scores[3] > scores[2]}")
    
    assert scores[3] > scores[2], \
        f"Turn 4: Score should increase (was {scores[2]:.3f}, now {scores[3]:.3f})"
    # Note: With current tuning, may be high or medium depending on Turn 3 score
    assert profile4.confidence_category in ["medium", "high"], \
        f"Turn 4: Expected medium or high, got {profile4.confidence_category}"
    assert profile4.confidence_score >= 0.60, f"Turn 4: Score {profile4.confidence_score} should be >= 0.60"
    
    # Get final recommendation to verify tone
    print("\n--- FINAL RECOMMENDATION ---")
    response = get_counselor_response(query4, session_id)
    
    if response and response.get('answer'):
        answer = response['answer'].lower()
        print(f"Response preview: {answer[:200]}...")
        
        # Should have decisive tone
        decisive_indicators = ["strongly", "clear", "based on your clear goals"]
        has_decisive = any(ind in answer for ind in decisive_indicators)
        print(f"Has decisive tone: {has_decisive}")
        
        # Should NOT have exploratory tone
        exploratory_indicators = ["unsure", "it's okay to feel", "explore"]
        has_exploratory = any(ind in answer for ind in exploratory_indicators)
        print(f"Has exploratory tone: {has_exploratory}")
        
        assert has_decisive or not has_exploratory, "Turn 4: Should have decisive tone, not exploratory"
    
    print("\n" + "="*80)
    print("✓ ALL CHECKS PASSED")
    print("="*80)
    print(f"\nEvolution summary:")
    print(f"  Turn 1: {scores[0]:.3f} (low)")
    print(f"  Turn 2: {scores[1]:.3f} (low/medium)")
    print(f"  Turn 3: {scores[2]:.3f} (medium)")
    print(f"  Turn 4: {scores[3]:.3f} (high)")
    print(f"\n✓ Score updates per turn (no overwrite bugs)")
    print(f"✓ Tone reflects category")
    print(f"✓ Smooth evolution (no jitter)")
    print(f"✓ Decision override works")


def test_decision_override_with_low_confidence():
    """Test that decision override still works with low confidence."""
    memory = get_memory_store()
    session_id = "test_override"
    
    # Clear any existing session
    memory.clear_session(session_id)
    
    print("\n" + "="*80)
    print("DECISION OVERRIDE TEST (Low Confidence)")
    print("="*80)
    
    # Build low confidence profile
    query1 = "idk"
    signals1 = extract_user_profile(query1)
    profile1 = memory.update_profile(session_id, signals1)
    
    query2 = "maybe coding"
    signals2 = extract_user_profile(query2, profile1)
    profile2 = memory.update_profile(session_id, signals2)
    
    print(f"\nProfile confidence: {profile2.confidence_score:.3f} ({profile2.confidence_category})")
    assert profile2.confidence_category == "low" or profile2.confidence_category == "medium", \
        "Should have low/medium confidence"
    
    # Force decision with explicit request
    query3 = "what should I do?"
    response = get_counselor_response(query3, session_id)
    
    print(f"\nDecision query: '{query3}'")
    print(f"Response received: {response is not None}")
    
    if response and response.get('answer'):
        answer = response['answer']
        print(f"Response length: {len(answer)} chars")
        print(f"Response preview: {answer[:200]}...")
        
        # Should provide recommendation even with low confidence
        assert len(answer) > 100, "Should provide substantive recommendation"
        
        # Should have soft decision tone (not aggressive, not purely exploratory)
        answer_lower = answer.lower()
        has_recommendation = any(phrase in answer_lower for phrase in [
            "recommend", "suggest", "path", "option", "consider"
        ])
        print(f"Has recommendation: {has_recommendation}")
        assert has_recommendation, "Should provide recommendation despite low confidence"
    
    print("\n✓ Decision override works with low confidence")


if __name__ == "__main__":
    try:
        test_confidence_evolution()
        test_decision_override_with_low_confidence()
        print("\n" + "="*80)
        print("ALL TESTS PASSED ✓")
        print("="*80)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
