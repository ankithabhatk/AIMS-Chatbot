"""
Unit tests for adjust_tone function in counselor_handler.py

Tests the tone adjustment logic based on user confidence level.
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.counselor_handler import adjust_tone
from app.services.conversation_memory import UserProfile


def test_adjust_tone_low_confidence():
    """Test that low confidence returns 'supportive' tone."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals=set(),
        education_level=None,
        ambiguity_signals={"confused", "not_sure"},
        previous_intents=[],
        confidence_level="low"
    )
    
    result = adjust_tone(profile)
    assert result == "supportive", "Low confidence should return 'supportive' tone"


def test_adjust_tone_medium_confidence():
    """Test that medium confidence returns 'normal' tone."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"high_salary"},
        education_level="12th",
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="medium"
    )
    
    result = adjust_tone(profile)
    assert result == "normal", "Medium confidence should return 'normal' tone"


def test_adjust_tone_high_confidence():
    """Test that high confidence returns 'normal' tone."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"high_salary"},
        education_level="12th",
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="high"
    )
    
    result = adjust_tone(profile)
    assert result == "normal", "High confidence should return 'normal' tone"


def test_adjust_tone_empty_profile_with_low_confidence():
    """Test that empty profile with low confidence still returns 'supportive'."""
    profile = UserProfile(
        interests=set(),
        constraints=set(),
        goals=set(),
        education_level=None,
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="low"
    )
    
    result = adjust_tone(profile)
    assert result == "supportive", "Low confidence should return 'supportive' even with empty profile"


def test_adjust_tone_empty_profile_with_high_confidence():
    """Test that empty profile with high confidence returns 'normal'."""
    profile = UserProfile(
        interests=set(),
        constraints=set(),
        goals=set(),
        education_level=None,
        ambiguity_signals=set(),
        previous_intents=[],
        confidence_level="high"
    )
    
    result = adjust_tone(profile)
    assert result == "normal", "High confidence should return 'normal' even with empty profile"


if __name__ == "__main__":
    # Run tests
    print("Running adjust_tone unit tests...\n")
    
    test_adjust_tone_low_confidence()
    print("✓ test_adjust_tone_low_confidence passed")
    
    test_adjust_tone_medium_confidence()
    print("✓ test_adjust_tone_medium_confidence passed")
    
    test_adjust_tone_high_confidence()
    print("✓ test_adjust_tone_high_confidence passed")
    
    test_adjust_tone_empty_profile_with_low_confidence()
    print("✓ test_adjust_tone_empty_profile_with_low_confidence passed")
    
    test_adjust_tone_empty_profile_with_high_confidence()
    print("✓ test_adjust_tone_empty_profile_with_high_confidence passed")
    
    print("\n✅ All adjust_tone tests passed!")
