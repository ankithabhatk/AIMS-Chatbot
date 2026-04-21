"""
Response Service Module

Handles:
- Filtering search results
- Calculating answer confidence
- Formatting responses
"""

from .filter import filter_results_by_relevance, filter_results_by_source
from .confidence import calculate_confidence, is_confident_enough, get_confidence_label
from .formatting import (
    format_json_response, format_plain_text, format_markdown,
    format_structured, format_error_response
)

__all__ = [
    'filter_results_by_relevance',
    'filter_results_by_source',
    'calculate_confidence',
    'is_confident_enough',
    'get_confidence_label',
    'format_json_response',
    'format_plain_text',
    'format_markdown',
    'format_structured',
    'format_error_response'
]
