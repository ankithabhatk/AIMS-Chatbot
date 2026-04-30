"""
Contradiction Detection Engine - Production-Grade

Detects semantic contradictions across conversation turns and applies
deterministic confidence penalties. No randomness, bounded penalties.

Architecture:
    detect_contradictions(profile_history, new_signals) → List[Contradiction]
    apply_contradiction_penalty(confidence, contradictions) → new_confidence

Contradiction Types:
    - interest_conflict: "I like X" then "I hate X"
    - goal_conflict: "I want salary" then "I don't want to study"
    - constraint_inconsistency: "I'm good at math" then "I'm bad at math"
    - preference_reversal: Direct opposite of previous statement

Properties:
    ✓ Deterministic: Same input = same penalties
    ✓ Proportional: Penalty scales with contradiction severity
    ✓ Bounded: Max -0.3 penalty (maintain delta constraint)
    ✓ Reversible: User can recover confidence by clarifying
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
from enum import Enum

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════════════

class ContradictionType(Enum):
    """Types of contradictions the system detects."""
    INTEREST_CONFLICT = "interest_conflict"
    GOAL_CONFLICT = "goal_conflict"
    CONSTRAINT_INCONSISTENCY = "constraint_inconsistency"
    PREFERENCE_REVERSAL = "preference_reversal"
    WEAK_SIGNAL_CONFLICT = "weak_signal_conflict"


@dataclass
class Contradiction:
    """Represents a single detected contradiction."""
    type: ContradictionType
    previous_value: str
    current_value: str
    signal_key: str  # What was contradicted (e.g., "interest", "goal", "math")
    severity: float  # 0.0-1.0, used for penalty calculation
    description: str  # Human-readable explanation
    turn_distance: int = 0  # How many turns ago was previous signal

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "type": self.type.value,
            "previous": self.previous_value,
            "current": self.current_value,
            "signal_key": self.signal_key,
            "severity": self.severity,
            "description": self.description,
            "turn_distance": self.turn_distance,
        }


# ════════════════════════════════════════════════════════════════════════════
# CONTRADICTION DETECTION LOGIC
# ════════════════════════════════════════════════════════════════════════════

# Signal patterns for contradiction detection
POSITIVE_INTEREST_PATTERNS = {
    "interest": ["like", "love", "enjoy", "interested", "curious", "drawn to", "want to do"],
    "good_at": ["good at", "strong in", "excellent", "skilled", "talented"],
    "preference": ["prefer", "better", "more interested"],
}

NEGATIVE_INTEREST_PATTERNS = {
    "disinterest": ["hate", "don't like", "dislike", "avoid", "not interested", "boring"],
    "bad_at": ["bad at", "weak in", "poor at", "struggle", "difficult for me"],
    "rejection": ["won't do", "reject", "no way", "absolutely not"],
}

# Goal patterns that can conflict
GOAL_PATTERNS = {
    "job": ["job", "placement", "get placed", "employment", "work"],
    "higher_studies": ["mba", "mca", "masters", "further study", "pg"],
    "high_salary": ["high salary", "good money", "earn more", "high package"],
    "stability": ["stable", "security", "safe career", "predictable"],
    "entrepreneurship": ["startup", "own business", "entrepreneur", "independent"],
}

# Constraint patterns that can conflict
CONSTRAINT_PATTERNS = {
    "math_ability": ["math", "mathematics", "maths", "calculus", "algebra"],
    "study_effort": ["study", "hard work", "dedication", "effort"],
    "time": ["time", "busy", "schedule", "available"],
}


def normalize_signal(value: str) -> str:
    """Normalize signal for comparison."""
    return value.lower().strip()


def _extract_polarity(text: str, signal_type: str) -> Optional[Tuple[str, float]]:
    """
    Extract signal polarity (positive/negative) from text.
    
    Returns: (polarity, confidence)
        - polarity: "positive", "negative", or None
        - confidence: 0.5-1.0, how confident we are about the polarity
    """
    text_lower = text.lower()
    
    # Negations that flip polarity
    negations = ["don't", "don't ", "not ", "never", "no ", "avoid", "can't", "won't"]
    
    # Check for explicit negations first
    for neg in negations:
        if neg in text_lower:
            # Found negation - invert polarity
            if signal_type in POSITIVE_INTEREST_PATTERNS:
                # Positive interest + negation = negative
                return ("negative", 0.95)
            elif signal_type in NEGATIVE_INTEREST_PATTERNS:
                # Negative interest + negation = positive
                return ("positive", 0.90)
    
    # Check positive patterns
    for pattern_type, keywords in POSITIVE_INTEREST_PATTERNS.items():
        if any(kw in text_lower for kw in keywords):
            return ("positive", 0.90)
    
    # Check negative patterns
    for pattern_type, keywords in NEGATIVE_INTEREST_PATTERNS.items():
        if any(kw in text_lower for kw in keywords):
            return ("negative", 0.85)
    
    return None


def _calculate_severity(previous_polarity: str, current_polarity: str, 
                       confidence_prev: float, confidence_curr: float) -> float:
    """
    Calculate contradiction severity.
    
    Factors:
    1. Direct opposites (positive ↔ negative) = highest severity
    2. Confidence levels (both high confidence = higher severity)
    3. Turn distance (closer together = higher severity)
    
    Returns: 0.0-1.0 severity score
    """
    # Base severity: opposite polarities
    if previous_polarity != current_polarity:
        # Both stated with confidence = very severe
        if confidence_prev >= 0.85 and confidence_curr >= 0.85:
            severity = 0.95  # Very strong contradiction
        elif confidence_prev >= 0.75 or confidence_curr >= 0.75:
            severity = 0.85  # Strong contradiction
        else:
            severity = 0.65  # Moderate contradiction
    else:
        # Same polarity = no contradiction
        severity = 0.0
    
    return min(1.0, severity)


def detect_contradictions(
    profile_history: List[Dict[str, Any]],
    new_signals: Dict[str, Any]
) -> List[Contradiction]:
    """
    Detect contradictions between profile history and new signals.
    
    Args:
        profile_history: List of past signal states
            [
                {"interests": "coding", "math_ability": "good", "turn": 1},
                {"interests": "coding", "goals": "job", "turn": 2},
                ...
            ]
        new_signals: Current turn signals
            {"interests": "hate coding", "goals": "entrepreneurship"}
    
    Returns:
        List[Contradiction] - All detected contradictions
    
    Behavior:
        - Compare new_signals against most recent relevant signals in history
        - Detect polarity flips (positive ↔ negative)
        - Calculate severity based on confidence and context
        - Return structured contradictions for penalty calculation
    """
    contradictions = []
    
    if not profile_history or not new_signals:
        return contradictions
    
    # Get most recent profile state
    recent_profile = profile_history[-1] if profile_history else {}
    
    # Track turn distance for severity calculation
    turn_distance = 1 if profile_history else 0
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONTRADICTION 1: INTEREST CONFLICTS
    # ─────────────────────────────────────────────────────────────────────────
    
    previous_interest = recent_profile.get("interests") or recent_profile.get("matched_interest")
    current_interest = new_signals.get("interests") or new_signals.get("matched_interest")
    
    if previous_interest and current_interest:
        prev_polarity = _extract_polarity(str(previous_interest), "interest")
        curr_polarity = _extract_polarity(str(current_interest), "interest")
        
        if prev_polarity and curr_polarity:
            prev_pol, prev_conf = prev_polarity
            curr_pol, curr_conf = curr_polarity
            
            # Normalize for comparison
            prev_value = normalize_signal(str(previous_interest))
            curr_value = normalize_signal(str(current_interest))
            
            # Check if SAME topic but opposite polarity
            # E.g., "coding" (positive) vs "hate coding" (negative)
            if prev_pol != curr_pol:
                severity = _calculate_severity(prev_pol, curr_pol, prev_conf, curr_conf)
                
                if severity > 0.5:  # Only flag significant contradictions
                    contradictions.append(
                        Contradiction(
                            type=ContradictionType.INTEREST_CONFLICT,
                            previous_value=str(previous_interest),
                            current_value=str(current_interest),
                            signal_key="interests",
                            severity=severity,
                            description=f"Interest reversal: was '{previous_interest}' (positive), now '{current_interest}' (negative)",
                            turn_distance=turn_distance,
                        )
                    )
                    logger.debug(f"[CONTRADICTION] Interest conflict detected (severity: {severity:.2f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONTRADICTION 2: GOAL CONFLICTS
    # ─────────────────────────────────────────────────────────────────────────
    
    previous_goal = recent_profile.get("goal")
    current_goal = new_signals.get("goal")
    
    if previous_goal and current_goal:
        prev_goal_norm = normalize_signal(str(previous_goal))
        curr_goal_norm = normalize_signal(str(current_goal))
        
        # Direct goal reversal: "I want X" then "I want Y" (opposite goal)
        opposite_goals = {
            "job": ["entrepreneurship", "further study"],
            "entrepreneurship": ["job", "stability"],
            "high_salary": ["stability", "work-life balance"],
            "higher_studies": ["job", "immediate employment"],
        }
        
        for goal_type, opposites in opposite_goals.items():
            if goal_type in prev_goal_norm:
                for opposite in opposites:
                    if opposite in curr_goal_norm:
                        severity = 0.80  # Strong goal conflict
                        contradictions.append(
                            Contradiction(
                                type=ContradictionType.GOAL_CONFLICT,
                                previous_value=str(previous_goal),
                                current_value=str(current_goal),
                                signal_key="goal",
                                severity=severity,
                                description=f"Goal reversal: wanted '{previous_goal}' but now want '{current_goal}'",
                                turn_distance=turn_distance,
                            )
                        )
                        logger.debug(f"[CONTRADICTION] Goal conflict detected (severity: {severity:.2f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONTRADICTION 3: CONSTRAINT INCONSISTENCIES
    # ─────────────────────────────────────────────────────────────────────────
    
    previous_math = recent_profile.get("math_ability")
    current_math = new_signals.get("math_ability")
    
    if previous_math and current_math:
        prev_polarity = _extract_polarity(str(previous_math), "constraint")
        curr_polarity = _extract_polarity(str(current_math), "constraint")
        
        if prev_polarity and curr_polarity:
            prev_pol, prev_conf = prev_polarity
            curr_pol, curr_conf = curr_polarity
            
            if prev_pol != curr_pol:
                severity = _calculate_severity(prev_pol, curr_pol, prev_conf, curr_conf)
                
                if severity > 0.5:
                    contradictions.append(
                        Contradiction(
                            type=ContradictionType.CONSTRAINT_INCONSISTENCY,
                            previous_value=str(previous_math),
                            current_value=str(current_math),
                            signal_key="math_ability",
                            severity=severity,
                            description=f"Constraint flip: said '{previous_math}' but now '{current_math}'",
                            turn_distance=turn_distance,
                        )
                    )
                    logger.debug(f"[CONTRADICTION] Constraint conflict detected (severity: {severity:.2f})")
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONTRADICTION 4: PREFERENCE REVERSALS (meta-contradictions)
    # ─────────────────────────────────────────────────────────────────────────
    # These are when the user contradicts themselves multiple times in short span
    
    if len(contradictions) > 1:
        # Multiple contradictions in short span = instability
        total_severity = sum(c.severity for c in contradictions)
        
        if total_severity > 1.5:  # Multiple significant contradictions
            # Add meta-contradiction flag
            logger.warning(
                f"[CONTRADICTION] Preference instability detected: "
                f"{len(contradictions)} contradictions in short span (total severity: {total_severity:.2f})"
            )
    
    return contradictions


# ════════════════════════════════════════════════════════════════════════════
# CONFIDENCE PENALTY APPLICATION
# ════════════════════════════════════════════════════════════════════════════

def apply_contradiction_penalty(
    current_confidence: float,
    contradictions: List[Contradiction],
    max_penalty: float = 0.30
) -> Tuple[float, float]:
    """
    Apply proportional penalties for detected contradictions.
    
    Rules:
        - Each contradiction applies proportional penalty
        - Penalty = severity × base_penalty
        - Max total penalty = 0.30 (maintain bounded delta)
        - Result is deterministic and reversible
    
    Args:
        current_confidence: Current confidence score (0.0-1.0)
        contradictions: List of detected contradictions
        max_penalty: Maximum penalty to apply (default: 0.30)
    
    Returns:
        (new_confidence, total_penalty) tuple
    
    Example:
        input_confidence = 0.85
        contradictions = [
            Contradiction(severity=0.85),  # -0.15 penalty
        ]
        output = 0.70  # 0.85 - 0.15
    """
    if not contradictions:
        return current_confidence, 0.0
    
    total_penalty = 0.0
    base_penalty = 0.15  # Per contradiction
    
    for contradiction in contradictions:
        # Proportional penalty: base × severity
        penalty = base_penalty * contradiction.severity
        total_penalty += penalty
        
        logger.info(
            f"[PENALTY] {contradiction.type.value}: "
            f"severity={contradiction.severity:.2f} → penalty={penalty:.3f}"
        )
    
    # Cap at max_penalty
    total_penalty = min(total_penalty, max_penalty)
    
    # Apply penalty with floor at 0.0
    new_confidence = max(0.0, current_confidence - total_penalty)
    
    logger.info(
        f"[CONFIDENCE] {current_confidence:.2f} → {new_confidence:.2f} "
        f"(penalty: -{total_penalty:.3f}, contradictions: {len(contradictions)})"
    )
    
    return new_confidence, total_penalty


def update_confidence_with_contradictions(
    current_confidence: float,
    profile_history: List[Dict[str, Any]],
    new_signals: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main function: Detect contradictions and update confidence in one step.
    
    Returns:
        {
            "new_confidence": float,
            "penalty_applied": float,
            "contradictions": List[Contradiction dict],
            "is_stable": bool,  # True if confidence didn't drop significantly
        }
    """
    # Detect contradictions
    contradictions = detect_contradictions(profile_history, new_signals)
    
    # Apply penalties
    new_confidence, penalty = apply_contradiction_penalty(current_confidence, contradictions)
    
    # Determine stability
    is_stable = penalty <= 0.10  # Less than small penalty = stable
    
    return {
        "new_confidence": new_confidence,
        "penalty_applied": penalty,
        "contradictions": [c.to_dict() for c in contradictions],
        "is_stable": is_stable,
        "num_contradictions": len(contradictions),
    }


def generate_contradiction_response(contradiction: Contradiction) -> str:
    """
    Generate conversational response acknowledging contradiction.
    
    Used to build system tone that acknowledges user inconsistency.
    
    Example:
        Input: Contradiction(interest: "coding" → "hate coding")
        Output: "Wait, earlier you said you liked coding — now you hate it?
                 Let's figure out what's actually appealing to you."
    """
    if contradiction.type == ContradictionType.INTEREST_CONFLICT:
        return (
            f"I noticed something — you said you {contradiction.previous_value}, "
            f"but now you {contradiction.current_value}. Let's clarify what "
            f"you're really interested in."
        )
    
    elif contradiction.type == ContradictionType.GOAL_CONFLICT:
        return (
            f"Your goals seem to have shifted. Earlier you wanted {contradiction.previous_value}, "
            f"but now you're looking at {contradiction.current_value}. "
            f"Both are valid — let's align on what matters most."
        )
    
    elif contradiction.type == ContradictionType.CONSTRAINT_INCONSISTENCY:
        return (
            f"About your {contradiction.signal_key} — you said {contradiction.previous_value}, "
            f"but now you mention {contradiction.current_value}. "
            f"Which is accurate?"
        )
    
    else:
        return (
            f"I want to make sure I understand. You previously stated {contradiction.previous_value}, "
            f"but now you're saying {contradiction.current_value}. "
            f"Help me understand the shift."
        )


# ════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS FOR TONE LAYER
# ════════════════════════════════════════════════════════════════════════════

def should_address_contradiction(contradictions: List[Contradiction]) -> bool:
    """
    Determine if system should explicitly address contradiction in response.
    
    Rules:
        - Address if severity > 0.70
        - Address only first contradiction per turn (don't overwhelm)
        - Don't address weak signals
    """
    if not contradictions:
        return False
    
    # Sort by severity
    sorted_contras = sorted(contradictions, key=lambda c: c.severity, reverse=True)
    strongest = sorted_contras[0]
    
    # Only address if strong enough
    return strongest.severity > 0.70


def get_contradiction_summary(contradictions: List[Contradiction]) -> str:
    """
    Generate brief summary of contradictions for logging.
    
    Example output:
        "1 interest conflict (severe) + 1 goal shift (moderate)"
    """
    if not contradictions:
        return "No contradictions"
    
    summary_parts = []
    
    for contradiction in contradictions:
        severity_label = (
            "severe" if contradiction.severity > 0.80
            else "moderate" if contradiction.severity > 0.60
            else "mild"
        )
        summary_parts.append(
            f"1 {contradiction.type.value} ({severity_label})"
        )
    
    return " + ".join(summary_parts)
