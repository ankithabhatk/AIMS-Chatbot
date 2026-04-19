"""Pydantic Request/Response Schemas"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class ChatRequestSchema(BaseModel):
    """Schema for chat requests"""
    query: str
    session_id: str
    user_context: Optional[dict] = None


class SourceSchema(BaseModel):
    """Schema for source citations"""
    url: str
    heading: str
    snippet: str


class ChatResponseSchema(BaseModel):
    """Schema for chat responses"""
    response: str
    confidence_score: float
    sources: List[SourceSchema]
    recommendations: List[str] = []
    is_fallback: bool = False


class LeadInputSchema(BaseModel):
    """Schema for lead capture"""
    session_id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    interested_programs: List[str]
    qualification: str
    state: str
    city: Optional[str] = None
    consent_marketing: bool = False


class AnalyticsSchema(BaseModel):
    """Schema for analytics data"""
    period: str
    chat_stats: dict
    lead_stats: dict
    fallback_rate: float
