"""Chat Endpoint - RAG-based Query Processing with Answer Synthesis"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging
import time

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.llm.answer_generator import get_answer_generator
from app.services.response.filter import filter_results_by_relevance
from app.services.response.confidence import calculate_confidence, get_confidence_label
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
    2. Validate FAISS index integrity
    3. Search FAISS index for similar chunks (local, fast)
    4. Filter results by relevance (remove low-quality matches)
    5. Calculate confidence score
    6. Check fallback threshold (0.4)
    7. Synthesize answer from filtered chunks
    8. Fetch full documents from Supabase for sources
    9. Log interaction and return response
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
        
        # 2. Check index integrity FIRST
        index = get_index()
        stats = index.get_stats()
        logger.info(f"Index stats: {stats}")
        
        if not index.validate_integrity():
            logger.error("Index corruption detected - returning fallback")
            return ChatResponse(
                response="System error: Please try again later.",
                confidence_score=0.0,
                sources=[],
                is_fallback=True,
                fallback_reason="system_error",
                processing_time_ms=int((time.time() - start_time) * 1000),
                project_phase=BRAIN.get_current_phase()
            )
        
        # 3. Search FAISS index (fast, local)
        retrieved_chunks = index.search(query_embedding, k=5)
        logger.info(f"Retrieved {len(retrieved_chunks) if retrieved_chunks else 0} chunks from FAISS")
        
        # 3. Filter results by relevance (remove low-quality matches)
        if retrieved_chunks:
            filtered_chunks = filter_results_by_relevance(retrieved_chunks, min_score=0.3)
            logger.info(f"Filtered: {len(retrieved_chunks)} → {len(filtered_chunks)} chunks")
        else:
            filtered_chunks = []
            logger.warning("No chunks retrieved from FAISS")
        
        # 4. Calculate confidence score from filtered results
        confidence = calculate_confidence(filtered_chunks) if filtered_chunks else 0.0
        confidence_label = get_confidence_label(confidence)
        logger.info(f"Confidence: {confidence:.2f} ({confidence_label})")
        
        # 5. Check if we should return fallback
        # CALIBRATED: 0.45 threshold allows good queries (0.48+) through
        # while catching wrong queries (< 0.35)
        # - Good queries (0.53+ scores) → confidence 0.48+ → answer
        # - Bad queries (< 0.45 scores) → confidence 0.0-0.35 → fallback
        # - Wrong queries (0.48 scores) → confidence 0.48 → answer (acceptable)
        fallback_threshold = 0.45
        is_fallback = confidence < fallback_threshold or not filtered_chunks
        
        # 6. Fetch full documents from Supabase for sources
        doc_store = get_document_store()
        sources_data = []
        
        if filtered_chunks:
            # Extract document IDs from FAISS results
            doc_ids = [chunk[4] if len(chunk) > 4 else None for chunk in filtered_chunks]
            doc_ids = [d for d in doc_ids if d]  # Filter None values
            logger.debug(f"Document IDs from chunks: {doc_ids}")
            
            # Fetch full documents from Supabase
            if doc_ids:
                full_docs = await doc_store.get_documents_by_ids(doc_ids)
                sources_data = full_docs[:3]  # Top 3
                logger.info(f"Fetched {len(sources_data)} full documents from Supabase")
        
        if is_fallback:
            logger.warning(f"Low confidence ({confidence:.2f} < {fallback_threshold}) - returning fallback")
            
            fallback_text = (
                "I don't have information about that in my knowledge base. "
                "Please contact admissions@theaims.ac.in for more details."
            )
            
            # Log fallback response
            chat_log_store = get_chat_log_store()
            try:
                user_email = request.user_context.get("email") if request.user_context else None
                await chat_log_store.log_chat(
                    query=query,
                    response=fallback_text,
                    session_id=request.session_id,
                    user_email=user_email,
                    confidence_score=confidence,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    is_fallback=True
                )
            except Exception as log_error:
                logger.error(f"Failed to log fallback: {log_error}")
            
            return ChatResponse(
                response=fallback_text,
                confidence_score=confidence,
                sources=[],
                is_fallback=True,
                fallback_reason=f"low_confidence_{confidence_label}",
                processing_time_ms=int((time.time() - start_time) * 1000),
                project_phase=BRAIN.get_current_phase()
            )
        
        # 7. Generate synthesized answer from filtered chunks
        answer_gen = get_answer_generator()
        response_text = answer_gen.synthesize(query, filtered_chunks)
        
        # 8. Build sources from Supabase data
        sources = [
            SourceCitation(
                url=doc.get("url", ""),
                heading=doc.get("heading", ""),
                snippet=doc.get("content", "")[:200]
            )
            for doc in sources_data
        ]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # 9. Log interaction to Supabase
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
                is_fallback=False
            )
        except Exception as log_error:
            logger.error(f"Failed to log chat: {log_error}")
            # Don't fail the response if logging fails
        
        logger.info(f"Response generated. Confidence: {confidence:.2f} ({confidence_label}), Time: {processing_time}ms")
        
        return ChatResponse(
            response=response_text,
            confidence_score=confidence,
            sources=sources,
            recommendations=[],
            is_fallback=False,
            processing_time_ms=processing_time,
            project_phase=BRAIN.get_current_phase()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
