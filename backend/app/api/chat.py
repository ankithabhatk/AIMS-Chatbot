"""Chat Endpoint - RAG-based Query Processing"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging
import time

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.llm.response_generator import get_generator
from app.core.brain import BRAIN
from app.services.database.supabase_client import (
    get_document_store,
    get_chat_log_store
)

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat query request"""
    query: str
    session_id: str
    user_context: Optional[dict] = None


class SourceCitation(BaseModel):
    """Source citation for response"""
    url: str
    heading: str
    snippet: str


class ChatResponse(BaseModel):
    """Chat response with sources"""
    response: str
    confidence_score: float
    sources: List[SourceCitation]
    recommendations: List[str] = []
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
    processing_time_ms: float = 0
    project_phase: Optional[str] = None  # Current project phase from brain


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - RAG Pipeline (FAISS + Supabase)
    
    Flow:
    1. Embed query using sentence-transformers
    2. Search FAISS index for similar chunks (local, fast)
    3. Fetch full documents from Supabase (persistent storage)
    4. Generate response from retrieved context
    5. Log interaction to Supabase
    6. Return with sources and confidence
    """
    start_time = time.time()
    
    try:
        # Validate input
        query = request.query.strip()
        if len(query) < 3:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 3 characters"
            )
        
        logger.info(f"Chat query: {query[:50]}... (session: {request.session_id})")
        
        # 1. Embed query
        query_embedding = embed_text(query)
        
        # 2. Search FAISS index (fast, local)
        index = get_index()
        retrieved_chunks = index.search(query_embedding, k=5)
        
        # 3. Fetch full documents from Supabase
        doc_store = get_document_store()
        sources_data = []
        
        if retrieved_chunks:
            # Extract document IDs from FAISS results
            doc_ids = [chunk[4] if len(chunk) > 4 else None for chunk in retrieved_chunks]
            doc_ids = [d for d in doc_ids if d]  # Filter None values
            
            # Fetch full documents from Supabase
            if doc_ids:
                full_docs = await doc_store.get_documents_by_ids(doc_ids)
                sources_data = full_docs[:3]  # Top 3
        
        if not retrieved_chunks or not sources_data:
            logger.warning(f"No results found for: {query}")
            
            # Log fallback response
            chat_log_store = get_chat_log_store()
            try:
                user_email = request.user_context.get("email") if request.user_context else None
                await chat_log_store.log_chat(
                    query=query,
                    response="I don't have information about that in my knowledge base.",
                    session_id=request.session_id,
                    user_email=user_email,
                    confidence_score=0.0,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    is_fallback=True
                )
            except Exception as log_error:
                logger.error(f"Failed to log fallback: {log_error}")
            
            return ChatResponse(
                response="I don't have information about that in my knowledge base. Please contact admissions@theaims.ac.in",
                confidence_score=0.0,
                sources=[],
                is_fallback=True,
                fallback_reason="no_results_found",
                processing_time_ms=int((time.time() - start_time) * 1000),
                project_phase=BRAIN.get_current_phase()
            )
        
        # 4. Generate response
        generator = get_generator(use_openai=False)
        response_text, confidence, is_fallback = generator.generate(query, retrieved_chunks)
        
        # 5. Build sources from Supabase data
        sources = [
            SourceCitation(
                url=doc.get("url", ""),
                heading=doc.get("heading", ""),
                snippet=doc.get("content", "")[:200]
            )
            for doc in sources_data
        ]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # 6. Log interaction to Supabase
        chat_log_store = get_chat_log_store()
        try:
            user_email = request.user_context.get("email") if request.user_context else None
            await chat_log_store.log_chat(
                query=query,
                response=response_text,
                session_id=request.session_id,
                user_email=user_email,
                confidence_score=confidence,
                processing_time_ms=processing_time,
                is_fallback=is_fallback
            )
        except Exception as log_error:
            logger.error(f"Failed to log chat: {log_error}")
            # Don't fail the response if logging fails
        
        logger.info(f"Response generated. Confidence: {confidence:.2f}, Time: {processing_time}ms")
        
        return ChatResponse(
            response=response_text,
            confidence_score=confidence,
            sources=sources,
            recommendations=[],
            is_fallback=is_fallback,
            processing_time_ms=processing_time,
            project_phase=BRAIN.get_current_phase()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
