"""
Integration test for build_progressive_response with _handle_general_exploration.

Tests that the progressive response function is properly integrated into the counselor handler.
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.counselor_handler import _handle_general_exploration
from app.services.conversation_memory import UserProfile


def test_general_exploration_uses_progressive_response_with_profile():
    """Test that _handle_general_exploration uses progressive response when profile exists."""
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
    )
    
    result = _handle_general_exploration("what should I do?", profile)
    
    # Should return dict with answer
    assert isinstance(result, dict)
    assert "answer" in result
    
    answer = result["answer"]
    
    # Should use progressive response (acknowledge signals)
    assert "You've mentioned: coding" in answer
    assert "You're dealing with: weak in math" in answer
    assert "You want: good salary" in answer
    assert "So let's narrow this down:" in answer
    
    # Should NOT be generic
    assert "I'm here to help you find the right path" not in answer


def test_general_exploration_uses_generic_without_profile():
    """Test that _handle_general_exploration uses generic response when no profile exists."""
    profile = UserProfile()  # Empty profile
    
    result = _handle_general_exploration("what should I do?", profile)
    
    # Should return dict with answer
    assert isinstance(result, dict)
    assert "answer" in result
    
    answer = result["answer"]
    
    # Should use generic response
    assert "I'm here to help you find the right path" in answer
    
    # Should NOT use progressive response format
    assert "You've mentioned:" not in answer
    assert "You're dealing with:" not in answer


def test_general_exploration_returns_correct_metadata():
    """Test that _handle_general_exploration returns correct metadata."""
    profile = UserProfile(interests={"coding"})
    
    result = _handle_general_exploration("what should I do?", profile)
    
    # Should have correct metadata
    assert result["intent"] == "counselor_general"
    assert result["confidence"] == 1.0
    assert result["mode"] == "counselor"
    assert "sources" in result
    assert len(result["sources"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
