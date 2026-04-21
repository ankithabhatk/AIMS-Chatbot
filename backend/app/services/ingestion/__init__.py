"""Ingestion services for external data (PDFs, documents, etc.)"""

from .document_processor import get_document_processor, DocumentProcessor
from .merge_external_data import ExternalDataMerger, IncrementalMergePipeline

__all__ = [
    "get_document_processor",
    "DocumentProcessor",
    "ExternalDataMerger",
    "IncrementalMergePipeline"
]
