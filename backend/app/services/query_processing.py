"""
Local query preprocessing and typo handling for the AIMS assistant.

The pipeline is intentionally deterministic:
- normalize input
- expand slang/short forms
- correct likely spelling noise from a local vocabulary
- map fuzzy course/topic mentions to canonical labels
- expose low-confidence corrections so the API can ask for clarification
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher, get_close_matches
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Set, Tuple

from app.services.taxonomy import (
    COURSE_ALIASES,
    SLANG_MAP,
    STOPWORDS,
    SYNONYM_MAP,
    TOPIC_ALIASES,
    alias_vocabulary,
    apply_slang_map,
    canonicalize_course,
    canonicalize_topic,
    keyword_set,
    normalize_text,
    tokenize,
)

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "faiss_index",
)
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")

GREETING_TERMS = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
EXIT_TERMS = {"bye", "goodbye", "thanks", "thank you", "see you"}
FOLLOW_UP_TERMS = {
    "details",
    "detail",
    "more",
    "explain",
    "expand",
    "continue",
    "what about",
    "how about",
    "same",
    "also",
}
YES_NO_STARTERS = {"is", "are", "can", "does", "do", "will", "has", "have"}


@dataclass
class TokenCorrection:
    original: str
    corrected: str
    confidence: float


class LocalQueryProcessor:
    """Preprocess and annotate user queries without external services."""

    def __init__(self) -> None:
        self.vocabulary = self._build_vocabulary()
        self.correction_vocabulary = self._build_correction_vocabulary()

    def process(self, query: str) -> Dict[str, object]:
        """Normalize, correct, and annotate a raw user query."""
        original_query = query or ""
        normalized_query = normalize_text(original_query)
        slang_expanded = apply_slang_map(normalized_query)
        raw_intent = self._detect_intent(slang_expanded)

        if raw_intent in {"greeting", "exit"}:
            corrected_query = slang_expanded
            corrections = []
            correction_confidence = 1.0
        else:
            corrected_query, corrections, correction_confidence = self._correct_text(slang_expanded)
        canonical_query = self._apply_synonym_map(corrected_query)

        course = canonicalize_course(canonical_query) or canonicalize_course(normalized_query)
        topic = canonicalize_topic(canonical_query) or canonicalize_topic(normalized_query)
        intent = raw_intent if raw_intent in {"greeting", "exit"} else self._detect_intent(canonical_query)
        control_tokens = self._build_control_tokens(intent, course, topic, correction_confidence)
        keywords = sorted(keyword_set([original_query, corrected_query, canonical_query]))
        needs_clarification = self._needs_clarification(
            original_query=original_query,
            canonical_query=canonical_query,
            corrections=corrections,
            correction_confidence=correction_confidence,
            course=course,
            topic=topic,
            intent=intent,
        )

        return {
            "original_query": original_query,
            "normalized_query": normalized_query,
            "corrected_query": corrected_query,
            "query": canonical_query,
            "query_variants": [original_query, normalized_query, corrected_query, canonical_query],
            "intent": intent,
            "course": course,
            "topic": topic,
            "category": topic,
            "keyword_terms": keywords,
            "corrections": [correction.__dict__ for correction in corrections],
            "correction_confidence": round(correction_confidence, 3),
            "needs_clarification": needs_clarification,
            "clarification_message": self._clarification_message(course, topic, correction_confidence)
            if needs_clarification
            else None,
            "control_tokens": control_tokens,
            "detail_level": self._detail_level(canonical_query),
        }

    def _build_vocabulary(self) -> Set[str]:
        vocabulary = alias_vocabulary()
        vocabulary.update({"mba", "bba", "mca", "bca", "phd", "bcom", "mcom", "aims"})

        for token in self._metadata_tokens():
            if token and len(token) > 1:
                vocabulary.add(token)

        return vocabulary

    def _build_correction_vocabulary(self) -> Set[str]:
        """Use a stricter correction vocabulary so unknown words stay untouched."""
        vocabulary = alias_vocabulary()
        vocabulary.update({"mba", "bba", "mca", "bca", "phd", "bcom", "mcom", "aims"})
        return vocabulary

    @lru_cache(maxsize=1)
    def _metadata_tokens(self) -> Tuple[str, ...]:
        if not os.path.exists(METADATA_FILE):
            return tuple()

        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:
            logger.warning("Could not load metadata vocabulary: %s", exc)
            return tuple()

        items = data.get("metadata", data) if isinstance(data, dict) else data
        tokens: Set[str] = set()

        for item in items or []:
            texts = [
                item.get("heading", ""),
                item.get("course", ""),
                item.get("category", ""),
                item.get("text", "")[:800],
            ]
            tokens.update(keyword_set(texts))

        return tuple(sorted(tokens))

    def _correct_text(self, text: str) -> Tuple[str, List[TokenCorrection], float]:
        corrections: List[TokenCorrection] = []
        corrected_tokens: List[str] = []
        confidence_values: List[float] = []

        for token in tokenize(text):
            corrected, confidence = self._correct_token(token)
            corrected_tokens.append(corrected)
            confidence_values.append(confidence)
            if corrected != token:
                corrections.append(
                    TokenCorrection(
                        original=token,
                        corrected=corrected,
                        confidence=round(confidence, 3),
                    )
                )

        if not corrected_tokens:
            return "", corrections, 0.0

        combined_confidence = sum(confidence_values) / max(len(confidence_values), 1)
        return " ".join(corrected_tokens).strip(), corrections, combined_confidence

    def _correct_token(self, token: str) -> Tuple[str, float]:
        if len(token) <= 2 or token in {"bye", "hi", "hey", "hello", "thanks"}:
            return token, 1.0

        if token in self.vocabulary or token in STOPWORDS or token.isdigit():
            return token, 1.0

        candidate_variants = [token]
        collapsed = re.sub(r"(.)\1{2,}", r"\1", token)
        single_repeat = re.sub(r"(.)\1{1,}", r"\1", token)
        for variant in (collapsed, single_repeat):
            if variant and variant not in candidate_variants:
                candidate_variants.append(variant)

        for variant in candidate_variants:
            if variant in self.correction_vocabulary:
                score = SequenceMatcher(None, token, variant).ratio()
                return variant, max(score, 0.84)

        close_matches = get_close_matches(token, self.correction_vocabulary, n=1, cutoff=0.72)
        if close_matches:
            candidate = close_matches[0]
            score = SequenceMatcher(None, token, candidate).ratio()
            if score >= 0.78:
                return candidate, score

        return token, 0.55

    def _apply_synonym_map(self, text: str) -> str:
        mapped_tokens: List[str] = []
        for token in tokenize(text):
            mapped_tokens.append(SYNONYM_MAP.get(token, token))
        return " ".join(mapped_tokens).strip()

    def _detect_intent(self, text: str) -> str:
        normalized = normalize_text(text)
        if not normalized:
            return "factual"

        if normalized in GREETING_TERMS or any(normalized.startswith(term + " ") for term in GREETING_TERMS):
            return "greeting"

        if normalized in EXIT_TERMS or any(term in normalized for term in EXIT_TERMS):
            return "exit"

        if any(term in normalized for term in FOLLOW_UP_TERMS):
            has_explicit_context = bool(canonicalize_course(normalized) or canonicalize_topic(normalized))
            if normalized.startswith(("what about", "how about")) or not has_explicit_context:
                return "follow_up"

        first_token = tokenize(normalized)[:1]
        if first_token and first_token[0] in YES_NO_STARTERS:
            return "yes_no"

        return "factual"

    def _detail_level(self, text: str) -> str:
        normalized = normalize_text(text)
        if any(term in normalized for term in ["brief", "short", "summary"]):
            return "brief"
        if any(term in normalized for term in ["detailed", "detail", "explain", "full"]):
            return "detailed"
        return "normal"

    def _build_control_tokens(
        self,
        intent: str,
        course: Optional[str],
        topic: Optional[str],
        correction_confidence: float,
    ) -> List[str]:
        tokens = [f"INTENT:{intent.upper()}"]
        if course:
            tokens.append(f"COURSE:{course.upper()}")
        if topic:
            tokens.append(f"TOPIC:{topic.upper()}")
        if correction_confidence < 0.75:
            tokens.append("<LOW_CONFIDENCE>")
        return tokens

    def _needs_clarification(
        self,
        original_query: str,
        canonical_query: str,
        corrections: Sequence[TokenCorrection],
        correction_confidence: float,
        course: Optional[str],
        topic: Optional[str],
        intent: str,
    ) -> bool:
        if intent in {"greeting", "exit"}:
            return False

        if not canonical_query:
            return True

        if corrections and correction_confidence < 0.72:
            return True

        if len(tokenize(original_query)) <= 2 and not (course or topic):
            return True

        return False

    def _clarification_message(
        self,
        course: Optional[str],
        topic: Optional[str],
        correction_confidence: float,
    ) -> str:
        if correction_confidence < 0.72:
            if topic and not course:
                return f"Did you mean {topic} information for a specific course like MBA or BBA?"
            return "I want to make sure I understood that correctly. Could you rephrase or mention the course/topic you need?"

        if topic and not course:
            return f"Which course would you like {topic} information for?"

        return "Could you share a little more detail so I can look up the right information?"


_query_processor: Optional[LocalQueryProcessor] = None


def get_query_processor() -> LocalQueryProcessor:
    """Return the shared local query processor."""
    global _query_processor
    if _query_processor is None:
        _query_processor = LocalQueryProcessor()
    return _query_processor
