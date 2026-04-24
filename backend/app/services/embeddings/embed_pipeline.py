"""
Offline batch embedding pipeline built on the shared embedding service.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Tuple

import numpy as np

from app.services.embeddings.embedding_service import embed_batch as shared_embed_batch
from app.services.embeddings.embedding_service import embed_text as shared_embed_text
from app.services.embeddings.embedding_service import load_embedding_model

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Thin batch wrapper around the shared offline embedding service."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 32, device: str = "cpu"):
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        logger.info("Loading embedding pipeline model: %s", self.model_name)
        self.model = load_embedding_model(self.model_name)

    def embed_text(self, text: str) -> np.ndarray:
        return shared_embed_text(text)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        return shared_embed_batch(texts)

    def embed_chunks(self, chunks: List[Dict]) -> Tuple[List[List[float]], List[Dict], List[str]]:
        logger.info("Embedding %s chunks", len(chunks))
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embed_batch(texts)

        metadata = [
            {
                "url": chunk["url"],
                "heading": chunk.get("heading", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "tokens": chunk.get("tokens", 0),
            }
            for chunk in chunks
        ]
        chunk_ids = [
            f"{chunk['url']}#{chunk.get('chunk_index', 0)}"
            for chunk in chunks
        ]

        return embeddings.tolist(), metadata, chunk_ids


async def async_embed_chunks(
    chunks: List[Dict],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
) -> Tuple[List[List[float]], List[Dict], List[str]]:
    loop = asyncio.get_event_loop()
    pipeline = EmbeddingPipeline(model_name=model_name, batch_size=batch_size)
    embeddings, metadata, chunk_ids = await loop.run_in_executor(
        None,
        pipeline.embed_chunks,
        chunks,
    )
    return embeddings, metadata, chunk_ids


def embed_for_search(query: str, model_name: str = "all-MiniLM-L6-v2") -> List[float]:
    pipeline = EmbeddingPipeline(model_name=model_name)
    embedding = pipeline.embed_text(query)
    return embedding.tolist()
