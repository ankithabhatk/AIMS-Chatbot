"""
Enhanced FAISS Index Builder with Metadata

Builds and maintains FAISS vector index with:
- Document ID tracking
- Metadata storage (URL, heading, chunk_index)
- Persistence to disk
- Batch operations
"""

import logging
import json
import os
from typing import List, Dict, Tuple, Optional
import numpy as np
import faiss

logger = logging.getLogger(__name__)


class FAISSIndexBuilder:
    """Build and manage FAISS index with metadata"""
    
    def __init__(self, index_path: str = "/Users/maneeth/Desktop/Chat-Bot/backend/app/data/faiss_index", dimension: int = 384):
        """
        Initialize index builder
        
        Args:
            index_path: Path to store index files
            dimension: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        self.index_path = index_path
        self.dimension = dimension
        self.index = None
        self.metadata = []  # [{doc_id, url, heading, chunk_index}, ...]
        self.doc_id_map = {}  # {document_uuid -> index_position}
        
        os.makedirs(index_path, exist_ok=True)
    
    def create_index(self) -> faiss.IndexFlatL2:
        """Create new FAISS index (L2 distance)"""
        logger.info(f"Creating new FAISS index (dimension={self.dimension})")
        return faiss.IndexFlatL2(self.dimension)
    
    def add_embeddings(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict],
        doc_ids: List[str]
    ) -> None:
        """
        Add embeddings and metadata to index
        
        Args:
            embeddings: (N, 384) array of embeddings
            metadata: List of {url, heading, chunk_index, tokens}
            doc_ids: List of document UUIDs (same length as embeddings)
        """
        if self.index is None:
            self.index = self.create_index()
        
        # Ensure embeddings are float32
        embeddings = np.array(embeddings, dtype=np.float32)
        
        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: {embeddings.shape[1]} vs {self.dimension}"
            )
        
        # Add to FAISS
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Track metadata
        for i, (doc_id, meta) in enumerate(zip(doc_ids, metadata)):
            idx = start_idx + i
            self.doc_id_map[doc_id] = idx
            self.metadata.append({
                'index_position': idx,
                'doc_id': doc_id,
                **meta
            })
        
        logger.info(f"Added {len(embeddings)} embeddings to index (total: {self.index.ntotal})")
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Dict]:
        """
        Search index
        
        Args:
            query_embedding: (384,) embedding array
            k: Number of results to return
        
        Returns:
            List of {distance, content, url, heading, chunk_index, score}
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        query_embedding = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            
            meta = self.metadata[idx]
            
            # Convert L2 distance to similarity score (0-1)
            # L2 distance in range [0, ∞], convert to [1, 0] similarity
            similarity = 1 / (1 + dist)  # Sigmoid-like conversion
            
            results.append({
                'distance': float(dist),
                'similarity_score': float(similarity),
                'url': meta.get('url', ''),
                'heading': meta.get('heading', ''),
                'chunk_index': meta.get('chunk_index', 0),
                'tokens': meta.get('tokens', 0),
                'index_position': idx
            })
        
        return results
    
    def save(self) -> None:
        """Save index to disk"""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        index_file = os.path.join(self.index_path, "index.faiss")
        metadata_file = os.path.join(self.index_path, "metadata.json")
        
        # Save FAISS index
        faiss.write_index(self.index, index_file)
        logger.info(f"Saved FAISS index to {index_file}")
        
        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump({
                'metadata': self.metadata,
                'doc_id_map': self.doc_id_map,
                'dimension': self.dimension,
                'total_vectors': self.index.ntotal
            }, f, indent=2)
        logger.info(f"Saved metadata to {metadata_file}")
    
    def load(self) -> bool:
        """Load index from disk"""
        index_file = os.path.join(self.index_path, "index.faiss")
        metadata_file = os.path.join(self.index_path, "metadata.json")
        
        if not os.path.exists(index_file) or not os.path.exists(metadata_file):
            logger.warning(f"Index files not found at {self.index_path}")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(index_file)
            logger.info(f"Loaded FAISS index from {index_file}")
            
            # Load metadata
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                self.metadata = data['metadata']
                self.doc_id_map = data['doc_id_map']
                self.dimension = data['dimension']
            
            logger.info(f"Loaded metadata: {len(self.metadata)} documents")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False


def build_faiss_index_from_embeddings(
    embeddings: List[List[float]],
    documents: List[Dict],
    doc_ids: List[str],
    index_path: str = "/Users/maneeth/Desktop/Chat-Bot/backend/app/data/faiss_index"
) -> FAISSIndexBuilder:
    """
    Build FAISS index from embeddings
    
    Args:
        embeddings: List of embedding vectors
        documents: List of {url, heading, chunk_index, tokens}
        doc_ids: List of document IDs
        index_path: Where to save index
    
    Returns:
        FAISSIndexBuilder instance
    """
    builder = FAISSIndexBuilder(index_path=index_path)
    embeddings_array = np.array(embeddings, dtype=np.float32)
    builder.add_embeddings(embeddings_array, documents, doc_ids)
    builder.save()
    return builder
