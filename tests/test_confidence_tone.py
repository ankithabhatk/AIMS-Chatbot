"""
Quick verification tests for confidence-calibrated tone layer.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.conversation_memory import (
    ToneProfile,
    get_tone_profile,
    apply_confidence_tone,
    _inject_tone_prefix,
    _adjust_judgment_strength,
    UserProfile,
    build_final_recommendation,
)


def test_tone_profile_creation():
    """Test ToneProfile creation with valid confidence_strength."""
    profile = ToneProfile(
        prefix="Test prefix",
        judgment_phrase="Test judgment",
        confidence_strength="exploratory"
    )
    assert profile.prefix == "Test prefix"
    assert profile.judgment_phrase == "Test judgment"
    assert profile.confidence_strength == "exploratory"


def test_tone_profile_validation():
    """Test ToneProfile validation rejects invalid confidence_strength."""
    try:
        ToneProfile(
            prefix="Test",
            judgment_phrase="Test",
            confidence_strength="invalid"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid confidence_strength" in str(e)


def test_get_tone_profile_low():
    """Test get_tone_profile returns exploratory tone for low confidence."""
    profile = get_tone_profile("low")
    assert "unsure" in profile.prefix.lower()
    assert profile.judgment_phrase == "Consider"
    assert profile.confidence_strength == "exploratory"


def test_get_tone_profile_medium():
    """Test get_tone_profile returns balanced tone for medium confidence."""
    profile = get_tone_profile("medium")
    assert "practical" in profile.prefix.lower()
    assert profile.judgment_phrase == "I'd recommend"
    assert profile.confidence_strength == "balanced"


def test_get_tone_profile_high():
    """Test get_tone_profile returns decisive tone for high confidence."""
    profile = get_tone_profile("high")
    assert "strongly" in profile.prefix.lower()
    assert profile.judgment_phrase == "I'd strongly recommend"
    assert profile.confidence_strength == "decisive"


def test_get_tone_profile_default():
    """Test get_tone_profile defaults to medium for invalid confidence."""
    profile = get_tone_profile("invalid")
    assert profile.confidence_strength == "balanced"
    
    profile = get_tone_profile(None)
    assert profile.confidence_strength == "balanced"


def test_apply_confidence_tone_empty():
    """Test apply_confidence_tone with empty recommendation returns empty string."""
    result = apply_confidence_tone("", "medium", False)
    assert result == ""
    
    result = apply_confidence_tone("   ", "medium", False)
    assert result == ""


def test_apply_confidence_tone_low():
    """Test apply_confidence_tone with low confidence applies exploratory tone."""
    base = "Based on what you've told me:\n• You like coding\n\nMy recommendation: Start with BCA"
    result = apply_confidence_tone(base, confidence="low", force=False)
    
    assert "unsure" in result.lower()
    assert "Consider" in result
    assert "My recommendation" not in result  # Should be replaced


def test_apply_confidence_tone_medium():
    """Test apply_confidence_tone with medium confidence applies balanced tone."""
    base = "Based on what you've told me:\n• You like coding\n\nMy recommendation: Start with BCA"
    result = apply_confidence_tone(base, confidence="medium", force=False)
    
    assert "practical" in result.lower()
    assert "I'd recommend" in result
    assert "My recommendation" not in result  # Should be replaced


def test_apply_confidence_tone_high():
    """Test apply_confidence_tone with high confidence applies decisive tone."""
    base = "Based on what you've told me:\n• You like coding\n\nMy recommendation: Start with BCA"
    result = apply_confidence_tone(base, confidence="high", force=False)
    
    assert "strongly" in result.lower()
    assert "I'd strongly recommend" in result
    assert "My recommendation" not in result  # Should be replaced


def test_apply_confidence_tone_force_low():
    """Test apply_confidence_tone with force=True + low confidence uses soft decision tone."""
    base = "Based on what you've told me:\n• You like coding\n\nMy recommendation: Start with BCA"
    result = apply_confidence_tone(base, confidence="low", force=True)
    
    assert "unsure" in result.lower()
    assert "I'd recommend" in result  # Soft decision, not "Consider"
    assert "My recommendation" not in result


def test_inject_tone_prefix_with_pattern():
    """Test _inject_tone_prefix finds and replaces opening patterns."""
    recommendation = "Based on what you've told me:\n• You like coding"
    prefix = "Test prefix"
    result = _inject_tone_prefix(recommendation, prefix)
    
    assert "Test prefix" in result
    assert result.index("Test prefix") < result.index("Based on what you've told me:")


def test_inject_tone_prefix_without_pattern():
    """Test _inject_tone_prefix prepends when no pattern found."""
    recommendation = "Some recommendation text"
    prefix = "Test prefix"
    result = _inject_tone_prefix(recommendation, prefix)
    
    assert result.startswith("Test prefix")
    assert "Some recommendation text" in result


def test_adjust_judgment_strength():
    """Test _adjust_judgment_strength replaces judgment phrases."""
    recommendation = "My recommendation: Start with BCA. I'd recommend focusing on web development."
    result = _adjust_judgment_strength(recommendation, "Consider")
    
    assert "My recommendation" not in result
    assert "I'd recommend" not in result
    assert result.count("Consider") == 2


def test_build_final_recommendation_with_tone():
    """Test build_final_recommendation applies tone layer."""
    profile = UserProfile(
        interests={"coding"},
        confidence_score=0.8  # High confidence
    )
    
    recommendation = build_final_recommendation(profile, "what should I do", force=True)
    
    assert recommendation is not None
    # Should have high confidence tone
    assert "strongly" in recommendation.lower()


def test_build_final_recommendation_low_confidence_no_force():
    """Test build_final_recommendation returns None for low confidence without force."""
    profile = UserProfile(
        interests={"coding"},
        confidence_score=0.2  # Low confidence
    )
    
    recommendation = build_final_recommendation(profile, "what should I do", force=False)
    
    assert recommendation is None


def test_build_final_recommendation_low_confidence_with_force():
    """Test build_final_recommendation provides soft decision for low confidence with force."""
    profile = UserProfile(
        interests={"coding"},
        confidence_score=0.2  # Low confidence
    )
    
    recommendation = build_final_recommendation(profile, "what should I do", force=True)
    
    assert recommendation is not None
    # Should have soft decision tone
    assert "unsure" in recommendation.lower()
    assert "I'd recommend" in recommendation


if __name__ == "__main__":
    # Run quick verification
    test_tone_profile_creation()
    test_tone_profile_validation()
    test_get_tone_profile_low()
    test_get_tone_profile_medium()
    test_get_tone_profile_high()
    test_get_tone_profile_default()
    test_apply_confidence_tone_empty()
    test_apply_confidence_tone_low()
    test_apply_confidence_tone_medium()
    test_apply_confidence_tone_high()
    test_apply_confidence_tone_force_low()
    test_inject_tone_prefix_with_pattern()
    test_inject_tone_prefix_without_pattern()
    test_adjust_judgment_strength()
    test_build_final_recommendation_with_tone()
    test_build_final_recommendation_low_confidence_no_force()
    test_build_final_recommendation_low_confidence_with_force()
    
    print("✅ All tone layer tests passed!")
