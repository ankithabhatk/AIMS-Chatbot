"""
Domain Guard - Hard protection against out-of-scope queries.

Rejects queries about other institutions unless explicitly comparing to AIMS.
"""

import logging

logger = logging.getLogger(__name__)

# Competitor institutions / outside scope
OUTSIDE_KEYWORDS = [
    "iit", "nit", "harvard", "stanford", "mit", "oxford",
    "cambridge", "caltech", "berkeley", "yale", "princeton",
    "delhi university", "du", "jnu", "bits pilani",
    "other college", "different university"
]

def is_out_of_domain(query: str) -> bool:
    """
    Check if query is asking about institutions outside AIMS Institutes.
    
    Args:
        query: User query
        
    Returns:
        True if query is out of domain (reject it)
    """
    q = query.lower().strip()
    
    # Check for outside institution mentions
    has_outside = any(keyword in q for keyword in OUTSIDE_KEYWORDS)
    
    # Check for AIMS mention (comparison is OK)
    has_aims = "aims" in q or "this" in q or "your" in q
    
    if has_outside and not has_aims:
        logger.warning(f"[GUARD] Out-of-domain query rejected: {query}")
        return True
    
    logger.debug(f"[GUARD] Query in domain: {query}")
    return False
