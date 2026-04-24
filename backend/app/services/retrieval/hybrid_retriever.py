"""
Hybrid retrieval for the offline AIMS assistant.

Combines:
- semantic vector similarity from FAISS
- keyword overlap against indexed metadata/text
- metadata-aware boosts for course/topic/source importance
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.taxonomy import (
    TOPIC_ALIASES,
    WEAK_TOPIC_INFERENCE_ALIASES,
    canonicalize_course,
    infer_topic_from_text,
    keyword_set,
    normalize_text,
)

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Retrieve and rerank chunks using local deterministic signals."""

    def __init__(self) -> None:
        self.index = get_index()
        self._document_cache: List[Dict] = []
        self._document_lookup: Dict[str, Dict] = {}
        self._cache_size = -1

    def search(self, query_data: Dict, k: int = 8, vector_k: int = 16, keyword_k: int = 16) -> List[Dict]:
        self._refresh_cache_if_needed()

        query_text = query_data.get("query", "")
        query_terms = set(query_data.get("keyword_terms", [])) or keyword_set([query_text])
        course = query_data.get("course")
        topic = query_data.get("topic")

        vector_hits = self._vector_hits(query_text, vector_k)
        keyword_hits = self._keyword_hits(query_text, query_terms, course=course, topic=topic, limit=keyword_k)

        merged: Dict[str, Dict] = {}

        for hit in vector_hits:
            merged[hit["key"]] = hit

        for hit in keyword_hits:
            if hit["key"] in merged:
                merged[hit["key"]]["keyword_score"] = max(
                    merged[hit["key"]].get("keyword_score", 0.0),
                    hit.get("keyword_score", 0.0),
                )
                merged[hit["key"]]["score"] = max(
                    merged[hit["key"]].get("score", 0.0),
                    hit.get("score", 0.0),
                )
            else:
                merged[hit["key"]] = hit

        ranked: List[Dict] = []
        for hit in merged.values():
            metadata_score = self._metadata_score(hit, course=course, topic=topic)
            vector_score = hit.get("vector_score", 0.0)
            keyword_score = hit.get("keyword_score", 0.0)
            final_score = (vector_score * 0.55) + (keyword_score * 0.25) + metadata_score
            final_score += self._penalty_adjustment(hit, course=course, topic=topic)
            hit["metadata_score"] = round(metadata_score, 4)
            hit["score"] = round(max(0.0, min(final_score, 1.0)), 4)
            ranked.append(hit)

        ranked.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        if topic:
            heading_topic_hits = [item for item in ranked if self._heading_matches_topic(item, topic)]
            if heading_topic_hits:
                non_heading_hits = [item for item in ranked if item not in heading_topic_hits]
                ranked = heading_topic_hits + non_heading_hits
            topical_hits = [item for item in ranked if item.get("topic") == topic]
            if topical_hits:
                non_topical_hits = [item for item in ranked if item.get("topic") != topic]
                ranked = topical_hits + non_topical_hits
        return ranked[:k]

    def to_chunk_tuples(self, results: List[Dict]) -> List[Tuple]:
        chunks: List[Tuple] = []
        for result in results:
            chunks.append(
                (
                    result.get("content", ""),
                    float(result.get("score", 0.0)),
                    result.get("url", ""),
                    result.get("heading", ""),
                    result.get("doc_id"),
                    result.get("source", "web"),
                    float(result.get("priority", 1.0)),
                    result.get("course"),
                    result.get("topic"),
                    float(result.get("importance", 1.0)),
                )
            )
        return chunks

    def _refresh_cache_if_needed(self) -> None:
        metadata = self.index.metadata or []
        if self._cache_size == len(metadata):
            return

        cache: List[Dict] = []
        for idx, meta in enumerate(metadata):
            content = meta.get("full_text") or meta.get("text", "")
            heading = meta.get("heading", "")
            key = str(meta.get("doc_id") or meta.get("id") or meta.get("index_position") or idx)
            course = (
                canonicalize_course(str(meta.get("course", "")))
                or canonicalize_course(heading)
                or canonicalize_course(content[:160])
            )
            topic = (
                infer_topic_from_text(heading)
                or infer_topic_from_text(content[:240])
            )
            cache.append(
                {
                    "key": key,
                    "doc_id": meta.get("doc_id") or meta.get("id") or meta.get("index_position") or idx,
                    "content": content,
                    "url": meta.get("url", ""),
                    "heading": heading,
                    "source": meta.get("source", "web"),
                    "priority": float(meta.get("priority", 1.0)),
                    "importance": float(meta.get("importance", meta.get("priority", 1.0))),
                    "course": course,
                    "topic": topic,
                    "tokens": keyword_set([content[:1200], heading, course or "", topic or ""]),
                }
            )

        self._document_cache = cache
        self._document_lookup = {item["key"]: item for item in cache}
        self._cache_size = len(metadata)
        logger.info("Hybrid retriever cache refreshed (%s chunks)", self._cache_size)

    def _vector_hits(self, query_text: str, limit: int) -> List[Dict]:
        query_embedding = embed_text(query_text)
        raw_results = self.index.search(query_embedding, k=limit)
        hits: List[Dict] = []

        for raw in raw_results:
            key = str(raw[4])
            cached = self._document_lookup.get(key, {})
            hits.append(
                {
                    "key": key,
                    "doc_id": raw[4],
                    "content": cached.get("content", raw[0]),
                    "url": cached.get("url", raw[2]),
                    "heading": cached.get("heading", raw[3]),
                    "vector_score": float(raw[1]),
                    "keyword_score": 0.0,
                    "score": float(raw[1]),
                    "source": cached.get("source", raw[5] if len(raw) > 5 else "web"),
                    "priority": cached.get("priority", float(raw[6]) if len(raw) > 6 else 1.0),
                    "course": cached.get("course", raw[7] if len(raw) > 7 else None),
                    "topic": cached.get("topic", raw[8] if len(raw) > 8 else None),
                    "importance": cached.get("importance", float(raw[9]) if len(raw) > 9 else 1.0),
                }
            )

        return hits

    def _keyword_hits(
        self,
        query_text: str,
        query_terms: set[str],
        course: Optional[str],
        topic: Optional[str],
        limit: int,
    ) -> List[Dict]:
        query_normalized = normalize_text(query_text)
        scored: List[Dict] = []

        for doc in self._document_cache:
            if not doc["content"]:
                continue

            overlap = len(query_terms & doc["tokens"]) / max(len(query_terms), 1)
            heading_tokens = keyword_set([doc["heading"]])
            heading_overlap = len(query_terms & heading_tokens) / max(len(query_terms), 1)
            fuzzy_heading = SequenceMatcher(None, query_normalized, normalize_text(doc["heading"][:120])).ratio()
            fuzzy_content = SequenceMatcher(None, query_normalized, normalize_text(doc["content"][:200])).ratio()

            score = (overlap * 0.6) + (heading_overlap * 0.2) + (fuzzy_heading * 0.12) + (fuzzy_content * 0.08)
            if course and doc.get("course") == course:
                score += 0.08
            if topic and doc.get("topic") == topic:
                score += 0.08

            if score <= 0.08:
                continue

            scored.append(
                {
                    **doc,
                    "vector_score": 0.0,
                    "keyword_score": round(score, 4),
                    "score": round(score, 4),
                }
            )

        scored.sort(key=lambda item: item.get("keyword_score", 0.0), reverse=True)
        return scored[:limit]

    def _metadata_score(self, hit: Dict, course: Optional[str], topic: Optional[str]) -> float:
        score = 0.0
        if course and hit.get("course") == course:
            score += 0.1
        if topic and hit.get("topic") == topic:
            score += 0.1
        if hit.get("source") == "official":
            score += 0.08
        score += min(float(hit.get("priority", 1.0)) / 20.0, 0.06)
        score += min(float(hit.get("importance", 1.0)) / 25.0, 0.04)
        return score

    def _penalty_adjustment(self, hit: Dict, course: Optional[str], topic: Optional[str]) -> float:
        penalty = 0.0
        hit_course = hit.get("course")
        hit_topic = hit.get("topic")

        if course and hit_course and hit_course != course:
            penalty -= 0.12

        if topic:
            if hit_topic and hit_topic != topic:
                penalty -= 0.16
            elif not hit_topic and hit.get("keyword_score", 0.0) < 0.08:
                penalty -= 0.08

        return penalty

    def _heading_matches_topic(self, hit: Dict, topic: str) -> bool:
        heading = normalize_text(hit.get("heading", ""))
        if not heading:
            return False

        topic_terms = {topic}
        for alias in TOPIC_ALIASES.get(topic, []):
            alias_normalized = normalize_text(alias)
            if alias_normalized and alias_normalized not in WEAK_TOPIC_INFERENCE_ALIASES:
                topic_terms.add(alias_normalized)

        return any(term in heading for term in topic_terms)


_hybrid_retriever: Optional[HybridRetriever] = None


def get_hybrid_retriever() -> HybridRetriever:
    """Return the shared hybrid retriever."""
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever
