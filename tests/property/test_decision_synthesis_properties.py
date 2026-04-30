"""
Property-Based Tests for Decision Synthesis Final Polish

This module contains property-based tests using the hypothesis library to verify
universal correctness guarantees across the Decision Synthesis Layer.

Each property test runs with minimum 100 iterations to explore the input space
and catch edge cases that unit tests might miss.

Properties tested:
1. Counselor Lock Activation
2. Structured Handler Respects Lock
3. Multi-Intent Handler Respects Lock
4. Profile Acknowledgment in Responses
5. No Generic Responses with Profile
6. Human Judgment Phrases Present
7. Session Memory Round-Trip
8. Counselor Lock Idempotence
9. Profile Accumulation Monotonicity
"""

import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from hypothesis import given, strategies as st, settings
import pytest

from app.services.counselor_lock import should_lock_counselor
from app.services.conversation_memory import UserProfile


# ============================================================================
# PROPERTY 1: Counselor Lock Activation
# ============================================================================
# **Validates: Requirements 1.1, 1.3**
# For any profile with signals (interests OR constraints OR goals), 
# counselor lock is active

@settings(max_examples=100)
@given(
    interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr"
        ]),
        min_size=0,
        max_size=5
    ),
    constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints"
        ]),
        min_size=0,
        max_size=5
    ),
    goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job"
        ]),
        min_size=0,
        max_size=5
    ),
    ambiguity_signals=st.sets(
        st.sampled_from([
            "confused", "not_sure", "maybe", "idk", "uncertain"
        ]),
        min_size=0,
        max_size=3
    )
)
def test_property_counselor_lock_activation(interests, constraints, goals, ambiguity_signals):
    """
    Property 1: Counselor Lock Activation
    
    **Validates: Requirements 1.1, 1.3**
    
    For any profile with at least one signal (interests OR constraints OR goals 
    OR ambiguity), the counselor lock SHALL be active.
    
    For any profile with NO signals, the counselor lock SHALL be inactive.
    """
    # Create profile with generated signals
    profile = UserProfile(
        interests=interests,
        constraints=constraints,
        goals=goals,
        ambiguity_signals=ambiguity_signals
    )
    
    # Determine if profile has any signals
    has_signals = bool(
        profile.interests or 
        profile.constraints or 
        profile.goals or 
        profile.ambiguity_signals
    )
    
    # Property: Lock is active if and only if profile has signals
    lock_active = should_lock_counselor(profile)
    
    assert lock_active == has_signals, (
        f"Counselor lock mismatch: "
        f"has_signals={has_signals}, lock_active={lock_active}, "
        f"profile={profile.to_dict()}"
    )


# ============================================================================
# EDGE CASE TESTS: Specific scenarios to complement property tests
# ============================================================================

def test_counselor_lock_with_only_interests():
    """Edge case: Profile with only interests should activate lock."""
    profile = UserProfile(interests={"coding"})
    assert should_lock_counselor(profile) is True


def test_counselor_lock_with_only_constraints():
    """Edge case: Profile with only constraints should activate lock."""
    profile = UserProfile(constraints={"weak_in_math"})
    assert should_lock_counselor(profile) is True


def test_counselor_lock_with_only_goals():
    """Edge case: Profile with only goals should activate lock."""
    profile = UserProfile(goals={"high_salary"})
    assert should_lock_counselor(profile) is True


def test_counselor_lock_with_only_ambiguity():
    """Edge case: Profile with only ambiguity signals should activate lock."""
    profile = UserProfile(ambiguity_signals={"confused"})
    assert should_lock_counselor(profile) is True


def test_counselor_lock_empty_profile():
    """Edge case: Empty profile should NOT activate lock."""
    profile = UserProfile()
    assert should_lock_counselor(profile) is False


def test_counselor_lock_with_all_signals():
    """Edge case: Profile with all signal types should activate lock."""
    profile = UserProfile(
        interests={"coding", "business"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        ambiguity_signals={"confused"}
    )
    assert should_lock_counselor(profile) is True


def test_counselor_lock_with_education_only():
    """Edge case: Profile with only education level should NOT activate lock."""
    profile = UserProfile(education_level="12th")
    assert should_lock_counselor(profile) is False


# ============================================================================
# PROPERTY 2: Structured Handler Respects Lock
# ============================================================================
# **Validates: Requirements 1.1, 1.2, 1.3**
# For any session with active lock, get_structured_response() returns None

@settings(max_examples=100)
@given(
    interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr"
        ]),
        min_size=1,  # At least one signal to activate lock
        max_size=5
    ),
    constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints"
        ]),
        min_size=0,
        max_size=3
    ),
    goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job"
        ]),
        min_size=0,
        max_size=3
    ),
    query=st.sampled_from([
        "what are the fees",
        "tell me about MBA fees",
        "BCA course details",
        "admission process",
        "what courses do you offer",
        "hostel facilities",
        "placement statistics",
        "contact information"
    ])
)
def test_property_structured_handler_respects_lock(interests, constraints, goals, query):
    """
    Property 2: Structured Handler Respects Lock
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    For any session with an active counselor lock, calling get_structured_response()
    with that session_id SHALL return None.
    
    This ensures users stay in counselor mode and don't get interrupted with
    structured responses mid-conversation.
    """
    from app.services.structured_knowledge import get_structured_response
    from app.services.conversation_memory import get_memory_store
    
    # Create profile with signals (will activate lock)
    profile = UserProfile(
        interests=interests,
        constraints=constraints,
        goals=goals
    )
    
    # Verify lock is active
    assert should_lock_counselor(profile) is True, "Lock should be active with signals"
    
    # Create mock session with this profile
    session_id = f"test_session_{hash((frozenset(interests), frozenset(constraints), frozenset(goals)))}"
    memory = get_memory_store()
    
    # Store profile in memory using internal API
    memory._sessions[session_id] = profile
    
    try:
        # Call get_structured_response with session_id
        result = get_structured_response(query, session_id=session_id)
        
        # Property: Should return None when lock is active
        assert result is None, (
            f"Structured handler should return None when counselor lock is active. "
            f"Got: {result}, Query: {query}, Profile: {profile.to_dict()}"
        )
    finally:
        # Clean up test session
        if session_id in memory._sessions:
            del memory._sessions[session_id]


# ============================================================================
# PROPERTY 3: Multi-Intent Handler Respects Lock
# ============================================================================
# **Validates: Requirements 1.1, 1.2, 1.3**
# For any session with active lock, get_multi_intent_response() returns None

@settings(max_examples=100)
@given(
    interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr"
        ]),
        min_size=1,  # At least one signal to activate lock
        max_size=5
    ),
    constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints"
        ]),
        min_size=0,
        max_size=3
    ),
    goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job"
        ]),
        min_size=0,
        max_size=3
    ),
    query=st.sampled_from([
        "fees and hostel",
        "admission and courses",
        "MBA fees and placement",
        "hostel and campus facilities",
        "courses and admission process",
        "fees and scholarship",
        "placement and hostel"
    ])
)
def test_property_multi_intent_handler_respects_lock(interests, constraints, goals, query):
    """
    Property 3: Multi-Intent Handler Respects Lock
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    For any session with an active counselor lock, calling get_multi_intent_response()
    with that session_id SHALL return None.
    
    This ensures users stay in counselor mode even when asking multi-intent queries
    like "fees and hostel" during their counselor conversation.
    """
    from app.services.structured_knowledge import get_multi_intent_response
    from app.services.conversation_memory import get_memory_store
    
    # Create profile with signals (will activate lock)
    profile = UserProfile(
        interests=interests,
        constraints=constraints,
        goals=goals
    )
    
    # Verify lock is active
    assert should_lock_counselor(profile) is True, "Lock should be active with signals"
    
    # Create mock session with this profile
    session_id = f"test_session_{hash((frozenset(interests), frozenset(constraints), frozenset(goals)))}"
    memory = get_memory_store()
    
    # Store profile in memory using internal API
    memory._sessions[session_id] = profile
    
    try:
        # Call get_multi_intent_response with session_id
        result = get_multi_intent_response(query, session_id=session_id)
        
        # Property: Should return None when lock is active
        assert result is None, (
            f"Multi-intent handler should return None when counselor lock is active. "
            f"Got: {result}, Query: {query}, Profile: {profile.to_dict()}"
        )
    finally:
        # Clean up test session
        if session_id in memory._sessions:
            del memory._sessions[session_id]


# ============================================================================
# EDGE CASE TESTS: Handlers respect lock in specific scenarios
# ============================================================================

def test_structured_handler_respects_lock_with_only_interests():
    """Edge case: Structured handler returns None when profile has only interests."""
    from app.services.structured_knowledge import get_structured_response
    from app.services.conversation_memory import get_memory_store
    
    profile = UserProfile(interests={"coding"})
    session_id = "test_interests_only"
    
    memory = get_memory_store()
    memory._sessions[session_id] = profile
    
    try:
        result = get_structured_response("what are the fees", session_id=session_id)
        assert result is None
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_structured_handler_respects_lock_with_only_constraints():
    """Edge case: Structured handler returns None when profile has only constraints."""
    from app.services.structured_knowledge import get_structured_response
    from app.services.conversation_memory import get_memory_store
    
    profile = UserProfile(constraints={"weak_in_math"})
    session_id = "test_constraints_only"
    
    memory = get_memory_store()
    memory._sessions[session_id] = profile
    
    try:
        result = get_structured_response("MBA courses", session_id=session_id)
        assert result is None
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_structured_handler_respects_lock_with_only_goals():
    """Edge case: Structured handler returns None when profile has only goals."""
    from app.services.structured_knowledge import get_structured_response
    from app.services.conversation_memory import get_memory_store
    
    profile = UserProfile(goals={"high_salary"})
    session_id = "test_goals_only"
    
    memory = get_memory_store()
    memory._sessions[session_id] = profile
    
    try:
        result = get_structured_response("admission process", session_id=session_id)
        assert result is None
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_multi_intent_handler_respects_lock_with_only_interests():
    """Edge case: Multi-intent handler returns None when profile has only interests."""
    from app.services.structured_knowledge import get_multi_intent_response
    from app.services.conversation_memory import get_memory_store
    
    profile = UserProfile(interests={"business"})
    session_id = "test_multi_interests"
    
    memory = get_memory_store()
    memory._sessions[session_id] = profile
    
    try:
        result = get_multi_intent_response("fees and hostel", session_id=session_id)
        assert result is None
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_multi_intent_handler_respects_lock_with_all_signals():
    """Edge case: Multi-intent handler returns None when profile has all signal types."""
    from app.services.structured_knowledge import get_multi_intent_response
    from app.services.conversation_memory import get_memory_store
    
    profile = UserProfile(
        interests={"coding", "business"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        ambiguity_signals={"confused"}
    )
    session_id = "test_multi_all_signals"
    
    memory = get_memory_store()
    memory._sessions[session_id] = profile
    
    try:
        result = get_multi_intent_response("admission and courses", session_id=session_id)
        assert result is None
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_structured_handler_works_without_lock():
    """Edge case: Structured handler returns response when no lock is active."""
    from app.services.structured_knowledge import get_structured_response
    from app.services.conversation_memory import get_memory_store
    
    profile = UserProfile()  # Empty profile - no lock
    session_id = "test_no_lock"
    
    memory = get_memory_store()
    memory._sessions[session_id] = profile
    
    try:
        result = get_structured_response("what are the fees", session_id=session_id)
        # Should return a response (not None) since no lock is active
        assert result is not None
        assert result.get("intent") == "fees"
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_multi_intent_handler_works_without_lock():
    """Edge case: Multi-intent handler returns response when no lock is active."""
    from app.services.structured_knowledge import get_multi_intent_response
    from app.services.conversation_memory import get_memory_store
    
    profile = UserProfile()  # Empty profile - no lock
    session_id = "test_multi_no_lock"
    
    memory = get_memory_store()
    memory._sessions[session_id] = profile
    
    try:
        result = get_multi_intent_response("fees and hostel", session_id=session_id)
        # Should return a response (not None) since no lock is active
        assert result is not None
        assert "fees" in result.get("intent", "").lower() or "hostel" in result.get("intent", "").lower()
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


# ============================================================================
# PROPERTY 4: Profile Acknowledgment in Responses
# ============================================================================
# **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
# For any profile with signals, response references those signals

@settings(max_examples=100)
@given(
    interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr"
        ]),
        min_size=0,
        max_size=3
    ),
    constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints"
        ]),
        min_size=0,
        max_size=3
    ),
    goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job"
        ]),
        min_size=0,
        max_size=3
    ),
    query=st.sampled_from([
        "what should I do",
        "help me decide",
        "what do you recommend",
        "which course is best",
        "tell me more",
        "what are my options",
        "I need guidance"
    ])
)
def test_property_profile_acknowledgment_in_responses(interests, constraints, goals, query):
    """
    Property 4: Profile Acknowledgment in Responses
    
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    
    For any profile with signals (interests, constraints, or goals), the counselor
    response SHALL reference at least one of those signals in the output text.
    
    This ensures the system builds forward from accumulated context rather than
    providing generic responses that ignore what the user has already shared.
    """
    from app.services.counselor_handler import build_progressive_response
    
    # Create profile with generated signals
    profile = UserProfile(
        interests=interests,
        constraints=constraints,
        goals=goals
    )
    
    # Only test profiles that have at least one signal
    has_signals = bool(profile.interests or profile.constraints or profile.goals)
    
    if not has_signals:
        # Skip empty profiles - they should get generic responses
        return
    
    # Call build_progressive_response
    response = build_progressive_response(profile, query)
    
    # Property: Response must reference at least one signal from the profile
    response_lower = response.lower()
    
    # Check if response references interests
    interest_referenced = False
    for interest in profile.interests:
        # Check for the interest keyword or related terms
        if interest in response_lower:
            interest_referenced = True
            break
        # Check for related terms
        if interest == "coding" and any(term in response_lower for term in ["bca", "programming", "tech", "software", "developer"]):
            interest_referenced = True
            break
        if interest == "business" and any(term in response_lower for term in ["bba", "entrepreneurship", "management"]):
            interest_referenced = True
            break
        if interest == "management" and any(term in response_lower for term in ["mba", "manager", "leadership"]):
            interest_referenced = True
            break
    
    # Check if response references constraints
    constraint_referenced = False
    for constraint in profile.constraints:
        # Check for constraint keywords or related terms
        if "math" in constraint and any(term in response_lower for term in ["math", "weak in math", "not good at math"]):
            constraint_referenced = True
            break
        if "stud" in constraint and any(term in response_lower for term in ["studies", "not strong in studies", "weak student"]):
            constraint_referenced = True
            break
        if "communication" in constraint and "communication" in response_lower:
            constraint_referenced = True
            break
        if "budget" in constraint or "financial" in constraint and any(term in response_lower for term in ["budget", "financial", "fees"]):
            constraint_referenced = True
            break
        if "time" in constraint and "time" in response_lower:
            constraint_referenced = True
            break
        if "technical" in constraint and any(term in response_lower for term in ["technical", "no technical background"]):
            constraint_referenced = True
            break
        # Generic check: if the constraint appears in the response (with underscores replaced by spaces)
        constraint_readable = constraint.replace("_", " ")
        if constraint_readable in response_lower:
            constraint_referenced = True
            break
        # Also check if the response mentions "dealing with" or "you're dealing with" which indicates constraint acknowledgment
        if "dealing with" in response_lower or "you're dealing with" in response_lower:
            constraint_referenced = True
            break
    
    # Check if response references goals
    goal_referenced = False
    for goal in profile.goals:
        # Check for goal keywords or related terms
        if "salary" in goal and any(term in response_lower for term in ["salary", "package", "pay", "earning"]):
            goal_referenced = True
            break
        if "quick" in goal and any(term in response_lower for term in ["quick", "quickly", "fast", "3 years"]):
            goal_referenced = True
            break
        if "stable" in goal and any(term in response_lower for term in ["stable", "stability"]):
            goal_referenced = True
            break
        if "work_life_balance" in goal and any(term in response_lower for term in ["work life", "balance"]):
            goal_referenced = True
            break
        if "entrepreneurship" in goal or "startup" in goal and any(term in response_lower for term in ["business", "startup", "entrepreneur"]):
            goal_referenced = True
            break
    
    # Property: At least one signal type must be referenced
    signal_acknowledged = interest_referenced or constraint_referenced or goal_referenced
    
    assert signal_acknowledged, (
        f"Response does not acknowledge any profile signals.\n"
        f"Profile: interests={profile.interests}, constraints={profile.constraints}, goals={profile.goals}\n"
        f"Query: {query}\n"
        f"Response: {response[:200]}..."
    )


# ============================================================================
# EDGE CASE TESTS: Profile acknowledgment in specific scenarios
# ============================================================================

def test_profile_acknowledgment_with_only_interests():
    """Edge case: Response acknowledges interests when profile has only interests."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(interests={"coding"})
    response = build_progressive_response(profile, "what should I do")
    
    response_lower = response.lower()
    assert any(term in response_lower for term in ["coding", "bca", "tech", "programming"]), \
        f"Response should acknowledge coding interest. Got: {response[:200]}"


def test_profile_acknowledgment_with_only_constraints():
    """Edge case: Response acknowledges constraints when profile has only constraints."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(constraints={"weak_in_math"})
    response = build_progressive_response(profile, "help me decide")
    
    response_lower = response.lower()
    assert any(term in response_lower for term in ["math", "weak in math", "dealing with"]), \
        f"Response should acknowledge math constraint. Got: {response[:200]}"


def test_profile_acknowledgment_with_only_goals():
    """Edge case: Response acknowledges goals when profile has only goals."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(goals={"high_salary"})
    response = build_progressive_response(profile, "what do you recommend")
    
    response_lower = response.lower()
    assert any(term in response_lower for term in ["salary", "package", "pay", "want"]), \
        f"Response should acknowledge salary goal. Got: {response[:200]}"


def test_profile_acknowledgment_with_all_signals():
    """Edge case: Response acknowledges signals when profile has all types."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"}
    )
    response = build_progressive_response(profile, "what should I do")
    
    response_lower = response.lower()
    
    # Should acknowledge at least one signal (ideally all, but at least one)
    has_interest = any(term in response_lower for term in ["coding", "bca", "tech"])
    has_constraint = any(term in response_lower for term in ["math", "weak"])
    has_goal = any(term in response_lower for term in ["salary", "package"])
    
    assert has_interest or has_constraint or has_goal, \
        f"Response should acknowledge at least one signal. Got: {response[:200]}"


def test_profile_acknowledgment_with_multiple_interests():
    """Edge case: Response acknowledges interests when profile has multiple interests."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(interests={"coding", "business"})
    response = build_progressive_response(profile, "tell me more")
    
    response_lower = response.lower()
    
    # Should acknowledge at least one interest
    has_coding = any(term in response_lower for term in ["coding", "bca", "tech"])
    has_business = any(term in response_lower for term in ["business", "bba"])
    
    assert has_coding or has_business, \
        f"Response should acknowledge at least one interest. Got: {response[:200]}"


def test_no_generic_response_with_profile():
    """Edge case: Response should NOT contain generic greeting when profile exists."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(interests={"coding"})
    response = build_progressive_response(profile, "what should I do")
    
    # Should NOT contain generic greeting phrases
    generic_phrases = [
        "i'm here to help you find the right path",
        "let's start with a few questions",
        "tell me more about your interests"
    ]
    
    response_lower = response.lower()
    for phrase in generic_phrases:
        assert phrase not in response_lower, \
            f"Response should not contain generic phrase '{phrase}' when profile exists. Got: {response[:200]}"


# ============================================================================
# PROPERTY 5: No Generic Responses with Profile
# ============================================================================
# **Validates: Requirements 2.5**
# For any non-empty profile, no generic greeting phrases

@settings(max_examples=100)
@given(
    interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr"
        ]),
        min_size=0,
        max_size=3
    ),
    constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints"
        ]),
        min_size=0,
        max_size=3
    ),
    goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job"
        ]),
        min_size=0,
        max_size=3
    ),
    query=st.sampled_from([
        "what should I do",
        "help me decide",
        "what do you recommend",
        "which course is best",
        "tell me more",
        "what are my options",
        "I need guidance",
        "what's next",
        "help me choose"
    ])
)
def test_property_no_generic_responses_with_profile(interests, constraints, goals, query):
    """
    Property 5: No Generic Responses with Profile
    
    **Validates: Requirements 2.5**
    
    For any non-empty user profile, the counselor response SHALL NOT contain
    generic greeting phrases like "I'm here to help you find the right path".
    
    This ensures the system builds forward from accumulated context rather than
    resetting to generic greetings mid-conversation.
    
    Generic phrases to avoid when profile exists:
    - "I'm here to help you find the right path"
    - "Let's start with a few questions"
    - "Tell me more about your interests"
    """
    from app.services.counselor_handler import build_progressive_response
    
    # Create profile with generated signals
    profile = UserProfile(
        interests=interests,
        constraints=constraints,
        goals=goals
    )
    
    # Only test profiles that have at least one signal
    has_signals = bool(profile.interests or profile.constraints or profile.goals)
    
    if not has_signals:
        # Skip empty profiles - they SHOULD get generic responses
        return
    
    # Call build_progressive_response
    response = build_progressive_response(profile, query)
    
    # Define generic greeting phrases that should NOT appear when profile exists
    generic_phrases = [
        "i'm here to help you find the right path",
        "let's start with a few questions",
        "tell me more about your interests",
        "tell me more about your interests, and i'll guide you",
        "what interests you most?",  # This is for first-time users
    ]
    
    response_lower = response.lower()
    
    # Property: Response must NOT contain any generic greeting phrases
    for phrase in generic_phrases:
        assert phrase not in response_lower, (
            f"Response contains generic phrase '{phrase}' when profile exists.\n"
            f"Profile: interests={profile.interests}, constraints={profile.constraints}, goals={profile.goals}\n"
            f"Query: {query}\n"
            f"Response: {response[:300]}..."
        )


# ============================================================================
# EDGE CASE TESTS: No generic responses in specific scenarios
# ============================================================================

def test_no_generic_with_only_interests():
    """Edge case: No generic phrases when profile has only interests."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(interests={"coding"})
    response = build_progressive_response(profile, "what should I do")
    
    response_lower = response.lower()
    assert "i'm here to help you find the right path" not in response_lower
    assert "let's start with a few questions" not in response_lower


def test_no_generic_with_only_constraints():
    """Edge case: No generic phrases when profile has only constraints."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(constraints={"weak_in_math"})
    response = build_progressive_response(profile, "help me decide")
    
    response_lower = response.lower()
    assert "i'm here to help you find the right path" not in response_lower
    assert "let's start with a few questions" not in response_lower


def test_no_generic_with_only_goals():
    """Edge case: No generic phrases when profile has only goals."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(goals={"high_salary"})
    response = build_progressive_response(profile, "what do you recommend")
    
    response_lower = response.lower()
    assert "i'm here to help you find the right path" not in response_lower
    assert "let's start with a few questions" not in response_lower


def test_no_generic_with_all_signals():
    """Edge case: No generic phrases when profile has all signal types."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"}
    )
    response = build_progressive_response(profile, "what should I do")
    
    response_lower = response.lower()
    assert "i'm here to help you find the right path" not in response_lower
    assert "let's start with a few questions" not in response_lower
    assert "tell me more about your interests" not in response_lower


def test_no_generic_with_multiple_interests():
    """Edge case: No generic phrases when profile has multiple interests."""
    from app.services.counselor_handler import build_progressive_response
    
    profile = UserProfile(interests={"coding", "business"})
    response = build_progressive_response(profile, "tell me more")
    
    response_lower = response.lower()
    assert "i'm here to help you find the right path" not in response_lower
    assert "let's start with a few questions" not in response_lower


def test_generic_allowed_with_empty_profile():
    """Edge case: Generic phrases ARE allowed when profile is empty (first turn)."""
    from app.services.counselor_handler import _handle_general_exploration
    
    profile = UserProfile()  # Empty profile
    result = _handle_general_exploration("help me", profile)
    
    response_lower = result["answer"].lower()
    # Generic phrases SHOULD appear for empty profiles
    assert "i'm here to help you find the right path" in response_lower or \
           "let's start with a few questions" in response_lower, \
           "Generic phrases should be present for empty profiles (first turn)"


# ============================================================================
# PROPERTY 6: Human Judgment Phrases Present
# ============================================================================
# **Validates: Requirements 3.1, 3.2, 3.3**
# Final recommendations contain human judgment phrases

@settings(max_examples=100)
@given(
    interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr"
        ]),
        min_size=1,  # Need at least one interest for recommendation
        max_size=3
    ),
    constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints"
        ]),
        min_size=0,
        max_size=3
    ),
    goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job"
        ]),
        min_size=0,
        max_size=3
    ),
    query=st.sampled_from([
        "what should i do",
        "what do you suggest",
        "what do you recommend",
        "which one should i choose",
        "what's your recommendation",
        "suggest me",
        "help me decide",
        "what's best for me"
    ])
)
def test_property_human_judgment_phrases_present(interests, constraints, goals, query):
    """
    Property 6: Human Judgment Phrases Present
    
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    For any final recommendation generated by build_final_recommendation(),
    the output SHALL contain at least one human judgment phrase from the set:
    - "If I were in your position"
    - "In my experience"
    - "Here's what I'd recommend"
    - "Here's the honest path"
    - "Let me break this down"
    
    This ensures recommendations feel like they come from a human counselor
    rather than a robotic system.
    """
    from app.services.conversation_memory import build_final_recommendation
    
    # Create profile with generated signals
    # Set confidence to medium/high so we get recommendations (not None)
    profile = UserProfile(
        interests=interests,
        constraints=constraints,
        goals=goals,
        confidence_level="medium"  # Ensure we get recommendations
    )
    
    # Call build_final_recommendation
    recommendation = build_final_recommendation(profile, query)
    
    # Skip if no recommendation generated (insufficient data)
    if recommendation is None:
        return
    
    # Define human judgment phrases that should appear
    human_judgment_phrases = [
        "if i were in your position",
        "in my experience",
        "here's what i'd recommend",
        "here's the honest path",
        "let me break this down",
    ]
    
    recommendation_lower = recommendation.lower()
    
    # Property: At least one human judgment phrase must be present
    phrase_found = False
    found_phrase = None
    
    for phrase in human_judgment_phrases:
        if phrase in recommendation_lower:
            phrase_found = True
            found_phrase = phrase
            break
    
    assert phrase_found, (
        f"Recommendation does not contain any human judgment phrases.\n"
        f"Profile: interests={profile.interests}, constraints={profile.constraints}, goals={profile.goals}\n"
        f"Query: {query}\n"
        f"Expected one of: {human_judgment_phrases}\n"
        f"Recommendation preview: {recommendation[:500]}..."
    )


# ============================================================================
# EDGE CASE TESTS: Human judgment phrases in specific scenarios
# ============================================================================

def test_human_judgment_with_coding_interest():
    """Edge case: Coding recommendation contains human judgment phrase."""
    from app.services.conversation_memory import build_final_recommendation
    
    profile = UserProfile(
        interests={"coding"},
        goals={"high_salary"},
        confidence_level="medium"
    )
    
    recommendation = build_final_recommendation(profile, "what should i do")
    
    if recommendation is None:
        pytest.skip("No recommendation generated for this profile")
    
    recommendation_lower = recommendation.lower()
    
    # Should contain at least one human judgment phrase
    human_phrases = [
        "if i were in your position",
        "in my experience",
        "here's what i'd recommend",
        "here's the honest path",
    ]
    
    assert any(phrase in recommendation_lower for phrase in human_phrases), \
        f"Coding recommendation should contain human judgment phrase. Got: {recommendation[:300]}"


def test_human_judgment_with_business_interest():
    """Edge case: Business recommendation contains human judgment phrase."""
    from app.services.conversation_memory import build_final_recommendation
    
    profile = UserProfile(
        interests={"business"},
        goals={"quick_job"},
        confidence_level="medium"
    )
    
    recommendation = build_final_recommendation(profile, "what do you recommend")
    
    if recommendation is None:
        pytest.skip("No recommendation generated for this profile")
    
    recommendation_lower = recommendation.lower()
    
    # Should contain at least one human judgment phrase
    human_phrases = [
        "if i were in your position",
        "in my experience",
        "here's what i'd recommend",
        "here's the honest path",
    ]
    
    assert any(phrase in recommendation_lower for phrase in human_phrases), \
        f"Business recommendation should contain human judgment phrase. Got: {recommendation[:300]}"


def test_human_judgment_with_conflicting_goals():
    """Edge case: Conflicting goals recommendation contains human judgment phrase."""
    from app.services.conversation_memory import build_final_recommendation
    
    profile = UserProfile(
        interests={"coding"},
        goals={"high_salary", "quick_job"},  # Conflicting goals
        confidence_level="medium"
    )
    
    recommendation = build_final_recommendation(profile, "what should i do")
    
    if recommendation is None:
        pytest.skip("No recommendation generated for this profile")
    
    recommendation_lower = recommendation.lower()
    
    # Should contain at least one human judgment phrase
    human_phrases = [
        "if i were in your position",
        "in my experience",
        "here's what i'd recommend",
        "here's the honest path",
    ]
    
    assert any(phrase in recommendation_lower for phrase in human_phrases), \
        f"Conflicting goals recommendation should contain human judgment phrase. Got: {recommendation[:300]}"


def test_human_judgment_with_constraints():
    """Edge case: Recommendation with constraints contains human judgment phrase."""
    from app.services.conversation_memory import build_final_recommendation
    
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        confidence_level="medium"
    )
    
    recommendation = build_final_recommendation(profile, "help me decide")
    
    if recommendation is None:
        pytest.skip("No recommendation generated for this profile")
    
    recommendation_lower = recommendation.lower()
    
    # Should contain at least one human judgment phrase
    human_phrases = [
        "if i were in your position",
        "in my experience",
        "here's what i'd recommend",
        "here's the honest path",
    ]
    
    assert any(phrase in recommendation_lower for phrase in human_phrases), \
        f"Recommendation with constraints should contain human judgment phrase. Got: {recommendation[:300]}"


def test_no_recommendation_with_low_confidence():
    """Edge case: Low confidence profile should NOT get final recommendation."""
    from app.services.conversation_memory import build_final_recommendation
    
    profile = UserProfile(
        interests={"coding"},
        goals={"high_salary"},
        confidence_level="low"  # Low confidence
    )
    
    recommendation = build_final_recommendation(profile, "what should i do")
    
    # Should return None for low confidence (Task 4.3 requirement)
    assert recommendation is None, \
        "Low confidence profile should not get final recommendation"


def test_no_recommendation_without_interests():
    """Edge case: Profile without interests should NOT get recommendation."""
    from app.services.conversation_memory import build_final_recommendation
    
    profile = UserProfile(
        constraints={"weak_in_math"},
        goals={"high_salary"},
        confidence_level="medium"
    )
    
    recommendation = build_final_recommendation(profile, "what should i do")
    
    # Should return None without interests (insufficient data)
    assert recommendation is None, \
        "Profile without interests should not get final recommendation"


# ============================================================================
# PROPERTY 12: Session Memory Round-Trip
# ============================================================================
# **Validates: Requirements 6.1**
# Storing then retrieving profile produces equivalent profile

@settings(max_examples=100)
@given(
    interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr",
            "hospitality", "commerce", "healthcare", "law", "arts"
        ]),
        min_size=0,
        max_size=5
    ),
    constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints",
            "parental_pressure", "internal_conflict", "budget_constraint"
        ]),
        min_size=0,
        max_size=5
    ),
    goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job",
            "higher_studies", "entrepreneurship", "work_abroad"
        ]),
        min_size=0,
        max_size=5
    ),
    ambiguity_signals=st.sets(
        st.sampled_from([
            "confused", "not_sure", "maybe", "idk", "uncertain"
        ]),
        min_size=0,
        max_size=3
    ),
    education_level=st.sampled_from([
        None, "10th", "12th", "bca", "bba", "bcom", "bhm", "graduate", "postgraduate"
    ]),
    confidence_level=st.sampled_from(["low", "medium", "high"]),
    previous_intents=st.lists(
        st.sampled_from([
            "fees", "courses", "admission", "hostel", "placements",
            "counselor_exploration", "counselor_decision", "boundary_external"
        ]),
        min_size=0,
        max_size=5
    )
)
def test_property_session_memory_round_trip(
    interests, constraints, goals, ambiguity_signals,
    education_level, confidence_level, previous_intents
):
    """
    Property 12: Session Memory Round-Trip
    
    **Validates: Requirements 6.1**
    
    For any valid user profile, storing the profile to session memory and then
    retrieving it SHALL produce an equivalent profile where:
    - All signal sets are equal (interests, constraints, goals, ambiguity_signals)
    - Education level is equal
    - Confidence level is equal
    - Previous intents list is equal
    
    This ensures session memory correctly persists and retrieves user profiles
    without data loss or corruption.
    """
    from app.services.conversation_memory import get_memory_store
    
    # Create original profile with generated data
    original_profile = UserProfile(
        interests=interests,
        constraints=constraints,
        goals=goals,
        ambiguity_signals=ambiguity_signals,
        education_level=education_level,
        confidence_level=confidence_level,
        previous_intents=previous_intents
    )
    
    # Generate unique session ID for this test
    session_hash = hash((
        frozenset(interests),
        frozenset(constraints),
        frozenset(goals),
        frozenset(ambiguity_signals),
        education_level,
        confidence_level,
        tuple(previous_intents)
    ))
    session_id = f"test_roundtrip_{session_hash}"
    
    # Get memory store
    memory = get_memory_store()
    
    try:
        # Store profile in session memory
        memory._sessions[session_id] = original_profile
        
        # Retrieve profile from session memory
        retrieved_profile = memory.get_profile(session_id)
        
        # Property: Retrieved profile must equal original profile
        # Check all signal sets
        assert retrieved_profile.interests == original_profile.interests, (
            f"Interests mismatch after round-trip.\n"
            f"Original: {original_profile.interests}\n"
            f"Retrieved: {retrieved_profile.interests}"
        )
        
        assert retrieved_profile.constraints == original_profile.constraints, (
            f"Constraints mismatch after round-trip.\n"
            f"Original: {original_profile.constraints}\n"
            f"Retrieved: {retrieved_profile.constraints}"
        )
        
        assert retrieved_profile.goals == original_profile.goals, (
            f"Goals mismatch after round-trip.\n"
            f"Original: {original_profile.goals}\n"
            f"Retrieved: {retrieved_profile.goals}"
        )
        
        assert retrieved_profile.ambiguity_signals == original_profile.ambiguity_signals, (
            f"Ambiguity signals mismatch after round-trip.\n"
            f"Original: {original_profile.ambiguity_signals}\n"
            f"Retrieved: {retrieved_profile.ambiguity_signals}"
        )
        
        # Check education level
        assert retrieved_profile.education_level == original_profile.education_level, (
            f"Education level mismatch after round-trip.\n"
            f"Original: {original_profile.education_level}\n"
            f"Retrieved: {retrieved_profile.education_level}"
        )
        
        # Check confidence level
        assert retrieved_profile.confidence_level == original_profile.confidence_level, (
            f"Confidence level mismatch after round-trip.\n"
            f"Original: {original_profile.confidence_level}\n"
            f"Retrieved: {retrieved_profile.confidence_level}"
        )
        
        # Check previous intents
        assert retrieved_profile.previous_intents == original_profile.previous_intents, (
            f"Previous intents mismatch after round-trip.\n"
            f"Original: {original_profile.previous_intents}\n"
            f"Retrieved: {retrieved_profile.previous_intents}"
        )
        
    finally:
        # Clean up test session
        if session_id in memory._sessions:
            del memory._sessions[session_id]


# ============================================================================
# EDGE CASE TESTS: Session memory round-trip in specific scenarios
# ============================================================================

def test_round_trip_with_empty_profile():
    """Edge case: Empty profile round-trip preserves empty state."""
    from app.services.conversation_memory import get_memory_store
    
    original_profile = UserProfile()
    session_id = "test_empty_profile"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = original_profile
        retrieved_profile = memory.get_profile(session_id)
        
        assert retrieved_profile.interests == set()
        assert retrieved_profile.constraints == set()
        assert retrieved_profile.goals == set()
        assert retrieved_profile.ambiguity_signals == set()
        assert retrieved_profile.education_level is None
        assert retrieved_profile.confidence_level == "medium"
        assert retrieved_profile.previous_intents == []
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_round_trip_with_full_profile():
    """Edge case: Fully populated profile round-trip preserves all data."""
    from app.services.conversation_memory import get_memory_store
    
    original_profile = UserProfile(
        interests={"coding", "business"},
        constraints={"weak_in_math", "not_good_at_studies"},
        goals={"high_salary", "quick_job"},
        ambiguity_signals={"confused"},
        education_level="12th",
        confidence_level="low",
        previous_intents=["fees", "courses", "counselor_exploration"]
    )
    session_id = "test_full_profile"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = original_profile
        retrieved_profile = memory.get_profile(session_id)
        
        assert retrieved_profile.interests == {"coding", "business"}
        assert retrieved_profile.constraints == {"weak_in_math", "not_good_at_studies"}
        assert retrieved_profile.goals == {"high_salary", "quick_job"}
        assert retrieved_profile.ambiguity_signals == {"confused"}
        assert retrieved_profile.education_level == "12th"
        assert retrieved_profile.confidence_level == "low"
        assert retrieved_profile.previous_intents == ["fees", "courses", "counselor_exploration"]
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_round_trip_with_only_interests():
    """Edge case: Profile with only interests preserves interests."""
    from app.services.conversation_memory import get_memory_store
    
    original_profile = UserProfile(interests={"coding"})
    session_id = "test_interests_only"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = original_profile
        retrieved_profile = memory.get_profile(session_id)
        
        assert retrieved_profile.interests == {"coding"}
        assert retrieved_profile.constraints == set()
        assert retrieved_profile.goals == set()
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_round_trip_with_only_constraints():
    """Edge case: Profile with only constraints preserves constraints."""
    from app.services.conversation_memory import get_memory_store
    
    original_profile = UserProfile(constraints={"weak_in_math"})
    session_id = "test_constraints_only"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = original_profile
        retrieved_profile = memory.get_profile(session_id)
        
        assert retrieved_profile.interests == set()
        assert retrieved_profile.constraints == {"weak_in_math"}
        assert retrieved_profile.goals == set()
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_round_trip_with_only_goals():
    """Edge case: Profile with only goals preserves goals."""
    from app.services.conversation_memory import get_memory_store
    
    original_profile = UserProfile(goals={"high_salary"})
    session_id = "test_goals_only"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = original_profile
        retrieved_profile = memory.get_profile(session_id)
        
        assert retrieved_profile.interests == set()
        assert retrieved_profile.constraints == set()
        assert retrieved_profile.goals == {"high_salary"}
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_round_trip_preserves_education_level():
    """Edge case: Education level is preserved across round-trip."""
    from app.services.conversation_memory import get_memory_store
    
    for education_level in ["10th", "12th", "bca", "bba", "graduate"]:
        original_profile = UserProfile(
            interests={"coding"},
            education_level=education_level
        )
        session_id = f"test_education_{education_level}"
        
        memory = get_memory_store()
        
        try:
            memory._sessions[session_id] = original_profile
            retrieved_profile = memory.get_profile(session_id)
            
            assert retrieved_profile.education_level == education_level, \
                f"Education level {education_level} not preserved"
        finally:
            if session_id in memory._sessions:
                del memory._sessions[session_id]


def test_round_trip_preserves_confidence_level():
    """Edge case: Confidence level is preserved across round-trip."""
    from app.services.conversation_memory import get_memory_store
    
    for confidence_level in ["low", "medium", "high"]:
        original_profile = UserProfile(
            interests={"coding"},
            confidence_level=confidence_level
        )
        session_id = f"test_confidence_{confidence_level}"
        
        memory = get_memory_store()
        
        try:
            memory._sessions[session_id] = original_profile
            retrieved_profile = memory.get_profile(session_id)
            
            assert retrieved_profile.confidence_level == confidence_level, \
                f"Confidence level {confidence_level} not preserved"
        finally:
            if session_id in memory._sessions:
                del memory._sessions[session_id]


def test_round_trip_preserves_previous_intents():
    """Edge case: Previous intents list is preserved across round-trip."""
    from app.services.conversation_memory import get_memory_store
    
    original_profile = UserProfile(
        interests={"coding"},
        previous_intents=["fees", "courses", "admission", "hostel", "placements"]
    )
    session_id = "test_previous_intents"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = original_profile
        retrieved_profile = memory.get_profile(session_id)
        
        assert retrieved_profile.previous_intents == ["fees", "courses", "admission", "hostel", "placements"]
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_round_trip_with_multiple_sessions():
    """Edge case: Multiple sessions maintain independent profiles."""
    from app.services.conversation_memory import get_memory_store
    
    profile1 = UserProfile(interests={"coding"}, goals={"high_salary"})
    profile2 = UserProfile(interests={"business"}, constraints={"weak_in_math"})
    profile3 = UserProfile(goals={"quick_job"}, ambiguity_signals={"confused"})
    
    session_id1 = "test_multi_session_1"
    session_id2 = "test_multi_session_2"
    session_id3 = "test_multi_session_3"
    
    memory = get_memory_store()
    
    try:
        # Store all profiles
        memory._sessions[session_id1] = profile1
        memory._sessions[session_id2] = profile2
        memory._sessions[session_id3] = profile3
        
        # Retrieve and verify each profile independently
        retrieved1 = memory.get_profile(session_id1)
        retrieved2 = memory.get_profile(session_id2)
        retrieved3 = memory.get_profile(session_id3)
        
        # Verify profile 1
        assert retrieved1.interests == {"coding"}
        assert retrieved1.goals == {"high_salary"}
        assert retrieved1.constraints == set()
        
        # Verify profile 2
        assert retrieved2.interests == {"business"}
        assert retrieved2.constraints == {"weak_in_math"}
        assert retrieved2.goals == set()
        
        # Verify profile 3
        assert retrieved3.goals == {"quick_job"}
        assert retrieved3.ambiguity_signals == {"confused"}
        assert retrieved3.interests == set()
        
    finally:
        # Clean up all test sessions
        for session_id in [session_id1, session_id2, session_id3]:
            if session_id in memory._sessions:
                del memory._sessions[session_id]


# ============================================================================
# PROPERTY 13: Counselor Lock Idempotence
# ============================================================================
# **Validates: Requirements 7.1, 7.4**
# Calling should_lock_counselor() multiple times returns same result

@settings(max_examples=100)
@given(
    interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr",
            "hospitality", "commerce", "healthcare", "law", "arts"
        ]),
        min_size=0,
        max_size=5
    ),
    constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints",
            "parental_pressure", "internal_conflict", "budget_constraint"
        ]),
        min_size=0,
        max_size=5
    ),
    goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job",
            "higher_studies", "entrepreneurship", "work_abroad"
        ]),
        min_size=0,
        max_size=5
    ),
    ambiguity_signals=st.sets(
        st.sampled_from([
            "confused", "not_sure", "maybe", "idk", "uncertain"
        ]),
        min_size=0,
        max_size=3
    ),
    education_level=st.sampled_from([
        None, "10th", "12th", "bca", "bba", "bcom", "bhm", "graduate", "postgraduate"
    ]),
    confidence_level=st.sampled_from(["low", "medium", "high"]),
    num_calls=st.integers(min_value=2, max_value=10)
)
def test_property_counselor_lock_idempotence(
    interests, constraints, goals, ambiguity_signals,
    education_level, confidence_level, num_calls
):
    """
    Property 13: Counselor Lock Idempotence
    
    **Validates: Requirements 7.1, 7.4**
    
    For any user profile, calling should_lock_counselor(profile) multiple times
    SHALL return the same boolean result on each call.
    
    This ensures the counselor lock check is a pure function that doesn't modify
    state or produce different results on repeated calls. Idempotence is critical
    for deterministic routing - the same profile should always produce the same
    routing decision.
    """
    # Create profile with generated data
    profile = UserProfile(
        interests=interests,
        constraints=constraints,
        goals=goals,
        ambiguity_signals=ambiguity_signals,
        education_level=education_level,
        confidence_level=confidence_level
    )
    
    # Call should_lock_counselor() multiple times
    results = []
    for i in range(num_calls):
        result = should_lock_counselor(profile)
        results.append(result)
    
    # Property: All results must be identical
    first_result = results[0]
    
    for i, result in enumerate(results[1:], start=2):
        assert result == first_result, (
            f"Counselor lock idempotence violated: call 1 returned {first_result}, "
            f"call {i} returned {result}.\n"
            f"Profile: {profile.to_dict()}\n"
            f"All results: {results}"
        )
    
    # Additional verification: Result should match expected based on profile
    has_signals = bool(
        profile.interests or 
        profile.constraints or 
        profile.goals or 
        profile.ambiguity_signals
    )
    
    assert first_result == has_signals, (
        f"Counselor lock result doesn't match expected value.\n"
        f"Expected: {has_signals} (based on signals present)\n"
        f"Got: {first_result}\n"
        f"Profile: {profile.to_dict()}"
    )


# ============================================================================
# EDGE CASE TESTS: Counselor lock idempotence in specific scenarios
# ============================================================================

def test_idempotence_with_empty_profile():
    """Edge case: Empty profile returns False consistently."""
    profile = UserProfile()
    
    # Call 5 times
    results = [should_lock_counselor(profile) for _ in range(5)]
    
    # All should be False
    assert all(result is False for result in results), \
        f"Empty profile should consistently return False. Got: {results}"


def test_idempotence_with_only_interests():
    """Edge case: Profile with only interests returns True consistently."""
    profile = UserProfile(interests={"coding"})
    
    # Call 5 times
    results = [should_lock_counselor(profile) for _ in range(5)]
    
    # All should be True
    assert all(result is True for result in results), \
        f"Profile with interests should consistently return True. Got: {results}"


def test_idempotence_with_only_constraints():
    """Edge case: Profile with only constraints returns True consistently."""
    profile = UserProfile(constraints={"weak_in_math"})
    
    # Call 5 times
    results = [should_lock_counselor(profile) for _ in range(5)]
    
    # All should be True
    assert all(result is True for result in results), \
        f"Profile with constraints should consistently return True. Got: {results}"


def test_idempotence_with_only_goals():
    """Edge case: Profile with only goals returns True consistently."""
    profile = UserProfile(goals={"high_salary"})
    
    # Call 5 times
    results = [should_lock_counselor(profile) for _ in range(5)]
    
    # All should be True
    assert all(result is True for result in results), \
        f"Profile with goals should consistently return True. Got: {results}"


def test_idempotence_with_only_ambiguity():
    """Edge case: Profile with only ambiguity signals returns True consistently."""
    profile = UserProfile(ambiguity_signals={"confused"})
    
    # Call 5 times
    results = [should_lock_counselor(profile) for _ in range(5)]
    
    # All should be True
    assert all(result is True for result in results), \
        f"Profile with ambiguity should consistently return True. Got: {results}"


def test_idempotence_with_all_signals():
    """Edge case: Profile with all signal types returns True consistently."""
    profile = UserProfile(
        interests={"coding", "business"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        ambiguity_signals={"confused"}
    )
    
    # Call 10 times
    results = [should_lock_counselor(profile) for _ in range(10)]
    
    # All should be True
    assert all(result is True for result in results), \
        f"Profile with all signals should consistently return True. Got: {results}"


def test_idempotence_with_education_only():
    """Edge case: Profile with only education level returns False consistently."""
    profile = UserProfile(education_level="12th")
    
    # Call 5 times
    results = [should_lock_counselor(profile) for _ in range(5)]
    
    # All should be False (education alone doesn't activate lock)
    assert all(result is False for result in results), \
        f"Profile with only education should consistently return False. Got: {results}"


def test_idempotence_across_different_confidence_levels():
    """Edge case: Confidence level doesn't affect lock idempotence."""
    for confidence_level in ["low", "medium", "high"]:
        profile = UserProfile(
            interests={"coding"},
            confidence_level=confidence_level
        )
        
        # Call 5 times
        results = [should_lock_counselor(profile) for _ in range(5)]
        
        # All should be True (confidence doesn't affect lock)
        assert all(result is True for result in results), \
            f"Profile with confidence={confidence_level} should consistently return True. Got: {results}"


def test_idempotence_with_large_signal_sets():
    """Edge case: Large signal sets return True consistently."""
    profile = UserProfile(
        interests={"coding", "business", "management", "teaching", "research"},
        constraints={"weak_in_math", "not_good_at_studies", "poor_communication"},
        goals={"high_salary", "quick_job", "stable_career", "work_life_balance"},
        ambiguity_signals={"confused", "not_sure", "maybe"}
    )
    
    # Call 10 times
    results = [should_lock_counselor(profile) for _ in range(10)]
    
    # All should be True
    assert all(result is True for result in results), \
        f"Profile with large signal sets should consistently return True. Got: {results}"


def test_idempotence_with_single_signal_each_type():
    """Edge case: One signal of each type returns True consistently."""
    profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"},
        ambiguity_signals={"confused"}
    )
    
    # Call 7 times
    results = [should_lock_counselor(profile) for _ in range(7)]
    
    # All should be True
    assert all(result is True for result in results), \
        f"Profile with one signal of each type should consistently return True. Got: {results}"


# ============================================================================
# PROPERTY 15: Profile Accumulation Monotonicity
# ============================================================================
# **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
# Adding signals never removes existing signals

@settings(max_examples=100)
@given(
    # Initial profile signals
    initial_interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr"
        ]),
        min_size=0,
        max_size=3
    ),
    initial_constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints"
        ]),
        min_size=0,
        max_size=3
    ),
    initial_goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job"
        ]),
        min_size=0,
        max_size=3
    ),
    # New signals to add
    new_interests=st.sets(
        st.sampled_from([
            "coding", "business", "management", "teaching", "research",
            "entrepreneurship", "design", "marketing", "finance", "hr",
            "hospitality", "commerce", "healthcare", "law", "arts"
        ]),
        min_size=0,
        max_size=3
    ),
    new_constraints=st.sets(
        st.sampled_from([
            "weak_in_math", "not_good_at_studies", "poor_communication",
            "no_technical_background", "limited_time", "financial_constraints",
            "parental_pressure", "internal_conflict", "budget_constraint"
        ]),
        min_size=0,
        max_size=3
    ),
    new_goals=st.sets(
        st.sampled_from([
            "high_salary", "quick_job", "stable_career", "work_life_balance",
            "remote_work", "startup_experience", "government_job",
            "higher_studies", "entrepreneurship", "work_abroad"
        ]),
        min_size=0,
        max_size=3
    )
)
def test_property_profile_accumulation_monotonicity(
    initial_interests, initial_constraints, initial_goals,
    new_interests, new_constraints, new_goals
):
    """
    Property 15: Profile Accumulation Monotonicity
    
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
    
    For any user profile and new signal set, adding signals to the profile
    SHALL result in a profile where:
    - len(new_profile.interests) >= len(old_profile.interests)
    - len(new_profile.constraints) >= len(old_profile.constraints)
    - len(new_profile.goals) >= len(old_profile.goals)
    
    AND adding signals of one type SHALL NOT remove signals of other types.
    
    This ensures profile accumulation is monotonic - signals are only added,
    never removed, maintaining conversation continuity across turns.
    """
    from app.services.conversation_memory import get_memory_store
    
    # Create initial profile
    old_profile = UserProfile(
        interests=initial_interests.copy(),
        constraints=initial_constraints.copy(),
        goals=initial_goals.copy()
    )
    
    # Store old profile sizes
    old_interests_size = len(old_profile.interests)
    old_constraints_size = len(old_profile.constraints)
    old_goals_size = len(old_profile.goals)
    
    # Store old profile signals for isolation check
    old_interests_copy = old_profile.interests.copy()
    old_constraints_copy = old_profile.constraints.copy()
    old_goals_copy = old_profile.goals.copy()
    
    # Create session and store initial profile
    session_id = f"test_monotonicity_{hash((frozenset(initial_interests), frozenset(initial_constraints), frozenset(initial_goals)))}"
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Add new signals using update_profile
        signals_to_add = {
            "interests": new_interests,
            "constraints": new_constraints,
            "goals": new_goals
        }
        
        new_profile = memory.update_profile(session_id, signals_to_add)
        
        # Property 1: Monotonic growth - signal sets never shrink
        assert len(new_profile.interests) >= old_interests_size, (
            f"Interests size decreased after adding signals.\n"
            f"Old size: {old_interests_size}, New size: {len(new_profile.interests)}\n"
            f"Old interests: {old_interests_copy}\n"
            f"New interests: {new_profile.interests}\n"
            f"Added interests: {new_interests}"
        )
        
        assert len(new_profile.constraints) >= old_constraints_size, (
            f"Constraints size decreased after adding signals.\n"
            f"Old size: {old_constraints_size}, New size: {len(new_profile.constraints)}\n"
            f"Old constraints: {old_constraints_copy}\n"
            f"New constraints: {new_profile.constraints}\n"
            f"Added constraints: {new_constraints}"
        )
        
        assert len(new_profile.goals) >= old_goals_size, (
            f"Goals size decreased after adding signals.\n"
            f"Old size: {old_goals_size}, New size: {len(new_profile.goals)}\n"
            f"Old goals: {old_goals_copy}\n"
            f"New goals: {new_profile.goals}\n"
            f"Added goals: {new_goals}"
        )
        
        # Property 2: Signal isolation - adding signals of one type doesn't remove signals of other types
        # All old interests should still be present
        for old_interest in old_interests_copy:
            assert old_interest in new_profile.interests, (
                f"Old interest '{old_interest}' was removed after adding new signals.\n"
                f"Old interests: {old_interests_copy}\n"
                f"New interests: {new_profile.interests}\n"
                f"Added interests: {new_interests}"
            )
        
        # All old constraints should still be present
        for old_constraint in old_constraints_copy:
            assert old_constraint in new_profile.constraints, (
                f"Old constraint '{old_constraint}' was removed after adding new signals.\n"
                f"Old constraints: {old_constraints_copy}\n"
                f"New constraints: {new_profile.constraints}\n"
                f"Added constraints: {new_constraints}"
            )
        
        # All old goals should still be present
        for old_goal in old_goals_copy:
            assert old_goal in new_profile.goals, (
                f"Old goal '{old_goal}' was removed after adding new signals.\n"
                f"Old goals: {old_goals_copy}\n"
                f"New goals: {new_profile.goals}\n"
                f"Added goals: {new_goals}"
            )
        
        # Property 3: Cross-type isolation - adding interests doesn't affect constraints/goals
        if new_interests and not new_constraints and not new_goals:
            # Only adding interests
            assert new_profile.constraints == old_constraints_copy, (
                f"Adding interests modified constraints.\n"
                f"Old constraints: {old_constraints_copy}\n"
                f"New constraints: {new_profile.constraints}"
            )
            assert new_profile.goals == old_goals_copy, (
                f"Adding interests modified goals.\n"
                f"Old goals: {old_goals_copy}\n"
                f"New goals: {new_profile.goals}"
            )
        
        # Adding constraints doesn't affect interests/goals
        if new_constraints and not new_interests and not new_goals:
            # Only adding constraints
            assert new_profile.interests == old_interests_copy, (
                f"Adding constraints modified interests.\n"
                f"Old interests: {old_interests_copy}\n"
                f"New interests: {new_profile.interests}"
            )
            assert new_profile.goals == old_goals_copy, (
                f"Adding constraints modified goals.\n"
                f"Old goals: {old_goals_copy}\n"
                f"New goals: {new_profile.goals}"
            )
        
        # Adding goals doesn't affect interests/constraints
        if new_goals and not new_interests and not new_constraints:
            # Only adding goals
            assert new_profile.interests == old_interests_copy, (
                f"Adding goals modified interests.\n"
                f"Old interests: {old_interests_copy}\n"
                f"New interests: {new_profile.interests}"
            )
            assert new_profile.constraints == old_constraints_copy, (
                f"Adding goals modified constraints.\n"
                f"Old constraints: {old_constraints_copy}\n"
                f"New constraints: {new_profile.constraints}"
            )
        
    finally:
        # Clean up test session
        if session_id in memory._sessions:
            del memory._sessions[session_id]


# ============================================================================
# EDGE CASE TESTS: Profile accumulation monotonicity in specific scenarios
# ============================================================================

def test_monotonicity_adding_interests_to_empty_profile():
    """Edge case: Adding interests to empty profile increases interests size."""
    from app.services.conversation_memory import get_memory_store
    
    old_profile = UserProfile()
    session_id = "test_add_interests_empty"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Add interests
        new_profile = memory.update_profile(session_id, {"interests": {"coding", "business"}})
        
        # Should have 2 interests now
        assert len(new_profile.interests) >= 0  # Monotonic
        assert len(new_profile.interests) == 2
        assert "coding" in new_profile.interests
        assert "business" in new_profile.interests
        
        # Other signal types should remain empty
        assert len(new_profile.constraints) == 0
        assert len(new_profile.goals) == 0
        
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_monotonicity_adding_constraints_to_existing_profile():
    """Edge case: Adding constraints to profile with interests preserves interests."""
    from app.services.conversation_memory import get_memory_store
    
    old_profile = UserProfile(interests={"coding"})
    session_id = "test_add_constraints"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Add constraints
        new_profile = memory.update_profile(session_id, {"constraints": {"weak_in_math"}})
        
        # Interests should be preserved
        assert "coding" in new_profile.interests
        assert len(new_profile.interests) >= 1  # Monotonic
        
        # Constraints should be added
        assert "weak_in_math" in new_profile.constraints
        assert len(new_profile.constraints) >= 0  # Monotonic
        
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_monotonicity_adding_goals_to_existing_profile():
    """Edge case: Adding goals to profile with interests and constraints preserves both."""
    from app.services.conversation_memory import get_memory_store
    
    old_profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"}
    )
    session_id = "test_add_goals"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Add goals
        new_profile = memory.update_profile(session_id, {"goals": {"high_salary"}})
        
        # Interests and constraints should be preserved
        assert "coding" in new_profile.interests
        assert "weak_in_math" in new_profile.constraints
        assert len(new_profile.interests) >= 1  # Monotonic
        assert len(new_profile.constraints) >= 1  # Monotonic
        
        # Goals should be added
        assert "high_salary" in new_profile.goals
        assert len(new_profile.goals) >= 0  # Monotonic
        
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_monotonicity_adding_duplicate_signals():
    """Edge case: Adding duplicate signals doesn't decrease size (idempotent)."""
    from app.services.conversation_memory import get_memory_store
    
    old_profile = UserProfile(interests={"coding"})
    session_id = "test_duplicate_signals"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Add same interest again
        new_profile = memory.update_profile(session_id, {"interests": {"coding"}})
        
        # Size should not decrease (monotonic)
        assert len(new_profile.interests) >= 1
        assert "coding" in new_profile.interests
        
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_monotonicity_adding_multiple_signal_types():
    """Edge case: Adding multiple signal types at once preserves all existing signals."""
    from app.services.conversation_memory import get_memory_store
    
    old_profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"}
    )
    session_id = "test_add_multiple_types"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Add interests, constraints, and goals all at once
        new_profile = memory.update_profile(session_id, {
            "interests": {"business"},
            "constraints": {"not_good_at_studies"},
            "goals": {"high_salary", "quick_job"}
        })
        
        # All old signals should be preserved
        assert "coding" in new_profile.interests
        assert "weak_in_math" in new_profile.constraints
        
        # New signals should be added
        assert "business" in new_profile.interests
        assert "not_good_at_studies" in new_profile.constraints
        assert "high_salary" in new_profile.goals
        assert "quick_job" in new_profile.goals
        
        # Sizes should be monotonic
        assert len(new_profile.interests) >= 1
        assert len(new_profile.constraints) >= 1
        assert len(new_profile.goals) >= 0
        
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_monotonicity_across_multiple_updates():
    """Edge case: Multiple sequential updates maintain monotonicity."""
    from app.services.conversation_memory import get_memory_store
    
    old_profile = UserProfile()
    session_id = "test_multiple_updates"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Update 1: Add interests
        profile1 = memory.update_profile(session_id, {"interests": {"coding"}})
        assert len(profile1.interests) == 1
        
        # Update 2: Add more interests
        profile2 = memory.update_profile(session_id, {"interests": {"business"}})
        assert len(profile2.interests) >= 1  # Monotonic
        assert "coding" in profile2.interests  # Old signal preserved
        assert "business" in profile2.interests  # New signal added
        
        # Update 3: Add constraints
        profile3 = memory.update_profile(session_id, {"constraints": {"weak_in_math"}})
        assert len(profile3.interests) >= 2  # Interests preserved
        assert len(profile3.constraints) >= 0  # Monotonic
        assert "coding" in profile3.interests
        assert "business" in profile3.interests
        assert "weak_in_math" in profile3.constraints
        
        # Update 4: Add goals
        profile4 = memory.update_profile(session_id, {"goals": {"high_salary"}})
        assert len(profile4.interests) >= 2  # Interests preserved
        assert len(profile4.constraints) >= 1  # Constraints preserved
        assert len(profile4.goals) >= 0  # Monotonic
        assert "coding" in profile4.interests
        assert "business" in profile4.interests
        assert "weak_in_math" in profile4.constraints
        assert "high_salary" in profile4.goals
        
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_monotonicity_with_empty_signal_additions():
    """Edge case: Adding empty signal sets doesn't decrease sizes."""
    from app.services.conversation_memory import get_memory_store
    
    old_profile = UserProfile(
        interests={"coding"},
        constraints={"weak_in_math"},
        goals={"high_salary"}
    )
    session_id = "test_empty_additions"
    
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Add empty signal sets
        new_profile = memory.update_profile(session_id, {
            "interests": set(),
            "constraints": set(),
            "goals": set()
        })
        
        # All signals should be preserved (monotonic)
        assert len(new_profile.interests) >= 1
        assert len(new_profile.constraints) >= 1
        assert len(new_profile.goals) >= 1
        assert "coding" in new_profile.interests
        assert "weak_in_math" in new_profile.constraints
        assert "high_salary" in new_profile.goals
        
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


def test_monotonicity_preserves_signal_identity():
    """Edge case: Adding new signals doesn't modify existing signal values."""
    from app.services.conversation_memory import get_memory_store
    
    old_profile = UserProfile(
        interests={"coding", "business"},
        constraints={"weak_in_math"},
        goals={"high_salary"}
    )
    
    # Store original signal values
    old_interests = old_profile.interests.copy()
    old_constraints = old_profile.constraints.copy()
    old_goals = old_profile.goals.copy()
    
    session_id = "test_signal_identity"
    memory = get_memory_store()
    
    try:
        memory._sessions[session_id] = old_profile
        
        # Add new signals
        new_profile = memory.update_profile(session_id, {
            "interests": {"management"},
            "constraints": {"not_good_at_studies"},
            "goals": {"quick_job"}
        })
        
        # All old signals should still be present with same values
        for old_interest in old_interests:
            assert old_interest in new_profile.interests, \
                f"Old interest '{old_interest}' was removed"
        
        for old_constraint in old_constraints:
            assert old_constraint in new_profile.constraints, \
                f"Old constraint '{old_constraint}' was removed"
        
        for old_goal in old_goals:
            assert old_goal in new_profile.goals, \
                f"Old goal '{old_goal}' was removed"
        
    finally:
        if session_id in memory._sessions:
            del memory._sessions[session_id]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
