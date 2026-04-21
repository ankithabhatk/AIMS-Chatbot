"""
Confidence Scoring - Calculate reliability of answer

Formula:
- Average relevance score (70% weight): How well chunks match query
- Coverage score (30% weight): How many sources support answer

Result: 0-1 confidence where:
- 0.0-0.3 = unreliable (fallback)
- 0.3-0.6 = low (flag as uncertain)
- 0.6-1.0 = confident (use answer)
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_confidence(results, max_sources: int = 5) -> float:
    """
    Calculate confidence score based on:
    - Average relevance of matched chunks
    - Coverage (how many sources support the answer)
    
    Args:
        results: FAISS tuples (text, score, url, heading) or dicts with similarity_score
        max_sources: Expected maximum sources (for coverage calculation)
    
    Returns:
        Confidence score 0-1
    """
    if not results:
        return 0.0
    
    # Extract relevance scores
    scores = []
    for r in results:
        if isinstance(r, tuple):
            # FAISS format: (text, score, url, heading, ...)
            if len(r) > 1:
                scores.append(float(r[1]))
        elif isinstance(r, dict):
            # Dict format with similarity_score
            scores.append(float(r.get('similarity_score', 0)))
    
    if not scores:
        return 0.0
    
    # === STRICT CALIBRATION ===
    # Based on empirical testing:
    # - Bad queries return FAISS scores of 0.35-0.51
    # - Good queries return FAISS scores of 0.50-0.68
    # - Need to penalize scores < 0.55
    
    max_score = max(scores)
    avg_score = sum(scores) / len(scores)
    
    # Confidence thresholds based on max relevance score
    if max_score < 0.40:
        # Very poor match - almost certainly wrong
        confidence = 0.0
    elif max_score < 0.48:
        # Poor match - likely wrong
        confidence = 0.15
    elif max_score < 0.55:
        # Weak match - uncertain
        confidence = 0.35
    elif max_score < 0.65:
        # Reasonable match - probably good
        confidence = 0.60
    else:
        # Strong match - likely correct
        confidence = 0.75
    
    # Boost for coverage (20% weight max)
    coverage_ratio = min(len(results) / max_sources, 1.0)
    confidence = confidence * 0.8 + (coverage_ratio * 0.2)
    
    # Penalty for inconsistent scores (wide variance = uncertain)
    if max_score > 0:
        score_range = max(scores) - min(scores)
        if score_range > 0.15:
            confidence *= 0.9
    
    # Ensure 0-1 range
    confidence = max(0, min(1, confidence))
    
    logger.debug(f"Confidence: max={max_score:.3f}, avg={avg_score:.3f}, "
                f"sources={len(results)} → {confidence:.2f}")
    
    return round(confidence, 2)


def is_confident_enough(confidence: float, threshold: float = 0.5) -> bool:
    """
    Check if confidence meets minimum threshold
    
    Args:
        confidence: Confidence score (0-1)
        threshold: Minimum acceptable confidence
    
    Returns:
        True if confident enough to answer
    """
    return confidence >= threshold


def get_confidence_label(confidence: float) -> str:
    """
    Get human-readable confidence label
    
    Args:
        confidence: Confidence score (0-1)
    
    Returns:
        Label: "very_low", "low", "medium", "high", "very_high"
    """
    if confidence < 0.2:
        return "very_low"
    elif confidence < 0.4:
        return "low"
    elif confidence < 0.6:
        return "medium"
    elif confidence < 0.8:
        return "high"
    else:
        return "very_high"
