"""
Query Type Detection - Classify queries as direct, exploratory, or multi-intent

This helps route queries to the appropriate handler:
- Direct: "BCA fees" → specific intent
- Exploratory: "I like coding" → guidance + courses
- Multi-intent: "fees and hostel" → multiple intents
"""

import logging

logger = logging.getLogger(__name__)


def detect_query_type(query: str) -> str:
    """
    Detect if query is direct, exploratory, or multi-intent.
    
    Returns: "direct" | "exploratory" | "multi_intent"
    
    Examples:
        "BCA fees" → "direct"
        "I like coding what should I choose" → "exploratory"
        "fees and hostel for BCA" → "multi_intent"
    """
    query_lower = query.lower()
    
    # Multi-intent: contains "and" or multiple topics
    if " and " in query_lower:
        logger.debug(f"[QUERY_TYPE] Multi-intent detected: '{query}'")
        return "multi_intent"
    
    # Exploratory: contains guidance/preference keywords
    exploratory_keywords = [
        "like", "interested", "best", "good", "should", "choose",
        "prefer", "suitable", "right", "fit", "match", "career",
        "future", "path", "option", "alternative"
    ]
    
    if any(keyword in query_lower for keyword in exploratory_keywords):
        logger.debug(f"[QUERY_TYPE] Exploratory detected: '{query}'")
        return "exploratory"
    
    # Default: direct
    logger.debug(f"[QUERY_TYPE] Direct detected: '{query}'")
    return "direct"


def get_query_type_handler(query_type: str) -> dict:
    """
    Get routing instructions for query type.
    
    Returns: {"primary_intent": str, "secondary_intent": str or None, "mode": str}
    """
    
    if query_type == "exploratory":
        return {
            "primary_intent": "guidance",
            "secondary_intent": "courses",
            "mode": "hybrid",
            "description": "User exploring options - provide guidance + course info"
        }
    
    elif query_type == "multi_intent":
        return {
            "primary_intent": None,  # Will be determined by intent detection
            "secondary_intent": None,  # Will be determined by intent detection
            "mode": "multi_intent",
            "description": "User asking about multiple topics - handle each separately"
        }
    
    else:  # direct
        return {
            "primary_intent": None,  # Will be determined by intent detection
            "secondary_intent": None,
            "mode": "direct",
            "description": "User asking for specific information - direct routing"
        }
