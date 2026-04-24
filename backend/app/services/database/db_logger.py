"""
Offline-safe database logger.

Prefers Supabase when reachable and transparently falls back to local JSON
storage so chat logging never breaks the assistant.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Callable

from app.services.database.local_store import fetch_local_chat_history, persist_chat_log_sync

logger = logging.getLogger(__name__)


def _get_supabase_client():
    """Create a fresh Supabase client using the loaded env vars."""
    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""
        if not url or not key:
            logger.warning("[DB] Supabase env missing; local persistence will be used")
            return None
        return create_client(url, key)
    except Exception as exc:
        logger.error("[DB] Failed to create Supabase client: %s", exc)
        return None


def _with_retry(fn: Callable[[], object], max_retries: int = 2, delay: float = 0.5):
    """Execute fn with a few retries before surfacing the last error."""
    last_exc = None
    for attempt in range(1, max_retries + 2):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt <= max_retries:
                logger.warning("[DB] Attempt %s failed: %s; retrying in %ss", attempt, exc, delay)
                time.sleep(delay)
    raise last_exc


def persist_chat_turn(
    *,
    session_id: str,
    query: str,
    response: str,
    intent: str = "QUESTION",
    confidence_score: float = 0.0,
    processing_time_ms: int = 0,
    status: str = "unlock",
    is_fallback: bool = False,
) -> bool:
    """Persist one chat turn to Supabase or local JSON."""
    payload = {
        "session_id": session_id,
        "query": query,
        "response": response[:2000],
        "intent": intent,
        "confidence_score": round(confidence_score, 4),
        "processing_time_ms": processing_time_ms,
        "status": status,
        "is_fallback": is_fallback,
    }

    client = _get_supabase_client()
    if client is None:
        persist_chat_log_sync(**payload)
        logger.warning("[DB][%s] Logged locally because Supabase is unavailable", session_id)
        return True

    try:
        _with_retry(lambda: client.table("chat_logs").insert(payload).execute())
        logger.debug("[DB][%s] Persisted to Supabase", session_id)
        return True
    except Exception as exc:
        persist_chat_log_sync(**payload)
        logger.warning("[DB][%s] Supabase write failed, logged locally: %s", session_id, exc)
        return True


def db_health_check() -> dict:
    """Quick connectivity check for the active persistence mode."""
    client = _get_supabase_client()
    if client is None:
        return {"status": "degraded", "detail": "Supabase unavailable; local persistence active"}

    start = time.time()
    try:
        client.table("chat_logs").select("id").limit(1).execute()
        latency_ms = round((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        latency_ms = round((time.time() - start) * 1000)
        logger.error("[DB] Health check failed: %s", exc)
        return {
            "status": "degraded",
            "detail": f"{exc}; local persistence active",
            "latency_ms": latency_ms,
        }


def fetch_chat_history(session_id: str) -> list:
    """Read session chat history from Supabase or local JSON."""
    client = _get_supabase_client()
    if client is None:
        return fetch_local_chat_history(session_id)

    try:
        result = (
            client.table("chat_logs")
            .select("query, response, intent, confidence_score, created_at")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        return [
            {
                "user": row["query"],
                "bot": row["response"],
                "timestamp": row["created_at"],
                "intent": row.get("intent", ""),
                "confidence": row.get("confidence_score", 0),
            }
            for row in (result.data or [])
        ]
    except Exception as exc:
        logger.error("[DB] fetch_chat_history(%s) failed: %s", session_id, exc)
        return fetch_local_chat_history(session_id)


def persist_session_summary(session_id: str) -> bool:
    """
    Generate an intelligence profile for a session and upsert it when Supabase
    is available. In offline mode this becomes a no-op success.
    """
    from app.services.summary_engine import generate_summary

    history = fetch_chat_history(session_id)
    if not history:
        logger.debug("[DB][%s] No history to summarise", session_id)
        return False

    profile = generate_summary(history)
    client = _get_supabase_client()
    if client is None:
        logger.debug("[DB][%s] Summary generated locally; remote upsert skipped", session_id)
        return True

    payload = {
        "session_id": session_id,
        "courses": profile["courses"],
        "primary_intent": profile["primary_intent"],
        "all_intents": profile["all_intents"],
        "sentiment": profile["sentiment"],
        "lead_score": profile["lead_score"],
        "conversion_probability": profile["conversion_probability"],
        "recommended_action": profile["recommended_action"],
        "summary_text": profile["summary"],
        "message_count": profile["messages"],
        "has_lead": False,
        "updated_at": "now()",
        "conversion_timeline": profile.get("conversion_timeline", ""),
        "next_expected_queries": profile.get("next_expected_queries", []),
    }

    try:
        _with_retry(lambda: client.table("session_summaries").upsert(payload).execute())
        logger.debug("[DB][%s] Summary persisted to Supabase", session_id)
        return True
    except Exception as exc:
        logger.warning("[DB][%s] Summary upsert skipped after Supabase failure: %s", session_id, exc)
        return True
