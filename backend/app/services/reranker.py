# backend/app/services/reranker.py
"""
Reranker Service — Production RAG Pipeline Re-ranking Layer
===========================================================
Pipeline upgrade:
  Query → Hybrid Retrieval (~20 docs) → Re-ranking → Top 5 → Response

Architecture:
  - RerankService: singleton class, model loaded once, no repeated init cost
  - Primary:   CrossEncoder model (env RERANKER_MODEL — NOT hardcoded)
  - Secondary: TF-IDF cosine similarity (zero model-download, scikit-learn)
  - Fallback:  simple_rerank heuristic (legacy, always available)

Performance profile (CPU, 20 docs):
  CrossEncoder (tiny model) → ~20–40 ms
  TF-IDF cosine similarity  → ~1–3 ms
  Heuristic keyword scoring → ~1 ms

Configuration:
  RERANKER_MODEL  env var — name of a sentence-transformers cross-encoder to load
                            (e.g. cross-encoder/ms-marco-TinyBERT-L-2-v2)
                            Leave unset to use TF-IDF (default, no download needed)

Usage:
    from app.services.reranker import get_reranker
    top5 = get_reranker().rerank(query, documents, top_k=5)

Legacy (backward-compatible):
    from app.services.reranker import simple_rerank
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────

_reranker_instance: Optional["RerankService"] = None


def get_reranker() -> "RerankService":
    """Return the shared RerankService instance (lazy singleton — no repeated init)."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = RerankService()
    return _reranker_instance


# ─────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────

class RerankService:
    """
    Lightweight re-ranking service for RAG retrieval results.

    Input:  query (str) + documents (List[dict], each with a "content" key)
    Output: top_k most relevant documents sorted by rerank_score descending.

    The scoring backend is selected automatically:
      1. CrossEncoder model  — if RERANKER_MODEL env var is set
      2. TF-IDF cosine sim   — default (scikit-learn, no model download)
      3. Heuristic keywords  — last resort (no external deps)
    """

    def __init__(self) -> None:
        self._cross_encoder = None
        self._mode: str = "none"
        self._load_model()

    def _load_model(self) -> None:
        """Select and initialise scoring backend. Called once at instantiation."""
        model_name = os.getenv("RERANKER_MODEL", "").strip()

        # Attempt CrossEncoder if RERANKER_MODEL env var is provided
        if model_name:
            try:
                from sentence_transformers import CrossEncoder
                self._cross_encoder = CrossEncoder(model_name, max_length=512)
                self._mode = "cross_encoder"
                logger.info("[RERANKER] CrossEncoder loaded: %s", model_name)
                return
            except Exception as exc:
                logger.warning(
                    "[RERANKER] CrossEncoder load failed (model=%s): %s — falling back to TF-IDF",
                    model_name, exc,
                )

        # TF-IDF cosine similarity — lightweight, zero model-download cost
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: F401
            from sklearn.metrics.pairwise import cosine_similarity        # noqa: F401
            self._mode = "tfidf"
            logger.info(
                "[RERANKER] TF-IDF mode active "
                "(set RERANKER_MODEL env var for ML cross-encoder scoring)"
            )
            return
        except ImportError:
            pass

        # Last resort: heuristic keyword scoring (simple_rerank)
        self._mode = "heuristic"
        logger.info("[RERANKER] Heuristic fallback mode (scikit-learn unavailable)")

    # ─────────────────────────────────────────
    # Public entry point
    # ─────────────────────────────────────────

    def rerank(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Re-rank documents by relevance to query and return top_k results.

        Args:
            query:     User query string.
            documents: List of dicts, each must contain a "content" key.
            top_k:     Number of top documents to return after re-ranking (default 5).

        Returns:
            Top-K documents sorted by relevance, each with "rerank_score" added.
            On any error, returns original order (stable fallback).
        """
        if not documents:
            return []

        logger.info(
            "[RERANKER] Scoring %d docs → top %d | mode=%s",
            len(documents), top_k, self._mode,
        )

        _log_top_docs("BEFORE", documents, n=3)  # debug comparison: before rerank

        try:
            if self._mode == "cross_encoder":
                ranked = self._score_cross_encoder(query, documents)
            elif self._mode == "tfidf":
                ranked = self._score_tfidf(query, documents)
            else:
                ranked = self._score_heuristic(query, documents)
        except Exception as exc:
            logger.error(
                "[RERANKER] Scoring error: %s — preserving original retrieval order", exc,
            )
            ranked = documents  # error fallback: keep retrieval order intact

        result = ranked[:top_k]
        _log_top_docs("AFTER", result, n=3)   # debug comparison: after rerank
        logger.info("[RERANKER] %d → %d documents returned", len(documents), len(result))
        return result

    # ─────────────────────────────────────────
    # Scoring backends (private)
    # ─────────────────────────────────────────

    def _score_cross_encoder(
        self, query: str, documents: List[Dict]
    ) -> List[Dict]:
        """Pairwise relevance scoring via a cross-encoder model."""
        pairs = [(query, doc.get("content", "")[:512]) for doc in documents]
        raw_scores = self._cross_encoder.predict(pairs)
        for doc, score in zip(documents, raw_scores):
            doc["rerank_score"] = round(float(score), 4)
        return sorted(documents, key=lambda d: d["rerank_score"], reverse=True)

    def _score_tfidf(
        self, query: str, documents: List[Dict]
    ) -> List[Dict]:
        """TF-IDF cosine similarity — fast, no model download required."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        contents = [doc.get("content", "") for doc in documents]
        corpus = [query] + contents

        vectorizer = TfidfVectorizer(sublinear_tf=True, max_features=8_000)
        tfidf_matrix = vectorizer.fit_transform(corpus)
        scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        for doc, score in zip(documents, scores):
            doc["rerank_score"] = round(float(score), 4)

        return sorted(documents, key=lambda d: d["rerank_score"], reverse=True)

    def _score_heuristic(
        self, query: str, documents: List[Dict]
    ) -> List[Dict]:
        """Delegate to simple_rerank as heuristic last-resort backend."""
        return simple_rerank(query, documents)


# ─────────────────────────────────────────────────────────
# Debug helper
# ─────────────────────────────────────────────────────────

def _log_top_docs(label: str, documents: List[Dict], n: int = 3) -> None:
    """Log top-N document snippets + scores for before/after pipeline comparison."""
    if not documents:
        return
    # INFO-level count summary always visible; DEBUG shows content snippets
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("[RERANKER][%s] top-%d:", label, min(n, len(documents)))
        for i, doc in enumerate(documents[:n], 1):
            snippet = doc.get("content", "")[:80].replace("\n", " ")
            score = doc.get("rerank_score", doc.get("score", "?"))
            logger.debug("  %d. score=%s | %s…", i, score, snippet)


# ─────────────────────────────────────────────────────────────────────────────
# Legacy heuristic reranker — preserved for full backward compatibility.
# Scripts (evaluate_reranker_real.py, test_reranker_impact.py, etc.) and any
# existing callers continue to work without modification.
# ─────────────────────────────────────────────────────────────────────────────

def simple_rerank(query: str, results: list, min_score: float = 0.2):
    """
    Rerank search results by combining semantic similarity with keyword overlap,
    bi-gram matching, and heading-intent matching.

    Args:
        query: The rewritten user query.
        results: List of dicts with keys 'content', 'score', 'heading'.
        min_score: Minimum threshold for inclusion.

    Returns:
        Top 5 reranked chunks (increased from 3 for better synthesis coverage).
    """
    # 1. Filter weak chunks
    filtered_results = [r for r in results if r.get("score", 0) >= min_score]
    if not filtered_results:
        return []

    # 2. Tokenise query — unigrams + bi-grams
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # Bi-grams: "highest package", "hostel fee", "last date", etc.
    words_list = query_lower.split()
    query_bigrams = set(
        f"{words_list[i]} {words_list[i+1]}"
        for i in range(len(words_list) - 1)
    )

    # 3. Intent → heading signals (tightened from v1 based on validation)
    INTENT_SIGNALS = [
        # Specializations
        (["specializ", "subject", "stream", "track"],
         ["mba specializ", "bba specializ", "specialization", "program"]),
        # Placements — covers recruiters AND stats queries
        (["recruiter", "recruit", "company", "placed", "hiring",
          "placement", "lpa", "package", "salary", "ctc", "average", "highest"],
         ["placement", "recruiters", "top recruiters", "placement statistics",
          "placement cell", "campus placement"]),
        # Hostel / campus
        (["hostel", "accommodation", "stay", "dormitor", "resident", "campus"],
         ["hostel", "campus facilities", "campus", "infrastructure"]),
        # Admission / eligibility
        (["admission", "apply", "application", "eligib", "process",
          "procedure", "last date", "deadline", "register"],
         ["admission", "admissions process", "eligibility", "apply"]),
        # Fees / cost
        (["fee", "fees", "cost", "tuition", "scholarship", "emi", "loan"],
         ["scholarship", "fees", "financial", "fee structure", "tuition"]),
        # Accreditation
        (["accredit", "naac", "iacbe", "ranking", "nirf"],
         ["accreditation", "ranking", "naac", "recognition"]),
        # Programs / courses overview
        (["program", "course", "offer", "mba", "bba", "bca", "mca",
          "pgdm", "degree"],
         ["programs", "courses", "mba program", "bba program", "overview"]),
        # FAQ / general
        (["is", "does", "can", "how", "what", "compulsory", "lateral", "medium"],
         ["faqs", "frequently asked questions", "general"]),
    ]

    def heading_boost(chunk) -> float:
        heading = chunk.get("heading", "").lower()
        boost = 0.0

        # MBA specializations super-boost (prevent BBA bleed)
        if any(t in query_lower for t in ["specializ", "subject", "stream"]):
            if "mba" in query_lower:
                if "mba specializ" in heading or ("specializ" in heading and "mba" in heading):
                    boost += 0.35
                if "bba" in heading and "bba" not in query_lower:
                    boost -= 0.15
                return boost  # short-circuit — this signal is decisive

        for query_triggers, heading_keywords in INTENT_SIGNALS:
            if any(t in query_lower for t in query_triggers):
                matched_headings = sum(1 for h in heading_keywords if h in heading)
                if matched_headings:
                    boost += 0.10 + (0.05 * min(matched_headings, 2))  # up to +0.20

        return min(boost, 0.25)  # cap to avoid dominating semantic score

    def source_boost(chunk) -> float:
        """Official institution data beats scraped data."""
        if chunk.get("source") == "official" or chunk.get("priority", 1) >= 2:
            return 0.20
        return 0.0

    def keyword_density_bonus(chunk) -> float:
        """Higher % of query words present in chunk = better relevance signal."""
        if not query_words:
            return 0.0
        content_words = set(chunk.get("content", "").lower().split())
        unigram_hits  = len(query_words & content_words)
        density = unigram_hits / max(len(query_words), 1)
        return round(density * 0.10, 3)  # max +0.10

    def bigram_bonus(chunk) -> float:
        """Bi-gram hits catch precise phrases better than unigrams."""
        if not query_bigrams:
            return 0.0
        content_lower = chunk.get("content", "").lower()
        hits = sum(1 for bg in query_bigrams if bg in content_lower)
        return round(hits * 0.06, 3)  # +0.06 per bi-gram match

    def calculate_rerank_score(chunk) -> float:
        return (
            chunk.get("score", 0)       # base semantic similarity
            + keyword_density_bonus(chunk)
            + bigram_bonus(chunk)
            + heading_boost(chunk)
            + source_boost(chunk)
        )

    # 4. Sort by boosted score
    ranked = sorted(filtered_results, key=calculate_rerank_score, reverse=True)

    # 5. Return top 5 (was 3) — synthesis selects best, more context = better answers
    return ranked[:5]
