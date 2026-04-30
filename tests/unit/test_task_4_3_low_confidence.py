"""
Unit tests for Task 4.3: Adjust Behavior for Low Confidence

Tests that counselor responses adjust appropriately when confidence is low:
- Avoid strong recommendations
- Add reassuring language
- Ask more clarifying questions
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.conversation_memory import UserProfile, build_final_recommendation
from app.services.counselor_handler import build_progressive_response, adjust_tone


class TestLowConfidenceAdjustment:
    """Test that low confidence triggers appropriate behavior changes."""
    
    def test_adjust_tone_returns_supportive_for_low_confidence(self):
        """Test that adjust_tone returns 'supportive' when confidence is low."""
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals=set(),
            education_level=None,
            ambiguity_signals={"uncertain"},
            previous_intents=[],
            confidence_level="low"
        )
        
        tone = adjust_tone(profile)
        assert tone == "supportive", "Should return 'supportive' for low confidence"
    
    def test_adjust_tone_returns_normal_for_medium_confidence(self):
        """Test that adjust_tone returns 'normal' when confidence is medium."""
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals=set(),
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        tone = adjust_tone(profile)
        assert tone == "normal", "Should return 'normal' for medium confidence"
    
    def test_adjust_tone_returns_normal_for_high_confidence(self):
        """Test that adjust_tone returns 'normal' when confidence is high."""
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals=set(),
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="high"
        )
        
        tone = adjust_tone(profile)
        assert tone == "normal", "Should return 'normal' for high confidence"
    
    def test_build_final_recommendation_returns_none_for_low_confidence(self):
        """Test that build_final_recommendation returns None when confidence is low."""
        profile = UserProfile(
            interests={"coding"},
            constraints={"weak_in_math"},
            goals={"high_salary"},
            education_level="12th",
            ambiguity_signals={"uncertain"},
            previous_intents=[],
            confidence_level="low"
        )
        
        recommendation = build_final_recommendation(profile, "what should I do?")
        assert recommendation is None, "Should return None for low confidence to avoid strong recommendations"
    
    def test_build_final_recommendation_works_for_normal_confidence(self):
        """Test that build_final_recommendation works normally when confidence is not low."""
        profile = UserProfile(
            interests={"coding"},
            constraints={"weak_in_math"},
            goals={"high_salary"},
            education_level="12th",
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        recommendation = build_final_recommendation(profile, "what should I do?")
        assert recommendation is not None, "Should return recommendation for normal confidence"
        assert "BCA" in recommendation or "MCA" in recommendation, "Should contain program recommendations"
    
    def test_progressive_response_includes_reassuring_language_for_low_confidence(self):
        """Test that progressive response includes reassuring language when confidence is low."""
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"high_salary"},
            education_level=None,
            ambiguity_signals={"uncertain"},
            previous_intents=[],
            confidence_level="low"
        )
        
        response = build_progressive_response(profile, "I'm not sure")
        
        # Check for reassuring language (Requirement 4.5)
        assert "It's okay to be unsure" in response or "we can figure this" in response, \
            "Should include reassuring language for low confidence"
    
    def test_progressive_response_asks_more_questions_for_low_confidence(self):
        """Test that progressive response asks more clarifying questions when confidence is low."""
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"high_salary"},
            education_level=None,
            ambiguity_signals={"uncertain"},
            previous_intents=[],
            confidence_level="low"
        )
        
        response = build_progressive_response(profile, "I'm not sure")
        
        # Count question marks (should have multiple questions)
        question_count = response.count("?")
        assert question_count >= 3, f"Should ask multiple clarifying questions for low confidence, found {question_count}"
    
    def test_progressive_response_softens_recommendations_for_low_confidence(self):
        """Test that progressive response softens recommendations when confidence is low."""
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"quick_job"},
            education_level=None,
            ambiguity_signals={"uncertain"},
            previous_intents=[],
            confidence_level="low"
        )
        
        response = build_progressive_response(profile, "I'm not sure")
        
        # Check for softened language (Requirement 4.3)
        # Should use "could be" or "might be" instead of "makes sense" or "is better"
        assert ("could be" in response or "might be" in response or "worth exploring" in response), \
            "Should use softened language for recommendations when confidence is low"
        
        # Should NOT use strong directive language
        assert "makes sense" not in response and "is better" not in response, \
            "Should avoid strong recommendations when confidence is low"
    
    def test_progressive_response_uses_exploratory_language_for_low_confidence(self):
        """Test that progressive response uses exploratory language when confidence is low."""
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals=set(),
            education_level=None,
            ambiguity_signals={"uncertain"},
            previous_intents=[],
            confidence_level="low"
        )
        
        response = build_progressive_response(profile, "I'm not sure")
        
        # Check for exploratory language (Requirement 4.4)
        assert "Let's explore" in response or "explore this together" in response, \
            "Should use exploratory language for low confidence"
    
    def test_progressive_response_normal_for_high_confidence(self):
        """Test that progressive response uses normal language when confidence is not low."""
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"quick_job"},
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        response = build_progressive_response(profile, "what should I choose")
        
        # Should use normal directive language
        assert "So let's narrow this down" in response, \
            "Should use normal language for medium/high confidence"
        
        # May use stronger recommendations
        assert "makes sense" in response or "is better" in response or "could be" in response, \
            "Should provide clear guidance for normal confidence"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
