import os
import logging
import time
from typing import Optional, Dict, Any
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Initialize Supabase client lazily
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """Get or initialize the Supabase client."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
        
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set. Analytics will be skipped.")
        return None
        
    try:
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

def log_conversation_analytics(
    session_id: str,
    detected_intent: Optional[str],
    confidence_score: float,
    contradiction_detected: bool,
    pivot_detected: bool,
    selected_program: Optional[str],
    provider_used: Optional[str],
    response_latency_ms: float
):
    """
    Fire-and-forget logging to Supabase conversation_analytics table.
    Designed to run in FastAPI BackgroundTasks.
    """
    client = get_supabase_client()
    if not client:
        return
        
    try:
        data = {
            "session_id": session_id,
            "detected_intent": detected_intent,
            "confidence_score": confidence_score,
            "contradiction_detected": contradiction_detected,
            "pivot_detected": pivot_detected,
            "selected_program": selected_program,
            "provider_used": provider_used,
            "response_latency_ms": response_latency_ms
            # created_at is automatically handled by Supabase default now()
        }
        
        # We don't await because supabase-py is synchronous right now, 
        # but running in FastAPI BackgroundTasks puts it in a separate threadpool.
        client.table("conversation_analytics").insert(data).execute()
        
    except Exception as e:
        # Passive telemetry must NEVER crash the app or spam logs too hard
        logger.warning(f"Failed to log analytics to Supabase: {e}")
