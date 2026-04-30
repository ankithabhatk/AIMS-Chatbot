"""
Unit tests for Task 1.2: Apply Lock Across Routing

Tests that counselor lock is properly integrated across routing layers:
- get_structured_response() checks lock before returning
- get_multi_intent_response() checks lock before returning
- chat.py passes session_id to structured handler
"""

import pytest
from unittest.mock import Mock, patch
from app.services.structured_knowledge import get_structured_response, get_multi_intent_response
from app.services.conversation_memory import UserProfile


class TestCounselorLockIntegration:
    """Test counselor lock integration in routing layers."""
    
    def test_structured_response_respects_lock_with_interests(self):
        """Test that get_structured_response returns None when user has interests."""
        # Create a profile with interests (should trigger lock)
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals=set(),
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Mock the memory store at the conversation_memory module level
        with patch('app.services.conversation_memory.get_memory_store') as mock_memory:
            mock_store = Mock()
            mock_store.get_profile.return_value = profile
            mock_memory.return_value = mock_store
            
            # Call get_structured_response with a fees query (normally would return structured response)
            result = get_structured_response("what are the fees for BCA?", session_id="test-session")
            
            # Should return None because counselor lock is active
            assert result is None, "Expected None when counselor lock is active (user has interests)"
    
    def test_structured_response_respects_lock_with_constraints(self):
        """Test that get_structured_response returns None when user has constraints."""
        # Create a profile with constraints (should trigger lock)
        profile = UserProfile(
            interests=set(),
            constraints={"weak_in_math"},
            goals=set(),
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Mock the memory store at the conversation_memory module level
        with patch('app.services.conversation_memory.get_memory_store') as mock_memory:
            mock_store = Mock()
            mock_store.get_profile.return_value = profile
            mock_memory.return_value = mock_store
            
            # Call get_structured_response with a fees query
            result = get_structured_response("what are the fees for BCA?", session_id="test-session")
            
            # Should return None because counselor lock is active
            assert result is None, "Expected None when counselor lock is active (user has constraints)"
    
    def test_structured_response_respects_lock_with_goals(self):
        """Test that get_structured_response returns None when user has goals."""
        # Create a profile with goals (should trigger lock)
        profile = UserProfile(
            interests=set(),
            constraints=set(),
            goals={"high_salary"},
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Mock the memory store at the conversation_memory module level
        with patch('app.services.conversation_memory.get_memory_store') as mock_memory:
            mock_store = Mock()
            mock_store.get_profile.return_value = profile
            mock_memory.return_value = mock_store
            
            # Call get_structured_response with a fees query
            result = get_structured_response("what are the fees for BCA?", session_id="test-session")
            
            # Should return None because counselor lock is active
            assert result is None, "Expected None when counselor lock is active (user has goals)"
    
    def test_structured_response_works_without_lock(self):
        """Test that get_structured_response works normally when no lock is active."""
        # Create an empty profile (no lock)
        profile = UserProfile(
            interests=set(),
            constraints=set(),
            goals=set(),
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Mock the memory store at the conversation_memory module level
        with patch('app.services.conversation_memory.get_memory_store') as mock_memory:
            mock_store = Mock()
            mock_store.get_profile.return_value = profile
            mock_memory.return_value = mock_store
            
            # Call get_structured_response with a fees query
            result = get_structured_response("what are the fees for BCA?", session_id="test-session")
            
            # Should return structured response (not None)
            assert result is not None, "Expected structured response when no counselor lock"
            assert result.get("intent") == "fees", "Expected fees intent"
    
    def test_multi_intent_respects_lock_with_interests(self):
        """Test that get_multi_intent_response returns None when user has interests."""
        # Create a profile with interests (should trigger lock)
        profile = UserProfile(
            interests={"coding"},
            constraints=set(),
            goals=set(),
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Mock the memory store at the conversation_memory module level
        with patch('app.services.conversation_memory.get_memory_store') as mock_memory:
            mock_store = Mock()
            mock_store.get_profile.return_value = profile
            mock_memory.return_value = mock_store
            
            # Call get_multi_intent_response with a multi-intent query
            result = get_multi_intent_response("what are the fees and hostel facilities?", session_id="test-session")
            
            # Should return None because counselor lock is active
            assert result is None, "Expected None when counselor lock is active (user has interests)"
    
    def test_multi_intent_works_without_lock(self):
        """Test that get_multi_intent_response works normally when no lock is active."""
        # Create an empty profile (no lock)
        profile = UserProfile(
            interests=set(),
            constraints=set(),
            goals=set(),
            education_level=None,
            ambiguity_signals=set(),
            previous_intents=[],
            confidence_level="medium"
        )
        
        # Mock the memory store at the conversation_memory module level
        with patch('app.services.conversation_memory.get_memory_store') as mock_memory:
            mock_store = Mock()
            mock_store.get_profile.return_value = profile
            mock_memory.return_value = mock_store
            
            # Call get_multi_intent_response with a multi-intent query
            result = get_multi_intent_response("what are the fees and hostel?", session_id="test-session")
            
            # Should return multi-intent response (not None)
            assert result is not None, "Expected multi-intent response when no counselor lock"
            assert "fees" in result.get("intent", ""), "Expected fees in intent"
            assert "hostel" in result.get("intent", ""), "Expected hostel in intent"
    
    def test_structured_response_without_session_id(self):
        """Test that get_structured_response works when no session_id is provided."""
        # Call without session_id (should work normally, no lock check)
        result = get_structured_response("what are the fees for BCA?", session_id=None)
        
        # Should return structured response (not None)
        assert result is not None, "Expected structured response when no session_id provided"
        assert result.get("intent") == "fees", "Expected fees intent"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
