# backend/app/services/input_handler.py

import re

GREETINGS = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "hi there", "hello there", "hey aims"
}

EXITS = {
    "bye", "goodbye", "thanks", "thank you", "see you", "bye bye", "exit", "quit"
}


def normalize(text: str) -> str:
    """Normalize text for consistent comparison"""
    return text.strip().lower()


def is_greeting(text: str) -> bool:
    """Detect simple greetings (exact match only to allow 'hi what is...' to go to RAG)"""
    text = normalize(text).replace('!', '').replace('.', '').replace(',', '')
    return text in GREETINGS


def is_exit(text: str) -> bool:
    """Detect simple exits/gratitude"""
    text = normalize(text).replace('!', '').replace('.', '').replace(',', '')
    return text in EXITS


def is_nonsense(text: str) -> bool:
    """Detect non-informational or mangled input"""
    text = normalize(text)

    # Too short to be a meaningful query for college info
    if len(text) < 3:
        return True

    # No alphabets or valid characters
    if not any(char.isalpha() for char in text):
        return True

    # Random repeated characters (e.g., "aaaaaa", "qqqq")
    if re.fullmatch(r"(.)\1{3,}", text):
        return True
    
    # Known domain words that should NOT be marked as nonsense
    # (prevents false negatives on legitimate college-related terms)
    KNOWN_DOMAIN_WORDS = {
        "python", "sql", "java", "c++", "javascript", "html", "css",
        "bca", "mba", "bba", "mca", "bcom", "bhm",
        "aims", "college", "course", "fees", "admission",
        "hostel", "campus", "placement", "job", "salary"
    }
    
    if text in KNOWN_DOMAIN_WORDS:
        return False
    
    # Random alphabetic strings with very low vowel ratio
    # "asdfgh" has 0 vowels, "qwerty" has 1 vowel
    # Real words typically have vowel ratio > 0.2
    vowels = sum(1 for c in text if c in 'aeiou')
    vowel_ratio = vowels / len(text) if text else 0
    
    # If < 20% vowels AND > 4 chars AND not a known word, likely random string
    if len(text) > 4 and vowel_ratio < 0.2:
        return True

    return False


def classify_intent(text: str) -> str:
    """Classify user intent into specialized categories"""
    if is_greeting(text):
        return "GREETING"
    elif is_exit(text):
        return "EXIT"
    elif is_nonsense(text):
        return "NONSENSE"
    else:
        return "QUESTION"
