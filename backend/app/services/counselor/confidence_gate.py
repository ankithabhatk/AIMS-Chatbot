"""
Confidence Gate - Context-Aware Interruption Logic

This is the FINAL behavioral layer that prevents annoying confirmations.

Rule 1: Don't interrupt action queries (fees, placement, how to apply)
Rule 2: Interrupt only when conversation is idle (short reply, no intent)
Rule 3: Multi-intent > confidence (always prioritize user intent richness)
Rule 4: Detect conflicting sentiment (hesitation override)
"""

import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# ============================================
# SENTIMENT VALIDATION (CRITICAL LAYER)
# ============================================
NEGATIVE_SIGNALS = [
    "not sure", "don't think", "maybe not", "no", "nah",
    "whatever", "idk", "confused", "i guess", "but what if",
    "change later", "hesitant", "doubt", "uncertain",
    "not convinced", "still thinking"
]

POSITIVE_SIGNALS = [
    "yes", "yeah", "okay", "ok", "fine", "sounds good",
    "looks good", "that works", "sure", "alright"
]

def has_conflicting_sentiment(query: str) -> bool:
    """
    Detect conflicting sentiment (positive + negative signals).
    
    This catches:
    - "yeah but not sure"
    - "okay I guess"
    - "fine whatever"
    - "yes but confused"
    
    Returns True if user is hesitant, even if they said positive words.
    """
    q = query.lower()
    
    has_pos = any(p in q for p in POSITIVE_SIGNALS)
    has_neg = any(n in q for n in NEGATIVE_SIGNALS)
    
    if has_pos and has_neg:
        logger.debug(f"[SENTIMENT_CONFLICT] Detected hesitation: '{query}'")
        return True
    
    return False

# ============================================
# ACTION INTENT DETECTION
# ============================================
ACTION_KEYWORDS = [
    "fee", "fees", "cost", "price",
    "placement", "salary", "package", "job",
    "apply", "admission", "process", "steps",
    "hostel", "campus", "facility",
    "eligibility", "duration", "curriculum",
    "how to", "what next", "tell me"
]

def has_action_intent(query: str) -> bool:
    """
    Check if query has action intent (user wants information).
    If yes, DON'T interrupt with confirmation.
    """
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in ACTION_KEYWORDS)


# ============================================
# MULTI-INTENT DETECTION
# ============================================
MULTI_INTENT_INDICATORS = ["but", "and", "also", "what about", "however", "though", "tell me"]

def has_multi_intent(query: str) -> bool:
    """
    Check if query has multiple intents.
    If yes, DON'T interrupt - answer everything first.
    """
    query_lower = query.lower()
    
    # Check for conjunction indicators
    has_conjunction = any(indicator in query_lower for indicator in MULTI_INTENT_INDICATORS)
    
    # Check for multiple question marks or multiple topics
    question_count = query.count("?")
    
    return has_conjunction or question_count > 1


# ============================================
# SHORT REPLY DETECTION
# ============================================
SHORT_POSITIVE = ["yeah", "yes", "okay", "ok", "sure", "fine", "cool", "alright", "yep", "yup"]

def is_short_reply(query: str) -> bool:
    """
    Check if query is a short reply (1-3 words, positive).
    These are the ONLY cases where we should ask confirmation.
    """
    query_lower = query.lower().strip()
    words = query_lower.split()
    
    # Must be short (1-3 words)
    if len(words) > 3:
        return False
    
    # Must contain positive word
    return any(pos in query_lower for pos in SHORT_POSITIVE)


# ============================================
# MAIN CONFIDENCE GATE
# ============================================
def should_interrupt_for_confirmation(query: str, confidence: float, context: Dict = None) -> Tuple[bool, str]:
    """
    Context-aware confidence gating with sentiment validation.
    
    Returns:
        (should_interrupt: bool, reason: str)
    
    Rules:
    0. Conflicting sentiment → ALWAYS clarify (UNLESS very high confidence)
    1. High confidence (>= 0.85) → never interrupt
    2. Multi-intent → never interrupt (PRIORITY: check before action)
    3. Has action intent → never interrupt
    4. Short reply only → interrupt
    5. Otherwise → don't interrupt
    """
    context = context or {}
    
    # Rule 0: SENTIMENT CONFLICT - OVERRIDE EVERYTHING
    # BUT: High confidence bypass (> 0.9) to avoid over-correction
    # This catches "yeah but not sure", "okay I guess", "fine whatever"
    if has_conflicting_sentiment(query):
        # High confidence bypass - trust decisive users
        if confidence > 0.9:
            logger.info(f"[CONFIDENCE_GATE] Sentiment conflict detected but HIGH CONFIDENCE ({confidence:.2f}) - bypassing: '{query}'")
            
            # FAILURE CAPTURE: Track sentiment conflict with bypass
            session_id = context.get("session_id")
            stage = context.get("current_stage", "unknown")
            if session_id:
                from app.services.counselor.production_analytics import track_sentiment_conflict
                track_sentiment_conflict(session_id, query, confidence, stage, bypassed=True)
            
            return False, "high_confidence_bypass"
        
        logger.debug(f"[CONFIDENCE_GATE] INTERRUPT - conflicting sentiment: '{query}'")
        
        # FAILURE CAPTURE: Track sentiment conflict without bypass
        session_id = context.get("session_id")
        stage = context.get("current_stage", "unknown")
        if session_id:
            from app.services.counselor.production_analytics import track_sentiment_conflict
            track_sentiment_conflict(session_id, query, confidence, stage, bypassed=False)
        
        return True, "conflicting_sentiment"
    
    # Rule 1: High confidence - never interrupt
    if confidence >= 0.85:
        logger.debug(f"[CONFIDENCE_GATE] No interrupt - high confidence: {confidence:.2f}")
        return False, "high_confidence"
    
    # Rule 2: Multi-intent - never interrupt (CHECK FIRST)
    if has_multi_intent(query):
        logger.debug(f"[CONFIDENCE_GATE] No interrupt - multi-intent detected: '{query}'")
        return False, "multi_intent"
    
    # Rule 3: Action intent - never interrupt
    if has_action_intent(query):
        logger.debug(f"[CONFIDENCE_GATE] No interrupt - action intent detected: '{query}'")
        return False, "action_intent"
    
    # Rule 4: Short reply - interrupt
    if is_short_reply(query):
        logger.debug(f"[CONFIDENCE_GATE] INTERRUPT - short reply: '{query}' (conf: {confidence:.2f})")
        return True, "short_reply"
    
    # Rule 5: Default - don't interrupt (let it flow)
    logger.debug(f"[CONFIDENCE_GATE] No interrupt - default flow: '{query}'")
    return False, "default_flow"


# ============================================
# TESTING
# ============================================
def test_confidence_gate():
    """Test confidence gate with real user queries"""
    print("=" * 60)
    print("CONFIDENCE GATE TESTS")
    print("=" * 60)
    
    test_cases = [
        # Should NOT interrupt (multi-intent takes priority)
        ("yeah tell me fees", 0.75, False, "multi_intent"),
        ("ok what about placement", 0.70, False, "multi_intent"),
        ("ok and fees?", 0.70, False, "multi_intent"),
        
        # Should NOT interrupt (action intent)
        ("fine how to apply", 0.72, False, "action_intent"),
        ("cool what next", 0.78, False, "action_intent"),
        
        # Should NOT interrupt (high confidence)
        ("BCA sounds good", 0.90, False, "high_confidence"),
        
        # SHOULD interrupt (short reply only)
        ("yeah", 0.75, True, "short_reply"),
        ("ok", 0.70, True, "short_reply"),
        ("fine", 0.72, True, "short_reply"),
        ("cool", 0.78, True, "short_reply"),
        
        # Should NOT interrupt (not short reply)
        ("I think that makes sense", 0.75, False, "default_flow"),
        ("that sounds like a good option", 0.70, False, "default_flow"),
    ]
    
    passed = 0
    failed = 0
    
    for query, confidence, expected_interrupt, expected_reason in test_cases:
        should_interrupt, reason = should_interrupt_for_confirmation(query, confidence)
        
        if should_interrupt == expected_interrupt and reason == expected_reason:
            print(f"✅ '{query}' (conf: {confidence:.2f}) → interrupt={should_interrupt}, reason={reason}")
            passed += 1
        else:
            print(f"❌ '{query}' (conf: {confidence:.2f}) → interrupt={should_interrupt}, reason={reason} (expected: {expected_interrupt}, {expected_reason})")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)


def test_sentiment_validation():
    """Test sentiment conflict detection (CRITICAL)"""
    print("\n" + "=" * 60)
    print("SENTIMENT VALIDATION TESTS (CRITICAL)")
    print("=" * 60)
    
    test_cases = [
        # SHOULD interrupt (conflicting sentiment - OVERRIDE EVERYTHING)
        ("yeah but not sure", 0.80, True, "conflicting_sentiment"),
        ("okay I guess", 0.75, True, "conflicting_sentiment"),
        ("fine whatever", 0.70, True, "conflicting_sentiment"),
        ("yes but confused", 0.80, True, "conflicting_sentiment"),
        ("ok but what if I change later", 0.75, True, "conflicting_sentiment"),
        ("yeah I don't think this is good", 0.80, True, "conflicting_sentiment"),
        ("okay but I'm not sure", 0.75, True, "conflicting_sentiment"),
        ("sounds good but maybe not", 0.80, True, "conflicting_sentiment"),
        ("alright but idk", 0.75, True, "conflicting_sentiment"),
        ("sure but still thinking", 0.70, True, "conflicting_sentiment"),
    ]
    
    passed = 0
    failed = 0
    
    for query, confidence, expected_interrupt, expected_reason in test_cases:
        should_interrupt, reason = should_interrupt_for_confirmation(query, confidence)
        
        if should_interrupt == expected_interrupt and reason == expected_reason:
            print(f"✅ '{query}' (conf: {confidence:.2f}) → INTERRUPT (reason: {reason})")
            passed += 1
        else:
            print(f"❌ '{query}' (conf: {confidence:.2f}) → interrupt={should_interrupt}, reason={reason} (expected: {expected_interrupt}, {expected_reason})")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return passed, failed


if __name__ == "__main__":
    test_confidence_gate()
    passed, failed = test_sentiment_validation()
    
    if failed == 0:
        print("\n🎉 ALL SENTIMENT VALIDATION TESTS PASSED")
        print("System now handles human hesitation correctly!")
    else:
        print(f"\n⚠️  {failed} sentiment tests failed")
