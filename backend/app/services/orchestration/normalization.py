"""
Query Normalization - Convert user language to system language

This layer normalizes common synonyms and variations BEFORE intent detection.
This prevents rule explosion and keeps the system maintainable.

Built from real user data during Phase 2.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# NORMALIZATION RULES - Built from real user queries
# These will be populated during Phase 2 based on actual user behavior
# ═══════════════════════════════════════════════════════════════════════════

SYNONYM_NORMALIZATION = {
    # ═══════════════════════════════════════════════════════════════════════════
    # DISCIPLINE: Only add rules with 5+ log occurrences
    # Each rule must have evidence from real user queries
    # ═══════════════════════════════════════════════════════════════════════════
    
    # FEES synonyms (add only after Phase 2 logs confirm frequency)
    # "cost": "fees",        # Add if seen 5+ times in logs
    # "price": "fees",       # Add if seen 5+ times in logs
    
    # ADMISSION synonyms (add only after Phase 2 logs confirm frequency)
    # "apply": "admission",  # Add if seen 5+ times in logs
    # "join": "admission",   # Add if seen 5+ times in logs
    
    # COURSES synonyms (add only after Phase 2 logs confirm frequency)
    # "program": "courses",  # Add if seen 5+ times in logs
    
    # Start empty. Populate from Phase 2 logs.
}

PHRASE_NORMALIZATION = {
    # ═══════════════════════════════════════════════════════════════════════════
    # DISCIPLINE: Only add patterns with evidence from Phase 2 logs
    # Start with strong patterns, add more only if logs confirm
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Strong patterns (likely to appear in real queries)
    # r"how to\s+(\w+)": "admission",  # "how to apply" → admission (add if seen 5+ times)
    
    # Exploratory patterns (add only if logs confirm frequency)
    # r"i like\s+(\w+)": "guidance",  # "i like coding" → guidance
    # r"which\s+(\w+)\s+is\s+best": "guidance",  # "which course is best" → guidance
    
    # Start empty. Populate from Phase 2 logs.
}


def normalize_query(query: str) -> str:
    """
    Normalize user query by replacing synonyms with standard forms.
    
    This is applied BEFORE intent detection to improve coverage.
    
    Example:
        "how much does it cost" → "how much does it fees"
        "what's the price" → "what's the fees"
    """
    normalized = query.lower()
    
    # Apply synonym normalization
    for user_term, standard_term in SYNONYM_NORMALIZATION.items():
        # Use word boundaries to avoid partial matches
        pattern = rf"\b{re.escape(user_term)}\b"
        normalized = re.sub(pattern, standard_term, normalized, flags=re.IGNORECASE)
    
    logger.debug(f"[NORMALIZATION] '{query}' → '{normalized}'")
    return normalized


def extract_phrase_intent(query: str) -> tuple:
    """
    Extract intent from phrase patterns.
    
    Returns: (intent, confidence)
    
    Example:
        "how to apply" → ("admission", 0.8)
        "what is bca like" → ("info", 0.7)
    """
    query_lower = query.lower()
    
    for pattern, intent in PHRASE_NORMALIZATION.items():
        if re.search(pattern, query_lower):
            logger.debug(f"[PHRASE_INTENT] Pattern '{pattern}' matched → {intent}")
            return (intent, 0.7)
    
    return (None, 0.0)


def get_normalization_stats() -> dict:
    """
    Return statistics about normalization rules.
    
    Useful for monitoring what's being normalized.
    """
    return {
        "synonym_rules": len(SYNONYM_NORMALIZATION),
        "phrase_rules": len(PHRASE_NORMALIZATION),
        "total_rules": len(SYNONYM_NORMALIZATION) + len(PHRASE_NORMALIZATION),
        "synonyms": SYNONYM_NORMALIZATION,
        "phrases": PHRASE_NORMALIZATION,
    }


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2 WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════
"""
During Phase 2 (after collecting 50 real user queries):

1. Extract synonym clusters from logs
   Example: "cost" (7x), "price" (3x), "charges" (2x) → all mean "fees"

2. Add to SYNONYM_NORMALIZATION
   "cost": "fees",
   "price": "fees",
   "charges": "fees",

3. Extract phrase patterns from logs
   Example: "how to apply" (5x), "how to join" (3x) → both mean "admission"

4. Add to PHRASE_NORMALIZATION
   r"how to\s+(apply|join)": "admission",

5. Re-deploy and verify improvement

This prevents rule explosion and keeps the system maintainable.
"""
