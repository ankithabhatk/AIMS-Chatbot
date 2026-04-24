"""
Low-latency response caching for frequent chat queries.

Primary goals:
- exact-match cache for repeated resolved queries
- safe TTL expiry
- bounded in-memory size
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class QueryResponseCache:
    """Thread-safe TTL + LRU cache for chat responses."""

    def __init__(self, max_entries: int = 256, ttl_seconds: int = 900) -> None:
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._lock = threading.RLock()
        self._store: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._hits = 0
        self._misses = 0

    def make_key(self, query_data: Dict[str, Any]) -> str:
        payload = {
            "query": query_data.get("query"),
            "course": query_data.get("course"),
            "topic": query_data.get("topic"),
            "intent": query_data.get("intent"),
            "detail": query_data.get("detail_level"),
            "clarify": query_data.get("needs_clarification"),
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.md5(encoded.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                self._misses += 1
                return None

            if entry["expires_at"] <= time.time():
                self._store.pop(key, None)
                self._misses += 1
                return None

            self._store.move_to_end(key)
            self._hits += 1
            return copy.deepcopy(entry["value"])

    def set(self, key: str, value: Dict[str, Any]) -> None:
        with self._lock:
            self._store[key] = {
                "value": copy.deepcopy(value),
                "expires_at": time.time() + self.ttl_seconds,
            }
            self._store.move_to_end(key)
            while len(self._store) > self.max_entries:
                self._store.popitem(last=False)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            live_entries = 0
            now = time.time()
            for entry in self._store.values():
                if entry["expires_at"] > now:
                    live_entries += 1
            total = self._hits + self._misses
            hit_rate = self._hits / total if total else 0.0
            return {
                "entries": live_entries,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 3),
                "ttl_seconds": self.ttl_seconds,
            }


_cache: Optional[QueryResponseCache] = None


def get_query_response_cache() -> QueryResponseCache:
    """Return the shared query response cache."""
    global _cache
    if _cache is None:
        settings = get_settings()
        _cache = QueryResponseCache(
            max_entries=getattr(settings, "query_cache_max_entries", 256),
            ttl_seconds=getattr(settings, "query_cache_ttl_seconds", 900),
        )
    return _cache
