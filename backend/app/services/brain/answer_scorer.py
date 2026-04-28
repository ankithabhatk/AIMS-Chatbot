"""
Answer Scorer - Validates LLM-generated answers for quality and relevance.

Scoring criteria:
- Length (must be substantial, >40 chars)
- Domain relevance (mentions AIMS)
- Content keywords (fees, placement, admission, salary)
- Negative signals (hallucination markers)
- Minimum text quality

CRITICAL: If score < 0.5, answer is rejected and fallback is used.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Keywords that indicate high-quality AIMS-specific content
POSITIVE_KEYWORDS = [
    "aims", "fee", "placement", "admission", "salary", 
    "package", "lpa", "campus", "hostel", "recruiter",
    "eligibility", "requirement", "process", "scholarship"
]

# Keywords that indicate hallucination/low-quality
NEGATIVE_KEYWORDS = [
    "i don't know", "not available", "unclear", "uncertain",
    "i'm not sure", "unable to", "can't say", "don't have",
    "no information", "error", "failed"
]

def score_answer(answer: str, query: str) -> Tuple[float, str]:
    """
    Score an LLM-generated answer for quality and relevance.
    
    Args:
        answer: The generated answer text
        query: The original user query
        
    Returns:
        Tuple of (score: float 0-1, reason: str for logging)
    """
    if not answer:
        return 0.0, "empty_answer"
    
    a = answer.lower().strip()
    reasons = []
    score = 0.0
    
    # ✅ LENGTH CHECK (must be substantial)
    if len(answer) > 60:
        score += 0.25
        reasons.append("length_good")
    elif len(answer) > 40:
        score += 0.15
        reasons.append("length_ok")
    else:
        reasons.append("length_too_short")
        score -= 0.2
    
    # ✅ DOMAIN RELEVANCE (mentions AIMS)
    if "aims" in a:
        score += 0.25
        reasons.append("aims_mentioned")
    else:
        score -= 0.1
        reasons.append("aims_missing")
    
    # ✅ CONTENT QUALITY (has key concepts)
    positive_count = sum(1 for k in POSITIVE_KEYWORDS if k in a)
    if positive_count >= 2:
        score += 0.25
        reasons.append(f"keywords_{positive_count}")
    elif positive_count >= 1:
        score += 0.15
        reasons.append("keyword_found")
    else:
        reasons.append("no_keywords")
    
    # ❌ HALLUCINATION CHECK (negative signals)
    negative_count = sum(1 for k in NEGATIVE_KEYWORDS if k in a)
    if negative_count > 0:
        score -= (0.2 * negative_count)
        reasons.append(f"hallucination_{negative_count}")
    
    # ❌ MINIMUM WORD COUNT
    word_count = len(a.split())
    if word_count < 5:
        score -= 0.25
        reasons.append("too_few_words")
    elif word_count > 3:
        reasons.append(f"words_{word_count}")
    
    # ❌ ALL CAPS OR WEIRD FORMAT (usually garbage)
    if a.isupper():
        score -= 0.2
        reasons.append("all_caps")
    
    # ❌ VERY LONG (might be unfocused)
    if len(a) > 500:
        score -= 0.1
        reasons.append("too_long")
    
    # Clamp to 0-1 range
    final_score = max(0.0, min(score, 1.0))
    reason_str = ", ".join(reasons)
    
    logger.info(f"[SCORER] Answer score: {final_score:.2f} | {reason_str}")
    return final_score, reason_str
