"""
Context Resolver - Handles follow-up queries using conversation memory.

Detects follow-up patterns and injects prior context:
- "What about hostel?" → "MBA hostel facilities"
- "How much?" (after fee query) → "MBA fees how much"
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Words that indicate a follow-up question
FOLLOWUP_WORDS = [
    "it", "that", "this", "these", "those", 
    "what about", "how about", "what else",
    "more about",  # Keep this for "more about hostel?" after course query
    "same", "similar", "like that",
    "how much", "how many",  # Specific quantities (not just "how")
    "when", "where"
]

CURRENT_INTENT_WORDS = [
    "fee", "fees", "cost", "price", "tuition",
    "admission", "apply", "eligibility", "document", "documents",
    "placement", "placements", "salary", "package",
    "course", "courses", "program", "programs",
    "hostel", "accommodation", "campus", "facility", "facilities",
    "scholarship", "exam", "exams", "location", "located", "address",
    "where", "how to reach",
]

def inject_context(query: str, context: Optional[Dict[str, Any]]) -> str:
    """
    Inject prior context into follow-up queries.
    
    Args:
        query: User's current query
        context: Dict with keys: last_intent, last_course, last_topic
        
    Returns:
        Enhanced query with context injected (if it's a follow-up)
    """
    if not context:
        return query
    
    query_lower = query.lower().strip()
    
    # Check if this looks like a follow-up
    is_followup = any(word in query_lower for word in FOLLOWUP_WORDS)
    
    if not is_followup:
        logger.debug(f"[CONTEXT] Not a follow-up: {query}")
        return query
    
    # Extract prior context
    last_course = context.get("last_course") or context.get("course")
    last_intent = context.get("last_intent")
    last_topic = context.get("last_topic")
    has_current_intent = any(word in query_lower for word in CURRENT_INTENT_WORDS)
    
    # Build context prefix
    prefix_parts = []
    if last_course:
        prefix_parts.append(last_course.upper())
    if last_intent and not has_current_intent:
        prefix_parts.append(last_intent)
    if last_topic:
        prefix_parts.append(last_topic)
    
    if prefix_parts:
        enhanced = " ".join(prefix_parts) + " " + query
        logger.info(f"[CONTEXT] Follow-up detected: '{query}' → '{enhanced}'")
        return enhanced
    
    return query
