"""
Admin API — Chat Intelligence Dashboard
=========================================
Provides session summaries and lead intelligence to authorized admins.

Routes:
  GET   /api/v1/admin/summaries              → all session profiles (sorted by priority)
  GET   /api/v1/admin/summaries/{sid}        → single session detail
  GET   /api/v1/admin/stats                  → aggregate stats (total users, intents, etc.)
  GET   /api/v1/admin/db-health              → live Supabase connectivity check (no key needed)
  PATCH /api/v1/admin/sessions/{id}/feedback → mark prediction correct/incorrect
  GET   /api/v1/admin/accuracy-stats         → model accuracy report from human reviews
  GET   /api/v1/admin/export-reviewed-data   → training dataset export (JSON or CSV)

Security:
  Protected by X-Admin-Key header (except db-health).
  Set ADMIN_SECRET_KEY env var (or defaults to "aims-admin-2024" for demo).
"""

import os
import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException

from app.services.chat_logger import get_all_sessions, get_chat, session_count, total_messages
from app.services.summary_engine import generate_summary
from app.services.database.db_logger import db_health_check

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


@router.get("/db-health")
def database_health():
    """
    Live Supabase connectivity and write-latency check.
    No API key required — safe for uptime monitors.
    Returns {"status": "ok", "latency_ms": N} or {"status": "error", "detail": str}
    """
    return db_health_check()


@router.patch("/sessions/{session_id}/feedback")
def submit_prediction_feedback(
    session_id: str,
    body: dict,
    x_admin_key: Optional[str] = Header(default=None),
):
    """
    Mark a session's intelligence prediction correct or incorrect.
    This is the feedback loop that creates training data for future model improvement.

    Body:
        { "is_correct": true/false, "notes": "optional reason", "reviewer": "name" }

    Example:
        curl -X PATCH http://localhost:8000/api/v1/admin/sessions/abc123/feedback \\
             -H "X-Admin-Key: aims-admin-2024" \\
             -H "Content-Type: application/json" \\
             -d '{"is_correct": false, "notes": "score too high for 2-msg session"}'
    """
    _require_admin(x_admin_key)

    is_correct = body.get("is_correct")
    if is_correct is None or not isinstance(is_correct, bool):
        raise HTTPException(status_code=422, detail="'is_correct' (boolean) is required")

    notes    = str(body.get("notes", ""))[:500]
    reviewer = str(body.get("reviewer", "admin"))[:100]

    from app.services.database.db_logger import _get_supabase_client
    from datetime import datetime, timezone
    client = _get_supabase_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        result = client.table("session_summaries").update({
            "is_prediction_correct": is_correct,
            "reviewed_at":           datetime.now(timezone.utc).isoformat(),
            "reviewed_by":           reviewer,
            "review_notes":          notes or None,
        }).eq("session_id", session_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

        logger.info(f"[Admin] Feedback saved: {session_id} → {'✅' if is_correct else '❌'} by {reviewer}")
        return {
            "session_id":          session_id,
            "is_prediction_correct": is_correct,
            "reviewer":            reviewer,
            "saved":               True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Feedback save failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accuracy-stats")
def get_accuracy_stats(x_admin_key: Optional[str] = Header(default=None)):
    """
    Overall model accuracy report based on human feedback.
    Shows how many predictions have been reviewed and what % were correct.
    This is your ground truth for knowing when to retrain the scoring model.
    """
    _require_admin(x_admin_key)

    from app.services.database.db_logger import _get_supabase_client
    client = _get_supabase_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        result = client.table("session_summaries").select(
            "is_prediction_correct, conversion_probability"
        ).execute()

        rows     = result.data or []
        total    = len(rows)
        reviewed = [r for r in rows if r["is_prediction_correct"] is not None]
        correct  = [r for r in reviewed if r["is_prediction_correct"] is True]
        wrong    = [r for r in reviewed if r["is_prediction_correct"] is False]

        # Breakdown of wrong predictions by band
        wrong_by_band: dict = {}
        for r in wrong:
            band = r["conversion_probability"] or "Unknown"
            wrong_by_band[band] = wrong_by_band.get(band, 0) + 1

        accuracy_pct = round(len(correct) / len(reviewed) * 100, 1) if reviewed else None

        return {
            "total_sessions":    total,
            "reviewed":          len(reviewed),
            "correct":           len(correct),
            "incorrect":         len(wrong),
            "accuracy_pct":      accuracy_pct,
            "unreviewed":        total - len(reviewed),
            "wrong_by_band":     wrong_by_band,
            "status":            "needs_more_data" if len(reviewed) < 10 else
                                 ("good" if accuracy_pct and accuracy_pct >= 85 else "needs_tuning"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-reviewed-data")
def export_reviewed_data(
    format: str = "json",
    reviewed_only: bool = True,
    x_admin_key: Optional[str] = Header(default=None),
):
    """
    Export session intelligence profiles + human feedback as a training dataset.
    Each reviewed row = one labeled example for future ML model training.

    Query params:
      format        : "json" (default) or "csv"
      reviewed_only : true (default) — only export rows with human labels

    Examples:
      curl "http://localhost:8000/api/v1/admin/export-reviewed-data" \\
           -H "X-Admin-Key: aims-admin-2024"

      curl "http://localhost:8000/api/v1/admin/export-reviewed-data?format=csv" \\
           -H "X-Admin-Key: aims-admin-2024" -o training_data.csv
    """
    _require_admin(x_admin_key)

    import io
    import csv
    import datetime
    from fastapi.responses import StreamingResponse

    from app.services.database.db_logger import _get_supabase_client
    client = _get_supabase_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        query = client.table("session_summaries").select(
            "session_id, courses, primary_intent, all_intents, sentiment, "
            "lead_score, conversion_probability, conversion_timeline, "
            "message_count, is_prediction_correct, review_notes, "
            "reviewed_by, reviewed_at, updated_at"
        )
        if reviewed_only:
            query = query.not_.is_("is_prediction_correct", "null")

        result = query.order("updated_at", desc=True).execute()
        rows   = result.data or []

        if not rows:
            return {
                "message": "No reviewed data yet. Run: python scripts/review_predictions.py",
                "rows": 0,
            }

        if format.lower() == "csv":
            fields = [
                "session_id", "primary_intent", "all_intents", "courses",
                "sentiment", "lead_score", "conversion_probability",
                "conversion_timeline", "message_count",
                "is_prediction_correct", "review_notes",
                "reviewed_by", "reviewed_at", "updated_at",
            ]
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                row["all_intents"] = " | ".join(row.get("all_intents") or [])
                row["courses"]     = " | ".join(row.get("courses")     or [])
                writer.writerow({f: row.get(f, "") for f in fields})

            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=aims_training_data.csv"},
            )

        # JSON (default)
        return {
            "exported_at":   datetime.datetime.utcnow().isoformat() + "Z",
            "total_rows":    len(rows),
            "reviewed_only": reviewed_only,
            "schema": {
                "is_prediction_correct": "boolean — human label (true=correct, false=wrong)",
                "lead_score":            "float 0–10 — model predicted score",
                "conversion_probability":"string — Very High / High / Moderate / Low",
                "review_notes":          "string — reason it was wrong (key training signal)",
            },
            "data": rows,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
