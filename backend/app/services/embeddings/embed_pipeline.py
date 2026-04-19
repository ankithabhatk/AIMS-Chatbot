"""
Complete Embedding Pipeline

Orchestrates:
- Loading pre-trained embeddings model
- Batch embedding of text chunks
- Persistence management
"""

import logging
import asyncio
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Efficient batch embedding pipeline"""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        device: str = "cpu"
    ):
        """
        Initialize embedding pipeline
        
        Args:
            model_name: HuggingFace model ID
            batch_size: Batch size for embedding
            device: 'cpu' or 'cuda'
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load embedding model (lazy load)"""
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.model.to(self.device)
        logger.info(f"Model loaded on {self.device}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed single text
        
        Args:
            text: Text to embed
        
        Returns:
            (384,) embedding vector
        """
        if not self.model:
            self._load_model()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Embed batch of texts
        
        Args:
            texts: List of texts to embed
        
        Returns:
            (N, 384) embedding matrix
        """
        if not self.model:
            self._load_model()
        
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings
    
    def embed_chunks(
        self,
        chunks: List[Dict]
    ) -> Tuple[List[List[float]], List[Dict], List[str]]:
        """
        Embed document chunks
        
        Args:
            chunks: List of {content, url, heading, chunk_index, tokens}
        
        Returns:
            Tuple of:
            - embeddings: List of embedding vectors
            - metadata: List of {url, heading, chunk_index, tokens}
            - chunk_ids: List of chunk identifiers (for deduplication)
        """
        logger.info(f"Embedding {len(chunks)} chunks")
        
        # Extract texts
        texts = [chunk['content'] for chunk in chunks]
        
        # Batch encode
        embeddings = self.embed_batch(texts)
        
        # Extract metadata
        metadata = [
            {
                'url': chunk['url'],
                'heading': chunk.get('heading', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'tokens': chunk.get('tokens', 0)
            }
            for chunk in chunks
        ]
        
        # Generate deterministic IDs (url + chunk_index)
        chunk_ids = [
            f"{chunk['url']}#{chunk.get('chunk_index', 0)}"
            for chunk in chunks
        ]
        
        logger.info(f"Embedded {len(embeddings)} chunks (shape: {embeddings.shape})")
        
        return embeddings.tolist(), metadata, chunk_ids


async def async_embed_chunks(
    chunks: List[Dict],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32
) -> Tuple[List[List[float]], List[Dict], List[str]]:
    """
    Async wrapper for embedding (runs embedding in thread pool)
    
    Args:
        chunks: List of document chunks
        model_name: HuggingFace model ID
        batch_size: Batch size for embedding
    
    Returns:
        Tuple of (embeddings, metadata, chunk_ids)
    """
    loop = asyncio.get_event_loop()
    pipeline = EmbeddingPipeline(model_name=model_name, batch_size=batch_size)
    
    # Run embedding in executor (non-blocking)
    embeddings, metadata, chunk_ids = await loop.run_in_executor(
        None,
        pipeline.embed_chunks,
        chunks
    )
    
    return embeddings, metadata, chunk_ids


def embed_for_search(
    query: str,
    model_name: str = "all-MiniLM-L6-v2"
) -> List[float]:
    """
    Embed search query
    
    Args:
        query: Search query text
        model_name: HuggingFace model ID
    
    Returns:
        (384,) embedding vector as list
    """
    pipeline = EmbeddingPipeline(model_name=model_name)
    embedding = pipeline.embed_text(query)
    return embedding.tolist()
