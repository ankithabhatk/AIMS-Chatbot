"""
Chat Logger — In-Memory Store (Demo-Safe)
==========================================
Stores every chat turn per session.
- Does NOT affect chatbot response speed (append-only, no DB call)
- In-memory: resets on restart (fine for demo)
- Thread-safe enough for single-process FastAPI (asyncio)
"""

from datetime import datetime, timezone
from typing import List, Dict


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL IN-MEMORY STORE
# ─────────────────────────────────────────────────────────────────────────────

_CHAT_STORE: Dict[str, List[Dict]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────────────

def log_chat(
    session_id: str,
    user_message: str,
    bot_response: str,
    *,
    confidence: float = 0.0,
    intent: str = "QUESTION",
    status: str = "unlock",
) -> None:
    """Append a single turn to the session log."""
    if session_id not in _CHAT_STORE:
        _CHAT_STORE[session_id] = []

    _CHAT_STORE[session_id].append({
        "user":       user_message,
        "bot":        bot_response,
        "confidence": round(confidence, 3),
        "intent":     intent,
        "status":     status,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────

def get_chat(session_id: str) -> List[Dict]:
    """Return full chat history for a session."""
    return _CHAT_STORE.get(session_id, [])


def get_all_sessions() -> Dict[str, List[Dict]]:
    """Return all sessions. Used by admin endpoint."""
    return _CHAT_STORE


def session_count() -> int:
    return len(_CHAT_STORE)


def total_messages() -> int:
    return sum(len(v) for v in _CHAT_STORE.values())
