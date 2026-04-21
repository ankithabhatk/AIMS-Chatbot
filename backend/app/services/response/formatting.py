"""
Response Formatting - Format answers for different output types

Supports:
- JSON (API responses with metadata)
- Plain text (simple text output)
- Markdown (formatted text with links)
- Structured (with confidence, sources, etc.)
"""

import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def format_json_response(
    answer: str,
    confidence: float,
    sources: List[str] = None,
    metadata: Dict = None
) -> str:
    """
    Format answer as JSON with metadata
    
    Args:
        answer: The answer text
        confidence: Confidence score (0-1)
        sources: List of source references
        metadata: Additional metadata
    
    Returns:
        JSON formatted response
    """
    response = {
        "success": True,
        "data": {
            "answer": answer,
            "confidence": confidence,
            "sources": sources or [],
            "metadata": metadata or {}
        }
    }
    
    return json.dumps(response, indent=2)


def format_plain_text(
    answer: str,
    confidence: float = None,
    sources: List[str] = None
) -> str:
    """
    Format answer as plain text
    
    Args:
        answer: The answer text
        confidence: Optional confidence score
        sources: Optional source references
    
    Returns:
        Plain text formatted response
    """
    output = answer
    
    if confidence is not None:
        output += f"\n\n[Confidence: {confidence*100:.0f}%]"
    
    if sources:
        output += f"\n\nSources:\n" + "\n".join([f"- {s}" for s in sources])
    
    return output


def format_markdown(
    answer: str,
    confidence: float = None,
    sources: List[str] = None,
    include_confidence_badge: bool = True
) -> str:
    """
    Format answer as Markdown
    
    Args:
        answer: The answer text
        confidence: Optional confidence score
        sources: Optional source references
        include_confidence_badge: Add confidence badge
    
    Returns:
        Markdown formatted response
    """
    output = answer
    
    if include_confidence_badge and confidence is not None:
        badge = _get_confidence_badge(confidence)
        output += f"\n\n{badge}"
    
    if sources:
        output += f"\n\n## Sources\n"
        for i, source in enumerate(sources, 1):
            output += f"{i}. {source}\n"
    
    return output


def format_structured(answer: str, confidence: float, sources: List[str] = None, **kwargs) -> Dict:
    """
    Format answer as structured dict with full metadata
    
    Args:
        answer: The answer text
        confidence: Confidence score (0-1)
        sources: Optional source references
        **kwargs: Additional metadata
    
    Returns:
        Structured response dict
    """
    return {
        "answer": answer,
        "confidence": confidence,
        "sources": sources or [],
        "metadata": kwargs
    }


def _get_confidence_badge(confidence: float) -> str:
    """Generate confidence badge for markdown"""
    if confidence < 0.4:
        return "⚠️ **Low Confidence** - This answer may be incomplete"
    elif confidence < 0.6:
        return "ℹ️ **Medium Confidence** - Use with caution"
    else:
        return "✅ **High Confidence**"


def format_error_response(error_message: str, error_code: str = "ERROR") -> str:
    """
    Format error as JSON response
    
    Args:
        error_message: Error description
        error_code: Error code/type
    
    Returns:
        JSON formatted error response
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": error_message
        }
    }
    
    return json.dumps(response, indent=2)
