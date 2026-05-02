# app/services/comparison_handler.py
"""
Generic comparison handler: works for any two entities the user mentions.
No LLM calls — pure rule-based, <1ms.
"""
from typing import Optional

# Known AIMS programs for fallback entity detection
_KNOWN_PROGRAMS = frozenset([
    "mba", "mca", "bba", "bca", "bcom", "b.com", "pgdm",
    "b.sc", "msc", "m.sc",
])

# Separator words that sit between two compared entities
_SEPARATORS = {"vs", "versus", "or"}


def extract_entities(query: str) -> list:
    """
    Pull out the two things being compared.
    Strategy 1 — words flanking vs/versus/or.
    Strategy 2 — fallback to any known program names in query.
    """
    q = query.lower().replace("?", "").replace(",", "")
    words = q.split()
    entities = []

    for i, w in enumerate(words):
        if w in _SEPARATORS:
            if i > 0:
                entities.append(words[i - 1])
            if i < len(words) - 1:
                entities.append(words[i + 1])

    # De-duplicate while preserving order
    seen = set()
    unique = []
    for e in entities:
        if e not in seen:
            seen.add(e)
            unique.append(e)

    # Fallback: scan for known program names if flanking failed
    if len(unique) < 2:
        for w in words:
            if w in _KNOWN_PROGRAMS and w not in seen:
                seen.add(w)
                unique.append(w)

    return unique[:2]  # only need the first two


def handle_comparison(query: str) -> Optional[dict]:
    """
    Entry point called by intent_router when intent == 'comparison'.
    Returns a response dict compatible with the chat API, or None to
    fall through to RAG when fewer than 2 entities can be found.
    """
    entities = extract_entities(query)

    if len(entities) < 2:
        return None  # let RAG handle it

    return _build_response(entities[0], entities[1])


def _build_response(e1: str, e2: str) -> dict:
    label1 = e1.upper()
    label2 = e2.upper()

    answer = (
        f"Here's a quick comparison of **{label1}** vs **{label2}**:\n\n"
        f"**{label1}**\n"
        f"- Focused on its core domain and curriculum\n"
        f"- Leads to roles aligned with {label1} specialization\n"
        f"- Choose if you prefer this specific field\n\n"
        f"**{label2}**\n"
        f"- Focused on its core domain and curriculum\n"
        f"- Leads to roles aligned with {label2} specialization\n"
        f"- Choose if you prefer this specific field\n\n"
        f"**Which suits you?**\n"
        f"- Technical / hands-on work? Tell me more about your interest.\n"
        f"- Management / business track? I can guide you further.\n\n"
        f"Ask me about fees, eligibility, or placements for either program!"
    )

    return {
        "answer": answer,
        "fallback": False,
        "confidence": 0.9,
        "sources": [],
        "options": [],
        "meta": {},
    }
