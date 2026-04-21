"""Health Check Endpoint - Production Grade (Phase 4)"""

from fastapi import APIRouter
from datetime import datetime
import logging

from app.services.retrieval.faiss_index import get_index
from app.services.embeddings.embedding_service import load_embedding_model

router = APIRouter(prefix="/api/v1", tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """
    GET /api/v1/health
    
    Returns system health status including FAISS index and embedding model
    
    Response:
        {
            "status": "ok",
            "faiss_loaded": true,
            "embedding_model_loaded": true,
            "documents_indexed": 46,
            "last_updated": "2026-04-19T12:00:00Z"
        }
    """
    try:
        # Check FAISS index
        index = get_index()
        stats = index.get_stats()
        faiss_loaded = stats['synced']
        documents_indexed = stats['document_count']
        
        logger.info(f"Health check - FAISS: {documents_indexed} docs, synced={faiss_loaded}")
        
        # Check embedding model
        try:
            model = load_embedding_model()
            embedding_model_loaded = model is not None
        except Exception as e:
            logger.error(f"Embedding model check failed: {e}")
            embedding_model_loaded = False
        
        # Determine overall status
        if faiss_loaded and embedding_model_loaded and documents_indexed > 0:
            status = "ok"
        elif documents_indexed == 0:
            status = "degraded"  # No documents indexed yet
        else:
            status = "error"
        
        return {
            "status": status,
            "faiss_loaded": faiss_loaded,
            "embedding_model_loaded": embedding_model_loaded,
            "documents_indexed": documents_indexed,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "error",
            "faiss_loaded": False,
            "embedding_model_loaded": False,
            "documents_indexed": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
