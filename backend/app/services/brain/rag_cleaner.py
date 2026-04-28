"""
RAG Chunk Cleaner - Removes noise from retrieved chunks.

Filters out:
- Marketing junk ("Apply now!", "Deadline...", "Click here!")
- Duplicate/near-duplicate content
- Very short garbage text
- Unrelated noise patterns
"""

import re
import logging

logger = logging.getLogger(__name__)

# Noise patterns to filter out
NOISE_PATTERNS = [
    r"deadline.*?(?=\n|$)",
    r"apply now.*?(?=\n|$)",
    r"admission open.*?(?=\n|$)",
    r"click here.*?(?=\n|$)",
    r"lorem ipsum.*?(?=\n|$)",
    r"^\s*[•\-\*]\s*$",  # Empty bullet points
    r"^https?://.*$",    # Raw URLs
    r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$",  # Email addresses only
]

def clean_chunks(chunks: list[str]) -> list[str]:
    """
    Clean and filter RAG chunks to remove noise and duplicates.
    
    Args:
        chunks: List of text chunks from RAG retrieval
        
    Returns:
        Cleaned, deduplicated list of chunks
    """
    if not chunks:
        return []
    
    cleaned = []
    seen_normalized = set()
    
    for text in chunks:
        if not text or not isinstance(text, str):
            continue
            
        t = text.strip()
        
        # Remove lines matching noise patterns
        for pattern in NOISE_PATTERNS:
            t = re.sub(pattern, "", t, flags=re.IGNORECASE | re.MULTILINE)
        
        t = t.strip()
        
        # Skip very short garbage (< 30 chars)
        if len(t) < 30:
            continue
        
        # Skip if it's just whitespace
        if not t or t.isspace():
            continue
        
        # Deduplication: normalize and check if we've seen this
        normalized = " ".join(t.split()).lower()[:100]  # First 100 chars
        if normalized in seen_normalized:
            logger.debug(f"[CLEANER] Skipping duplicate: {t[:50]}...")
            continue
        
        seen_normalized.add(normalized)
        cleaned.append(t)
    
    # Limit to top 5 for cost/quality
    result = cleaned[:5]
    logger.info(f"[CLEANER] Cleaned {len(chunks)} chunks → {len(result)} quality chunks")
    return result
