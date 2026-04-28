"""
Production Decision Detector - Confidence-Based

Layered approach:
1. Fast normalization (cheap + deterministic)
2. Fuzzy matching (handles typos + variations)
3. Pattern intent (regex for complex patterns)
4. Context-aware boost (short positive replies)

Returns confidence score to prevent false positives.
"""

import re
import logging
from typing import Dict, Tuple
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# ============================================
# LAYER 1: NORMALIZATION
# ============================================
def normalize(text: str) -> str:
    """Fast normalization - lowercase + strip"""
    return text.lower().strip()


# ============================================
# LAYER 2: DECISION PHRASES (for fuzzy matching)
# ============================================
DECISION_PHRASES = [
    # Explicit decisions
    "sounds good",
    "looks good",
    "that works",
    "this works",
    "i'll go with this",
    "let's go with this",
    "i choose this",
    "i prefer this",
    "going with this",
    
    # Implicit decisions
    "yeah okay",
    "yeah ok",
    "okay cool",
    "alright sure",
    "makes sense",
    "that's good",
    "sounds right",
    
    # Course-specific
    "bca sounds good",
    "bba sounds good",
    "i'll do bca",
    "i'll do bba",
]

# Short positive replies (context-dependent)
SHORT_POSITIVE = [
    "yeah",
    "yes",
    "okay",
    "ok",
    "sure",
    "fine",
    "cool",
    "alright",
    "yep",
    "yup"
]

# Neutral/ambiguous replies (NOT decisions)
NEUTRAL_AMBIGUOUS = [
    "hmm",
    "maybe",
    "let me think",
    "not sure",
    "idk",
    "i don't know",
    "confused"
]


# ============================================
# LAYER 3: PATTERN INTENT (regex)
# ============================================
DECISION_PATTERNS = [
    r"\bi think\b.*\b(bca|bba|mba|bcom|bhm|mca)\b",
    r"\bi'll go with\b",
    r"\blet's go with\b",
    r"\bgo with\b.*\b(bca|bba|mba|bcom|bhm|mca)\b",
    r"\bchoose\b.*\b(bca|bba|mba|bcom|bhm|mca)\b",
    r"\bprefer\b.*\b(bca|bba|mba|bcom|bhm|mca)\b",
    r"\btake\b.*\b(bca|bba|mba|bcom|bhm|mca)\b",
    r"\bfinal\b.*\b(bca|bba|mba|bcom|bhm|mca)\b",
]


# ============================================
# LAYER 4: FUZZY MATCHING
# ============================================
def fuzzy_match_decision(query: str, threshold: int = 80) -> Tuple[bool, float]:
    """
    Fuzzy match against decision phrases.
    Returns (is_match, confidence_score)
    """
    query_norm = normalize(query)
    
    best_score = 0
    for phrase in DECISION_PHRASES:
        score = fuzz.partial_ratio(query_norm, phrase)
        best_score = max(best_score, score)
        
        if score >= threshold:
            confidence = score / 100.0
            logger.debug(f"[FUZZY_MATCH] '{query}' matched '{phrase}' (score: {score})")
            return True, confidence
    
    # Return best score even if below threshold
    return False, best_score / 100.0


def is_short_positive(query: str) -> bool:
    """Check if query is a short positive reply"""
    query_norm = normalize(query)
    words = query_norm.split()
    
    # Must be short (1-3 words)
    if len(words) > 3:
        return False
    
    # Check if contains positive word
    return any(pos in query_norm for pos in SHORT_POSITIVE)


def is_neutral_ambiguous(query: str) -> bool:
    """Check if query is neutral/ambiguous (NOT a decision)"""
    query_norm = normalize(query)
    return any(neutral in query_norm for neutral in NEUTRAL_AMBIGUOUS)


# ============================================
# LAYER 5: PATTERN MATCHING
# ============================================
def pattern_match_decision(query: str) -> Tuple[bool, float]:
    """
    Pattern-based decision detection.
    Returns (is_match, confidence_score)
    """
    query_norm = normalize(query)
    
    for pattern in DECISION_PATTERNS:
        if re.search(pattern, query_norm):
            logger.debug(f"[PATTERN_MATCH] '{query}' matched pattern: {pattern}")
            return True, 0.95  # High confidence for pattern matches
    
    return False, 0.0


# ============================================
# LAYER 6: CONTEXT-AWARE BOOST
# ============================================
def context_boost(query: str, context: Dict) -> Tuple[bool, float]:
    """
    Context-aware decision detection.
    Short positive replies count as decisions if context suggests it.
    """
    # Check if we have a top course recommendation
    has_recommendation = bool(
        context.get("top_course") or 
        context.get("courses") or
        context.get("recommended_courses")
    )
    
    if not has_recommendation:
        return False, 0.0
    
    # Check if query is short positive
    if is_short_positive(query):
        logger.debug(f"[CONTEXT_BOOST] Short positive '{query}' with recommendation context")
        return True, 0.75  # Medium-high confidence
    
    return False, 0.0


# ============================================
# MAIN DECISION DETECTOR
# ============================================
def detect_decision(query: str, context: Dict = None) -> Dict:
    """
    Production decision detector with confidence scoring.
    
    Returns:
        {
            "is_decision": bool,
            "confidence": float (0.0 to 1.0),
            "method": str (how it was detected),
            "needs_clarification": bool
        }
    """
    context = context or {}
    query_norm = normalize(query)
    
    # GUARD: Check for neutral/ambiguous first
    if is_neutral_ambiguous(query_norm):
        logger.debug(f"[DECISION_DETECTOR] '{query}' is neutral/ambiguous - NOT a decision")
        return {
            "is_decision": False,
            "confidence": 0.0,
            "method": "neutral_ambiguous",
            "needs_clarification": False
        }
    
    # LAYER 1: Pattern matching (highest confidence)
    pattern_match, pattern_conf = pattern_match_decision(query_norm)
    if pattern_match:
        return {
            "is_decision": True,
            "confidence": pattern_conf,
            "method": "pattern",
            "needs_clarification": False
        }
    
    # LAYER 2: Fuzzy matching
    fuzzy_match, fuzzy_conf = fuzzy_match_decision(query_norm)
    if fuzzy_match:
        return {
            "is_decision": True,
            "confidence": fuzzy_conf,
            "method": "fuzzy",
            "needs_clarification": fuzzy_conf < 0.85  # Ask confirmation if low confidence
        }
    
    # LAYER 3: Context boost (short positive with recommendation)
    context_match, context_conf = context_boost(query_norm, context)
    if context_match:
        return {
            "is_decision": True,
            "confidence": context_conf,
            "method": "context",
            "needs_clarification": True  # Always confirm context-based decisions
        }
    
    # NO MATCH
    # Return highest confidence score found (for debugging)
    max_conf = max(pattern_conf, fuzzy_conf, context_conf)
    return {
        "is_decision": False,
        "confidence": max_conf,
        "method": "none",
        "needs_clarification": False
    }


# ============================================
# MULTI-INTENT DETECTION
# ============================================
def detect_multi_intent(query: str) -> Dict:
    """
    Detect if query has multiple intents.
    
    Example: "BCA sounds good but what about salary and MBA options?"
    - Primary: decision (BCA)
    - Secondary: salary, MBA comparison
    """
    query_norm = normalize(query)
    
    # Multi-intent indicators
    multi_indicators = ["but", "and", "also", "what about", "however", "though"]
    has_multi = any(indicator in query_norm for indicator in multi_indicators)
    
    if not has_multi:
        return {"is_multi": False, "intents": []}
    
    # Detect secondary intents
    secondary_intents = []
    
    if any(word in query_norm for word in ["salary", "package", "pay", "earn"]):
        secondary_intents.append("salary")
    
    if any(word in query_norm for word in ["mba", "masters", "higher studies"]):
        secondary_intents.append("higher_studies")
    
    if any(word in query_norm for word in ["compare", "vs", "versus", "better"]):
        secondary_intents.append("comparison")
    
    if any(word in query_norm for word in ["fees", "cost", "price"]):
        secondary_intents.append("fees")
    
    if any(word in query_norm for word in ["placement", "jobs", "recruit"]):
        secondary_intents.append("placement")
    
    return {
        "is_multi": len(secondary_intents) > 0,
        "intents": secondary_intents
    }


# ============================================
# CLARIFICATION GENERATOR
# ============================================
def generate_clarification(query: str, context: Dict) -> str:
    """
    Generate clarification question for low-confidence decisions.
    """
    top_course = context.get("top_course") or context.get("courses", [""])[0] if context.get("courses") else "this course"
    
    clarifications = [
        f"Sounds like you're leaning toward **{top_course}** — should I lock this as your choice?",
        f"Just to confirm — are you ready to move forward with **{top_course}**?",
        f"I want to make sure I understood correctly — you're choosing **{top_course}**, right?",
    ]
    
    import random
    return random.choice(clarifications)


# ============================================
# TESTING
# ============================================
def test_decision_detector():
    """Test decision detector with various inputs"""
    print("=" * 60)
    print("DECISION DETECTOR TESTS")
    print("=" * 60)
    
    test_cases = [
        # High confidence decisions
        ("BCA sounds good", {}, True, ">0.85"),
        ("I'll go with BBA", {}, True, ">0.85"),
        ("yeah okay", {}, True, ">0.80"),
        
        # Context-based decisions
        ("yeah", {"top_course": "BCA"}, True, "0.75"),
        ("okay", {"top_course": "BBA"}, True, "0.75"),
        
        # Neutral/ambiguous (NOT decisions)
        ("hmm", {}, False, "0.0"),
        ("maybe", {}, False, "0.0"),
        ("let me think", {}, False, "0.0"),
        
        # Typos (fuzzy matching)
        ("lets go wid this", {}, True, ">0.70"),
        ("yeah ok cool", {}, True, ">0.70"),
        
        # Multi-intent
        ("BCA sounds good but what about salary", {}, True, ">0.80"),
    ]
    
    passed = 0
    failed = 0
    
    for query, context, expected_decision, expected_conf in test_cases:
        result = detect_decision(query, context)
        is_decision = result["is_decision"]
        confidence = result["confidence"]
        method = result["method"]
        
        # Check if decision matches
        decision_match = is_decision == expected_decision
        
        # Check confidence range
        if expected_conf.startswith(">"):
            threshold = float(expected_conf[1:])
            conf_match = confidence >= threshold
        else:
            conf_match = abs(confidence - float(expected_conf)) < 0.1
        
        if decision_match and conf_match:
            print(f"✅ '{query}' → {is_decision} (conf: {confidence:.2f}, method: {method})")
            passed += 1
        else:
            print(f"❌ '{query}' → {is_decision} (conf: {confidence:.2f}, method: {method}) - Expected: {expected_decision}, {expected_conf}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    test_decision_detector()
