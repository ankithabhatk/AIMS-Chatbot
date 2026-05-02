# app/services/llm/prompt_builder.py
import re
from typing import List, Any

FALLBACK_ANSWER = (
    "I don't have that information right now. "
    "Please contact the college for details."
)

_FALLBACK_VARIANTS = [
    FALLBACK_ANSWER,
    ("I couldn't find that information in the available data. "
     "Please contact the college for more details."),
    ("That information is not available in the current data. "
     "Please reach out to the college directly."),
]

# Anchors shared by all variants — used for fast membership test
_FALLBACK_ANCHORS = frozenset([
    "please contact the college",
    "please reach out to the college",
    "couldn't find that information",
    "not available in the current data",
    "don't have that information",
])

GROUNDING_PREFIX       = "Based on the provided information: "
PARTIAL_PREFIX         = "Based on available details: "
_PREFIXES              = (GROUNDING_PREFIX, PARTIAL_PREFIX)

_SYSTEM_INSTRUCTION = (
    "You are a concise assistant for AIMS College. "
    "Answer primarily using the provided context. "
    "Do NOT include information not supported by the context. "
    "If the answer is not in the context, reply exactly: "
    f'"{FALLBACK_ANSWER}" '
    "Keep answers to 2–5 sentences."
)

_CHUNK_CHAR_LIMIT = 380
_MAX_CHUNKS = 5
_RANK_LABELS = ["Most relevant", "Next relevant", "Also relevant", "Additional", "Supporting"]

# Strict fallback triggers (empty/short/impossible to answer)
_VAGUE_PHRASES = [
    "it depends", "not sure", "may vary", "i'm not certain", "i am not certain",
    "not clearly specified", "not mentioned", "no information available",
    "cannot be determined", "unclear from context",
]

# Partial-confidence signals — answer exists but hedged
_PARTIAL_SIGNALS = frozenset(["may", "might", "typically", "generally", "varies"])

# Rotating fallback counter (thread-safe via GIL on int increment)
_fallback_counter = 0


def _extract_text(chunk: Any) -> str:
    if isinstance(chunk, dict):
        return chunk.get("content", chunk.get("text", ""))
    if isinstance(chunk, (list, tuple)) and len(chunk) > 0:
        return str(chunk[0])
    return str(chunk)


def _extract_heading(chunk: Any) -> str:
    if isinstance(chunk, dict):
        return chunk.get("heading", "")
    if isinstance(chunk, (list, tuple)) and len(chunk) > 3:
        return str(chunk[3])
    return ""


def _sentence_safe_trim(text: str, limit: int = _CHUNK_CHAR_LIMIT) -> str:
    """Trim at the nearest sentence boundary before `limit`; fall back to word boundary."""
    if len(text) <= limit:
        return text
    window = text[:limit]
    last_dot = window.rfind(".")
    if last_dot > limit // 2:
        return window[: last_dot + 1]
    last_space = window.rfind(" ")
    return (window[:last_space] if last_space > 0 else window) + "…"


_RANK_PREFIX_RE = re.compile(r"^\[\d+\] [^:]+: ")


def _dedup(texts: List[str]) -> List[str]:
    seen, out = set(), []
    for t in texts:
        body = _RANK_PREFIX_RE.sub("", t, count=1)
        key = re.sub(r"\s+", " ", body[:120].lower())
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


def build_context(chunks: List[Any]) -> str:
    """Sentence-safe trimmed, ranked, deduped context string."""
    parts = []
    for i, chunk in enumerate(chunks[:_MAX_CHUNKS]):
        text = _extract_text(chunk).strip()
        heading = _extract_heading(chunk).strip()
        if not text:
            continue
        trimmed = _sentence_safe_trim(text)
        label = _RANK_LABELS[min(i, len(_RANK_LABELS) - 1)]
        head = f" — {heading}" if heading else ""
        parts.append(f"[{i + 1}] {label}{head}: {trimmed}")

    parts = _dedup(parts)
    return "\n\n".join(parts) if parts else ""


def build_messages(query: str, chunks: List[Any]) -> List[dict]:
    """Build OpenAI chat messages with ranked context and strict system prompt."""
    context = build_context(chunks)
    if not context:
        context = "No relevant information found."

    user_content = f"Context:\n{context}\n\nQuestion: {query}"
    return [
        {"role": "system", "content": _SYSTEM_INSTRUCTION},
        {"role": "user",   "content": user_content},
    ]


def next_fallback() -> str:
    """Return the next fallback variant in rotation (deterministic, no randomness)."""
    global _fallback_counter
    variant = _FALLBACK_VARIANTS[_fallback_counter % len(_FALLBACK_VARIANTS)]
    _fallback_counter += 1
    return variant


def validate_answer(text: str) -> str:
    """Return a rotated fallback if the answer is empty, too short, or contains vague phrases."""
    t = (text or "").strip()
    if not t or len(t) < 20:
        return next_fallback()
    t_lower = t.lower()
    if any(phrase in t_lower for phrase in _VAGUE_PHRASES):
        return next_fallback()
    return t


def _is_partial(answer: str) -> bool:
    """True if the answer contains hedging/uncertainty words."""
    a = answer.lower()
    return any(f" {sig} " in a or a.startswith(sig + " ") for sig in _PARTIAL_SIGNALS)


def apply_grounding_prefix(answer: str) -> str:
    """Prepend confidence-appropriate prefix; idempotent, no prefix on fallback."""
    if is_fallback_answer(answer):
        return answer
    if any(answer.startswith(p) for p in _PREFIXES):
        return answer
    prefix = PARTIAL_PREFIX if _is_partial(answer) else GROUNDING_PREFIX
    return prefix + answer


def is_fallback_answer(answer: str) -> bool:
    """True if the answer matches any known fallback variant via anchor strings."""
    a = (answer or "").lower()
    return any(anchor in a for anchor in _FALLBACK_ANCHORS)
