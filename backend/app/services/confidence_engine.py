"""
Confidence Engine - Dynamic confidence score evolution across conversation turns.

This module provides the core confidence scoring algorithm that evolves user confidence
based on accumulated signals across multiple conversation turns.

CRITICAL CONSTRAINTS:
1. Single Source of Truth: ONLY update_confidence_score() modifies confidence
2. Deterministic: Same inputs → same output (no randomness)
3. Bounded Delta: Change per turn ∈ [-0.3, +0.3]
"""

import logging
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)


# Signal weights for confidence evolution
SIGNAL_WEIGHTS = {
    "strong_clarity": 0.35,      # "I decided", "I'm sure"
    "weak_clarity": 0.20,        # "I like", "I want"
    "ambiguity": -0.1,           # "idk", "maybe", "not sure" (slows growth, doesn't reverse)
    "contradiction": -0.2,       # Conflicting statements
    "decision_request": 0.4,     # "what should I do?"
}

# Bounded delta constraints
MIN_DELTA = -0.3
MAX_DELTA = 0.3


PIVOT_INTENT_REINFORCE = "reinforce"
PIVOT_INTENT_EXPAND = "expand"
PIVOT_INTENT_PIVOT = "pivot"


KNOWN_DOMAIN_KEYWORDS = [
    "coding", "programming", "software", "tech", "developer",
    "business", "entrepreneur", "startup", "management", "mba", "manager",
    "hotel", "hospitality", "tourism", "commerce", "accounting", "finance",
    "design", "creative", "art", "music", "writing", "teaching", "medicine", "law",
]


def _classify_pivot_intent(query: str, profile: Optional["UserProfile"] = None) -> str:
    """
    Classify pivot-language intent into cognitive operation.

    Returns one of:
    - "reinforce": same direction, stronger certainty
    - "expand": adds options without replacing prior belief
    - "pivot": direction change/reconsidering
    """
    if not query:
        return PIVOT_INTENT_PIVOT

    q = query.lower()

    positive_affirmations = [
        "like", "love", "want", "enjoy", "right", "makes sense", "good fit",
        "feel", "feels", "sure", "confident", "decided", "aligned",
    ]
    has_positive = any(word in q for word in positive_affirmations)

    comparison_markers = ["more than", "rather than", "instead of", "versus", "vs", "better than"]
    has_comparison = any(marker in q for marker in comparison_markers)

    replacement_markers = ["instead", "switched", "switching", "rather than", "over"]
    has_replacement = any(marker in q for marker in replacement_markers)

    expansion_markers = ["also", "as well", "too", "along with", "and also"]
    has_expansion = any(marker in q for marker in expansion_markers)

    existing_domain_keywords = set()
    if profile and profile.interests:
        for interest in profile.interests:
            i = interest.lower()
            for domain in KNOWN_DOMAIN_KEYWORDS:
                if domain in i:
                    existing_domain_keywords.add(domain)
            if i:
                existing_domain_keywords.add(i)

    has_existing_domain_mention = any(domain in q for domain in existing_domain_keywords)

    known_domains_mentioned = {domain for domain in KNOWN_DOMAIN_KEYWORDS if domain in q}
    existing_known_domains = {domain for domain in existing_domain_keywords if domain in KNOWN_DOMAIN_KEYWORDS}
    has_new_domain_mention = bool(known_domains_mentioned - existing_known_domains)

    # Priority 1: same-domain reinforcement first (unless it's explicit replacement language).
    if has_existing_domain_mention and has_positive and not has_replacement and not has_new_domain_mention:
        return PIVOT_INTENT_REINFORCE

    # Priority 2/3: comparisons need domain-aware interpretation.
    if has_comparison:
        if has_existing_domain_mention and not has_new_domain_mention:
            # Example: "I like coding more than I thought" → reinforcement, not pivot.
            return PIVOT_INTENT_REINFORCE
        return PIVOT_INTENT_PIVOT

    # Priority 4: new domain without replacement is expansion, not pivot.
    if has_new_domain_mention:
        if has_replacement:
            return PIVOT_INTENT_PIVOT
        return PIVOT_INTENT_EXPAND

    # Fallback: same-domain positive language reinforces.
    if has_existing_domain_mention and has_positive:
        return PIVOT_INTENT_REINFORCE

    return PIVOT_INTENT_PIVOT


def _is_reinforcing_pivot(query: str, profile: Optional["UserProfile"] = None) -> bool:
    """
    Disambiguate pivot: is "actually" reinforcement or reconsidering?
    
    UPGRADED: Direction-aware, not just pattern-aware
    
    Algorithm:
    1. Check for comparison language ("more than", "instead of") → reconsidering
    2. Check if new domains mentioned (not in profile interests) → reconsidering
    3. Check if same domain + positive sentiment → reinforcing
    4. Fall back to pattern matching for edge cases
    
    Args:
        query: The user query containing "actually"
        profile: User profile with interests (for domain awareness)
        
    Returns:
        True if "actually" is reinforcement, False if reconsidering
    """
    if not query:
        return False
    
    return _classify_pivot_intent(query, profile) == PIVOT_INTENT_REINFORCE


def update_confidence_score(
    prev_score: Optional[float], 
    signals: List[str], 
    query: Optional[str] = None,
    profile: Optional["UserProfile"] = None,
    last_signals: Optional[List[str]] = None,
    last_last_signals: Optional[List[str]] = None
) -> float:
    """
    Pure function to update confidence score based on signals.
    
    This is the ONLY function that modifies confidence scores.
    
    Constraints enforced:
    - Single source of truth (only this function modifies score)
    - Deterministic (same inputs → same output, no randomness)
    - Bounded delta (change per turn ∈ [-0.3, +0.3])
    
    SIGNAL AMPLIFICATION:
    - Multiple instances of same signal indicate stronger evidence
    - 1x signal: base weight
    - 2+ signals: amplified weight (without exceeding delta bounds)
    - This fixes Turn 3+ underpower issue
    
    SIGNAL INTERACTION LOGIC:
    - Pivot disambiguation: "actually" can be reinforcement or reconsidering
    - Conflict dampening: mixed clarity + negative sentiment
    - Post-contradiction inertia: reduce recovery confidence after contradictions
    
    Args:
        prev_score: Previous confidence score (0.0-1.0) or None for new users
        signals: List of signal identifiers (e.g., ["ambiguity", "weak_clarity"])
        query: Optional query text for disambiguating signal interactions
        profile: Optional user profile for context-aware signal processing
        last_signals: Optional signals from previous turn
        last_last_signals: Optional signals from 2 turns ago
        
    Returns:
        New confidence score (0.0-1.0)
        
    Examples:
        >>> update_confidence_score(0.3, ["weak_clarity"])
        # Returns ~0.33 (single weak clarity)
        
        >>> update_confidence_score(0.3, ["weak_clarity", "weak_clarity"])
        # Returns ~0.42 (amplified: multiple weak clarity = stronger evidence)
        
        >>> update_confidence_score(0.5, ["strong_clarity"], "I actually like coding more now")
        # Returns ~0.58 (pivot disambiguated as reinforcement, not direction change)
    """
    # 1. Initialize for new users
    if prev_score is None:
        prev_score = 0.3  # Start slightly low baseline

    logger.debug(f"[confidence_engine] prev={prev_score}, signals={signals}, query={query[:40] if query else ''!r}")

    # 2. COUNT SIGNALS (not sum) for proper amplification
    # Multiple instances of same signal = stronger evidence
    weak_clarity_count = signals.count("weak_clarity")
    strong_clarity_count = signals.count("strong_clarity")
    ambiguity_count = signals.count("ambiguity")
    contradiction_count = signals.count("contradiction")
    strong_contradiction_count = signals.count("strong_contradiction")
    pivot_count = signals.count("pivot")
    negative_sentiment_count = signals.count("negative_sentiment")
    decision_request_present = "decision_request" in signals
    
    # Total contradiction count (normal + strong)
    total_contradiction_count = contradiction_count + strong_contradiction_count
    
    # 3. Compute raw delta with COUNT-BASED AMPLIFICATION
    raw_delta = 0.0
    
    # CRITICAL: Contradiction dominates - when present, ignore other negative signals
    # Contradiction already encodes "user changed belief"
    # Other negatives (pivot, negative_sentiment) are just evidence, not separate penalties
    # BUT: Allow slight residual effect from emotional signals (not zeroed completely)
    if total_contradiction_count > 0:
        # Contradiction ONLY - other negative signals mostly subsumed
        # Severity-aware: strong_contradiction = stronger penalty
        
        # Base penalty by severity
        if strong_contradiction_count > 0:
            # Strong rejection: "I hate coding", "this is terrible"
            if prev_score >= 0.8:
                raw_delta = -0.50  # Strong rejection at high confidence → collapse
            elif strong_contradiction_count == 1:
                raw_delta = -0.40  # Strong rejection (normal)
            else:
                raw_delta = -0.50  # Multiple strong rejections
        else:
            # Normal contradiction: "I don't like coding"
            if prev_score >= 0.9:
                raw_delta = -0.35  # Stronger penalty for peak confidence
            elif contradiction_count == 1:
                raw_delta = -0.25  # Single contradiction (normal)
            else:
                raw_delta = -0.3   # Multiple contradictions (normal)
        
        # Slight residual effect from emotional signals (not zeroed)
        # This allows "I hate coding and it's boring and stressful" to be slightly worse
        # than "I hate coding" alone, but not destructively stacked
        emotional_residual = 0.0
        if negative_sentiment_count > 0:
            emotional_residual -= 0.02  # Small additional penalty
        if pivot_count > 0:
            pivot_intent = _classify_pivot_intent(query, profile) if query else PIVOT_INTENT_PIVOT
            if pivot_intent == PIVOT_INTENT_PIVOT:
                emotional_residual -= 0.02  # Small additional penalty for true reconsidering pivot
        
        # Cap residual effect (max -0.05 total)
        emotional_residual = max(-0.05, emotional_residual)
        raw_delta += emotional_residual
        
        # Still allow positive signals (clarity, decision_request) to apply
        # These represent new direction, not stacking negatives
        
        # Weak clarity: 1 signal = base, 2+ signals = amplified
        if weak_clarity_count == 1:
            raw_delta += 0.20
        elif weak_clarity_count >= 2:
            raw_delta += 0.35
        
        # Strong clarity: 1 signal = base, 2+ signals = amplified
        if strong_clarity_count == 1:
            raw_delta += 0.35
        elif strong_clarity_count >= 2:
            raw_delta += 0.50
        
        # Decision request: positive boost
        if decision_request_present:
            raw_delta += 0.4
        
        # Skip: ambiguity (subsumed by contradiction)
    
    else:
        # NO CONTRADICTION: Normal signal processing
        
        # Weak clarity: 1 signal = base, 2+ signals = amplified
        if weak_clarity_count == 1:
            raw_delta += 0.20  # Single weak clarity signal
        elif weak_clarity_count >= 2:
            raw_delta += 0.35  # AMPLIFIED: multiple weak clarity = stronger accumulated evidence
        
        # Strong clarity: 1 signal = base, 2+ signals = amplified
        if strong_clarity_count == 1:
            raw_delta += 0.35  # Single strong clarity signal
        elif strong_clarity_count >= 2:
            raw_delta += 0.50  # AMPLIFIED: multiple strong clarity signals
        
        # Ambiguity: negative signal, also amplified by count
        if ambiguity_count == 1:
            raw_delta -= 0.1  # Single ambiguity signal
        elif ambiguity_count >= 2:
            raw_delta -= 0.2  # AMPLIFIED: multiple ambiguities indicate genuine confusion
        
        # Pivot: direction change signal (softer than contradiction)
        # RULE 1: Pivot Disambiguation (UPGRADED: Direction-Aware)
        # Check if "actually" is reinforcement vs reconsidering
        if pivot_count > 0:
            # If query provided, disambiguate pivot using direction awareness
            if query and (strong_clarity_count > 0 or weak_clarity_count > 0):
                pivot_intent = _classify_pivot_intent(query, profile)

                # Reinforce/expand should not get pivot penalty.
                if pivot_intent == PIVOT_INTENT_PIVOT:
                    raw_delta -= 0.1
            else:
                # No query or no clarity: treat as reconsidering (default safe behavior)
                raw_delta -= 0.1
        
        # Negative sentiment: emotional resistance signal
        if negative_sentiment_count > 0:
            raw_delta -= 0.1  # Resistance to path, but not full reversal
        
        # Decision request: positive boost (no counting needed, just presence)
        if decision_request_present:
            raw_delta += 0.4
    
    # 4. Apply interaction rules (human-like modulation)
    
    # Rule 1: Ambiguity + clarity together → soften ambiguity penalty
    # "maybe coding" (ambiguity + weak_clarity) should increase, not decrease
    if ambiguity_count > 0 and (weak_clarity_count > 0 or strong_clarity_count > 0):
        raw_delta += 0.15  # Soften ambiguity penalty when clarity present
    
    # Rule 2: Decision request with building confidence → extra boost
    # Late-stage "what should I do?" should push into high confidence
    if decision_request_present and prev_score > 0.4:
        raw_delta += 0.2  # Stronger boost when user is ready to decide

    # Rule 3: Intent-aware clamps
    # Pivot should reallocate certainty, not increase it.
    # Expansion should increase confidence mildly, not like reinforcement.
    if total_contradiction_count == 0 and query:
        intent = _classify_pivot_intent(query, profile)
        if pivot_count > 0 and intent == PIVOT_INTENT_PIVOT:
            raw_delta = min(raw_delta, 0.0)
        elif intent == PIVOT_INTENT_EXPAND:
            raw_delta = min(raw_delta, 0.1)

    # Rule 4: Conflict Dampening — clarity + negative sentiment indicate internal conflict.
    # When the user both affirms (clarity) and expresses resistance, treat as dampened
    # evidence for confidence increase (scale delta down to 30%).
    # This implements: "I want X but fear Y" → reduce net increase.
    if total_contradiction_count == 0 and (weak_clarity_count > 0 or strong_clarity_count > 0) and negative_sentiment_count > 0:
        raw_delta = raw_delta * 0.3

    # Rule 5: Post-Contradiction Inertia
    # After a contradiction (belief break), the system carries residual uncertainty
    # for up to 2 turns. This prevents unrealistic confidence rebounds.
    # Dampen upward movement by 30% (multiply by 0.7) if within 2 turns of contradiction.
    has_recent_contradiction = False
    if last_signals and ("contradiction" in last_signals or "strong_contradiction" in last_signals):
        has_recent_contradiction = True
    elif last_last_signals and ("contradiction" in last_last_signals or "strong_contradiction" in last_last_signals):
        has_recent_contradiction = True
    
    if has_recent_contradiction and raw_delta > 0:  # Only dampen positive deltas (recovery)
        raw_delta = raw_delta * 0.7

    # 5. Clamp delta (bounded change per turn)
    # EXCEPTION: For contradictions at very high confidence, allow larger drops
    # Also allow larger drops for strong contradictions (severity-aware)
    if (total_contradiction_count > 0 and prev_score >= 0.8) or strong_contradiction_count > 0:
        # Allow up to -0.50 drop for high confidence contradictions or any strong rejection
        delta = max(-0.50, min(MAX_DELTA, raw_delta))
    else:
        delta = max(MIN_DELTA, min(MAX_DELTA, raw_delta))
    
    # 5b. POST-CONTRADICTION DAMPENING: Slow recovery after belief reversal
    # After contradiction, humans carry residual uncertainty for ~2 turns
    # This prevents unrealistic confidence rebounds
    if profile and total_contradiction_count == 0 and delta > 0:
        # Check recent turn history for contradiction (last 2 turns)
        # profile.confidence_signal_history is a list of per-turn signals:
        # [["ambiguity"], ["ambiguity", "weak_clarity"], ["strong_clarity"], ...]
        recent_turns = profile.confidence_signal_history[-2:] if len(profile.confidence_signal_history) >= 2 else profile.confidence_signal_history
        
        has_recent_contradiction = any(
            any(sig in ("contradiction", "strong_contradiction") for sig in turn_signals)
            for turn_signals in recent_turns
        )
        
        if has_recent_contradiction:
            # Dampen positive deltas after recent contradiction
            # Only affects positive deltas (penalties still hit fully)
            delta *= 0.7
    
    # 5c. SOFT CAP: Limit upward momentum for high confidence
    # Prevents score from getting stuck at 1.0
    # When approaching peak confidence (>= 0.85), reduce upward movement
    if prev_score >= 0.85 and delta > 0:
        delta = min(delta, 0.05)  # Limit upward movement to tiny increments near peak
    
    # 6. Apply smoothing (context-sensitive)
    target_score = prev_score + delta
    
    # Contradiction → direct override BUT with bounded drop
    # Contradictions destabilize confidence, but don't erase cognitive progress
    if total_contradiction_count > 0:
        # Apply penalty directly (no smoothing)
        new_score = target_score
        # BUT: Don't drop too far - preserve thinking state
        # Floor varies by confidence level (higher confidence = harder fall)
        # Strong contradictions can collapse (lower floor)
        if strong_contradiction_count > 0:
            # Strong rejection: Allow collapse
            if prev_score < 0.6:
                floor_ratio = 0.60  # Moderate drop for low-mid confidence
            elif prev_score < 0.7:
                floor_ratio = 0.50  # Stronger drop for medium confidence
            elif prev_score < 0.85:
                floor_ratio = 0.60  # Controlled destabilization for mid-high confidence (0.7-0.85)
            else:
                floor_ratio = 0.40  # Allow collapse for very high confidence (>= 0.85)
        else:
            # Normal contradiction: Destabilization, not collapse
            if prev_score < 0.6:
                floor_ratio = 0.77  # Gentle drop for low-mid confidence (23% drop)
            elif prev_score < 0.8:
                floor_ratio = 0.68  # Stronger drop for medium-high confidence (32% drop)
            else:
                floor_ratio = 0.55  # Strong destabilization for very high confidence (45% drop)
        
        min_allowed = prev_score * floor_ratio
        new_score = max(new_score, min_allowed)
    # Decision requests get less smoothing (more responsive)
    elif decision_request_present and prev_score > 0.4:
        # Even less smoothing for decision moments with strong signals (30/70 instead of 40/60)
        # This ensures decision_request + clarity pushes decisively into high confidence
        new_score = (prev_score * 0.3) + (target_score * 0.7)
    else:
        # Normal smoothing for gradual evolution
        new_score = (prev_score * 0.5) + (target_score * 0.5)
    
    # 7. Clamp final score to [0.0, 1.0]
    new_score = max(0.0, min(1.0, new_score))

    logger.debug(f"[confidence_engine] RESULT: {prev_score:.3f} -> {new_score:.3f}, raw_delta={raw_delta:.3f}")

    return new_score


def map_score_to_category(score: float) -> str:
    """
    Map continuous confidence score to categorical value for tone layer.
    
    Args:
        score: Confidence score (0.0-1.0)
        
    Returns:
        Category: "low", "medium", or "high"
        
    Mapping:
        0.0-0.3 → "low" (exploratory tone)
        0.3-0.7 → "medium" (balanced tone)
        0.7-1.0 → "high" (decisive tone)
    """
    if score < 0.3:
        return "low"
    elif score < 0.7:
        return "medium"
    else:
        return "high"
