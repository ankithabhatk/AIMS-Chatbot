"""
Integration tests for Task 4.1: Detect Low Confidence Signals

Tests verify end-to-end behavior:
- Uncertainty signals are extracted and stored in session profile
- Profile updates correctly accumulate ambiguity signals
- Confidence level is set to "low" when uncertainty detected
"""

import pytest
from backend.app.services.conversation_memory import (
    ConversationMemory,
    extract_user_profile,
    UserProfile,
)


class TestUncertaintyIntegration:
    """Integration tests for uncertainty detection in conversation flow."""

    def test_uncertainty_stored_in_session_profile(self):
        """Test that uncertainty signals are stored in session profile."""
        memory = ConversationMemory()
        session_id = "test_session_1"
        
        # User expresses uncertainty
        query = "I'm not sure what to do after 12th"
        signals = extract_user_profile(query)
        
        # Update profile
        profile = memory.update_profile(session_id, signals)
        
        # Verify uncertainty is stored
        assert "uncertain" in profile.ambiguity_signals
        assert profile.confidence_level == "low"

    def test_uncertainty_persists_across_turns(self):
        """Test that uncertainty signals persist across conversation turns."""
        memory = ConversationMemory()
        session_id = "test_session_2"
        
        # Turn 1: User expresses interest
        query1 = "I like coding"
        signals1 = extract_user_profile(query1)
        profile1 = memory.update_profile(session_id, signals1)
        
        # Turn 2: User expresses uncertainty
        query2 = "but I'm not sure if it's right for me"
        signals2 = extract_user_profile(query2)
        profile2 = memory.update_profile(session_id, signals2)
        
        # Verify both interest and uncertainty are stored
        assert "coding" in profile2.interests
        assert "uncertain" in profile2.ambiguity_signals
        assert profile2.confidence_level == "low"

    def test_multiple_uncertainty_signals_accumulate(self):
        """Test that multiple uncertainty expressions accumulate."""
        memory = ConversationMemory()
        session_id = "test_session_3"
        
        # Turn 1: First uncertainty
        query1 = "idk what to choose"
        signals1 = extract_user_profile(query1)
        profile1 = memory.update_profile(session_id, signals1)
        
        # Turn 2: Second uncertainty
        query2 = "maybe I should try BCA"
        signals2 = extract_user_profile(query2)
        profile2 = memory.update_profile(session_id, signals2)
        
        # Verify uncertainty persists (set deduplication means still one "uncertain")
        assert "uncertain" in profile2.ambiguity_signals
        assert profile2.confidence_level == "low"

    def test_confidence_level_updates_to_low(self):
        """Test that confidence level updates from default to low."""
        memory = ConversationMemory()
        session_id = "test_session_4"
        
        # Turn 1: Confident query (default confidence)
        query1 = "I want to do BCA"
        signals1 = extract_user_profile(query1)
        profile1 = memory.update_profile(session_id, signals1)
        
        # Initial confidence should be medium (default)
        assert profile1.confidence_level == "medium"
        
        # Turn 2: Uncertain query
        query2 = "but I'm confused about the fees"
        signals2 = extract_user_profile(query2)
        profile2 = memory.update_profile(session_id, signals2)
        
        # Confidence should now be low
        assert profile2.confidence_level == "low"
        assert "uncertain" in profile2.ambiguity_signals

    def test_profile_retrieval_preserves_uncertainty(self):
        """Test that retrieving profile preserves uncertainty signals."""
        memory = ConversationMemory()
        session_id = "test_session_5"
        
        # Store uncertainty in profile
        query = "I'm not sure which course is better"
        signals = extract_user_profile(query)
        memory.update_profile(session_id, signals)
        
        # Retrieve profile
        retrieved_profile = memory.get_profile(session_id)
        
        # Verify uncertainty is preserved
        assert "uncertain" in retrieved_profile.ambiguity_signals
        assert retrieved_profile.confidence_level == "low"

    def test_uncertainty_with_interests_and_constraints(self):
        """Test uncertainty detection alongside other signal types."""
        memory = ConversationMemory()
        session_id = "test_session_6"
        
        # Complex query with multiple signal types
        query = "I like coding but I'm weak in math and not sure if BCA is right"
        signals = extract_user_profile(query)
        profile = memory.update_profile(session_id, signals)
        
        # Verify all signal types are captured
        assert "coding" in profile.interests
        assert any("math" in c for c in profile.constraints)
        assert "uncertain" in profile.ambiguity_signals
        assert profile.confidence_level == "low"

    def test_profile_to_dict_includes_uncertainty(self):
        """Test that profile serialization includes uncertainty signals."""
        memory = ConversationMemory()
        session_id = "test_session_7"
        
        # Create profile with uncertainty
        query = "idk what to do"
        signals = extract_user_profile(query)
        profile = memory.update_profile(session_id, signals)
        
        # Convert to dict
        profile_dict = profile.to_dict()
        
        # Verify uncertainty is in dict
        assert "uncertain" in profile_dict["ambiguity_signals"]
        assert profile_dict["confidence_level"] == "low"

    def test_profile_from_dict_restores_uncertainty(self):
        """Test that profile deserialization restores uncertainty signals."""
        # Create dict with uncertainty
        profile_dict = {
            "interests": ["coding"],
            "constraints": [],
            "goals": [],
            "education_level": None,
            "ambiguity_signals": ["uncertain"],
            "previous_intents": [],
            "confidence_level": "low",
        }
        
        # Restore from dict
        profile = UserProfile.from_dict(profile_dict)
        
        # Verify uncertainty is restored
        assert "uncertain" in profile.ambiguity_signals
        assert profile.confidence_level == "low"

    def test_clear_session_removes_uncertainty(self):
        """Test that clearing session removes uncertainty signals."""
        memory = ConversationMemory()
        session_id = "test_session_8"
        
        # Create profile with uncertainty
        query = "I'm confused about my options"
        signals = extract_user_profile(query)
        memory.update_profile(session_id, signals)
        
        # Clear session
        memory.clear_session(session_id)
        
        # Get profile (should be new empty profile)
        new_profile = memory.get_profile(session_id)
        
        # Verify uncertainty is gone
        assert len(new_profile.ambiguity_signals) == 0
        assert new_profile.confidence_level == "medium"  # default


class TestUncertaintyKeywordCoverage:
    """Test all required uncertainty keywords from task specification."""

    def test_all_required_keywords_detected(self):
        """Test that all keywords from task spec are detected."""
        # Keywords from task spec: "idk", "maybe", "not sure", "confused", "don't know"
        test_cases = [
            ("idk what to choose", "idk"),
            ("maybe I should try BCA", "maybe"),
            ("I'm not sure about this", "not sure"),
            ("I'm confused about my options", "confused"),
            ("I don't know what to do", "don't know"),
        ]
        
        for query, keyword in test_cases:
            signals = extract_user_profile(query)
            assert "uncertain" in signals["ambiguity_signals"], f"Failed to detect: {keyword}"
            assert signals["confidence_level"] == "low", f"Failed to set low confidence for: {keyword}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
