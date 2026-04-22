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
