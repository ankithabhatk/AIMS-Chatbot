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

# Persistent index directory
INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "faiss_index")
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
        persist_dir = "/Users/maneeth/Desktop/Chat-Bot/backend/app/data/faiss_index"
        os.makedirs(persist_dir, exist_ok=True)
        
        # Default paths
        self.index_dir = persist_dir
        self.index_file = os.path.join(persist_dir, "index.faiss")
        self.metadata_file = os.path.join(persist_dir, "metadata.json")
        
        # Load existing index if available
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
            Score is similarity (0-1, higher = more similar)
        """
        if self.doc_count == 0:
            logger.warning("Search on empty index")
            return []
        
        # Ensure float32
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, self.doc_count))
        
        logger.debug(f"FAISS returned {len(indices[0])} results. Metadata has {len(self.metadata)} entries.")
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:  # Invalid result
                continue
            
            # CRITICAL: Check bounds to prevent KeyError
            if idx >= len(self.metadata):
                logger.error(
                    f"Index mismatch: FAISS returned idx={idx} "
                    f"but metadata only has {len(self.metadata)} entries. "
                    f"FAISS index has {self.index.ntotal} vectors. "
                    f"This indicates index corruption - skipping this result."
                )
                continue
            
            meta = self.metadata[idx]
            
            # Handle both metadata formats
            # FAISSIndex format: {full_text, url, heading, id}
            # FAISSIndexBuilder format: {text, url, heading, chunk_index, tokens}
            full_text = meta.get("full_text") or meta.get("text", "")
            
            if not full_text:
                logger.warning(f"No text found in metadata for idx={idx}")
                continue
            
            # Convert L2 distance to similarity score (0-1)
            # Lower distance = higher similarity
            similarity = 1.0 / (1.0 + dist)
            
            results.append((
                full_text,
                float(similarity),
                meta.get("url", ""),
                meta.get("heading", ""),
                meta.get("id") or meta.get("index_position") or idx  # Document ID for tracing
            ))
        
        logger.debug(f"Search returned {len(results)} valid results")
        return results
    
    def save(self) -> None:
        """Persist index to disk"""
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f)
            logger.info(f"✅ Index saved ({self.doc_count} documents)")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def load(self) -> None:
        """Load index from disk if exists"""
        try:
            if os.path.exists(self.index_file):
                self.index = faiss.read_index(self.index_file)
                
                # Load metadata with format detection
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                
                # Handle two formats:
                # 1. List format from FAISSIndex: [{id, text, url, heading, full_text}, ...]
                # 2. Dict format from FAISSIndexBuilder: {metadata: [...], doc_id_map: {...}, ...}
                if isinstance(data, list):
                    # Direct list format
                    self.metadata = data
                elif isinstance(data, dict) and 'metadata' in data:
                    # FAISSIndexBuilder format
                    self.metadata = data['metadata']
                    logger.info(f"Converted from FAISSIndexBuilder format")
                else:
                    logger.error(f"Unknown metadata format: {type(data)}")
                    self.metadata = []
                
                self.doc_count = len(self.metadata)
                faiss_size = self.index.ntotal
                
                if faiss_size != self.doc_count:
                    logger.error(
                        f"⚠️ Index/Metadata mismatch on load:\n"
                        f"  FAISS vectors: {faiss_size}\n"
                        f"  Metadata entries: {self.doc_count}\n"
                        f"  This might cause search errors"
                    )
                
                logger.info(f"✅ Loaded existing index ({self.doc_count} documents)")
            else:
                logger.info("No existing index found, starting fresh")
        except Exception as e:
            logger.warning(f"Could not load index: {e}, starting fresh")
            self.metadata = []
            self.doc_count = 0
    
    def get_stats(self) -> Dict[str, int]:
        """Get index statistics"""
        return {
            "document_count": self.doc_count,
            "index_size": self.index.ntotal,
            "dimension": self.dimension,
            "metadata_count": len(self.metadata),
            "synced": self.doc_count == self.index.ntotal == len(self.metadata)
        }
    
    def validate_integrity(self) -> bool:
        """
        Check if index and metadata are in sync
        
        Returns:
            True if valid, False if corrupted
        """
        faiss_size = self.index.ntotal
        metadata_size = len(self.metadata)
        
        if faiss_size != metadata_size:
            logger.error(
                f"❌ INDEX CORRUPTION DETECTED:\n"
                f"  FAISS vectors: {faiss_size}\n"
                f"  Metadata entries: {metadata_size}\n"
                f"  Synced: {faiss_size == metadata_size}"
            )
            return False
        
        if faiss_size != self.doc_count:
            logger.error(
                f"❌ DOC COUNT MISMATCH:\n"
                f"  FAISS vectors: {faiss_size}\n"
                f"  doc_count: {self.doc_count}"
            )
            return False
        
        logger.info(f"✅ Index integrity OK ({self.doc_count} documents)")
        return True


# Global instance
_index: FAISSIndex = None


def get_index() -> FAISSIndex:
    """Get or create global FAISS index"""
    global _index
    if _index is None:
        _index = FAISSIndex(dimension=384)
    return _index
