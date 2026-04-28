"""
Interest Mapper - Production-Grade Signal-Based Mapping

Maps user interests to college courses using signal groups.
Handles redirects for unsupported interests intelligently.

Architecture:
1. SIGNAL GROUPS: Multi-keyword matching (not single keyword)
2. SCORING: Handles multiple interest matches deterministically
3. HARD BLOCKS: Rejects interests we cannot serve
4. SOFT REDIRECTS: Maps related interests to closest course
"""

from typing import Dict, Optional, List
import re

# ============================================
# INTEREST SIGNAL GROUPS (Production-Grade)
# ============================================
INTEREST_SIGNALS = {
    "BCA": [
        # Core tech
        "coding", "programming", "software", "tech", "technology",
        "computers", "computer", "developer", "development",
        # Specific domains
        "ai", "data", "machine learning", "web development",
        "app development", "cybersecurity", "database",
        # Related terms
        "it", "information technology", "digital", "algorithm"
    ],
    "BBA": [
        # Core business
        "business", "management", "entrepreneur", "entrepreneurship",
        "leadership", "marketing", "sales",
        # Specific domains
        "hr", "human resources", "operations", "strategy",
        "consulting", "corporate", "startup",
        # Related terms
        "manager", "executive", "administration"
    ],
    "B.Com": [
        # Core finance
        "finance", "accounts", "accounting", "accountancy",
        "commerce", "tax", "taxation", "banking",
        # Specific domains
        "audit", "auditing", "bookkeeping", "financial",
        "investment", "stock market", "ca", "chartered accountant",
        # Related terms
        "money", "numbers", "calculation"
    ],
    "BHM": [
        # Core hospitality
        "hotel", "hospitality", "events", "event management",
        "travel", "tourism", "customer service",
        # Specific domains
        "restaurant", "catering", "food service",
        "hotel management", "guest relations",
        # Related terms
        "service", "hosting", "accommodation"
    ]
}

# ============================================
# SOFT REDIRECTS (Interests NOT offered → Closest Match)
# ============================================
SOFT_REDIRECT_MAP = {
    "psychology": {
        "closest": "BBA",
        "reason": "HR specialization",
        "message": "We don't offer Psychology directly, but **BBA with HR specialization** covers organizational behavior, people management, and workplace psychology."
    },
    "design": {
        "closest": "BCA",
        "reason": "UI/UX and creative tech",
        "message": "We don't offer pure Design, but **BCA** includes UI/UX design, web design, and creative technology paths."
    },
    "graphics": {
        "closest": "BCA",
        "reason": "digital design and multimedia",
        "message": "We don't offer Graphic Design specifically, but **BCA** covers digital design, multimedia, and visual development."
    },
    "engineering": {
        "closest": "BCA",
        "reason": "technical foundation",
        "message": "We don't offer traditional Engineering, but **BCA** provides strong technical training in software development and IT systems."
    },
    "science": {
        "closest": "BCA",
        "reason": "applied science in tech",
        "message": "We don't offer pure Science, but **BCA** applies scientific principles to computer applications and technology."
    },
    "arts": {
        "closest": "BBA",
        "reason": "creative business roles",
        "message": "We don't offer Arts specifically, but **BBA** opens paths in creative industries like marketing, media, and brand management."
    },
    "social work": {
        "closest": "BBA",
        "reason": "HR and organizational development",
        "message": "We don't offer Social Work, but **BBA with HR** covers organizational development and people-focused roles."
    }
}

# ============================================
# HARD BLOCKS (Interests we CANNOT serve)
# ============================================
HARD_BLOCK_INTERESTS = [
    # Medical
    "mbbs", "doctor", "medical", "medicine", "nursing",
    "pharmacy", "physiotherapy", "dentistry",
    # Aviation
    "pilot", "aviation", "aircraft", "flying",
    # Law
    "law", "llb", "legal", "lawyer", "advocate",
    # Specialized fields
    "architecture", "civil engineering", "mechanical engineering",
    "electrical engineering", "agriculture", "veterinary"
]


def _check_hard_block(interest: str) -> Optional[Dict]:
    """Check if interest is in hard block category"""
    interest_lower = interest.lower()
    
    for block in HARD_BLOCK_INTERESTS:
        if block in interest_lower:
            return {
                "course": None,
                "type": "hard_block",
                "is_direct_match": False,
                "redirect_message": f"We don't offer programs in this field. AIMS focuses on **management, technology, commerce, and hospitality**. Would you like to explore our available programs?"
            }
    
    return None


def _check_soft_redirect(interest: str) -> Optional[Dict]:
    """Check if interest can be redirected to closest course"""
    interest_lower = interest.lower()
    
    for key, redirect_info in SOFT_REDIRECT_MAP.items():
        if key in interest_lower:
            return {
                "course": redirect_info["closest"],
                "type": "soft_redirect",
                "is_direct_match": False,
                "redirect_message": redirect_info["message"],
                "reason": redirect_info["reason"]
            }
    
    return None


def _score_interest_signals(interest: str) -> Dict[str, int]:
    """
    Score each course based on interest signal matches.
    Returns: {"BCA": 3, "BBA": 1, ...}
    """
    interest_lower = interest.lower()
    scores = {course: 0 for course in INTEREST_SIGNALS}
    
    for course, signals in INTEREST_SIGNALS.items():
        for signal in signals:
            if signal in interest_lower:
                scores[course] += 1
    
    return scores


def map_interest_to_course(interest: str) -> Dict:
    """
    Maps user interest to college course using signal-based matching.
    
    Returns:
        {
            "course": "BCA" or None,
            "type": "direct_match" | "soft_redirect" | "hard_block" | "no_match",
            "is_direct_match": bool,
            "redirect_message": str or None,
            "confidence": float
        }
    """
    if not interest or len(interest.strip()) < 2:
        return {
            "course": None,
            "type": "no_match",
            "is_direct_match": False,
            "redirect_message": "Could you tell me more about what you're interested in?",
            "confidence": 0.0
        }
    
    # 1. Check HARD BLOCK first (highest priority)
    hard_block = _check_hard_block(interest)
    if hard_block:
        return hard_block
    
    # 2. Check DIRECT MATCH using signal scoring
    scores = _score_interest_signals(interest)
    best_course = max(scores, key=scores.get)
    best_score = scores[best_course]
    
    if best_score > 0:
        # Direct match found
        confidence = min(0.95, 0.6 + (best_score * 0.1))  # Scale confidence with matches
        return {
            "course": best_course,
            "type": "direct_match",
            "is_direct_match": True,
            "redirect_message": None,
            "confidence": confidence,
            "match_count": best_score
        }
    
    # 3. Check SOFT REDIRECT (no direct match, but can redirect)
    soft_redirect = _check_soft_redirect(interest)
    if soft_redirect:
        soft_redirect["confidence"] = 0.75
        return soft_redirect
    
    # 4. NO MATCH (generic fallback)
    return {
        "course": None,
        "type": "no_match",
        "is_direct_match": False,
        "redirect_message": "We offer programs in **business (BBA), technology (BCA), commerce (B.Com), and hospitality (BHM)**. Which area interests you most?",
        "confidence": 0.0
    }


def map_multiple_interests(interests: List[str]) -> Dict:
    """
    Handle multiple interests (e.g., "I like business and coding").
    Returns the best match with priority scoring.
    """
    if not interests:
        return map_interest_to_course("")
    
    # Score all interests
    combined_scores = {course: 0 for course in INTEREST_SIGNALS}
    
    for interest in interests:
        scores = _score_interest_signals(interest)
        for course, score in scores.items():
            combined_scores[course] += score
    
    best_course = max(combined_scores, key=combined_scores.get)
    best_score = combined_scores[best_course]
    
    if best_score > 0:
        confidence = min(0.95, 0.6 + (best_score * 0.05))
        return {
            "course": best_course,
            "type": "direct_match",
            "is_direct_match": True,
            "redirect_message": None,
            "confidence": confidence,
            "match_count": best_score,
            "note": f"Based on your interests in {', '.join(interests)}"
        }
    
    # Fallback to single interest mapping
    return map_interest_to_course(interests[0])


def extract_interest_from_query(query: str) -> Optional[str]:
    """
    Extract interest signals from free-form query.
    Examples:
        "I like coding" → "coding"
        "interested in business" → "business"
        "want to study finance" → "finance"
    """
    query_lower = query.lower()
    
    # Pattern 1: "I like/love/enjoy X"
    match = re.search(r"(?:i\s+(?:like|love|enjoy|want|prefer)\s+)(\w+(?:\s+\w+)?)", query_lower)
    if match:
        return match.group(1)
    
    # Pattern 2: "interested in X"
    match = re.search(r"interested\s+in\s+(\w+(?:\s+\w+)?)", query_lower)
    if match:
        return match.group(1)
    
    # Pattern 3: "study X" or "learn X"
    match = re.search(r"(?:study|learn|pursue)\s+(\w+(?:\s+\w+)?)", query_lower)
    if match:
        return match.group(1)
    
    # Pattern 4: Direct mention of interest signals
    for course, signals in INTEREST_SIGNALS.items():
        for signal in signals:
            if signal in query_lower:
                return signal
    
    return None


# ============================================
# TESTING / VALIDATION
# ============================================
def test_interest_mapper():
    """Test cases for interest mapper"""
    test_cases = [
        # Direct matches
        ("coding", "BCA", "direct_match"),
        ("business", "BBA", "direct_match"),
        ("finance", "B.Com", "direct_match"),
        ("hotel", "BHM", "direct_match"),
        
        # Soft redirects
        ("psychology", "BBA", "soft_redirect"),
        ("design", "BCA", "soft_redirect"),
        
        # Hard blocks
        ("mbbs", None, "hard_block"),
        ("pilot", None, "hard_block"),
        ("law", None, "hard_block"),
        
        # Multiple interests
        ("business and coding", "BBA", "direct_match"),  # BBA likely wins with more signals
    ]
    
    print("Testing Interest Mapper...")
    for query, expected_course, expected_type in test_cases:
        result = map_interest_to_course(query)
        status = "✅" if result["course"] == expected_course and result["type"] == expected_type else "❌"
        print(f"{status} '{query}' → {result['course']} ({result['type']})")


if __name__ == "__main__":
    test_interest_mapper()
