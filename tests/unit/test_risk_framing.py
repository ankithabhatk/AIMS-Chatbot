"""
Unit tests for Task 3.2: Add Risk Framing to Recommendations

Tests that build_final_recommendation includes risk awareness phrases
in the trade-off sections as specified in Requirements 3.4.
"""

import pytest
from backend.app.services.conversation_memory import UserProfile, build_final_recommendation


class TestRiskFraming:
    """Test suite for risk framing in recommendations."""

    def test_conflict_resolution_has_risk_framing(self):
        """Test that conflict resolution (high salary + quick job) includes risk framing."""
        # Profile with conflicting goals
        profile = UserProfile(
            interests={"coding"},
            goals={"high_salary", "quick_job"},
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None
        
        # Verify risk framing phrase is present
        assert "The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term" in recommendation
        
        # Verify it appears in the conflict section (early in the recommendation)
        lines = recommendation.split('\n')
        risk_line_index = None
        for i, line in enumerate(lines):
            if "The risk with rushing into a decision" in line:
                risk_line_index = i
                break
        
        assert risk_line_index is not None, "Risk framing phrase not found"
        # Should appear before the options section
        assert risk_line_index < 20, "Risk framing should appear early in conflict resolution"

    def test_quick_job_path_has_risk_framing(self):
        """Test that quick job path includes risk framing in trade-off section."""
        # Profile with quick job goal only
        profile = UserProfile(
            interests={"coding"},
            goals={"quick_job"},
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None
        
        # Verify risk framing phrase is present
        assert "The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term" in recommendation
        
        # Verify it appears after the trade-off section
        assert "**Trade-off**" in recommendation
        trade_off_index = recommendation.index("**Trade-off**")
        risk_index = recommendation.index("The risk with rushing into a decision")
        assert risk_index > trade_off_index, "Risk framing should appear after trade-off"

    def test_high_salary_path_has_risk_framing(self):
        """Test that high salary path includes risk framing in trade-off section."""
        # Profile with high salary goal
        profile = UserProfile(
            interests={"coding"},
            goals={"high_salary"},
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None
        
        # Verify risk framing phrase is present
        assert "The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term" in recommendation
        
        # Verify it appears after the trade-off section
        assert "**Trade-off**" in recommendation
        trade_off_index = recommendation.index("**Trade-off**")
        risk_index = recommendation.index("The risk with rushing into a decision")
        assert risk_index > trade_off_index, "Risk framing should appear after trade-off"

    def test_business_path_has_risk_framing(self):
        """Test that business interest path includes risk framing."""
        # Profile with business interest
        profile = UserProfile(
            interests={"business"},
            goals={"quick_job"},
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None
        
        # Verify risk framing phrase is present
        assert "The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term" in recommendation
        
        # Verify it appears after the trade-off section
        assert "**Trade-off**" in recommendation
        trade_off_index = recommendation.index("**Trade-off**")
        risk_index = recommendation.index("The risk with rushing into a decision")
        assert risk_index > trade_off_index, "Risk framing should appear after trade-off"

    def test_risk_framing_uses_empathetic_language(self):
        """Test that risk framing uses empathetic language as per Requirements 3.4."""
        # Profile with coding interest and goals
        profile = UserProfile(
            interests={"coding"},
            goals={"high_salary", "quick_job"},
        )
        
        # Build recommendation
        recommendation = build_final_recommendation(profile, "what should I do?")
        
        # Verify recommendation exists
        assert recommendation is not None
        
        # Verify the risk framing phrase is empathetic (uses "you" and "your")
        assert "you might lock yourself" in recommendation.lower()
        
        # Verify it's positioned in a trade-off context
        assert "**Trade-off**" in recommendation or "competing goals" in recommendation

    def test_all_coding_paths_have_risk_framing(self):
        """Test that all coding recommendation paths include risk framing."""
        # Test different goal combinations
        test_cases = [
            {"high_salary", "quick_job"},  # Conflict
            {"quick_job"},                  # Quick job only
            {"high_salary"},                # High salary only
        ]
        
        for goals in test_cases:
            profile = UserProfile(
                interests={"coding"},
                goals=goals,
            )
            
            recommendation = build_final_recommendation(profile, "what should I do?")
            
            assert recommendation is not None, f"No recommendation for goals: {goals}"
            assert "The risk with rushing into a decision is you might lock yourself into something that doesn't fit long-term" in recommendation, \
                f"Risk framing missing for goals: {goals}"
