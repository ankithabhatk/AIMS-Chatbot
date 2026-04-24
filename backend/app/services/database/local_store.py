"""
Offline JSON-backed persistence for leads and chat logs.

This keeps the backend operational when Supabase/Postgres is unreachable.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "..",
    "data",
)
LEADS_FILE = os.path.abspath(os.path.join(DATA_DIR, "local_leads.json"))
CHAT_LOGS_FILE = os.path.abspath(os.path.join(DATA_DIR, "local_chat_logs.json"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _JsonCollectionStore:
    """Thread-safe JSON document store keyed by one top-level collection."""

    def __init__(self, path: str, collection: str) -> None:
        self.path = path
        self.collection = collection
        self._lock = threading.RLock()
        self._data: Dict[str, List[Dict[str, Any]]] = {collection: []}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._load()

    def all(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [dict(item) for item in self._data.get(self.collection, [])]

    def insert(self, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            items = self._data.setdefault(self.collection, [])
            items.append(dict(item))
            self._save()
            return dict(item)

    def update(self, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            items = self._data.setdefault(self.collection, [])
            for index, item in enumerate(items):
                if item.get("id") != item_id:
                    continue
                merged = dict(item)
                merged.update(updates)
                items[index] = merged
                self._save()
                return dict(merged)
        return None

    def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for item in self._data.get(self.collection, []):
                if item.get("id") == item_id:
                    return dict(item)
        return None

    def filter(self, **criteria: Any) -> List[Dict[str, Any]]:
        with self._lock:
            matches: List[Dict[str, Any]] = []
            for item in self._data.get(self.collection, []):
                if all(item.get(key) == value for key, value in criteria.items()):
                    matches.append(dict(item))
            return matches

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict) and isinstance(data.get(self.collection), list):
                self._data = data
        except Exception as exc:
            logger.error("Failed to load local store %s: %s", self.path, exc)

    def _save(self) -> None:
        temp_file = f"{self.path}.tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2)
            os.replace(temp_file, self.path)
        except PermissionError:
            logger.debug("Atomic save blocked for %s; falling back to direct write", self.path)
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2)
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    logger.debug("Local temp cleanup skipped for %s", temp_file, exc_info=True)


_lead_store = _JsonCollectionStore(LEADS_FILE, "leads")
_chat_log_store = _JsonCollectionStore(CHAT_LOGS_FILE, "chat_logs")


def create_local_lead(
    *,
    name: str,
    email: str,
    phone: Optional[str] = None,
    interest: Optional[str] = None,
    source: str = "chatbot_local",
) -> Dict[str, Any]:
    lead = {
        "id": str(uuid4()),
        "name": name,
        "email": email,
        "phone": phone,
        "interest": interest,
        "source": source,
        "lead_score": 0.5,
        "status": "new",
        "storage": "local",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    return _lead_store.insert(lead)


def get_local_lead(lead_id: str) -> Optional[Dict[str, Any]]:
    return _lead_store.get(lead_id)


def get_local_leads_by_email(email: str) -> List[Dict[str, Any]]:
    return _lead_store.filter(email=email)


def update_local_lead(lead_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    merged = dict(updates)
    merged["updated_at"] = _utc_now()
    return _lead_store.update(lead_id, merged)


def persist_chat_log_sync(
    *,
    query: str,
    response: str,
    session_id: str,
    confidence_score: float,
    processing_time_ms: int,
    is_fallback: bool = False,
    user_email: Optional[str] = None,
    intent: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    entry = {
        "id": str(uuid4()),
        "query": query,
        "response": response,
        "session_id": session_id,
        "user_email": user_email,
        "confidence_score": float(confidence_score),
        "processing_time_ms": int(processing_time_ms),
        "is_fallback": bool(is_fallback),
        "intent": intent,
        "status": status,
        "storage": "local",
        "created_at": _utc_now(),
    }
    return _chat_log_store.insert(entry)


def get_local_chat_logs(
    *,
    session_id: Optional[str] = None,
    user_email: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    logs = _chat_log_store.all()
    if session_id:
        logs = [log for log in logs if log.get("session_id") == session_id]
    if user_email:
        logs = [log for log in logs if log.get("user_email") == user_email]
    logs.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return logs[:limit]


def fetch_local_chat_history(session_id: str) -> List[Dict[str, Any]]:
    history = get_local_chat_logs(session_id=session_id, limit=500)
    history.reverse()
    return [
        {
            "user": row.get("query", ""),
            "bot": row.get("response", ""),
            "timestamp": row.get("created_at", ""),
            "intent": row.get("intent", ""),
            "confidence": row.get("confidence_score", 0),
        }
        for row in history
    ]
