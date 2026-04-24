"""
Dynamic confidence scoring for the local retrieval-first assistant.
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Tuple

from app.services.taxonomy import keyword_set

logger = logging.getLogger(__name__)


def calculate_confidence(query: str, results: list, query_data: Optional[Dict] = None, max_sources: int = 5) -> float:
    """
    Blend retrieval quality signals into a single 0-1 confidence score.

    Signals:
    - top semantic score
    - average score across top results
    - keyword alignment between query and retrieved text
    - metadata alignment for course/topic
    - agreement between vector and lexical signals when available
    """
    if not results or not query:
        return 0.0

    top_results = results[:max_sources]
    query_terms = keyword_set([query])
    texts: List[str] = []
    scores: List[float] = []
    vector_scores: List[float] = []
    keyword_scores: List[float] = []
    metadata_alignment = 0.0

    expected_course = query_data.get("course") if query_data else None
    expected_topic = query_data.get("topic") if query_data else None

    for result in top_results:
        text, score, course, topic, vector_score, keyword_score = _result_parts(result)
        texts.append(text)
        scores.append(score)
        vector_scores.append(vector_score)
        keyword_scores.append(keyword_score)

        if expected_course and course == expected_course:
            metadata_alignment += 0.5
        if expected_topic and topic == expected_topic:
            metadata_alignment += 0.5

    top_score = max(scores) if scores else 0.0
    avg_score = sum(scores) / max(len(scores), 1)
    keyword_alignment = _keyword_alignment(query_terms, texts)
    metadata_alignment = min(metadata_alignment / max(len(top_results), 1), 1.0)
    signal_agreement = _signal_agreement(vector_scores, keyword_scores)

    confidence = (
        (top_score * 0.32)
        + (avg_score * 0.24)
        + (keyword_alignment * 0.22)
        + (metadata_alignment * 0.12)
        + (signal_agreement * 0.10)
    )

    if query_data and query_data.get("needs_clarification"):
        confidence *= 0.6

    if len(query_terms) >= 2:
        if keyword_alignment < 0.34:
            confidence *= 0.45
        elif keyword_alignment < 0.5:
            confidence *= 0.65

    confidence = max(0.0, min(confidence, 1.0))
    logger.debug(
        "Confidence top=%.3f avg=%.3f kw=%.3f meta=%.3f agree=%.3f -> %.3f",
        top_score,
        avg_score,
        keyword_alignment,
        metadata_alignment,
        signal_agreement,
        confidence,
    )
    return round(confidence, 3)


def is_confident_enough(confidence: float, threshold: float = 0.5) -> bool:
    return confidence >= threshold


def get_confidence_label(confidence: float) -> str:
    if confidence < 0.35:
        return "Low Confidence"
    if confidence < 0.55:
        return "Needs Review"
    if confidence < 0.75:
        return "Moderate Confidence"
    return "Verified Information"


def _result_parts(result: object) -> Tuple[str, float, Optional[str], Optional[str], float, float]:
    if isinstance(result, dict):
        return (
            result.get("content", ""),
            float(result.get("score", result.get("similarity_score", 0.0))),
            result.get("course"),
            result.get("topic"),
            float(result.get("vector_score", result.get("score", 0.0))),
            float(result.get("keyword_score", 0.0)),
        )

    if isinstance(result, tuple):
        return (
            result[0] if len(result) > 0 else "",
            float(result[1]) if len(result) > 1 else 0.0,
            result[7] if len(result) > 7 else None,
            result[8] if len(result) > 8 else None,
            float(result[1]) if len(result) > 1 else 0.0,
            0.0,
        )

    return ("", 0.0, None, None, 0.0, 0.0)


def _keyword_alignment(query_terms: set[str], texts: Iterable[str]) -> float:
    if not query_terms:
        return 0.0
    text_terms = keyword_set(texts)
    overlap = len(query_terms & text_terms)
    return overlap / max(len(query_terms), 1)


def _signal_agreement(vector_scores: List[float], keyword_scores: List[float]) -> float:
    if not vector_scores:
        return 0.0

    avg_vector = sum(vector_scores) / max(len(vector_scores), 1)
    avg_keyword = sum(keyword_scores) / max(len(keyword_scores), 1)
    if avg_keyword == 0.0:
        return min(avg_vector, 1.0)

    difference = abs(avg_vector - avg_keyword)
    return max(0.0, 1.0 - difference)
