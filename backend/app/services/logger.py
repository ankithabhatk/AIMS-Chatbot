# app/services/logger.py
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

ENABLE_LOGGING: bool = os.getenv("ENABLE_STRUCTURED_LOGGING", "true").lower() != "false"
_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs.jsonl")
_LOG_FILE = os.path.abspath(_LOG_FILE)

_lock = threading.Lock()
_in_memory: List[Dict[str, Any]] = []   # ring-buffer cap
_MAX_IN_MEMORY = 500
_CHUNK_TRIM = 200
_LOG_CHUNKS = 3


# ── Core helpers ──────────────────────────────────────────────────────────────

def _trim_chunk(chunk: Any) -> str:
    if isinstance(chunk, dict):
        text = chunk.get("content", chunk.get("text", ""))
    elif isinstance(chunk, (list, tuple)) and len(chunk) > 0:
        text = str(chunk[0])
    else:
        text = str(chunk)
    text = text.strip()
    return text[:_CHUNK_TRIM] + ("…" if len(text) > _CHUNK_TRIM else "")


def _extract_scores(chunks: List[Any], limit: int = 3) -> List[float]:
    """Pull numeric scores from top `limit` chunks (dict or tuple format)."""
    out: List[float] = []
    for c in chunks[:limit]:
        raw = None
        if isinstance(c, dict):
            raw = c.get("score") or c.get("similarity")
        elif isinstance(c, (list, tuple)) and len(c) > 1:
            raw = c[1]
        if raw is not None:
            try:
                out.append(float(raw))
            except (TypeError, ValueError):
                pass
    return out


def compute_confidence(chunks: List[Any]) -> float:
    """Confidence from avg reranker scores (clamped 0–1); fallback = min(len/5, 1)."""
    if not chunks:
        return 0.0
    scores = _extract_scores(chunks, limit=len(chunks))
    if scores:
        avg = sum(scores) / len(scores)
        return round(min(max(avg, 0.0), 1.0), 4)
    return round(min(len(chunks) / 5.0, 1.0), 4)


def _write_jsonl(record: dict) -> None:
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # never let logging crash the app


# ── Public API ────────────────────────────────────────────────────────────────

def log_event(
    *,
    session_id: str = "",
    query: str = "",
    rewritten_query: str = "",
    intent: str = "",
    chunks: Optional[List[Any]] = None,
    confidence: Optional[float] = None,
    response: str = "",
    response_time_ms: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    if not ENABLE_LOGGING:
        return

    chunk_list = chunks or []
    top_chunks = [_trim_chunk(c) for c in chunk_list[:_LOG_CHUNKS]]
    scores = _extract_scores(chunk_list, limit=_LOG_CHUNKS)
    conf = confidence if confidence is not None else compute_confidence(chunk_list)

    record: Dict[str, Any] = {
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "session_id":       session_id,
        "query":            query,
        "rewritten_query":  rewritten_query,
        "intent":           intent,
        "retrieved_chunks": top_chunks,
        "scores":           scores,
        "confidence":       conf,
        "response":         response[:400] + ("…" if len(response) > 400 else ""),
        "response_time_ms": response_time_ms,
    }
    if error is not None:
        record["error"] = error

    with _lock:
        _in_memory.append(record)
        if len(_in_memory) > _MAX_IN_MEMORY:
            _in_memory.pop(0)

    _write_jsonl(record)


# ── Analytics helpers ─────────────────────────────────────────────────────────

def get_recent_logs(n: int = 20) -> List[Dict[str, Any]]:
    with _lock:
        return list(_in_memory[-n:])


def get_avg_confidence() -> float:
    with _lock:
        scores = [r["confidence"] for r in _in_memory if r.get("confidence") is not None]
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def get_low_confidence_queries(threshold: float = 0.4) -> List[Dict[str, Any]]:
    with _lock:
        return [r for r in _in_memory if r.get("confidence", 1.0) < threshold]
