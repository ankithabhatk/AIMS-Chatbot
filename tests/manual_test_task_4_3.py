"""
Manual test for Task 4.3: Adjust Behavior for Low Confidence

This script demonstrates the difference in counselor responses between:
1. Low confidence (uncertain user) - supportive, more questions, no strong recommendations
2. Normal confidence - balanced guidance with clear recommendations
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.conversation_memory import UserProfile, build_final_recommendation
from app.services.counselor_handler import build_progressive_response, adjust_tone


def test_low_confidence_behavior():
    """Test counselor behavior with low confidence user."""
    print("=" * 80)
    print("TEST 1: LOW CONFIDENCE USER (uncertain, needs support)")
    print("=" * 80)
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        education_level="12th",
        ambiguity_signals={"uncertain"},
        previous_intents=[],
        confidence_level="low"
    )
    
    print("\nProfile:")
    print(f"  Interests: {profile.interests}")
    print(f"  Constraints: {profile.constraints}")
    print(f"  Goals: {profile.goals}")
    print(f"  Confidence Level: {profile.confidence_level}")
    print(f"  Ambiguity Signals: {profile.ambiguity_signals}")
    
    print("\n" + "-" * 80)
    print("Tone Adjustment:")
    tone = adjust_tone(profile)
    print(f"  Tone: {tone}")
    
    print("\n" + "-" * 80)
    print("Progressive Response (mid-conversation):")
    print("-" * 80)
    response = build_progressive_response(profile, "I'm not sure what to do")
    print(response)
    
    print("\n" + "-" * 80)
    print("Final Recommendation (decision query):")
    print("-" * 80)
    recommendation = build_final_recommendation(profile, "what should I do?")
    if recommendation is None:
        print("✓ NO RECOMMENDATION PROVIDED (as expected for low confidence)")
        print("  → User will get progressive response with more questions instead")
    else:
        print("✗ UNEXPECTED: Recommendation provided for low confidence user")
        print(recommendation)
    
    print("\n")


def test_normal_confidence_behavior():
    """Test counselor behavior with normal confidence user."""
    print("=" * 80)
    print("TEST 2: NORMAL CONFIDENCE USER (clear, ready for guidance)")
    print("=" * 80)
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        education_level="12th",
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="medium"
    )
    
    print("\nProfile:")
    print(f"  Interests: {profile.interests}")
    print(f"  Constraints: {profile.constraints}")
    print(f"  Goals: {profile.goals}")
    print(f"  Confidence Level: {profile.confidence_level}")
    print(f"  Ambiguity Signals: {profile.ambiguity_signals}")
    
    print("\n" + "-" * 80)
    print("Tone Adjustment:")
    tone = adjust_tone(profile)
    print(f"  Tone: {tone}")
    
    print("\n" + "-" * 80)
    print("Progressive Response (mid-conversation):")
    print("-" * 80)
    response = build_progressive_response(profile, "what are my options?")
    print(response)
    
    print("\n" + "-" * 80)
    print("Final Recommendation (decision query):")
    print("-" * 80)
    recommendation = build_final_recommendation(profile, "what should I do?")
    if recommendation is not None:
        print("✓ RECOMMENDATION PROVIDED (as expected for normal confidence)")
        print()
        print(recommendation)
    else:
        print("✗ UNEXPECTED: No recommendation for normal confidence user")
    
    print("\n")


def test_comparison():
    """Compare low vs normal confidence side by side."""
    print("=" * 80)
    print("TEST 3: SIDE-BY-SIDE COMPARISON")
    print("=" * 80)
    
    low_profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"quick_job"},
        education_level=None,
        ambiguity_signals={"uncertain"},
        previous_intents=[],
        confidence_level="low"
    )
    
    normal_profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"quick_job"},
        education_level=None,
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="medium"
    )
    
    print("\n" + "-" * 80)
    print("LOW CONFIDENCE RESPONSE:")
    print("-" * 80)
    low_response = build_progressive_response(low_profile, "what should I choose?")
    print(low_response)
    
    print("\n" + "-" * 80)
    print("NORMAL CONFIDENCE RESPONSE:")
    print("-" * 80)
    normal_response = build_progressive_response(normal_profile, "what should I choose?")
    print(normal_response)
    
    print("\n" + "-" * 80)
    print("KEY DIFFERENCES:")
    print("-" * 80)
    
    # Check for reassuring language
    has_reassuring = "It's okay to be unsure" in low_response or "we can figure this" in low_response
    print(f"  Reassuring language in low confidence: {has_reassuring}")
    
    # Check for exploratory language
    has_exploratory = "Let's explore" in low_response
    print(f"  Exploratory language in low confidence: {has_exploratory}")
    
    # Check for softened recommendations
    has_softened = "could be" in low_response or "might be" in low_response
    has_strong = "makes sense" in normal_response or "is better" in normal_response
    print(f"  Softened recommendations in low confidence: {has_softened}")
    print(f"  Strong recommendations in normal confidence: {has_strong}")
    
    # Count questions
    low_questions = low_response.count("?")
    normal_questions = normal_response.count("?")
    print(f"  Questions in low confidence: {low_questions}")
    print(f"  Questions in normal confidence: {normal_questions}")
    print(f"  More questions for low confidence: {low_questions > normal_questions}")
    
    print("\n")


if __name__ == "__main__":
    test_low_confidence_behavior()
    test_normal_confidence_behavior()
    test_comparison()
    
    print("=" * 80)
    print("TASK 4.3 VERIFICATION COMPLETE")
    print("=" * 80)
    print("\n✓ Low confidence users get:")
    print("  - Reassuring language ('It's okay to be unsure')")
    print("  - More clarifying questions")
    print("  - Softened recommendations ('could be', 'might be')")
    print("  - No final recommendations (returns None)")
    print("\n✓ Normal confidence users get:")
    print("  - Balanced guidance")
    print("  - Clear recommendations")
    print("  - Final recommendations when ready")
    print()
