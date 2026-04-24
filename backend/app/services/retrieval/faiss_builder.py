"""
FAISS builder that persists cosine-compatible indexes and rich metadata.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class FAISSIndexBuilder:
    """Build and load a cosine-similarity FAISS index."""

    def __init__(self, index_path: Optional[str] = None, dimension: int = 384):
        if index_path is None:
            index_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "data",
                "faiss_index",
            )

        self.index_path = index_path
        self.dimension = dimension
        self.index = None
        self.metadata: List[Dict] = []
        self.doc_id_map: Dict[str, int] = {}
        os.makedirs(index_path, exist_ok=True)

    def create_index(self) -> faiss.IndexFlatIP:
        logger.info("Creating FAISS cosine index (dimension=%s)", self.dimension)
        return faiss.IndexFlatIP(self.dimension)

    def add_embeddings(self, embeddings: np.ndarray, metadata: List[Dict], doc_ids: List[str]) -> None:
        if self.index is None:
            self.index = self.create_index()

        embeddings = np.asarray(embeddings, dtype=np.float32)
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array")

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: {embeddings.shape[1]} vs {self.dimension}"
            )

        faiss.normalize_L2(embeddings)
        start_idx = self.index.ntotal
        self.index.add(embeddings)

        for offset, (doc_id, meta) in enumerate(zip(doc_ids, metadata)):
            idx = start_idx + offset
            self.doc_id_map[doc_id] = idx
            self.metadata.append(
                {
                    "index_position": idx,
                    "doc_id": doc_id,
                    **meta,
                }
            )

        logger.info("Added %s embeddings to index (total=%s)", len(embeddings), self.index.ntotal)

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        results: List[Dict] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]
            similarity = max(0.0, min((float(dist) + 1.0) / 2.0, 1.0))
            results.append(
                {
                    "distance": float(dist),
                    "similarity_score": similarity,
                    "url": meta.get("url", ""),
                    "heading": meta.get("heading", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "tokens": meta.get("tokens", 0),
                    "index_position": idx,
                    "doc_id": meta.get("doc_id"),
                }
            )

        return results

    def save(self) -> None:
        if self.index is None:
            logger.warning("No FAISS index to save")
            return

        index_file = os.path.join(self.index_path, "index.faiss")
        metadata_file = os.path.join(self.index_path, "metadata.json")

        faiss.write_index(self.index, index_file)
        with open(metadata_file, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "metadata": self.metadata,
                    "doc_id_map": self.doc_id_map,
                    "dimension": self.dimension,
                    "metric": "cosine_ip",
                    "total_vectors": self.index.ntotal,
                },
                handle,
                indent=2,
            )

        logger.info("Saved FAISS index to %s", index_file)

    def load(self) -> bool:
        index_file = os.path.join(self.index_path, "index.faiss")
        metadata_file = os.path.join(self.index_path, "metadata.json")

        if not os.path.exists(index_file) or not os.path.exists(metadata_file):
            logger.warning("Index files not found at %s", self.index_path)
            return False

        try:
            self.index = faiss.read_index(index_file)
            with open(metadata_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)

            self.metadata = data["metadata"]
            self.doc_id_map = data.get("doc_id_map", {})
            self.dimension = data.get("dimension", self.dimension)
            logger.info("Loaded FAISS index: %s vectors", self.index.ntotal)
            return True
        except Exception as exc:
            logger.error("Failed to load FAISS index: %s", exc)
            return False


def build_faiss_index_from_embeddings(
    embeddings: List[List[float]],
    documents: List[Dict],
    doc_ids: List[str],
    index_path: Optional[str] = None,
) -> FAISSIndexBuilder:
    builder = FAISSIndexBuilder(index_path=index_path, dimension=len(embeddings[0]) if embeddings else 384)
    embeddings_array = np.asarray(embeddings, dtype=np.float32)
    builder.add_embeddings(embeddings_array, documents, doc_ids)
    builder.save()
    return builder
