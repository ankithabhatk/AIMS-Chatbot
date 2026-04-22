"""
Supabase Database Client

Handles all database operations:
- Document storage
- Lead capture
- Chat logs
- Analytics

Uses Supabase (PostgreSQL) for persistent storage.
FAISS remains local for fast vector search.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

import supabase
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase database client"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client (singleton)"""
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL", "")
            # Accept either key name (service role preferred for backend writes)
            key = (
                os.getenv("SUPABASE_SERVICE_ROLE_KEY") or
                os.getenv("SUPABASE_ANON_KEY") or
                ""
            )
            
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
            
            try:
                cls._instance = create_client(url, key)
                logger.info("✅ Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                raise
        
        return cls._instance


class DocumentStore:
    """Handle document storage and retrieval"""
    
    TABLE_NAME = "documents"
    
    def __init__(self):
        self.client = SupabaseClient.get_client()
    
    async def store_document(
        self,
        content: str,
        url: str,
        heading: str,
        chunk_index: int = 0,
        source: str = "website"
    ) -> Dict[str, Any]:
        """Store a document chunk in Supabase"""
        try:
            doc_id = str(uuid4())
            
            data = {
                "id": doc_id,
                "content": content,
                "url": url,
                "heading": heading,
                "chunk_index": chunk_index,
                "source": source,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table(self.TABLE_NAME).insert(data).execute()
            logger.info(f"Stored document: {doc_id}")
            return response.data[0] if response.data else data
        
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document by ID"""
        try:
            response = self.client.table(self.TABLE_NAME).select("*").eq("id", doc_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    async def get_documents_by_ids(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieve multiple documents by IDs"""
        try:
            response = self.client.table(self.TABLE_NAME).select("*").in_("id", doc_ids).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []
    
    async def get_all_documents(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all documents (for indexing)"""
        try:
            response = self.client.table(self.TABLE_NAME).select("*").limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to get all documents: {e}")
            return []
    
    async def count_documents(self) -> int:
        """Count total documents"""
        try:
            response = self.client.table(self.TABLE_NAME).select("id", count="exact").execute()
            return response.count if hasattr(response, 'count') else 0
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0


class LeadStore:
    """Handle lead capture and management"""
    
    TABLE_NAME = "leads"
    
    def __init__(self):
        self.client = SupabaseClient.get_client()
    
    async def create_lead(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        interest: Optional[str] = None,
        source: str = "chatbot"
    ) -> Dict[str, Any]:
        """Create a new lead"""
        try:
            lead_id = str(uuid4())
            
            data = {
                "id": lead_id,
                "name": name,
                "email": email,
                "phone": phone,
                "interest": interest,
                "source": source,
                "lead_score": 0.5,  # Initial score
                "status": "new",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table(self.TABLE_NAME).insert(data).execute()
            logger.info(f"Created lead: {lead_id}")
            return response.data[0] if response.data else data
        
        except Exception as e:
            logger.error(f"Failed to create lead: {e}")
            raise
    
    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead by ID"""
        try:
            response = self.client.table(self.TABLE_NAME).select("*").eq("id", lead_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get lead: {e}")
            return None
    
    async def get_leads_by_email(self, email: str) -> List[Dict[str, Any]]:
        """Check if email exists (deduplication)"""
        try:
            response = self.client.table(self.TABLE_NAME).select("*").eq("email", email).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to get leads: {e}")
            return []
    
    async def update_lead(self, lead_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update lead information"""
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            response = self.client.table(self.TABLE_NAME).update(updates).eq("id", lead_id).execute()
            logger.info(f"Updated lead: {lead_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update lead: {e}")
            raise


class ChatLogStore:
    """Handle chat message logging and analytics"""
    
    TABLE_NAME = "chat_logs"
    
    def __init__(self):
        self.client = SupabaseClient.get_client()
    
    async def log_chat(
        self,
        query: str,
        response: str,
        session_id: str,
        confidence_score: float,
        processing_time_ms: int,
        is_fallback: bool = False,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Log a chat interaction for analytics"""
        try:
            log_id = str(uuid4())
            
            data = {
                "id": log_id,
                "query": query,
                "response": response,
                "session_id": session_id,
                "user_email": user_email,
                "confidence_score": confidence_score,
                "processing_time_ms": processing_time_ms,
                "is_fallback": is_fallback,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table(self.TABLE_NAME).insert(data).execute()
            logger.debug(f"Logged chat: {log_id}")
            return response.data[0] if response.data else data
        
        except Exception as e:
            logger.error(f"Failed to log chat: {e}")
            # Don't raise - logging shouldn't break the chat endpoint
            return {}
    
    async def get_chat_logs(
        self,
        session_id: Optional[str] = None,
        user_email: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve chat logs for analytics"""
        try:
            query = self.client.table(self.TABLE_NAME).select("*")
            
            if session_id:
                query = query.eq("session_id", session_id)
            if user_email:
                query = query.eq("user_email", user_email)
            
            response = query.limit(limit).order("created_at", desc=True).execute()
            return response.data if response.data else []
        
        except Exception as e:
            logger.error(f"Failed to get chat logs: {e}")
            return []


# Singleton instances
_documents = None
_leads = None
_chat_logs = None


def get_document_store() -> DocumentStore:
    """Get document store singleton"""
    global _documents
    if _documents is None:
        _documents = DocumentStore()
    return _documents


def get_lead_store() -> LeadStore:
    """Get lead store singleton"""
    global _leads
    if _leads is None:
        _leads = LeadStore()
    return _leads


def get_chat_log_store() -> ChatLogStore:
    """Get chat log store singleton"""
    global _chat_logs
    if _chat_logs is None:
        _chat_logs = ChatLogStore()
    return _chat_logs
