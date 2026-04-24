"""Stats Endpoint - Analytics and Metrics (Phase 4)"""

from fastapi import APIRouter
from datetime import datetime
import logging

from app.services.conversation_store import get_conversation_store
from app.services.logging.query_logger import get_query_logger
from app.services.query_cache import get_query_response_cache

router = APIRouter(prefix="/api/v1", tags=["stats"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_stats():
    """
    GET /api/v1/stats
    
    Returns analytics metrics from recent queries
    
    Response:
        {
            "total_queries": 128,
            "fallback_rate": 0.42,
            "avg_confidence": 0.67,
            "avg_response_time_ms": 45.2,
            "top_queries": ["admission process", "courses offered"],
            "top_fallbacks": ["space engineering", "company names"]
        }
    """
    try:
        query_logger = get_query_logger()
        stats = query_logger.get_stats()
        cache_stats = get_query_response_cache().get_stats()
        store_stats = get_conversation_store().get_stats()
        
        logger.info(f"Stats retrieved: {stats['total_queries']} queries, "
                   f"fallback_rate={stats['fallback_rate']}")
        
        return {
            "total_queries": stats.get("total_queries", 0),
            "fallback_rate": stats.get("fallback_rate", 0.0),
            "avg_confidence": stats.get("avg_confidence", 0.0),
            "avg_response_time_ms": stats.get("avg_response_time_ms", 0.0),
            "top_queries": stats.get("top_queries", []),
            "top_fallbacks": stats.get("top_fallbacks", []),
            "query_cache": cache_stats,
            "conversation_store": store_stats,
        }
    
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}", exc_info=True)
        return {
            "total_queries": 0,
            "fallback_rate": 0.0,
            "avg_confidence": 0.0,
            "avg_response_time_ms": 0.0,
            "top_queries": [],
            "top_fallbacks": [],
            "query_cache": {},
            "conversation_store": {},
        }
