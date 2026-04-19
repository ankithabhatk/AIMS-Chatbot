"""
Common utilities for validation, logging, and error handling
"""

import logging
import json
from typing import Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def validate_query(query: str, min_length: int = 3) -> tuple[bool, str]:
    """
    Validate chat query
    
    Args:
        query: User query string
        min_length: Minimum query length
    
    Returns:
        (is_valid, error_message)
    """
    if not query:
        return False, "Query cannot be empty"
    
    query = query.strip()
    if len(query) < min_length:
        return False, f"Query must be at least {min_length} characters"
    
    if len(query) > 5000:
        return False, "Query exceeds maximum length of 5000 characters"
    
    return True, ""


def log_event(event_type: str, event_data: Dict[str, Any]) -> None:
    """
    Structured event logging
    
    Args:
        event_type: Type of event (chat, lead, error)
        event_data: Event details as dictionary
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": event_data
    }
    logger.info(json.dumps(log_entry))


def calculate_token_count(text: str) -> int:
    """
    Estimate token count (rough approximation)
    Actual count from OpenAI API during embedding/LLM calls
    
    Average: ~4 characters = 1 token
    """
    return len(text) // 4


def format_error_response(error: Exception, include_details: bool = False) -> Dict[str, Any]:
    """
    Format error response for API
    
    Args:
        error: Exception object
        include_details: Whether to include stack trace (only in debug mode)
    
    Returns:
        Formatted error dictionary
    """
    response = {
        "status": "error",
        "message": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if include_details:
        import traceback
        response["details"] = traceback.format_exc()
    
    return response
