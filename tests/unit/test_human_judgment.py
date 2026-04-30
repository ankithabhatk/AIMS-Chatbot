"""
Unit tests for Task 3.1: Add Human Judgment Layer to build_final_recommendation

Tests that build_final_recommendation includes human judgment phrases
in the final recommendations as specified in Requirements 3.1, 3.2, 3.3.
"""

import pytest
from backend.app.services.conversation_memory import UserProfile, build_final_recommendation


class TestHumanJudgmentLayer:
    """Test human judgment phrases in final recommendations."""
    
    def test_conflict_resolution_has_human_judgment(self):
        """Test that conflict resolution recommendation includes 'If I were in your position' phrase."""
        # Create profile with conflicting goals (high salary + quick job)
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"high_salary", "quick_job"},
            education_level="12th",
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None, "Expected recommendation for coding interest with conflicting goals"
        
        # Verify human judgment phrase is present
        assert "If I were in your position" in recommendation, \
            "Expected 'If I were in your position' phrase in conflict resolution recommendation"
        
        # Verify separator line before human judgment
        assert "---" in recommendation, \
            "Expected separator line before human judgment phrase"
    
    def test_quick_job_recommendation_has_human_judgment(self):
        """Test that quick job recommendation includes human judgment phrase."""
        # Create profile with quick job goal
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"quick_job"},
            education_level="12th",
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None, "Expected recommendation for coding interest with quick job goal"
        
        # Verify human judgment phrase is present
        assert "If I were in your position" in recommendation, \
            "Expected 'If I were in your position' phrase in quick job recommendation"
    
    def test_high_salary_recommendation_has_human_judgment(self):
        """Test that high salary recommendation includes human judgment phrase."""
        # Create profile with high salary goal
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"high_salary"},
            education_level="12th",
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None, "Expected recommendation for coding interest with high salary goal"
        
        # Verify human judgment phrase is present
        assert "If I were in your position" in recommendation, \
            "Expected 'If I were in your position' phrase in high salary recommendation"
    
    def test_business_recommendation_has_human_judgment(self):
        """Test that business recommendation includes human judgment phrase."""
        # Create profile with business interest
        profile = UserProfile(
            interests={"business"},
            constraints=set(),
            goals={"quick_job"},
            education_level="12th",
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None, "Expected recommendation for business interest"
        
        # Verify human judgment phrase is present
        assert "If I were in your position" in recommendation, \
            "Expected 'If I were in your position' phrase in business recommendation"
    
    def test_recommendation_has_conversational_language(self):
        """Test that recommendations use conversational language like 'Here's the honest path'."""
        # Create profile with coding interest
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"quick_job"},
            education_level="12th",
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None, "Expected recommendation for coding interest"
        
        # Verify conversational language is present
        assert "Here's the honest path" in recommendation, \
            "Expected 'Here's the honest path' conversational phrase in recommendation"
    
    def test_recommendation_avoids_robotic_language(self):
        """Test that recommendations avoid robotic language like 'Based on analysis'."""
        # Create profile with coding interest
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals={"high_salary"},
            education_level="12th",
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None, "Expected recommendation for coding interest"
        
        # Verify robotic language is NOT present
        robotic_phrases = ["Based on analysis", "The optimal solution is", "According to data", "Algorithmically determined"]
        for phrase in robotic_phrases:
            assert phrase not in recommendation, \
                f"Expected recommendation to avoid robotic phrase: '{phrase}'"
    
    def test_no_recommendation_without_interests(self):
        """Test that no recommendation is generated without interests."""
        # Create profile without interests
        profile = UserProfile(
            interests=set(),
            constraints={"weak_in_math"},
            goals={"high_salary"},
            education_level="12th",
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify no recommendation is generated
        assert recommendation is None, "Expected None when profile has no interests"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
