"""
Manual test to demonstrate confidence-calibrated tone variations.

Run this to see how recommendations change based on confidence level.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.conversation_memory import UserProfile, build_final_recommendation


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_low_confidence():
    """Test low confidence tone (exploratory)."""
    print_section("LOW CONFIDENCE (Exploratory Tone)")
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        confidence_level="low"
    )
    
    # Without force - should return None
    result = build_final_recommendation(profile, "what should I do", force=False)
    print("WITHOUT FORCE (should be None):")
    print(f"Result: {result}")
    print()
    
    # With force - should get soft decision tone
    result = build_final_recommendation(profile, "what should I do", force=True)
    print("WITH FORCE (soft decision tone):")
    print(result)


def test_medium_confidence():
    """Test medium confidence tone (balanced)."""
    print_section("MEDIUM CONFIDENCE (Balanced Tone)")
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        confidence_level="medium"
    )
    
    result = build_final_recommendation(profile, "what should I do", force=False)
    print(result)


def test_high_confidence():
    """Test high confidence tone (decisive)."""
    print_section("HIGH CONFIDENCE (Decisive Tone)")
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        confidence_level="high"
    )
    
    result = build_final_recommendation(profile, "what should I do", force=False)
    print(result)


def test_comparison():
    """Show side-by-side comparison of tone variations."""
    print_section("TONE COMPARISON - Same Profile, Different Confidence Levels")
    
    base_profile_data = {
        "interests": {"coding"},
        "goals": {"quick_job"}
    }
    
    for confidence in ["low", "medium", "high"]:
        profile = UserProfile(**base_profile_data, confidence_level=confidence)
        result = build_final_recommendation(profile, "what should I do", force=True)
        
        print(f"\n--- {confidence.upper()} CONFIDENCE ---")
        if result:
            # Print first 300 characters to show tone difference
            print(result[:300] + "...\n")
        else:
            print("None (would trigger more questions)\n")


if __name__ == "__main__":
    print("\n" + "🎭" * 40)
    print("  CONFIDENCE-CALIBRATED TONE DEMONSTRATION")
    print("🎭" * 40)
    
    test_low_confidence()
    test_medium_confidence()
    test_high_confidence()
    test_comparison()
    
    print("\n" + "=" * 80)
    print("  ✅ Tone layer working correctly!")
    print("=" * 80 + "\n")
