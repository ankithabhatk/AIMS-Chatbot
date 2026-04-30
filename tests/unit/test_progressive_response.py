"""
Unit tests for build_progressive_response function.

Tests Task 2.1: Build Progressive Response Function
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.counselor_handler import build_progressive_response
from app.services.conversation_memory import UserProfile


def test_progressive_response_with_interests():
    """Test that response acknowledges interests when present."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should acknowledge interests
    assert "You've mentioned: coding" in response
    # Should add forward step
    assert "So let's narrow this down:" in response
    # Should NOT be generic greeting
    assert "I'm here to help you find the right path" not in response


def test_progressive_response_with_constraints():
    """Test that response acknowledges constraints when present."""
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should acknowledge interests
    assert "You've mentioned: coding" in response
    # Should acknowledge constraints
    assert "You're dealing with: weak in math" in response
    # Should add forward step
    assert "So let's narrow this down:" in response


def test_progressive_response_with_goals():
    """Test that response acknowledges goals when present."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"high_salary"},
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should acknowledge interests
    assert "You've mentioned: coding" in response
    # Should acknowledge goals
    assert "You want: good salary" in response
    # Should add forward step
    assert "So let's narrow this down:" in response


def test_progressive_response_with_all_signals():
    """Test that response acknowledges all signal types when present."""
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary", "quick_job"},
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should acknowledge interests
    assert "You've mentioned: coding" in response
    # Should acknowledge constraints
    assert "You're dealing with: weak in math" in response
    # Should acknowledge goals (at least one)
    assert "You want:" in response
    assert "good salary" in response or "quick job" in response
    # Should add forward step
    assert "So let's narrow this down:" in response


def test_progressive_response_provides_next_steps_for_coding():
    """Test that response provides next steps based on coding interest."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should provide coding-specific paths
    assert "BCA" in response
    assert "MCA" in response
    # Should ask for more info
    assert "What else would help me give you a clear recommendation?" in response


def test_progressive_response_provides_next_steps_for_business():
    """Test that response provides next steps based on business interest."""
    profile = UserProfile(
        interests={"business"},
        constraints=set(),
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should provide business-specific paths
    assert "BBA" in response
    assert "MBA" in response
    # Should ask for more info
    assert "What else would help me give you a clear recommendation?" in response


def test_progressive_response_adapts_to_math_constraint():
    """Test that response adapts advice when math constraint is present."""
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should provide math-adapted advice
    assert "weak in math" in response.lower()
    assert "web/app development" in response.lower() or "less math" in response.lower()


def test_progressive_response_adapts_to_quick_job_goal():
    """Test that response adapts advice when quick job goal is present."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"quick_job"},
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should recommend shorter path
    assert "quick" in response.lower()
    assert "BCA (3 years)" in response


def test_progressive_response_adapts_to_salary_goal():
    """Test that response adapts advice when salary goal is present."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"high_salary"},
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should recommend longer path for higher salary
    assert "salary" in response.lower()
    assert "BCA + MCA" in response or "5 years" in response


def test_progressive_response_handles_multiple_constraints():
    """Test that response handles multiple constraint types."""
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math", "not_great_at_studies"},
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should acknowledge constraints
    assert "You're dealing with:" in response
    # Should mention at least one constraint
    assert "weak in math" in response.lower() or "not strong in studies" in response.lower()


def test_progressive_response_handles_multiple_goals():
    """Test that response handles multiple goal types."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals={"high_salary", "quick_job", "stable_career"},
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should acknowledge goals
    assert "You want:" in response
    # Should mention at least one goal
    assert "good salary" in response.lower() or "quick job" in response.lower() or "stable career" in response.lower()


def test_progressive_response_handles_parental_pressure():
    """Test that response handles parental pressure constraint."""
    profile = UserProfile(
        interests={"coding"},
        constraints={"parental_pressure"},
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should acknowledge parental pressure
    assert "parental pressure" in response.lower()


def test_progressive_response_handles_budget_constraint():
    """Test that response handles budget constraint."""
    profile = UserProfile(
        interests={"coding"},
        constraints={"budget_constraint"},
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should acknowledge budget constraint
    assert "budget" in response.lower()


def test_progressive_response_never_generic_with_profile():
    """Test that response is never generic when profile exists."""
    profile = UserProfile(
        interests={"coding"},
        constraints=set(),
        goals=set(),
    )
    
    response = build_progressive_response(profile, "what should I do?")
    
    # Should NOT contain generic greeting
    assert "I'm here to help you find the right path" not in response
    # Should reference known information
    assert "You've mentioned:" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
