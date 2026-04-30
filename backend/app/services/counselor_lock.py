"""
Counselor Lock Module - Centralized counselor lock logic for deterministic routing.

This module provides a single source of truth for determining whether a user
should be locked in counselor mode based on their accumulated profile signals.

The counselor lock prevents mid-conversation routing failures by ensuring users
stay in counselor mode once they have an active profile (interests, constraints,
goals, or ambiguity signals).

Used by:
- Multi-Intent Handler (structured_knowledge.py)
- Structured Knowledge Handler (structured_knowledge.py)
- Boundary Handler (boundary_handler.py)
- Chat Routing Layer (api/chat.py)
"""

import logging
from typing import Optional
from app.services.conversation_memory import UserProfile

logger = logging.getLogger(__name__)


def should_lock_counselor(profile: UserProfile) -> bool:
    """
    Determine if user should be locked in counselor mode.
    
    Returns True if the user has ANY of the following signals:
    - Interests (exploring career options: coding, business, management, etc.)
    - Constraints (weaknesses: weak in math, not good at studies, etc.)
    - Goals (objectives: high salary, quick job, stable career, etc.)
    - Ambiguity signals (uncertainty: confused, not sure, etc.)
    
    This function ensures deterministic routing across all layers. Once a user
    has provided any profile signals, they should stay in counselor mode to
    maintain conversation continuity and prevent jarring routing switches.
    
    Args:
        profile: UserProfile with accumulated signals from conversation turns
        
    Returns:
        bool: True if user should stay in counselor mode, False otherwise
        
    Examples:
        >>> profile = UserProfile(interests={"coding"})
        >>> should_lock_counselor(profile)
        True
        
        >>> profile = UserProfile(constraints={"weak_in_math"})
        >>> should_lock_counselor(profile)
        True
        
        >>> profile = UserProfile()  # Empty profile
        >>> should_lock_counselor(profile)
        False
    """
    # Check if profile has ANY signals
    has_interests = bool(profile.interests)
    has_constraints = bool(profile.constraints)
    has_goals = bool(profile.goals)
    has_ambiguity = bool(profile.ambiguity_signals)
    
    # Determine lock status
    locked = has_interests or has_constraints or has_goals or has_ambiguity
    
    # Log decision for debugging routing
    if locked:
        reasons = []
        if has_interests:
            reasons.append(f"interests={list(profile.interests)}")
        if has_constraints:
            reasons.append(f"constraints={list(profile.constraints)}")
        if has_goals:
            reasons.append(f"goals={list(profile.goals)}")
        if has_ambiguity:
            reasons.append(f"ambiguity={list(profile.ambiguity_signals)}")
        
        reason_str = ", ".join(reasons)
        logger.info(f"[counselor_lock] LOCKED - User has active profile: {reason_str}")
    else:
        logger.info("[counselor_lock] UNLOCKED - Empty profile, allowing normal routing")
    
    return locked


def get_lock_reason(profile: UserProfile) -> Optional[str]:
    """
    Get human-readable reason for counselor lock status.
    
    Useful for debugging and logging to understand why a user was locked
    in counselor mode.
    
    Args:
        profile: UserProfile with accumulated signals
        
    Returns:
        Optional[str]: Human-readable reason if locked, None if not locked
        
    Examples:
        >>> profile = UserProfile(interests={"coding"}, constraints={"weak_in_math"})
        >>> get_lock_reason(profile)
        'has_interests (coding), has_constraints (weak_in_math)'
    """
    if not should_lock_counselor(profile):
        return None
    
    reasons = []
    
    if profile.interests:
        interests_str = ", ".join(profile.interests)
        reasons.append(f"has_interests ({interests_str})")
    
    if profile.constraints:
        constraints_str = ", ".join(profile.constraints)
        reasons.append(f"has_constraints ({constraints_str})")
    
    if profile.goals:
        goals_str = ", ".join(profile.goals)
        reasons.append(f"has_goals ({goals_str})")
    
    if profile.ambiguity_signals:
        ambiguity_str = ", ".join(profile.ambiguity_signals)
        reasons.append(f"has_ambiguity ({ambiguity_str})")
    
    return ", ".join(reasons)


def get_profile_summary(profile: UserProfile) -> str:
    """
    Get concise summary of user profile for logging.
    
    Args:
        profile: UserProfile with accumulated signals
        
    Returns:
        str: Concise profile summary
        
    Examples:
        >>> profile = UserProfile(interests={"coding"}, goals={"high_salary"})
        >>> get_profile_summary(profile)
        'Profile(interests=1, constraints=0, goals=1, ambiguity=0)'
    """
    return (
        f"Profile("
        f"interests={len(profile.interests)}, "
        f"constraints={len(profile.constraints)}, "
        f"goals={len(profile.goals)}, "
        f"ambiguity={len(profile.ambiguity_signals)}"
        f")"
    )
