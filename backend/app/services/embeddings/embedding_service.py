"""
Offline embedding service using locally cached sentence-transformer models.
"""

from __future__ import annotations

import logging
import os
import threading
from collections import OrderedDict
from functools import lru_cache
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)

_model: Optional[SentenceTransformer] = None
_model_name: Optional[str] = None
_embedding_cache_lock = threading.RLock()
_embedding_cache: "OrderedDict[str, np.ndarray]" = OrderedDict()


def _cache_snapshot_path(model_name: str) -> Optional[str]:
    normalized = model_name.replace("\\", "/").strip("/")
    if os.path.isdir(normalized):
        return normalized

    if "/" not in normalized:
        normalized = f"sentence-transformers/{normalized}"

    org, model = normalized.split("/", 1)
    cache_root = os.path.join(
        os.path.expanduser("~"),
        ".cache",
        "huggingface",
        "hub",
        f"models--{org}--{model.replace('/', '--')}",
        "snapshots",
    )
    if not os.path.isdir(cache_root):
        return None

    snapshots = sorted(
        [
            os.path.join(cache_root, entry)
            for entry in os.listdir(cache_root)
            if os.path.isdir(os.path.join(cache_root, entry))
        ]
    )
    return snapshots[-1] if snapshots else None


def _resolve_model_name(requested_name: Optional[str] = None) -> tuple[str, str]:
    settings = get_settings()
    model_name = requested_name or getattr(settings, "embedding_model_name", "all-MiniLM-L6-v2")

    for candidate in (model_name, "sentence-transformers/all-MiniLM-L6-v2", "all-MiniLM-L6-v2"):
        local_path = _cache_snapshot_path(candidate)
        if local_path:
            return candidate, local_path

    raise RuntimeError(
        "No local embedding model cache found. Expected a cached sentence-transformers model."
    )


def load_embedding_model(model_name: Optional[str] = None) -> SentenceTransformer:
    """Load the cached embedding model exactly once."""
    global _model, _model_name
    resolved_name, local_path = _resolve_model_name(model_name)

    if _model is None or _model_name != resolved_name:
        logger.info("Loading offline embedding model from %s", local_path)
        _model = SentenceTransformer(local_path, local_files_only=True)
        _model_name = resolved_name
        logger.info(
            "Embedding model ready. Dimension: %s",
            _model.get_sentence_embedding_dimension(),
        )

    return _model


def _normalize_cache_key(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _embedding_cache_limit() -> int:
    settings = get_settings()
    return max(int(getattr(settings, "embedding_cache_max_entries", 512)), 64)


def _get_cached_embedding(text: str) -> Optional[np.ndarray]:
    key = _normalize_cache_key(text)
    if not key:
        return None

    with _embedding_cache_lock:
        embedding = _embedding_cache.get(key)
        if embedding is None:
            return None
        _embedding_cache.move_to_end(key)
        return embedding.copy()


def _set_cached_embedding(text: str, embedding: np.ndarray) -> None:
    key = _normalize_cache_key(text)
    if not key:
        return

    with _embedding_cache_lock:
        _embedding_cache[key] = embedding.copy()
        _embedding_cache.move_to_end(key)
        while len(_embedding_cache) > _embedding_cache_limit():
            _embedding_cache.popitem(last=False)


def get_embedding_cache_stats() -> dict:
    with _embedding_cache_lock:
        return {
            "entries": len(_embedding_cache),
            "max_entries": _embedding_cache_limit(),
        }


def embed_text(text: str) -> np.ndarray:
    """Embed a single text string using normalized vectors."""
    cached = _get_cached_embedding(text)
    if cached is not None:
        return cached.astype(np.float32)

    model = load_embedding_model()
    embedding = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    embedding = embedding.astype(np.float32)
    _set_cached_embedding(text, embedding)
    return embedding.copy()


def embed_batch(texts: List[str]) -> np.ndarray:
    """Embed multiple texts efficiently using normalized vectors."""
    if not texts:
        return np.array([], dtype=np.float32)

    cached_embeddings: List[Optional[np.ndarray]] = []
    missing_texts: List[str] = []
    missing_positions: List[int] = []

    for index, text in enumerate(texts):
        cached = _get_cached_embedding(text)
        cached_embeddings.append(cached)
        if cached is None:
            missing_texts.append(text)
            missing_positions.append(index)

    if not missing_texts:
        return np.stack([embedding.astype(np.float32) for embedding in cached_embeddings], axis=0)

    model = load_embedding_model()
    embeddings = model.encode(
        missing_texts,
        convert_to_numpy=True,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    embeddings = embeddings.astype(np.float32)

    for offset, position in enumerate(missing_positions):
        embedding = embeddings[offset]
        cached_embeddings[position] = embedding
        _set_cached_embedding(texts[position], embedding)

    return np.stack([embedding.astype(np.float32) for embedding in cached_embeddings], axis=0)


@lru_cache(maxsize=1)
def get_embedding_dimension() -> int:
    """Get the active embedding vector dimension."""
    model = load_embedding_model()
    return model.get_sentence_embedding_dimension()
