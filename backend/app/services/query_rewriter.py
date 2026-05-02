# backend/app/services/query_rewriter.py

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── Vague-query detection ─────────────────────────────────────────────────────

_VAGUE_STARTERS = re.compile(
    r"^(what about|and |tell me more|how about|more about|"
    r"what is it|what are they|and what|also |so what)\b",
    re.IGNORECASE,
)
_PRONOUN_PATTERN = re.compile(
    r"\b(it|this|that|they|their|there|these|those)\b", re.IGNORECASE
)
_VAGUE_PHRASES = re.compile(
    r"\b(what about|tell me more|more details|anything else|and this|and that)\b",
    re.IGNORECASE,
)

# Topics — priority order (most discriminative first)
_TOPIC_PRIORITY = [
    "placement", "hostel", "admission", "fees", "fee", "scholarship",
    "eligibility", "campus", "faculty", "accreditation", "recruiter",
    "salary", "infrastructure", "ranking", "cutoff", "course", "program",
]

# Recognized course/program entities
_ENTITIES = ["mba", "bba", "bca", "mca", "pgdm", "phd", "executive mba"]

# Intent → (compact_with_entity, question_with_entity, fallback_no_entity)
_INTENT_TEMPLATES = {
    "fee":         ("{entity} fees at AIMS College",
                   "What are the {entity} fees at AIMS College?",
                   "What are the fees at AIMS College?"),
    "fees":        ("{entity} fees at AIMS College",
                   "What are the {entity} fees at AIMS College?",
                   "What are the fees at AIMS College?"),
    "hostel":      ("Hostel fees for {entity} at AIMS College",
                   "What are the hostel facilities for {entity} at AIMS College?",
                   "What are the hostel facilities at AIMS College?"),
    "placement":   ("{entity} placement packages at AIMS College",
                   "What are the {entity} placement packages at AIMS College?",
                   "What are the placement statistics at AIMS College?"),
    "admission":   ("{entity} admission process at AIMS College",
                   "What is the {entity} admission process at AIMS College?",
                   "What is the admission process at AIMS College?"),
    "eligibility": ("{entity} eligibility criteria at AIMS College",
                   "What is the {entity} eligibility criteria at AIMS College?",
                   "What is the eligibility criteria at AIMS College?"),
    "scholarship": ("{entity} scholarships at AIMS College",
                   "What {entity} scholarships are available at AIMS College?",
                   "What scholarships are available at AIMS College?"),
    "campus":      ("Campus facilities at AIMS College",
                   "What are the campus facilities at AIMS College?",
                   "What are the campus facilities at AIMS College?"),
    "recruiter":   ("Top {entity} recruiters at AIMS College",
                   "Which companies recruit {entity} from AIMS College?",
                   "Which companies recruit from AIMS College?"),
    "salary":      ("{entity} salary package at AIMS College",
                   "What is the average {entity} salary at AIMS College?",
                   "What is the average salary at AIMS College?"),
    "ranking":     ("AIMS College ranking and accreditation",
                   "What is the ranking of AIMS College?",
                   "What is the ranking of AIMS College?"),
}


def _is_question(query: str) -> bool:
    q = query.strip()
    return q.endswith("?") or q.lower().split()[0] in (
        "what", "how", "when", "where", "who", "which", "is", "are", "can", "does"
    ) if q else False


def _clean_output(text: str) -> str:
    text = text.strip()
    # Remove duplicate consecutive words (case-insensitive)
    words = text.split()
    deduped = [words[0]] + [
        w for i, w in enumerate(words[1:], 1)
        if w.lower() != words[i - 1].lower()
    ]
    result = " ".join(deduped)
    # Capitalize first letter, preserve rest
    return result[0].upper() + result[1:] if result else result


def _needs_rewrite(query: str) -> tuple:
    """Returns (needs_rewrite: bool, reason: str)."""
    q = query.strip().lower()
    if _VAGUE_STARTERS.match(q):
        return True, "vague_phrase"
    if _VAGUE_PHRASES.search(q):
        return True, "vague_phrase"
    if _PRONOUN_PATTERN.search(q) and len(q.split()) < 7:
        return True, "pronoun"
    # Only rewrite short queries if they contain NO clear AIMS topic
    if len(q.split()) < 3 and not any(kw in q for kw in _TOPIC_PRIORITY):
        return True, "incomplete"
    return False, ""


def _extract_entity(messages: list) -> Optional[str]:
    """Return most recently mentioned course entity from last 4 messages."""
    for msg in reversed(messages[-4:]):
        text = msg.get("content", "").lower()
        for entity in _ENTITIES:
            if entity in text:
                return entity.upper()
    return None


def _extract_topic(messages: list) -> Optional[str]:
    """Recency-first from last 4 messages; priority breaks ties."""
    for msg in reversed(messages[-4:]):
        text = msg.get("content", "").lower()
        for kw in _TOPIC_PRIORITY:
            if kw in text:
                return kw
    return None


def _heuristic_rewrite(
    query: str,
    topic: Optional[str],
    entity: Optional[str] = None,
) -> str:
    """Produce a specific, natural, retrieval-friendly query."""
    q_lower = query.strip().lower()
    inline_topic = next((kw for kw in _TOPIC_PRIORITY if kw in q_lower), None)
    resolved_topic = inline_topic or topic

    if not resolved_topic:
        return query  # strict guard: no topic — no rewrite

    triple = _INTENT_TEMPLATES.get(resolved_topic)
    if triple:
        compact, question, fallback = triple
        if entity and "{entity}" in compact:
            out = question.format(entity=entity) if _is_question(query) else compact.format(entity=entity)
        else:
            out = fallback
        return _clean_output(out)

    base = f"{entity} {resolved_topic}" if entity else resolved_topic
    return _clean_output(f"{base} at AIMS College")


# ── Public API ────────────────────────────────────────────────────────────────

_APPLY_PATTERNS = re.compile(
    r"\b(how\s+to\s+apply|apply\s+for\s+admission|admission\s+process|"
    r"application\s+form|how\s+do\s+i\s+apply|steps\s+to\s+apply|"
    r"register\s+for\s+admission|enroll\s+at\s+aims)\b",
    re.IGNORECASE,
)


def rewrite_with_context(query: str, session_id: str) -> str:
    """
    Rewrite vague/follow-up queries using conversation history.
    Heuristic-only — no LLM calls. Falls back to original on error.
    """
    if not query:
        return ""
    original = query

    # Direct interception: apply/admission-process queries retrieve scholarship chunks
    # without this normalization — force to application-specific terms
    if _APPLY_PATTERNS.search(query):
        rewritten = "admission application process steps apply AIMS College form documents"
        logger.info("[REWRITER] apply-intercept '%s' → '%s'", original, rewritten)
        return rewritten

    needs, reason = _needs_rewrite(query)

    if not needs:
        result = _base_rewrite(query)
        logger.info("[REWRITER] no rewrite | query='%s'", result)
        return result

    topic, entity = None, None
    try:
        from app.services.conversation_store import get_conversation_store
        session = get_conversation_store().get_session(session_id)
        messages = session.get("messages", []) if session else []
        topic  = _extract_topic(messages)
        entity = _extract_entity(messages)
    except Exception as exc:
        logger.warning("[REWRITER] context fetch failed: %s", exc)

    # Confidence guard: skip rewrite if no topic found
    if not topic and not any(kw in query.lower() for kw in _TOPIC_PRIORITY):
        logger.info("[REWRITER] low confidence — no rewrite | query='%s'", original)
        return _base_rewrite(query)

    rewritten = _heuristic_rewrite(query, topic, entity)

    # Validation: reject if unchanged, shorter without gain, or empty
    if (
        not rewritten
        or rewritten.strip().lower() == query.strip().lower()
        or (len(rewritten) < len(query) and not entity and not topic)
    ):
        rewritten = _base_rewrite(query)

    logger.info(
        "[REWRITER] '%s' → '%s' | reason=%s topic=%s entity=%s",
        original, rewritten, reason, topic or "none", entity or "none",
    )
    return rewritten


# ── Preserved backward-compatible functions ───────────────────────────────────

def clean_query(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def expand_query(text: str) -> str:
    words = text.split()
    if len(words) <= 3 and "aims" not in text.lower():
        return f"{text} aims college"
    return text


def _base_rewrite(text: str) -> str:
    return expand_query(clean_query(text))


def rewrite_query(text: str) -> str:
    if not text:
        return ""
    return _base_rewrite(text)
