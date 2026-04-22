"""
Admin API — Chat Intelligence Dashboard
=========================================
Provides session summaries and lead intelligence to authorized admins.

Routes:
  GET  /api/v1/admin/summaries          → all session profiles (sorted by priority)
  GET  /api/v1/admin/summaries/{sid}    → single session detail
  GET  /api/v1/admin/stats              → aggregate stats (total users, intents, etc.)

Security:
  Protected by X-Admin-Key header.
  Set ADMIN_SECRET_KEY env var (or defaults to "aims-admin-2024" for demo).
"""

import os
import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException

from app.services.chat_logger import get_all_sessions, get_chat, session_count, total_messages
from app.services.summary_engine import generate_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Intelligence"])

# ─────────────────────────────────────────────────────────────────────────────
# AUTH HELPER
# ─────────────────────────────────────────────────────────────────────────────

ADMIN_KEY = os.getenv("ADMIN_SECRET_KEY", "aims-admin-2024")


def _require_admin(x_admin_key: Optional[str]) -> None:
    """Raise 401 if wrong key, 403 if missing."""
    if x_admin_key is None:
        raise HTTPException(status_code=403, detail="Missing X-Admin-Key header")
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/summaries")
def get_all_summaries(x_admin_key: Optional[str] = Header(default=None)):
    """
    Returns all session intelligence profiles sorted by lead priority.
    Priority 1 = highest intent (contact now), Priority 4 = low intent.
    """
    _require_admin(x_admin_key)

    all_sessions = get_all_sessions()

    profiles = []
    for session_id, chat_history in all_sessions.items():
        summary = generate_summary(chat_history)
        profiles.append({
            "session_id":             session_id,
            "first_message_at":       chat_history[0]["timestamp"] if chat_history else None,
            "last_message_at":        chat_history[-1]["timestamp"] if chat_history else None,
            **summary,
        })

    # Sort by priority ascending (1 = most urgent first)
    profiles.sort(key=lambda p: (p["priority"], -p["lead_score"]))

    return {
        "total_sessions": len(profiles),
        "sessions": profiles,
    }


@router.get("/summaries/{session_id}")
def get_session_detail(
    session_id: str,
    x_admin_key: Optional[str] = Header(default=None),
):
    """
    Returns the full chat transcript + intelligence profile for one session.
    """
    _require_admin(x_admin_key)

    chat_history = get_chat(session_id)
    if not chat_history:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    summary = generate_summary(chat_history)

    return {
        "session_id":   session_id,
        "summary":      summary,
        "transcript":   chat_history,
    }


@router.get("/stats")
def get_admin_stats(x_admin_key: Optional[str] = Header(default=None)):
    """
    Aggregate stats: total sessions, messages, intent distribution, top courses.
    """
    _require_admin(x_admin_key)

    all_sessions = get_all_sessions()

    intent_counts: dict = {}
    course_counts: dict = {}
    conversion_counts: dict = {}

    for chat_history in all_sessions.values():
        profile = generate_summary(chat_history)

        # Count intents
        for intent in profile["all_intents"]:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        # Count courses
        for course in profile["courses"]:
            course_counts[course] = course_counts.get(course, 0) + 1

        # Count conversion bands
        band = profile["conversion_probability"]
        conversion_counts[band] = conversion_counts.get(band, 0) + 1

    return {
        "total_sessions":      session_count(),
        "total_messages":      total_messages(),
        "avg_messages_per_session": round(
            total_messages() / max(session_count(), 1), 1
        ),
        "intent_distribution":     dict(sorted(intent_counts.items(), key=lambda x: -x[1])),
        "course_interest":         dict(sorted(course_counts.items(), key=lambda x: -x[1])),
        "conversion_distribution": conversion_counts,
        "high_priority_leads":     sum(
            1 for ch in all_sessions.values()
            if generate_summary(ch)["priority"] <= 2
        ),
    }
