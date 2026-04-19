"""
Embedding Service using Sentence Transformers

Provides local embeddings without API calls.
Model: all-MiniLM-L6-v2 (384-dim, fast, good quality)
"""

import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global model instance (loaded once)
_model: Optional[SentenceTransformer] = None


def load_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load embedding model globally (cached after first call)"""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {model_name}...")
        _model = SentenceTransformer(model_name)
        logger.info(f"✅ Embedding model loaded. Dimension: {_model.get_sentence_embedding_dimension()}")
    return _model


def embed_text(text: str) -> np.ndarray:
    """
    Embed a single text string
    
    Args:
        text: Text to embed
        
    Returns:
        numpy array of shape (384,)
    """
    model = load_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


def embed_batch(texts: List[str]) -> np.ndarray:
    """
    Embed multiple texts efficiently
    
    Args:
        texts: List of strings to embed
        
    Returns:
        numpy array of shape (len(texts), 384)
    """
    if not texts:
        return np.array([])
    
    model = load_embedding_model()
    embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32)
    return embeddings


def get_embedding_dimension() -> int:
    """Get embedding vector dimension"""
    model = load_embedding_model()
    return model.get_sentence_embedding_dimension()
