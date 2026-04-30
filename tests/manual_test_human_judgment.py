"""
Manual test to verify human judgment layer implementation.
This script demonstrates that the human judgment phrases are properly positioned.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.conversation_memory import UserProfile, build_final_recommendation


def test_conflict_resolution():
    """Test conflict resolution recommendation with human judgment."""
    print("=" * 80)
    print("TEST: Conflict Resolution (High Salary + Quick Job)")
    print("=" * 80)
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary", "quick_job"},
        education_level="12th",
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="medium"
    )
    
    recommendation = build_final_recommendation(profile, "what should I do?")
    print(recommendation)
    print("\n")
    
    # Verify human judgment phrase is present
    assert "If I were in your position" in recommendation
    assert "---" in recommendation
    print("✓ Human judgment phrase found")
    print("✓ Separator line found")


def test_quick_job():
    """Test quick job recommendation with human judgment."""
    print("=" * 80)
    print("TEST: Quick Job Goal")
    print("=" * 80)
    
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"quick_job"},
        education_level="12th",
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="medium"
    )
    
    recommendation = build_final_recommendation(profile, "what should I do?")
    print(recommendation)
    print("\n")
    
    # Verify human judgment phrase is present
    assert "If I were in your position" in recommendation
    assert "Here's the honest path" in recommendation
    print("✓ Human judgment phrase found")
    print("✓ Conversational language found")


def test_business():
    """Test business recommendation with human judgment."""
    print("=" * 80)
    print("TEST: Business Interest")
    print("=" * 80)
    
    profile = UserProfile(
        interests={"business"},
        constraints=set(),
        goals={"high_salary"},
        education_level="12th",
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="medium"
    )
    
    recommendation = build_final_recommendation(profile, "what should I do?")
    print(recommendation)
    print("\n")
    
    # Verify human judgment phrase is present
    assert "If I were in your position" in recommendation
    print("✓ Human judgment phrase found")


if __name__ == "__main__":
    test_conflict_resolution()
    test_quick_job()
    test_business()
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
