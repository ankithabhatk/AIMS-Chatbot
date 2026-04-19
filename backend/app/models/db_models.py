"""Database Models using SQLAlchemy"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Document(Base):
    """Document model - scraped web pages"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    url = Column(String, unique=True, index=True)
    title = Column(String)
    content = Column(Text)
    content_hash = Column(String, index=True)  # For change detection
    scraped_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="active")  # active, archived, error
    error_count = Column(Integer, default=0)
    metadata = Column(JSON)


class Chunk(Base):
    """Chunk model - document chunks for embeddings"""
    __tablename__ = "chunks"
    
    id = Column(String, primary_key=True)
    document_id = Column(String, index=True)
    content = Column(Text)
    chunk_index = Column(Integer)
    tokens = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)


class Embedding(Base):
    """Embedding model - vector embeddings"""
    __tablename__ = "embeddings"
    __table_args__ = (
        Index('idx_chunk_id', 'chunk_id'),
    )
    
    id = Column(String, primary_key=True)
    chunk_id = Column(String, index=True)
    embedding = Column(String)  # Stored as string, cast to vector with pgvector
    model = Column(String, default="text-embedding-3-small")
    dim = Column(Integer, default=1536)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatEvent(Base):
    """Chat event model - query/response logging"""
    __tablename__ = "chat_events"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    query = Column(Text)
    response = Column(Text)
    confidence_score = Column(Float)
    is_fallback = Column(Boolean, default=False)
    fallback_reason = Column(String, nullable=True)
    sources = Column(JSON)
    tokens_used = Column(Integer)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_feedback = Column(String, nullable=True)  # helpful, unhelpful, etc.


class Lead(Base):
    """Lead model - student information"""
    __tablename__ = "leads"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    interested_programs = Column(JSON)
    qualification = Column(String)
    state = Column(String)
    city = Column(String, nullable=True)
    lead_score = Column(Float, default=0.0)
    consent_marketing = Column(Boolean, default=False)
    salesforce_id = Column(String, nullable=True, index=True)
    salesforce_status = Column(String, default="pending")  # pending, synced, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    synced_at = Column(DateTime, nullable=True)
    metadata = Column(JSON)


class CacheEntry(Base):
    """Cache model - for query/embedding caching"""
    __tablename__ = "cache_entries"
    
    id = Column(String, primary_key=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    ttl = Column(Integer)  # Time to live in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
