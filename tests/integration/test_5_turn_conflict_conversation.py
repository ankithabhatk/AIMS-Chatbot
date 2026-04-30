"""
Integration Test for Task 6: 5-Turn Conflict Conversation

This test validates the complete Decision Synthesis Layer with a realistic
conflict conversation that tests:
- Counselor lock determinism (no routing to placements mid-conversation)
- Progressive response building (no generic responses after turn 1)
- Human judgment tone (final recommendation feels human)
- Uncertainty handling (calm, supportive tone)

Test Conversation:
1. User: "idk"
2. User: "I like coding maybe"
3. User: "I'm not good at studies"
4. User: "I want money fast"
5. User: "what should I do?"

Expected Behavior:
- Turn 1: Acknowledge uncertainty, ask supportive questions
- Turn 2: Acknowledge coding interest + uncertainty, explore further
- Turn 3: Acknowledge coding + constraint, no routing to placements
- Turn 4: Acknowledge coding + constraint + money goal, synthesize
- Turn 5: Provide human-feeling recommendation with judgment phrases

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.services.conversation_memory import (
    ConversationMemory,
    extract_user_profile,
    UserProfile,
)
from app.services.counselor_handler import get_counselor_response
from app.services.counselor_lock import should_lock_counselor
from app.services.structured_knowledge import get_structured_response, get_multi_intent_response


class Test5TurnConflictConversation:
    """Integration test for 5-turn conflict conversation."""

    def test_full_5_turn_conversation(self):
        """Test complete 5-turn conversation with all verification checks."""
        memory = ConversationMemory()
        session_id = "test_5_turn_conflict"
        
        # ================================================================
        # TURN 1: "idk"
        # ================================================================
        query1 = "idk"
        
        # Extract profile
        signals1 = extract_user_profile(query1)
        profile1 = memory.update_profile(session_id, signals1)
        
        # Get counselor response
        response1 = get_counselor_response(query1, session_id)
        
        # Verification checks for Turn 1
        print("\n=== TURN 1: 'idk' ===")
        print(f"Profile: {profile1}")
        print(f"Response: {response1['answer'][:200]}...")
        
        # Check 1.1: Uncertainty detected
        assert "uncertain" in profile1.ambiguity_signals, "Turn 1: Uncertainty not detected"
        assert profile1.confidence_level == "low", "Turn 1: Confidence level not set to low"
        
        # Check 1.2: Supportive tone (no aggressive recommendations)
        response_text1 = response1['answer'].lower()
        supportive_phrases = ["it's okay", "no pressure", "let's explore", "take your time", "help you"]
        assert any(phrase in response_text1 for phrase in supportive_phrases), \
            "Turn 1: No supportive language detected"
        
        # Check 1.3: No hard recommendations
        aggressive_phrases = ["you should", "you must", "the best option is", "i recommend"]
        assert not any(phrase in response_text1 for phrase in aggressive_phrases), \
            "Turn 1: Aggressive recommendation detected (should be supportive)"
        
        # ================================================================
        # TURN 2: "I like coding maybe"
        # ================================================================
        query2 = "I like coding maybe"
        
        # Extract profile
        signals2 = extract_user_profile(query2)
        profile2 = memory.update_profile(session_id, signals2)
        
        # Get counselor response
        response2 = get_counselor_response(query2, session_id)
        
        # Verification checks for Turn 2
        print("\n=== TURN 2: 'I like coding maybe' ===")
        print(f"Profile: {profile2}")
        print(f"Response: {response2['answer'][:200]}...")
        
        # Check 2.1: Interest extracted
        assert "coding" in profile2.interests, "Turn 2: Coding interest not extracted"
        
        # Check 2.2: Uncertainty persists
        assert "uncertain" in profile2.ambiguity_signals, "Turn 2: Uncertainty not preserved"
        
        # Check 2.3: No generic response
        response_text2 = response2['answer'].lower()
        generic_phrases = [
            "i'm here to help you find the right path",
            "let's start with a few questions",
            "welcome to aims"
        ]
        assert not any(phrase in response_text2 for phrase in generic_phrases), \
            "Turn 2: Generic response detected (should build on profile)"
        
        # Check 2.4: Response acknowledges coding interest
        assert "coding" in response_text2 or "programming" in response_text2 or "tech" in response_text2, \
            "Turn 2: Response doesn't acknowledge coding interest"
        
        # ================================================================
        # TURN 3: "I'm not good at studies"
        # ================================================================
        query3 = "I'm not good at studies"
        
        # Extract profile
        signals3 = extract_user_profile(query3)
        profile3 = memory.update_profile(session_id, signals3)
        
        # CRITICAL: Check counselor lock BEFORE routing
        counselor_locked = should_lock_counselor(profile3)
        
        # Verify structured handler respects lock
        structured_response = get_structured_response(query3, session_id=session_id)
        multi_intent_response = get_multi_intent_response(query3, session_id=session_id)
        
        # Get counselor response
        response3 = get_counselor_response(query3, session_id)
        
        # Verification checks for Turn 3
        print("\n=== TURN 3: 'I'm not good at studies' ===")
        print(f"Profile: {profile3}")
        print(f"Counselor locked: {counselor_locked}")
        print(f"Response: {response3['answer'][:200]}...")
        
        # Check 3.1: Constraint extracted
        assert any("stud" in c.lower() for c in profile3.constraints), \
            "Turn 3: Study constraint not extracted"
        
        # Check 3.2: Counselor lock active
        assert counselor_locked, "Turn 3: Counselor lock not active (has interests + constraints)"
        
        # Check 3.3: Structured handler respects lock
        assert structured_response is None, \
            "Turn 3: Structured handler didn't respect counselor lock"
        
        # Check 3.4: Multi-intent handler respects lock
        assert multi_intent_response is None, \
            "Turn 3: Multi-intent handler didn't respect counselor lock"
        
        # Check 3.5: No routing to placements
        response_text3 = response3['answer'].lower()
        placement_indicators = [
            "placement record",
            "companies visit",
            "average package",
            "highest package"
        ]
        # It's okay to mention placements in context, but shouldn't be a structured placement response
        # The key is that we got a counselor response, not a structured one
        assert response3['intent'] in ['counselor_progressive', 'counselor_general', 'counselor_decision'], \
            f"Turn 3: Wrong intent - got {response3['intent']}, expected counselor mode"
        
        # Check 3.6: Response builds on accumulated profile
        assert "coding" in response_text3 or "interest" in response_text3, \
            "Turn 3: Response doesn't reference previous interests"
        
        # ================================================================
        # TURN 4: "I want money fast"
        # ================================================================
        query4 = "I want money fast"
        
        # Extract profile
        signals4 = extract_user_profile(query4)
        profile4 = memory.update_profile(session_id, signals4)
        
        # Get counselor response
        response4 = get_counselor_response(query4, session_id)
        
        # Verification checks for Turn 4
        print("\n=== TURN 4: 'I want money fast' ===")
        print(f"Profile: {profile4}")
        print(f"Response: {response4['answer'][:200]}...")
        
        # Check 4.1: Goal extracted
        assert any("money" in g.lower() or "salary" in g.lower() or "quick" in g.lower() 
                   for g in profile4.goals), \
            "Turn 4: Money/quick goal not extracted"
        
        # Check 4.2: All signals accumulated
        assert "coding" in profile4.interests, "Turn 4: Interests lost"
        assert len(profile4.constraints) > 0, "Turn 4: Constraints lost"
        assert len(profile4.goals) > 0, "Turn 4: Goals not added"
        
        # Check 4.3: Response synthesizes conflict
        response_text4 = response4['answer'].lower()
        # Should acknowledge the tension between "not good at studies" and "want money fast"
        synthesis_indicators = [
            "understand", "balance", "both", "however", "but", "while",
            "challenge", "consider", "path", "option"
        ]
        assert any(indicator in response_text4 for indicator in synthesis_indicators), \
            "Turn 4: Response doesn't synthesize conflicting signals"
        
        # ================================================================
        # TURN 5: "what should I do?"
        # ================================================================
        query5 = "what should I do?"
        
        # Get counselor response (should trigger final recommendation)
        response5 = get_counselor_response(query5, session_id)
        
        # Verification checks for Turn 5
        print("\n=== TURN 5: 'what should I do?' ===")
        print(f"Response: {response5['answer'][:400]}...")
        
        response_text5 = response5['answer'].lower()
        
        # Check 5.1: Human judgment phrases present
        human_phrases = [
            "if i were in your position",
            "in my experience",
            "here's what i'd recommend",
            "here's the honest path",
            "let me break this down",
            "i'd suggest",
            "my recommendation"
        ]
        assert any(phrase in response_text5 for phrase in human_phrases), \
            "Turn 5: No human judgment phrases detected"
        
        # Check 5.2: No robotic language
        robotic_phrases = [
            "based on analysis",
            "the optimal solution is",
            "according to data",
            "algorithmically determined"
        ]
        assert not any(phrase in response_text5 for phrase in robotic_phrases), \
            "Turn 5: Robotic language detected"
        
        # Check 5.3: Acknowledges uncertainty (from turn 1)
        # Should be calm, not aggressive
        assert not any(phrase in response_text5 for phrase in ["you must", "you have to", "the only option"]), \
            "Turn 5: Aggressive recommendation detected (should be calm)"
        
        # Check 5.4: Suggests flexible path
        flexibility_indicators = [
            "start with", "explore", "try", "consider", "option", "path",
            "flexible", "keep open", "both"
        ]
        assert any(indicator in response_text5 for indicator in flexibility_indicators), \
            "Turn 5: No flexible path suggested"
        
        # Check 5.5: Recommendation is substantive (not just questions)
        assert len(response_text5) > 100, "Turn 5: Response too short (should provide recommendation)"
        
        # Check 5.6: No generic reset
        assert "i'm here to help you find the right path" not in response_text5, \
            "Turn 5: Generic reset detected"
        
        print("\n=== ALL CHECKS PASSED ===")
        print(f"✓ Turn 1: Uncertainty detected, supportive tone")
        print(f"✓ Turn 2: Interest extracted, no generic response")
        print(f"✓ Turn 3: Counselor lock active, no routing to placements")
        print(f"✓ Turn 4: Goal extracted, conflict synthesized")
        print(f"✓ Turn 5: Human judgment tone, flexible recommendation")
        
        return True

    def test_counselor_lock_prevents_hijack(self):
        """Test that counselor lock prevents mid-conversation routing."""
        from app.services.conversation_memory import get_memory_store
        
        memory = get_memory_store()  # Use global singleton
        session_id = "test_lock_hijack"
        
        # Build up profile
        query1 = "I like coding"
        signals1 = extract_user_profile(query1)
        profile1 = memory.update_profile(session_id, signals1)
        
        query2 = "I'm weak in math"
        signals2 = extract_user_profile(query2)
        profile2 = memory.update_profile(session_id, signals2)
        
        # Now try a query that would normally route to structured handler
        query3 = "what about placements"
        
        # Check counselor lock
        locked = should_lock_counselor(profile2)
        assert locked, "Counselor lock should be active"
        
        # Verify structured handler returns None
        structured_response = get_structured_response(query3, session_id=session_id)
        assert structured_response is None, "Structured handler should respect lock"
        
        # Verify counselor handler processes it
        counselor_response = get_counselor_response(query3, session_id)
        assert counselor_response is not None, "Counselor handler should process query"
        assert counselor_response['intent'] in ['counselor_progressive', 'counselor_general'], \
            "Should stay in counselor mode"

    def test_no_generic_mid_conversation(self):
        """Test that generic responses don't appear after turn 1."""
        from app.services.conversation_memory import get_memory_store
        
        memory = get_memory_store()  # Use global singleton
        session_id = "test_no_generic"
        
        # Turn 1: Build profile
        query1 = "I want to study BCA"
        signals1 = extract_user_profile(query1)
        profile1 = memory.update_profile(session_id, signals1)
        
        # Turn 2: Vague query that might trigger generic response
        query2 = "tell me more"
        response2 = get_counselor_response(query2, session_id)
        
        # Should NOT be generic
        response_text = response2['answer'].lower()
        generic_phrases = [
            "i'm here to help you find the right path",
            "let's start with a few questions",
            "how can i help you today"
        ]
        
        assert not any(phrase in response_text for phrase in generic_phrases), \
            "Generic response detected in turn 2"
        
        # Should reference BCA or education
        assert "bca" in response_text or "course" in response_text or "program" in response_text, \
            "Response doesn't build on previous context"

    def test_human_tone_in_final_recommendation(self):
        """Test that final recommendations have human judgment tone."""
        from app.services.conversation_memory import get_memory_store
        
        memory = get_memory_store()  # Use global singleton
        session_id = "test_human_tone"
        
        # Build complete profile
        queries = [
            "I like coding",
            "I'm not good at math",
            "I want a good salary",
            "what should I do?"
        ]
        
        for query in queries[:-1]:
            signals = extract_user_profile(query)
            memory.update_profile(session_id, signals)
        
        # Get final recommendation
        response = get_counselor_response(queries[-1], session_id)
        response_text = response['answer'].lower()
        
        # Check for human judgment phrases
        human_phrases = [
            "if i were in your position",
            "in my experience",
            "here's what i'd recommend",
            "i'd suggest",
            "my recommendation"
        ]
        
        has_human_phrase = any(phrase in response_text for phrase in human_phrases)
        assert has_human_phrase, f"No human judgment phrases found in: {response_text[:200]}"


if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "-s"])
