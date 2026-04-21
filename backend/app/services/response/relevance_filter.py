"""
Relevance Filter - Kill garbage results before answer generation

Strategy:
- Filter results by minimum relevance threshold
- Remove weak matches
- Sort by quality
- Return only confident matches
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RelevanceFilter:
    """Filter search results by relevance score"""
    
    def __init__(self, threshold: float = 0.6):
        """
        Initialize filter
        
        Args:
            threshold: Minimum similarity score to keep (0-1)
        """
        self.threshold = threshold
    
    def filter(self, results: List[Dict]) -> List[Dict]:
        """
        Filter and rank results by relevance
        
        Args:
            results: List of search results with 'score' field
        
        Returns:
            Filtered results sorted by score (highest first)
        """
        if not results:
            return []
        
        # Remove low-confidence results
        filtered = [
            r for r in results
            if r.get('similarity_score', 0) >= self.threshold
        ]
        
        # Sort by score (highest first)
        filtered.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # Keep top 5
        return filtered[:5]
    
    def set_threshold(self, threshold: float):
        """Adjust relevance threshold"""
        self.threshold = max(0, min(1, threshold))
        logger.info(f"Relevance threshold set to {self.threshold}")


def remove_duplicates(chunks: List[Dict], fingerprint_length: int = 150) -> List[Dict]:
    """
    Remove duplicate chunks
    
    Strategy:
    - Create text fingerprint (first N chars)
    - Track seen fingerprints
    - Keep only first occurrence
    
    Args:
        chunks: List of chunk dictionaries
        fingerprint_length: Characters to use for dedup
    
    Returns:
        Deduplicated chunks
    """
    seen = set()
    unique = []
    
    for chunk in chunks:
        # Create fingerprint from content
        content = chunk.get('snippet', chunk.get('content', ''))
        fingerprint = content[:fingerprint_length].strip().lower()
        
        if fingerprint and fingerprint not in seen:
            seen.add(fingerprint)
            unique.append(chunk)
    
    logger.info(f"Dedup: {len(chunks)} → {len(unique)} chunks")
    return unique
