"""
Filter Module - Filter FAISS search results by relevance and quality

Works with FAISS result format: (text, similarity_score, url, heading, doc_id)
"""

from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def filter_results_by_relevance(
    results: List[Tuple],
    min_score: float = 0.5,
    max_results: int = 5
) -> List[Tuple]:
    """
    Filter search results by minimum relevance score
    
    Args:
        results: List of FAISS results (text, score, url, heading, doc_id)
        min_score: Minimum similarity score threshold (0-1)
        max_results: Maximum number of results to keep
    
    Returns:
        Filtered results sorted by score (highest first)
    """
    if not results:
        return []
    
    # Extract similarity scores (index 1 in tuple)
    filtered = []
    for result in results:
        if len(result) > 1:
            score = result[1]
            if score >= min_score:
                filtered.append(result)
    
    # Sort by score (highest first)
    filtered.sort(key=lambda x: x[1] if len(x) > 1 else 0, reverse=True)
    
    # Keep top N
    filtered = filtered[:max_results]
    
    logger.debug(f"Filtered {len(results)} → {len(filtered)} results (min_score={min_score})")
    
    return filtered


def filter_results_by_source(
    results: List[Tuple],
    exclude_sources: List[str] = None,
    include_sources: List[str] = None
) -> List[Tuple]:
    """
    Filter results by source document
    
    Args:
        results: List of FAISS results
        exclude_sources: Source URLs to exclude
        include_sources: If set, only include these sources
    
    Returns:
        Filtered results
    """
    if not results:
        return []
    
    exclude_sources = exclude_sources or []
    include_sources = include_sources or []
    
    filtered = []
    for result in results:
        # URL is at index 2 in tuple
        url = result[2] if len(result) > 2 else ""
        
        # Check exclusions
        if exclude_sources and url in exclude_sources:
            continue
        
        # Check inclusions
        if include_sources and url not in include_sources:
            continue
        
        filtered.append(result)
    
    logger.debug(f"Filtered {len(results)} → {len(filtered)} results by source")
    
    return filtered


def remove_duplicates(
    results: List[Tuple],
    similarity_threshold: float = 0.95
) -> List[Tuple]:
    """
    Remove duplicate/near-duplicate results
    
    Args:
        results: List of FAISS results
        similarity_threshold: How similar texts must be to be considered duplicates (0-1)
    
    Returns:
        Deduplicated results
    """
    if not results:
        return []
    
    unique = []
    seen_texts = []
    
    for result in results:
        text = result[0] if len(result) > 0 else ""
        
        # Check if similar to any seen text
        is_duplicate = False
        for seen_text in seen_texts:
            if _text_similarity(text, seen_text) >= similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique.append(result)
            seen_texts.append(text)
    
    logger.debug(f"Dedup: {len(results)} → {len(unique)} results")
    
    return unique


def _text_similarity(text1: str, text2: str) -> float:
    """
    Simple text similarity based on character overlap
    
    Returns: Score 0-1 where 1 = identical
    """
    if not text1 or not text2:
        return 1.0 if text1 == text2 else 0.0
    
    # Simple: character set overlap
    set1 = set(text1.lower())
    set2 = set(text2.lower())
    
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0
