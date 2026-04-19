"""
FAISS Vector Store for RAG Retrieval

Manages vector index and document metadata for semantic search.
"""

import logging
import json
import os
from typing import List, Tuple, Dict, Any
import numpy as np
import faiss

logger = logging.getLogger(__name__)

# Default paths
INDEX_DIR = "/tmp/chatbot_faiss"
INDEX_FILE = os.path.join(INDEX_DIR, "index.faiss")
METADATA_FILE = os.path.join(INDEX_DIR, "metadata.json")


class FAISSIndex:
    """FAISS vector index with metadata storage"""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize FAISS index
        
        Args:
            dimension: Embedding vector dimension
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance
        self.metadata: List[Dict[str, Any]] = []
        self.doc_count = 0
        
        # Create index directory if needed
        os.makedirs(INDEX_DIR, exist_ok=True)
        
        # Try to load existing index
        self.load()
    
    def add_documents(self, texts: List[str], embeddings: np.ndarray, 
                     urls: List[str] = None, headings: List[str] = None) -> None:
        """
        Add documents to index
        
        Args:
            texts: Document text chunks
            embeddings: Precomputed embeddings (n, 384)
            urls: Source URLs
            headings: Document headings/titles
        """
        if len(texts) != len(embeddings):
            raise ValueError("texts and embeddings must have same length")
        
        if urls is None:
            urls = ["unknown"] * len(texts)
        if headings is None:
            headings = ["untitled"] * len(texts)
        
        # Add to FAISS index
        embeddings_float32 = embeddings.astype(np.float32)
        self.index.add(embeddings_float32)
        
        # Store metadata
        for i, (text, url, heading) in enumerate(zip(texts, urls, headings)):
            self.metadata.append({
                "id": self.doc_count + i,
                "text": text[:500],  # Store first 500 chars for display
                "url": url,
                "heading": heading,
                "full_text": text  # Store full for return
            })
        
        self.doc_count += len(texts)
        logger.info(f"Added {len(texts)} documents. Total: {self.doc_count}")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float, str, str]]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding (384,)
            k: Number of results to return
            
        Returns:
            List of (text, score, url, heading)
            Score is L2 distance (lower = more similar)
        """
        if self.doc_count == 0:
            logger.warning("Search on empty index")
            return []
        
        # Ensure float32
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, self.doc_count))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:  # Invalid result
                continue
            
            meta = self.metadata[idx]
            # Convert L2 distance to similarity score (0-1)
            # Lower distance = higher similarity
            similarity = 1.0 / (1.0 + dist)
            
            results.append((
                meta["full_text"],
                float(similarity),
                meta["url"],
                meta["heading"]
            ))
        
        return results
    
    def save(self) -> None:
        """Persist index to disk"""
        try:
            faiss.write_index(self.index, INDEX_FILE)
            with open(METADATA_FILE, "w") as f:
                json.dump(self.metadata, f)
            logger.info(f"✅ Index saved ({self.doc_count} documents)")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def load(self) -> None:
        """Load index from disk if exists"""
        try:
            if os.path.exists(INDEX_FILE):
                self.index = faiss.read_index(INDEX_FILE)
                with open(METADATA_FILE, "r") as f:
                    self.metadata = json.load(f)
                self.doc_count = len(self.metadata)
                logger.info(f"✅ Loaded existing index ({self.doc_count} documents)")
            else:
                logger.info("No existing index found, starting fresh")
        except Exception as e:
            logger.warning(f"Could not load index: {e}, starting fresh")
    
    def get_stats(self) -> Dict[str, int]:
        """Get index statistics"""
        return {
            "document_count": self.doc_count,
            "index_size": self.index.ntotal,
            "dimension": self.dimension
        }


# Global instance
_index: FAISSIndex = None


def get_index() -> FAISSIndex:
    """Get or create global FAISS index"""
    global _index
    if _index is None:
        _index = FAISSIndex(dimension=384)
    return _index
