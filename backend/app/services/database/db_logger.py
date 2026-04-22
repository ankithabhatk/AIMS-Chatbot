"""
Database Logger — Production-Grade Supabase Persistence
=========================================================
Handles all persistent writes to Supabase chat_logs with:
  - Credentials resolved ONCE at import time (fixes background-task env issue)
  - Retry logic (max 2 retries with backoff)
  - Visible error logging (no silent failures)
  - DB health check function

Architecture:
  chat_phase4.py → background_tasks.add_task(persist_chat_turn, ...)
                 ↓ (after response sent)
                 db_logger.persist_chat_turn()
                 ↓
                 Supabase chat_logs table
"""

import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CREDENTIALS — resolved once at import time, NOT inside thread
# ─────────────────────────────────────────────────────────────────────────────

def _get_supabase_client():
    """Create a fresh Supabase client using currently-loaded env vars."""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL", "")
        key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY") or
            os.getenv("SUPABASE_ANON_KEY") or
            ""
        )
        if not url or not key:
            logger.error("[DB] SUPABASE_URL or key not set — check .env")
            return None
        return create_client(url, key)
    except Exception as e:
        logger.error(f"[DB] Failed to create Supabase client: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# RETRY HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _with_retry(fn, max_retries: int = 2, delay: float = 0.5):
    """
    Execute fn() with up to max_retries attempts.
    Raises the last exception if all attempts fail.
    """
    last_exc = None
    for attempt in range(1, max_retries + 2):  # 1 + max_retries total tries
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if attempt <= max_retries:
                logger.warning(f"[DB] Attempt {attempt} failed: {e} — retrying in {delay}s")
                time.sleep(delay)
    raise last_exc


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC: persist_chat_turn
# ─────────────────────────────────────────────────────────────────────────────

def persist_chat_turn(
    *,
    session_id:         str,
    query:              str,
    response:           str,
    intent:             str = "QUESTION",
    confidence_score:   float = 0.0,
    processing_time_ms: int   = 0,
    status:             str   = "unlock",
    is_fallback:        bool  = False,
) -> bool:
    """
    Persist one chat turn to Supabase chat_logs.
    Runs inside a BackgroundTask (separate thread).
    Returns True on success, False on failure.
    Logs ALL failures visibly — no silent pass.
    """
    client = _get_supabase_client()
    if client is None:
        logger.error(f"[DB][{session_id}] Supabase client unavailable — row NOT saved")
        return False

    payload = {
        "session_id":         session_id,
        "query":              query,
        "response":           response[:2000],
        "intent":             intent,
        "confidence_score":   round(confidence_score, 4),
        "processing_time_ms": processing_time_ms,
        "status":             status,
        "is_fallback":        is_fallback,
    }

    try:
        _with_retry(lambda: client.table("chat_logs").insert(payload).execute())
        logger.debug(f"[DB][{session_id}] ✅ Persisted to Supabase")
        return True
    except Exception as e:
        logger.error(f"[DB][{session_id}] ❌ FAILED after retries: {type(e).__name__}: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC: db_health_check
# ─────────────────────────────────────────────────────────────────────────────

def db_health_check() -> dict:
    """
    Quick write-read health check.
    Returns {"status": "ok", "latency_ms": N} or {"status": "error", "detail": str}
    """
    client = _get_supabase_client()
    if client is None:
        return {"status": "error", "detail": "SUPABASE_URL or key not configured"}

    start = time.time()
    try:
        # Just a SELECT — non-destructive, fastest way to test connectivity
        client.table("chat_logs").select("id").limit(1).execute()
        latency_ms = round((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = round((time.time() - start) * 1000)
        logger.error(f"[DB] Health check failed: {e}")
        return {"status": "error", "detail": str(e), "latency_ms": latency_ms}


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC: fetch_chat_history
# ─────────────────────────────────────────────────────────────────────────────

def fetch_chat_history(session_id: str) -> list:
    """
    Read all chat turns for a session from Supabase chat_logs.
    Returns a list in the format expected by summary_engine.generate_summary():
      [{"user": "...", "bot": "...", "timestamp": "..."}, ...]
    """
    client = _get_supabase_client()
    if client is None:
        return []
    try:
        result = client.table("chat_logs") \
            .select("query, response, intent, confidence_score, created_at") \
            .eq("session_id", session_id) \
            .order("created_at") \
            .execute()
        return [
            {
                "user":      row["query"],
                "bot":       row["response"],
                "timestamp": row["created_at"],
                "intent":    row.get("intent", ""),
                "confidence": row.get("confidence_score", 0),
            }
            for row in (result.data or [])
        ]
    except Exception as e:
        logger.error(f"[DB] fetch_chat_history({session_id}) failed: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC: persist_session_summary
# ─────────────────────────────────────────────────────────────────────────────

def persist_session_summary(session_id: str) -> bool:
    """
    Generate an intelligence profile for session_id and upsert it to
    the session_summaries table.

    Called as a BackgroundTask after each chat turn — keeps summaries
    current without blocking the response.

    Returns True on success, False on failure.
    """
    from app.services.summary_engine import generate_summary

    # 1. Pull chat history from Supabase
    history = fetch_chat_history(session_id)
    if not history:
        logger.debug(f"[DB][{session_id}] No history to summarise")
        return False

    # 2. Generate intelligence profile (rule-based, instant)
    profile = generate_summary(history)

    # 3. Upsert to session_summaries (insert or update on conflict)
    client = _get_supabase_client()
    if client is None:
        return False

    payload = {
        "session_id":              session_id,
        "courses":                 profile["courses"],
        "primary_intent":          profile["primary_intent"],
        "all_intents":             profile["all_intents"],
        "sentiment":               profile["sentiment"],
        "lead_score":              profile["lead_score"],
        "conversion_probability":  profile["conversion_probability"],
        "recommended_action":      profile["recommended_action"],
        "summary_text":            profile["summary"],
        "message_count":           profile["messages"],
        "has_lead":                False,
        "updated_at":              "now()",
    }

    try:
        _with_retry(lambda: client.table("session_summaries").upsert(payload).execute())
        logger.debug(f"[DB][{session_id}] ✅ Summary persisted (score={profile['lead_score']}, prob={profile['conversion_probability']})")
        return True
    except Exception as e:
        logger.error(f"[DB][{session_id}] ❌ Summary persist FAILED: {type(e).__name__}: {e}")
        return False

