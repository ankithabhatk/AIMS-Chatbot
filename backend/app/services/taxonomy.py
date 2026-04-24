"""
Shared domain taxonomy for the local AIMS assistant.

This module keeps course/topic aliases and light-weight normalization helpers in
one place so query processing, retrieval, and response shaping stay consistent.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Set


COURSE_ALIASES: Dict[str, List[str]] = {
    "mba": [
        "mba",
        "m b a",
        "mbaa",
        "master of business administration",
    ],
    "bba": [
        "bba",
        "b b a",
        "bbaa",
        "bachelor of business administration",
    ],
    "mca": [
        "mca",
        "m c a",
        "master of computer applications",
    ],
    "bca": [
        "bca",
        "b c a",
        "bachelor of computer applications",
    ],
    "phd": [
        "phd",
        "ph d",
        "doctorate",
        "doctoral",
        "doctoral program",
        "doctoral programme",
    ],
    "bcom": [
        "bcom",
        "b com",
        "b.com",
        "bachelor of commerce",
    ],
    "mcom": [
        "mcom",
        "m com",
        "m.com",
        "master of commerce",
    ],
    "aviation": [
        "aviation",
        "aviation management",
        "bba aviation",
        "bba aviation management",
    ],
}

TOPIC_ALIASES: Dict[str, List[str]] = {
    "fees": [
        "fee",
        "fees",
        "cost",
        "price",
        "pricing",
        "tuition",
        "payment",
        "payments",
        "scholarship",
        "scholarships",
        "loan",
        "loans",
        "emi",
        "installment",
        "installments",
    ],
    "placements": [
        "placement",
        "placements",
        "job",
        "jobs",
        "career",
        "careers",
        "salary",
        "package",
        "packages",
        "ctc",
        "lpa",
        "recruiter",
        "recruiters",
        "internship",
        "internships",
        "ppo",
        "hiring",
        "companies",
    ],
    "hostel": [
        "hostel",
        "hostels",
        "accommodation",
        "stay",
        "room",
        "rooms",
        "mess",
        "residence",
        "residential",
        "dorm",
        "dormitory",
        "amenities",
    ],
    "admission": [
        "admission",
        "admissions",
        "apply",
        "application",
        "applications",
        "eligibility",
        "eligible",
        "criteria",
        "deadline",
        "deadlines",
        "process",
        "procedure",
        "entrance",
        "exam",
        "documents",
        "selection",
        "seat",
    ],
    "course": [
        "course",
        "courses",
        "program",
        "programs",
        "programme",
        "programmes",
        "degree",
        "curriculum",
        "duration",
        "semester",
        "semesters",
        "specialization",
        "specializations",
        "stream",
        "streams",
        "subject",
        "subjects",
        "syllabus",
    ],
    "campus": [
        "campus",
        "facility",
        "facilities",
        "infrastructure",
        "transport",
        "wifi",
        "wi fi",
        "library",
        "lab",
        "labs",
        "classroom",
        "classrooms",
        "location",
    ],
}

SLANG_MAP: Dict[str, str] = {
    "plz": "please",
    "pls": "please",
    "info": "information",
    "abt": "about",
    "u": "you",
    "ur": "your",
    "thx": "thanks",
    "msg": "message",
    "yr": "year",
}

SYNONYM_MAP: Dict[str, str] = {
    "cost": "fees",
    "price": "fees",
    "pricing": "fees",
    "tuition": "fees",
    "salary": "placements",
    "job": "placements",
    "jobs": "placements",
    "career": "placements",
    "stay": "hostel",
    "accommodation": "hostel",
    "room": "hostel",
    "apply": "admission",
    "application": "admission",
    "eligibility": "admission",
    "duration": "course",
    "curriculum": "course",
    "specialization": "course",
}

STOPWORDS: Set[str] = {
    "a",
    "an",
    "and",
    "are",
    "about",
    "at",
    "can",
    "do",
    "for",
    "from",
    "i",
    "in",
    "is",
    "me",
    "of",
    "on",
    "or",
    "please",
    "tell",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "with",
    "you",
    "your",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")
WEAK_TOPIC_INFERENCE_ALIASES: Set[str] = {
    "stay",
    "career",
    "careers",
    "job",
    "jobs",
    "process",
    "program",
    "programs",
    "programme",
    "programmes",
    "course",
    "courses",
    "stream",
    "streams",
    "subject",
    "subjects",
    "facility",
    "facilities",
    "seat",
    "room",
    "rooms",
    "amenities",
}


def normalize_text(text: str) -> str:
    """Lowercase and clean punctuation without losing domain words."""
    text = (text or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[%/|]", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    """Tokenize normalized text into simple lowercase tokens."""
    return TOKEN_RE.findall(normalize_text(text))


def apply_slang_map(text: str) -> str:
    """Expand common short forms into their canonical wording."""
    tokens = tokenize(text)
    expanded = [SLANG_MAP.get(token, token) for token in tokens]
    return " ".join(expanded).strip()


def alias_vocabulary() -> Set[str]:
    """Collect the domain vocabulary used for fuzzy matching."""
    vocabulary: Set[str] = set(SLANG_MAP)
    vocabulary.update(SLANG_MAP.values())
    vocabulary.update(SYNONYM_MAP)
    vocabulary.update(SYNONYM_MAP.values())
    for canonical, aliases in COURSE_ALIASES.items():
        vocabulary.add(canonical)
        for alias in aliases:
            vocabulary.update(tokenize(alias))
    for canonical, aliases in TOPIC_ALIASES.items():
        vocabulary.add(canonical)
        for alias in aliases:
            vocabulary.update(tokenize(alias))
    return {token for token in vocabulary if token}


def _best_alias_match(text: str, alias_map: Dict[str, List[str]], threshold: float) -> Optional[str]:
    normalized = normalize_text(text)
    if not normalized:
        return None

    best_label: Optional[str] = None
    best_score = 0.0
    haystack_tokens = tokenize(normalized)
    haystack_phrases = haystack_tokens + [
        " ".join(haystack_tokens[i : i + 2])
        for i in range(max(0, len(haystack_tokens) - 1))
    ]

    for label, aliases in alias_map.items():
        candidates = [label, *aliases]
        for candidate in candidates:
            candidate_normalized = normalize_text(candidate)
            if candidate_normalized and candidate_normalized in normalized:
                return label

            for phrase in haystack_phrases:
                score = SequenceMatcher(None, phrase, candidate_normalized).ratio()
                if score > best_score:
                    best_score = score
                    best_label = label

    if best_score >= threshold:
        return best_label
    return None


def canonicalize_course(text: str) -> Optional[str]:
    """Map noisy text to a canonical course label."""
    return _best_alias_match(text, COURSE_ALIASES, threshold=0.76)


def canonicalize_topic(text: str) -> Optional[str]:
    """Map noisy text to a canonical topic label."""
    return _best_alias_match(text, TOPIC_ALIASES, threshold=0.78)


def canonicalize_metadata_value(value: Optional[str]) -> Optional[str]:
    """Normalize stored metadata category/course values when possible."""
    if not value:
        return None
    return canonicalize_course(value) or canonicalize_topic(value) or normalize_text(value)


def infer_topic_from_text(text: str) -> Optional[str]:
    """Infer a topic from explicit lexical evidence.

    This is intentionally stricter than fuzzy canonicalization and is better
    suited for document tagging, where long unrelated text can otherwise get
    mislabeled by approximate matching.
    """
    normalized = normalize_text(text)
    if not normalized:
        return None

    tokens = set(tokenize(normalized))
    best_label: Optional[str] = None
    best_score = 0.0

    for label, aliases in TOPIC_ALIASES.items():
        score = 0.0
        for candidate in {label, *aliases}:
            candidate_normalized = normalize_text(candidate)
            if not candidate_normalized:
                continue
            if candidate_normalized != label and candidate_normalized in WEAK_TOPIC_INFERENCE_ALIASES:
                continue

            if " " in candidate_normalized:
                if candidate_normalized in normalized:
                    score += 2.0
            elif candidate_normalized in tokens:
                score += 1.0

        if score > best_score:
            best_score = score
            best_label = label

    if best_score >= 1.0:
        return best_label
    return None


def keyword_set(texts: Iterable[str]) -> Set[str]:
    """Convert text fragments into a normalized keyword set."""
    keywords: Set[str] = set()
    for text in texts:
        for token in tokenize(text):
            if token not in STOPWORDS:
                keywords.add(SYNONYM_MAP.get(token, token))
    return keywords


def mentioned_courses(text: str) -> Set[str]:
    """Return all courses explicitly mentioned in text."""
    normalized = normalize_text(text)
    matches: Set[str] = set()
    for label, aliases in COURSE_ALIASES.items():
        for candidate in [label, *aliases]:
            candidate_normalized = normalize_text(candidate)
            if candidate_normalized and re.search(rf"\b{re.escape(candidate_normalized)}\b", normalized):
                matches.add(label)
                break
    return matches


def mentioned_topics(text: str) -> Set[str]:
    """Return all topics explicitly mentioned in text."""
    normalized = normalize_text(text)
    matches: Set[str] = set()
    for label, aliases in TOPIC_ALIASES.items():
        for candidate in [label, *aliases]:
            candidate_normalized = normalize_text(candidate)
            if candidate_normalized and re.search(rf"\b{re.escape(candidate_normalized)}\b", normalized):
                matches.add(label)
                break
    return matches
