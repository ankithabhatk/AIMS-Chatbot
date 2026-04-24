"""
FAISS vector store used by the production chat endpoint.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np

from app.services.taxonomy import canonicalize_course, canonicalize_topic

logger = logging.getLogger(__name__)

INDEX_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "faiss_index",
)
INDEX_FILE = os.path.join(INDEX_DIR, "index.faiss")
METADATA_FILE = os.path.join(INDEX_DIR, "metadata.json")


class FAISSIndex:
    """FAISS index with metadata-aware retrieval helpers."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata: List[Dict[str, Any]] = []
        self.doc_count = 0
        os.makedirs(INDEX_DIR, exist_ok=True)
        self.index_dir = INDEX_DIR
        self.index_file = INDEX_FILE
        self.metadata_file = METADATA_FILE
        self.load()

    def add_documents(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        urls: List[str] | None = None,
        headings: List[str] | None = None,
    ) -> None:
        if len(texts) != len(embeddings):
            raise ValueError("texts and embeddings must have the same length")

        urls = urls or ["unknown"] * len(texts)
        headings = headings or ["untitled"] * len(texts)

        embeddings_float32 = np.asarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_float32)
        self.index.add(embeddings_float32)

        for offset, (text, url, heading) in enumerate(zip(texts, urls, headings)):
            self.metadata.append(
                {
                    "id": self.doc_count + offset,
                    "text": text[:500],
                    "full_text": text,
                    "url": url,
                    "heading": heading,
                    "source": "web",
                    "priority": 1.0,
                    "importance": 1.0,
                }
            )

        self.doc_count += len(texts)
        logger.info("Added %s documents to FAISS index", len(texts))

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple]:
        if self.doc_count == 0 and self.index.ntotal == 0:
            logger.warning("Search requested on an empty FAISS index")
            return []

        query_embedding = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        metric_type = getattr(self.index, "metric_type", faiss.METRIC_INNER_PRODUCT)
        if metric_type == faiss.METRIC_INNER_PRODUCT:
            faiss.normalize_L2(query_embedding)

        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        results: List[Tuple] = []

        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]
            full_text = meta.get("full_text") or meta.get("text", "")
            heading = meta.get("heading", "")
            url = meta.get("url", "")

            if metric_type == faiss.METRIC_INNER_PRODUCT:
                similarity = max(0.0, min((float(dist) + 1.0) / 2.0, 1.0))
            else:
                similarity = 1.0 / (1.0 + max(float(dist), 0.0))

            course = (
                canonicalize_course(str(meta.get("course", "")))
                or canonicalize_course(heading)
                or canonicalize_course(full_text[:160])
            )
            topic = (
                canonicalize_topic(str(meta.get("category", "")))
                or canonicalize_topic(heading)
                or canonicalize_topic(full_text[:160])
            )

            results.append(
                (
                    full_text,
                    round(similarity, 4),
                    url,
                    heading,
                    meta.get("doc_id") or meta.get("id") or meta.get("index_position") or idx,
                    meta.get("source", "web"),
                    float(meta.get("priority", 1.0)),
                    course,
                    topic,
                    float(meta.get("importance", meta.get("priority", 1.0))),
                )
            )

        return results

    def save(self) -> None:
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.metadata_file, "w", encoding="utf-8") as handle:
                json.dump(self.metadata, handle, indent=2)
            logger.info("Saved FAISS index with %s documents", self.doc_count)
        except Exception as exc:
            logger.error("Failed to save FAISS index: %s", exc)

    def load(self) -> None:
        try:
            if not os.path.exists(self.index_file):
                logger.info("No existing FAISS index found, starting fresh")
                return

            self.index = faiss.read_index(self.index_file)
            with open(self.metadata_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)

            if isinstance(data, list):
                self.metadata = data
            elif isinstance(data, dict) and "metadata" in data:
                self.metadata = data["metadata"]
                self.dimension = data.get("dimension", self.dimension)
            else:
                raise ValueError(f"Unsupported metadata format: {type(data)}")

            self.doc_count = len(self.metadata)
            logger.info(
                "Loaded FAISS index (%s documents, metric=%s)",
                self.doc_count,
                getattr(self.index, "metric_type", "unknown"),
            )
        except Exception as exc:
            logger.warning("Could not load FAISS index: %s", exc)
            self.metadata = []
            self.doc_count = 0

    def get_stats(self) -> Dict[str, Any]:
        return {
            "document_count": self.doc_count,
            "index_size": self.index.ntotal,
            "dimension": self.index.d,
            "metadata_count": len(self.metadata),
            "metric_type": getattr(self.index, "metric_type", "unknown"),
            "synced": self.doc_count == self.index.ntotal == len(self.metadata),
        }

    def validate_integrity(self) -> bool:
        faiss_size = self.index.ntotal
        metadata_size = len(self.metadata)

        if faiss_size != metadata_size:
            logger.error(
                "FAISS integrity mismatch: vectors=%s metadata=%s",
                faiss_size,
                metadata_size,
            )
            return False

        if faiss_size != self.doc_count:
            logger.error(
                "FAISS document count mismatch: vectors=%s doc_count=%s",
                faiss_size,
                self.doc_count,
            )
            return False

        return True


_index: FAISSIndex | None = None


def get_index() -> FAISSIndex:
    """Return the shared FAISS index instance."""
    global _index
    if _index is None:
        _index = FAISSIndex(dimension=384)
    return _index
