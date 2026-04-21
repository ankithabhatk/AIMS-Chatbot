"""Query Logging Service - Log all chat interactions for analytics"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import deque
import threading

logger = logging.getLogger(__name__)

# Log file locations
LOG_DIR = Path("/tmp/chatbot_logs")
QUERIES_LOG_FILE = LOG_DIR / "queries.jsonl"

# In-memory stats (for fast access)
MAX_QUERIES_IN_MEMORY = 500
queries_buffer = deque(maxlen=MAX_QUERIES_IN_MEMORY)
stats_lock = threading.Lock()  # Thread-safe access


class QueryLogger:
    """Log and retrieve chat query analytics"""
    
    def __init__(self):
        """Initialize logger with file storage"""
        LOG_DIR.mkdir(exist_ok=True)
        self.log_file = QUERIES_LOG_FILE
        logger.info(f"Query logger initialized: {self.log_file}")
    
    def log_query(self,
                  query: str,
                  answer: Optional[str],
                  confidence: float,
                  fallback: bool,
                  response_time_ms: int,
                  chunks_used: int = 0,
                  user_email: Optional[str] = None,
                  session_id: Optional[str] = None,
                  sources: Optional[List[Dict[str, str]]] = None) -> None:
        """
        Log a single query-answer pair
        
        Args:
            query: User's question
            answer: System's answer (None if fallback)
            confidence: Confidence score (0.0-1.0)
            fallback: Whether fallback was used
            response_time_ms: Response time in milliseconds
            chunks_used: Number of chunks used in synthesis
            user_email: User's email (optional)
            session_id: Session ID (optional)
            sources: List of source links used
        """
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "query": query[:500],  # Truncate long queries
                "answer": answer[:300] if answer else None,  # Truncate answers
                "confidence": round(confidence, 3),
                "fallback": fallback,
                "response_time_ms": response_time_ms,
                "chunks_used": chunks_used,
                "user_email": user_email,
                "session_id": session_id,
                "sources_count": len(sources) if sources else 0
            }
            
            # Write to file (JSONL format for easy parsing)
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Add to in-memory buffer (thread-safe)
            with stats_lock:
                queries_buffer.append(log_entry)
            
            logger.debug(f"Logged query: {query[:30]}... (fallback={fallback})")
            
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get analytics stats from recent queries
        
        Returns:
            Dict with total_queries, fallback_rate, avg_confidence, top_queries
        """
        try:
            with stats_lock:
                if not queries_buffer:
                    return {
                        "total_queries": 0,
                        "fallback_rate": 0.0,
                        "avg_confidence": 0.0,
                        "top_queries": [],
                        "avg_response_time_ms": 0.0
                    }
                
                # Calculate statistics
                total = len(queries_buffer)
                fallbacks = sum(1 for q in queries_buffer if q["fallback"])
                fallback_rate = fallbacks / total if total > 0 else 0.0
                
                confidences = [q["confidence"] for q in queries_buffer]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                response_times = [q.get("response_time_ms", 0) for q in queries_buffer]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
                
                # Top queries (most frequent)
                query_counts = {}
                for q in queries_buffer:
                    query_text = q["query"][:50]  # Normalize by truncating
                    query_counts[query_text] = query_counts.get(query_text, 0) + 1
                
                top_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                top_queries_list = [q[0] for q in top_queries]
                
                # Most common fallback queries
                fallback_queries = {}
                for q in queries_buffer:
                    if q["fallback"]:
                        query_text = q["query"][:50]
                        fallback_queries[query_text] = fallback_queries.get(query_text, 0) + 1
                
                top_fallbacks = sorted(fallback_queries.items(), key=lambda x: x[1], reverse=True)[:5]
                top_fallbacks_list = [q[0] for q in top_fallbacks]
                
                return {
                    "total_queries": total,
                    "fallback_rate": round(fallback_rate, 3),
                    "avg_confidence": round(avg_confidence, 3),
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "top_queries": top_queries_list,
                    "top_fallbacks": top_fallbacks_list
                }
        
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "total_queries": 0,
                "fallback_rate": 0.0,
                "avg_confidence": 0.0,
                "top_queries": [],
                "avg_response_time_ms": 0.0
            }
    
    def get_recent_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most recent queries (FIFO order)"""
        try:
            with stats_lock:
                return list(queries_buffer)[-limit:]
        except Exception as e:
            logger.error(f"Failed to get recent queries: {e}")
            return []


# Global singleton instance
_logger_instance: Optional[QueryLogger] = None


def get_query_logger() -> QueryLogger:
    """Get or initialize global query logger"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = QueryLogger()
    return _logger_instance
