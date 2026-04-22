# backend/app/services/query_rewriter.py

import re


def clean_query(text: str) -> str:
    """
    Lowercase, remove special characters, and collapse multiple spaces.
    """
    text = text.lower().strip()

    # Remove special characters (keep alphanumeric and spaces)
    text = re.sub(r"[^\w\s]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def expand_query(text: str) -> str:
    """
    Add 'aims college' context to short queries if not already present.
    """
    words = text.split()

    # Only expand if query is short (<= 3 words) AND 'aims' not already present
    if len(words) <= 3 and "aims" not in text.lower():
        return f"{text} aims college"

    return text


def rewrite_query(text: str) -> str:
    """
    Coordinate the cleaning and expansion of user queries for improved retrieval.
    """
    if not text:
        return ""
        
    cleaned = clean_query(text)
    rewritten = expand_query(cleaned)
    
    return rewritten
