"""Pydantic Request/Response Schemas - Production API Spec"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# PHASE 4 API SCHEMAS (Production Grade)
# ============================================================================


class UserInfo(BaseModel):
    """Optional user information for lead capture"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ContextInfo(BaseModel):
    """Optional context information"""
    session_id: Optional[str] = None


class ChatRequest(BaseModel):
    """POST /api/v1/chat - Request body"""
    query: str
    user: Optional[UserInfo] = None
    context: Optional[ContextInfo] = None
    session_id: Optional[str] = None  # legacy fallback for older frontend calls

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the admission process?",
                "user": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+91-9999999999"
                },
                "context": {
                    "session_id": "session-uuid-123"
                }
            }
        }


class SourceCitation(BaseModel):
    """Source citation in response"""
    title: str  # Page title or heading
    url: str    # Source URL


class ChatResponseSuccess(BaseModel):
    """POST /api/v1/chat - Success response"""
    answer: str
    sources: List[SourceCitation]
    confidence: float  # 0.0-1.0
    status: str = "unlock" # "lock" or "unlock"
    intent: str = "factual"
    course: str = "General"
    fallback: bool = False
    suggestions: List[str] = []
    meta: Dict[str, Any] = {}  # Contains response_time_ms, chunks_used, etc.

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Candidates must have completed 12th grade...",
                "sources": [
                    {
                        "title": "Admissions - AIMS",
                        "url": "https://www.theaims.ac.in/admissions"
                    }
                ],
                "confidence": 0.78,
                "fallback": False,
                "suggestions": [
                    "What documents are required?",
                    "What is the eligibility criteria?"
                ],
                "meta": {
                    "response_time_ms": 42,
                    "chunks_used": 4
                }
            }
        }


class ContactInfo(BaseModel):
    """Contact information for fallback"""
    email: str
    phone: Optional[str] = None


class ChatResponseFallback(BaseModel):
    """POST /api/v1/chat - Fallback response"""
    answer: Optional[str] = None
    fallback: bool = True
    status: str = "unlock"
    confidence: float  # Will be low (< 0.45)
    message: str  # Friendly fallback message
    contact: ContactInfo
    suggestions: List[str] = []
    meta: Dict[str, Any] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "answer": None,
                "fallback": True,
                "confidence": 0.32,
                "message": "I couldn't find reliable information. Please contact admissions.",
                "contact": {
                    "email": "admissions@theaims.ac.in",
                    "phone": "+91-XXXXXXXXXX"
                },
                "suggestions": [],
                "meta": {
                    "response_time_ms": 30
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: bool = True
    message: str
    code: int

    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "message": "Invalid query",
                "code": 400
            }
        }


class HealthResponse(BaseModel):
    """GET /api/v1/health - Response"""
    status: str  # "ok", "degraded", "error"
    faiss_loaded: bool
    embedding_model_loaded: bool
    documents_indexed: int
    last_updated: str  # ISO format timestamp


class StatsResponse(BaseModel):
    """GET /api/v1/stats - Response"""
    total_queries: int
    fallback_rate: float  # 0.0-1.0
    avg_confidence: float  # 0.0-1.0
    top_queries: List[str]
    top_fallbacks: List[str] = []
    response_time_avg_ms: float = 0.0


# ============================================================================
# LEGACY SCHEMAS (Kept for backward compatibility if needed)
# ============================================================================


class LeadInputSchema(BaseModel):
    """Schema for lead capture - legacy"""
    session_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    interested_programs: List[str]
    qualification: str
    state: str
    city: Optional[str] = None
    consent_marketing: bool = False


class AnalyticsSchema(BaseModel):
    """Schema for analytics data - legacy"""
    period: str
    chat_stats: dict
    lead_stats: dict
    fallback_rate: float
