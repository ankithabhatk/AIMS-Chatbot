# app/services/evaluator.py
"""
Lightweight RAG evaluation pipeline.
Calls embed → retrieve → rerank → synthesize directly (no HTTP, no server needed).
"""

import json
import logging
import math
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_HISTORY_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "evaluation_logs.json")
)

logger = logging.getLogger(__name__)

_FALLBACK_MARKERS = [
    "don't have that information",
    "couldn't find that information",
    "not available in the current data",
    "please contact the college",
]

_FAISS_K = 20
_TOP_K   = 5

CATEGORY_WEIGHTS: Dict[str, float] = {
    "fees":          1.5,
    "admission":     1.3,
    "placements":    1.2,
    "courses":       1.0,
    "campus":        0.8,
    "accreditation": 1.0,
    "general":       1.0,
}


# ── Pipeline helpers ──────────────────────────────────────────────────────────

def _run_pipeline(query: str) -> Dict[str, Any]:
    """Execute embed → retrieve → rerank → synthesize; return dict with response + meta."""
    t0 = time.time()
    try:
        from app.services.embeddings.embedding_service import embed_text
        from app.services.retrieval.faiss_index import get_index
        from app.services.reranker import get_reranker
        from app.services.llm.answer_generator import get_answer_generator
        from app.services.logger import compute_confidence

        embedding = embed_text(query)
        index     = get_index()
        if not index or not index.validate_integrity():
            return _error_result(query, "index unavailable", t0)

        raw_chunks = index.search(embedding, k=_FAISS_K) or []
        if not raw_chunks:
            return _fallback_result(query, "no chunks retrieved", t0)

        candidate_dicts = [
            {
                "content":  c[0],
                "score":    c[1],
                "url":      c[2] if len(c) > 2 else "",
                "heading":  c[3] if len(c) > 3 else "",
            }
            for c in raw_chunks
        ]
        reranked = get_reranker().rerank(query, candidate_dicts, top_k=_TOP_K)

        # Convert back to tuples for AnswerGenerator
        chunk_tuples = [
            (d.get("content", ""), d.get("score", 0.0), d.get("url", ""), d.get("heading", ""))
            for d in reranked
        ]

        answer     = get_answer_generator().synthesize(query, chunk_tuples)
        confidence = compute_confidence(reranked)
        is_fb      = any(m in (answer or "").lower() for m in _FALLBACK_MARKERS)

        return {
            "query":            query,
            "response":         answer or "",
            "confidence":       confidence,
            "fallback":         is_fb,
            "response_time_ms": int((time.time() - t0) * 1000),
            "error":            None,
        }

    except Exception as exc:
        logger.error("Evaluator pipeline error: %s", exc)
        return _error_result(query, str(exc), t0)


def _fallback_result(query: str, reason: str, t0: float) -> Dict[str, Any]:
    return {"query": query, "response": reason, "confidence": 0.0,
            "fallback": True, "response_time_ms": int((time.time() - t0) * 1000), "error": None}


def _error_result(query: str, reason: str, t0: float) -> Dict[str, Any]:
    return {"query": query, "response": "", "confidence": 0.0,
            "fallback": True, "response_time_ms": int((time.time() - t0) * 1000), "error": reason}


# ── Semantic similarity ─────────────────────────────────────────────────────

def compute_similarity(text1: str, text2: str) -> Optional[float]:
    """Cosine similarity via embedding service; returns None if unavailable."""
    if not text1 or not text2:
        return None
    try:
        from app.services.embeddings.embedding_service import embed_text
        e1 = embed_text(text1)
        e2 = embed_text(text2)
        dot  = sum(a * b for a, b in zip(e1, e2))
        mag1 = math.sqrt(sum(a * a for a in e1))
        mag2 = math.sqrt(sum(b * b for b in e2))
        if mag1 == 0 or mag2 == 0:
            return None
        return round(dot / (mag1 * mag2), 4)
    except Exception:
        return None


# ── Scoring ───────────────────────────────────────────────────────────────────

def _keywords_match(response: str, keywords: List[str]) -> bool:
    r = response.lower()
    return all(kw.lower() in r for kw in keywords)


def score_response(
    response: str,
    expected_keywords: List[str],
    expected_answer: str = "",
) -> float:
    """
    Tries semantic similarity first (embedding cosine); falls back to keyword logic.
    1.0 — similarity > 0.75 OR all kw + answer token hit
    0.5 — similarity 0.5–0.75 OR partial kw match
    0.0 — no match
    """
    if not response:
        return 0.0

    if expected_answer:
        sim = compute_similarity(response, expected_answer)
        if sim is not None:
            if sim > 0.68:
                return 1.0
            if sim > 0.45:
                return 0.5
            return 0.0

    r = response.lower()
    keywords = expected_keywords or []
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw.lower() in r)
    if hits == len(keywords):
        if expected_answer:
            answer_tokens = [t for t in expected_answer.lower().split() if len(t) > 3]
            answer_hit = any(tok in r for tok in answer_tokens) if answer_tokens else True
            return 1.0 if answer_hit else 0.5
        return 1.0
    return 0.5 if hits > 0 else 0.0


# ── History ───────────────────────────────────────────────────────────────────

def _append_history(summary: Dict[str, Any]) -> None:
    history: List[Dict[str, Any]] = []
    if os.path.exists(_HISTORY_FILE):
        try:
            with open(_HISTORY_FILE, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    history.append(summary)
    try:
        with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        logger.warning("Could not write evaluation history: %s", exc)


# ── Public API ────────────────────────────────────────────────────────────────

def run_evaluation(
    dataset: List[Dict[str, Any]],
    save_history: bool = True,
) -> Dict[str, Any]:
    """
    Run every test case through the pipeline.
    Supports optional fields: expected_answer, category.
    Scores: 1.0 (correct) / 0.5 (partial) / 0.0 (incorrect).
    """
    details: List[Dict[str, Any]] = []
    total_score      = 0.0
    total_confidence = 0.0
    weighted_score   = 0.0
    total_weight     = 0.0
    fallbacks        = 0
    correct_count    = 0
    partial_count    = 0
    incorrect_count  = 0
    high_conf_wrong  = 0
    low_conf_correct = 0
    cat_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {"total": 0, "score": 0.0, "weighted": 0.0, "weight": 0.0})

    for case in dataset:
        query           = case["query"]
        keywords        = case.get("expected_keywords", [])
        expected_answer = case.get("expected_answer", "")
        category        = case.get("category", "general")
        weight          = CATEGORY_WEIGHTS.get(category, 1.0)

        result = _run_pipeline(query)
        conf   = result["confidence"]
        sc     = score_response(result["response"], keywords, expected_answer)

        total_score      += sc
        total_confidence += conf
        weighted_score   += sc * weight
        total_weight     += weight

        if result["fallback"]:
            fallbacks += 1
        if sc == 1.0:
            correct_count += 1
            if conf < 0.4:
                low_conf_correct += 1
        elif sc == 0.5:
            partial_count += 1
        else:
            incorrect_count += 1
            if conf > 0.7:
                high_conf_wrong += 1

        cat_stats[category]["total"]    += 1
        cat_stats[category]["score"]    += sc
        cat_stats[category]["weighted"] += sc * weight
        cat_stats[category]["weight"]   += weight

        details.append({
            "query":             query,
            "category":          category,
            "weight":            weight,
            "expected_keywords": keywords,
            "expected_answer":   expected_answer,
            "response":          result["response"][:300],
            "confidence":        conf,
            "response_time_ms":  result["response_time_ms"],
            "score":             sc,
            "correct":           sc == 1.0,
            "fallback":          result["fallback"],
            "error":             result["error"],
        })

    total             = len(dataset)
    accuracy          = round(total_score / total, 4) if total else 0.0
    weighted_accuracy = round(weighted_score / total_weight, 4) if total_weight else 0.0
    avg_conf          = round(total_confidence / total, 4) if total else 0.0

    category_accuracy = {
        cat: round(v["score"] / v["total"], 4) if v["total"] else 0.0
        for cat, v in cat_stats.items()
    }
    weighted_category_accuracy = {
        cat: round(v["weighted"] / v["weight"], 4) if v["weight"] else 0.0
        for cat, v in cat_stats.items()
    }

    report = {
        "total":                     total,
        "correct":                   correct_count,
        "partial":                   partial_count,
        "incorrect":                 incorrect_count,
        "total_score":               round(total_score, 4),
        "accuracy":                  accuracy,
        "weighted_accuracy":         weighted_accuracy,
        "fallback_rate":             round(fallbacks / total, 4) if total else 0.0,
        "avg_confidence":            avg_conf,
        "high_conf_wrong":           high_conf_wrong,
        "low_conf_correct":          low_conf_correct,
        "category_accuracy":         category_accuracy,
        "weighted_category_accuracy": weighted_category_accuracy,
        "failed_queries":            [d["query"] for d in details if d["score"] == 0.0],
        "details":                   details,
    }

    if save_history and total:
        _append_history({
            "timestamp":          datetime.now(timezone.utc).isoformat(),
            "accuracy":           accuracy,
            "weighted_accuracy":  weighted_accuracy,
            "avg_confidence":     avg_conf,
            "total":              total,
            "correct":            correct_count,
            "partial":            partial_count,
            "incorrect":          incorrect_count,
            "high_conf_wrong":    high_conf_wrong,
            "low_conf_correct":   low_conf_correct,
        })

    return report


def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── Auto dataset expansion ────────────────────────────────────────────────────

_CANDIDATES_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "tests", "eval_candidates.json")
)


def generate_dataset_candidates(
    threshold: float = 0.4,
    max_candidates: int = 20,
) -> List[Dict[str, Any]]:
    """
    Pull low-confidence queries from logger, de-duplicate, format as dataset
    candidates, and save to tests/eval_candidates.json.
    """
    try:
        from app.services.logger import get_low_confidence_queries
        low_conf = get_low_confidence_queries(threshold)
    except Exception as exc:
        logger.warning("generate_dataset_candidates: logger unavailable: %s", exc)
        low_conf = []

    existing: List[Dict[str, Any]] = []
    if os.path.exists(_CANDIDATES_FILE):
        try:
            with open(_CANDIDATES_FILE, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing_queries = {e["query"].lower() for e in existing}
    new_candidates: List[Dict[str, Any]] = []

    for record in low_conf[:max_candidates]:
        q = record.get("query", "").strip()
        if not q or q.lower() in existing_queries:
            continue
        new_candidates.append({
            "query":             q,
            "expected_keywords": [],
            "expected_answer":   "",
            "category":          "unknown",
        })
        existing_queries.add(q.lower())

    all_candidates = existing + new_candidates
    try:
        with open(_CANDIDATES_FILE, "w", encoding="utf-8") as f:
            json.dump(all_candidates, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        logger.warning("generate_dataset_candidates: write failed: %s", exc)

    return new_candidates
