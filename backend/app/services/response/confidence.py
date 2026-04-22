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


def calculate_confidence(query: str, results: list, max_sources: int = 5) -> float:
    """
    Calculate confidence score based on:
    - Average relevance of matched chunks (60%)
    - Keyword overlap ratio (30%)
    - Context volume / coverage (10%)
    
    Args:
        query: The user's rewritten query
        results: FAISS tuples or dicts
        max_sources: Reference for coverage calculation
    
    Returns:
        Confidence score 0-1
    """
    if not results or not query:
        return 0.0
    
    # 1. Extract relevance scores (Average Similarity)
    scores = []
    texts = []
    for r in results:
        if isinstance(r, tuple):
            if len(r) > 1:
                scores.append(float(r[1]))
                texts.append(r[0])
        elif isinstance(r, dict):
            # Try 'similarity_score' then 'score'
            s = r.get('similarity_score') or r.get('score', 0)
            scores.append(float(s))
            texts.append(r.get('content', ''))
    
    if not scores:
        return 0.0
    
    avg_similarity = sum(scores) / len(scores)
    
    # 2. Keyword Overlap Ratio
    query_words = set(query.lower().split())
    if not query_words:
        keyword_overlap_ratio = 0.0
    else:
        # Check overlap across ALL retrieved text
        all_text = " ".join(texts).lower()
        all_words = set(all_text.split())
        overlap = len(query_words & all_words)
        keyword_overlap_ratio = overlap / len(query_words)
        
    # 3. Context Volume Factor (bounded at 1.0)
    context_factor = min(len(results) / 3, 1.0)
    
    # 4. FINAL WEIGHTED FORMULA
    # similarity (60%) + keyword (30%) + context (10%)
    confidence = (avg_similarity * 0.6) + (keyword_overlap_ratio * 0.3) + (context_factor * 0.1)
    
    # Ensure 0-1 range
    confidence = max(0, min(1, confidence))
    
    logger.debug(f"Confidence: sim={avg_similarity:.3f}, kw={keyword_overlap_ratio:.3f}, "
                f"context={context_factor:.1f} → {confidence:.2f}")
    
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
    if confidence < 0.45:
        return "Not Verified"
    elif confidence < 0.65:
        return "General Assistance"
    else:
        return "Verified Information"
