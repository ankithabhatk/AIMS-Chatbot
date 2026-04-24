"""
Local persistent conversation store.

This is the offline-first source of truth for user chat history.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
)
STORE_FILE = os.path.join(DATA_DIR, "chat_sessions.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _estimate_tokens(text: str) -> int:
    return max(len((text or "").split()), len((text or "")) // 4)


class ConversationStore:
    """Thread-safe JSON-backed conversation persistence."""

    def __init__(self, store_file: str = STORE_FILE) -> None:
        self.store_file = store_file
        self._lock = threading.RLock()
        self._data: Dict[str, Dict[str, Any]] = {"sessions": {}}
        os.makedirs(os.path.dirname(store_file), exist_ok=True)
        self._load()

    def append_turn(
        self,
        *,
        session_id: str,
        user_query: str,
        assistant_answer: str,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        confidence: float = 0.0,
        status: str = "unlock",
        intent: str = "factual",
        fallback: bool = False,
        response_time_ms: int = 0,
        original_query: Optional[str] = None,
        corrected_query: Optional[str] = None,
        control_tokens: Optional[List[str]] = None,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
        suggestions: Optional[List[str]] = None,
        active_course: Optional[str] = None,
        active_topic: Optional[str] = None,
        last_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            sessions = self._data.setdefault("sessions", {})
            now = _utc_now()
            session = sessions.get(session_id)
            if not session:
                session = {
                    "id": session_id,
                    "title": self._title_from_query(user_query),
                    "user_email": user_email,
                    "user_name": user_name,
                    "created_at": now,
                    "updated_at": now,
                    "messages": [],
                    "message_count": 0,
                    "active_course": active_course,
                    "active_topic": active_topic,
                    "last_intent": last_intent or intent,
                }
                sessions[session_id] = session

            if user_email:
                session["user_email"] = user_email
            if user_name:
                session["user_name"] = user_name
            if active_course:
                session["active_course"] = active_course
            if active_topic:
                session["active_topic"] = active_topic
            session["last_intent"] = last_intent or intent
            session["updated_at"] = now

            user_message = {
                "id": f"{session_id}-u-{session['message_count'] + 1}",
                "role": "user",
                "content": user_query,
                "timestamp": now,
                "token_count": _estimate_tokens(user_query),
                "original_query": original_query or user_query,
                "corrected_query": corrected_query or user_query,
            }
            assistant_message = {
                "id": f"{session_id}-a-{session['message_count'] + 2}",
                "role": "assistant",
                "content": assistant_answer,
                "timestamp": now,
                "token_count": _estimate_tokens(assistant_answer),
                "confidence": round(confidence, 3),
                "status": status,
                "intent": intent,
                "fallback": fallback,
                "response_time_ms": response_time_ms,
                "sources": sources or [],
                "suggestions": suggestions or [],
                "control_tokens": control_tokens or [],
                "retrieved_chunks": retrieved_chunks or [],
            }
            session["messages"].extend([user_message, assistant_message])
            session["message_count"] = len(session["messages"])

            self._save()
            return copy.deepcopy(session)

    def list_sessions(self, user_email: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            sessions = list(self._data.get("sessions", {}).values())
            if user_email:
                needle = user_email.strip().lower()
                sessions = [
                    session
                    for session in sessions
                    if (session.get("user_email") or "").strip().lower() == needle
                ]

            sessions.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
            selected = sessions[:limit]
            return [self._session_summary(session) for session in selected]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            session = self._data.get("sessions", {}).get(session_id)
            return copy.deepcopy(session) if session else None

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            sessions = list(self._data.get("sessions", {}).values())
            total_messages = sum(len(session.get("messages", [])) for session in sessions)
            return {
                "stored_sessions": len(sessions),
                "stored_messages": total_messages,
                "store_file": self.store_file,
            }

    def _session_summary(self, session: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": session["id"],
            "title": session.get("title", "Conversation"),
            "user_email": session.get("user_email"),
            "user_name": session.get("user_name"),
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at"),
            "message_count": session.get("message_count", len(session.get("messages", []))),
            "active_course": session.get("active_course"),
            "active_topic": session.get("active_topic"),
            "last_intent": session.get("last_intent"),
            "messages": copy.deepcopy(session.get("messages", [])),
        }

    def _title_from_query(self, query: str) -> str:
        trimmed = (query or "").strip()
        if not trimmed:
            return "New Conversation"
        return trimmed[:42] + ("..." if len(trimmed) > 42 else "")

    def _load(self) -> None:
        if not os.path.exists(self.store_file):
            return
        try:
            with open(self.store_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict) and "sessions" in data:
                self._data = data
        except Exception as exc:
            logger.error("Failed to load conversation store: %s", exc)

    def _save(self) -> None:
        temp_file = f"{self.store_file}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2)
            os.replace(temp_file, self.store_file)
        except PermissionError:
            logger.debug("Atomic conversation store replace was blocked; using direct write fallback")
            with open(self.store_file, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2)
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    logger.debug("Temporary conversation store cleanup skipped", exc_info=True)


_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """Return the shared persistent conversation store."""
    global _store
    if _store is None:
        _store = ConversationStore()
    return _store
