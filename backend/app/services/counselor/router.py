from typing import Dict, List, Tuple

# -------------------------
# INTENT KEYWORD MAP
# -------------------------
INTENT_KEYWORDS = {
    "guidance": {
        "keywords": [
            # Original
            "which course", "what should i study", "confused",
            "suggest", "recommend", "what to choose", "career option",
            # New: marks-only patterns
            "i got", "got %", "after 12th", "after 12th class",
            "what can i do", "what should i do", "idk what",
            "don't know what", "no idea", "not sure what",
            # Interest signals
            "i like", "i love", "i enjoy", "interested in",
            "finance", "coding", "programming", "tech",
            "business", "commerce", "accounts", "management",
            "hospitality", "hotel",
            # Goal signals
            "high salary", "good salary", "good job",
            "career in", "become a",
            # 12th specific
            "12th", "class 12", "board",
        ],
        "weight": 1.0
    },
    "compare": {
        "keywords": [
            "vs", "difference", "compare", "better than",
            "bba or bcom", "which is better", "or bca", "or mba",
        ],
        "weight": 1.0
    },
    "career": {
        "keywords": [
            "job", "salary", "career", "placement",
            "future", "scope", "package", "role", "work as",
        ],
        "weight": 0.9
    },
    "constraint": {
        "keywords": [
            "eligible", "can i", "cutoff", "requirement",
            "qualify", "minimum marks", "admission criteria",
        ],
        # Note: "marks" and "%" removed here — they now route to guidance
        # Constraint fires only when user asks if they qualify, not just mentions marks
        "weight": 1.1
    },
    "life": {
        "keywords": [
            "hostel", "campus", "timing",
            "sports", "library", "environment",
            "location", "travel",
        ],
        "weight": 0.7
    },
    "unavailable": {
        "keywords": [
            "mbbs", "nursing", "mbbs course",
            "medical course", "bsc nursing",
        ],
        "weight": 1.2
    },
    "conversion": {
        # Handles "sounds good", "yes", "how to apply", "job after"
        "keywords": [
            "sounds good", "looks good", "that works", "seems good",
            "how to apply", "how do i apply", "apply now", "admission process",
            "enroll", "register", "job after", "start working",
            "yes", "sure", "okay", "ok", "tell me more", "show me",
        ],
        "weight": 0.8
    },
    "about_aims": {
        "keywords": [
            "what is aims", "about aims", "tell me about aims",
            "aims overview", "aims introduction", "who is aims",
            "what does aims offer", "aims institutes",
        ],
        "weight": 1.0
    },
    "why_aims": {
        "keywords": [
            "why aims", "why choose aims", "why should i join aims",
            "advantages of aims", "benefits of aims", "why aims is good",
            "why aims over others", "why aims better",
        ],
        "weight": 1.0
    },
    "aims_features": {
        "keywords": [
            "features", "facilities", "campus facilities", "infrastructure",
            "what facilities", "campus", "labs", "library", "classrooms",
            "smart classroom", "wi-fi", "sports", "hostel facilities",
        ],
        "weight": 0.9
    },
}


def compute_intent_scores(query: str) -> Dict[str, float]:
    query_lower = query.lower()
    scores = {}
    
    import logging
    logger = logging.getLogger(__name__)
    
    for intent, config in INTENT_KEYWORDS.items():
        score = 0.0
        matched_keywords = []
        for keyword in config["keywords"]:
            if keyword in query_lower:
                score += config["weight"]
                matched_keywords.append(keyword)
                
        # normalize (avoid overpowering)
        if score > 0:
            score = min(score, 2.0)
            
        scores[intent] = round(score, 2)
        if score > 0:
            logger.info(f"[DEBUG] intent='{intent}' matched={matched_keywords} score={scores[intent]}")
    
    logger.info(f"[DEBUG] compute_intent_scores query='{query}' final_scores={scores}")
    return scores


def detect_intents(
    query: str,
    threshold: float = 0.6
) -> List[Tuple[str, float]]:
    """
    Returns ranked intents above threshold.
    """
    scores = compute_intent_scores(query)
    
    filtered = [
        (intent, score)
        for intent, score in scores.items()
        if score >= threshold
    ]
    
    ranked = sorted(filtered, key=lambda x: x[1], reverse=True)[:2]
    return ranked


def handle_ambiguity(query: str) -> str:
    """
    Returns a clarification prompt only for truly vague single-word queries.
    
    Previously fired at ≤3 words which caught "I got 60%" and "I think finance".
    Now only fires for ≤1 meaningful word with no intent signals.
    """
    words = query.strip().split()
    # Only ambiguous if 1 word AND no intent detected
    if len(words) <= 1:
        scores = compute_intent_scores(query)
        if all(s < 0.6 for s in scores.values()):
            return "Do you mean course details, fees, or career options?"
    return ""



# -------------------------
# PRIMARY + SECONDARY SPLIT
# -------------------------
def split_primary_secondary(intents: List[Tuple[str, float]]):
    """
    Separates main intent vs supporting intents.
    """
    if not intents:
        return None, []
        
    primary = intents[0][0]
    secondary = [i[0] for i in intents[1:]]
    return primary, secondary
