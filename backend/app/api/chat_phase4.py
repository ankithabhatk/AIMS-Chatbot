"""
Chat Endpoint - Production Grade RAG API (Phase 4)

POST /api/v1/chat
- Input: query, user (name/email/phone), context (session_id)
- Output: answer, sources, confidence, fallback flag, suggestions
- Features: Real-time RAG, confidence calibration, fallback safety, analytics logging
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import time
import uuid

from app.models.schemas import (
    ChatRequest, ChatResponseSuccess, ChatResponseFallback, 
    SourceCitation, ContactInfo, ErrorResponse
)
from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.llm.answer_generator import get_answer_generator
from app.services.response.filter import filter_results_by_relevance
from app.services.response.confidence import calculate_confidence
from app.services.logging.query_logger import get_query_logger
from app.services.suggestions.engine import get_suggestion_engine

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)

# Configuration
FALLBACK_THRESHOLD = 0.45  # Calibrated for ~38% answer rate + 75% wrong query rejection
MIN_QUERY_LENGTH = 3
MIN_SCORE_FILTER = 0.3
FAISS_K = 5


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint - Production RAG Pipeline
    
    Request:
        {
            "query": "What is the admission process?",
            "user": {"name": "John", "email": "john@example.com", "phone": "..."},
            "context": {"session_id": "uuid-optional"}
        }
    
    Response (Success):
        {
            "answer": "...",
            "sources": [...],
            "confidence": 0.78,
            "fallback": false,
            "suggestions": [...],
            "meta": {"response_time_ms": 42, "chunks_used": 4}
        }
    
    Response (Fallback):
        {
            "answer": null,
            "fallback": true,
            "confidence": 0.32,
            "message": "I couldn't find...",
            "contact": {"email": "...", "phone": "..."},
            "suggestions": [],
            "meta": {"response_time_ms": 30}
        }
    """
    start_time = time.time()
    session_id = None
    
    try:
        # ================================================================
        # 1. VALIDATE INPUT
        # ================================================================
        query = request.query.strip()
        
        if len(query) < MIN_QUERY_LENGTH:
            logger.warning(f"Query too short: {len(query)} chars")
            return {
                "error": True,
                "message": f"Query must be at least {MIN_QUERY_LENGTH} characters",
                "code": 400
            }
        
        # Extract context
        session_id = None
        if request.context and request.context.session_id:
            session_id = request.context.session_id
        else:
            session_id = str(uuid.uuid4())  # Generate if not provided
        
        user_email = None
        if request.user and request.user.email:
            user_email = request.user.email
        
        logger.info(f"[{session_id}] Query: {query[:60]}...")
        
        # ================================================================
        # 2. EMBED QUERY
        # ================================================================
        try:
            query_embedding = embed_text(query)
            logger.debug(f"[{session_id}] Embedded query (dim={len(query_embedding)})")
        except Exception as e:
            logger.error(f"[{session_id}] Embedding failed: {e}")
            return {
                "error": True,
                "message": "Failed to process query",
                "code": 500
            }
        
        # ================================================================
        # 3. CHECK FAISS INDEX HEALTH
        # ================================================================
        index = get_index()
        stats = index.get_stats()
        logger.info(f"[{session_id}] Index: {stats['document_count']} docs, synced={stats['synced']}")
        
        if not index.validate_integrity():
            logger.error(f"[{session_id}] Index corruption detected")
            # Log as system error and return fallback
            query_logger = get_query_logger()
            query_logger.log_query(
                query=query,
                answer=None,
                confidence=0.0,
                fallback=True,
                response_time_ms=int((time.time() - start_time) * 1000),
                chunks_used=0,
                user_email=user_email,
                session_id=session_id
            )
            
            return _build_fallback_response(
                message="System error. Please try again later.",
                confidence=0.0,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # ================================================================
        # 4. SEARCH FAISS INDEX
        # ================================================================
        try:
            retrieved_chunks = index.search(query_embedding, k=FAISS_K)
            logger.info(f"[{session_id}] Retrieved {len(retrieved_chunks) if retrieved_chunks else 0} chunks")
        except Exception as e:
            logger.error(f"[{session_id}] FAISS search failed: {e}")
            return {
                "error": True,
                "message": "Search failed",
                "code": 500
            }
        
        if not retrieved_chunks:
            logger.warning(f"[{session_id}] No chunks retrieved")
            # Log and return fallback
            query_logger = get_query_logger()
            query_logger.log_query(
                query=query,
                answer=None,
                confidence=0.0,
                fallback=True,
                response_time_ms=int((time.time() - start_time) * 1000),
                chunks_used=0,
                user_email=user_email,
                session_id=session_id
            )
            
            return _build_fallback_response(
                confidence=0.0,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # ================================================================
        # 5. FILTER RESULTS BY RELEVANCE
        # ================================================================
        filtered_chunks = filter_results_by_relevance(retrieved_chunks, min_score=MIN_SCORE_FILTER)
        logger.info(f"[{session_id}] Filtered: {len(retrieved_chunks)} → {len(filtered_chunks)} chunks")
        
        # ================================================================
        # 6. CALCULATE CONFIDENCE
        # ================================================================
        confidence = calculate_confidence(filtered_chunks) if filtered_chunks else 0.0
        logger.info(f"[{session_id}] Confidence: {confidence:.3f}")
        
        # ================================================================
        # 7. CHECK FALLBACK THRESHOLD
        # ================================================================
        is_fallback = confidence < FALLBACK_THRESHOLD
        logger.info(f"[{session_id}] Fallback={is_fallback} (threshold={FALLBACK_THRESHOLD})")
        
        if is_fallback:
            logger.warning(f"[{session_id}] Low confidence fallback ({confidence:.3f})")
            
            # Log fallback
            query_logger = get_query_logger()
            query_logger.log_query(
                query=query,
                answer=None,
                confidence=confidence,
                fallback=True,
                response_time_ms=int((time.time() - start_time) * 1000),
                chunks_used=0,
                user_email=user_email,
                session_id=session_id
            )
            
            return _build_fallback_response(
                confidence=confidence,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # ================================================================
        # 8. SYNTHESIZE ANSWER
        # ================================================================
        answer_gen = get_answer_generator()
        answer = answer_gen.synthesize(query, filtered_chunks)
        
        if not answer or answer.strip() == "":
            logger.warning(f"[{session_id}] Empty answer after synthesis")
            
            # Log as fallback
            query_logger = get_query_logger()
            query_logger.log_query(
                query=query,
                answer=None,
                confidence=confidence,
                fallback=True,
                response_time_ms=int((time.time() - start_time) * 1000),
                chunks_used=len(filtered_chunks),
                user_email=user_email,
                session_id=session_id
            )
            
            return _build_fallback_response(
                confidence=confidence,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
        
        logger.info(f"[{session_id}] Generated answer ({len(answer)} chars)")
        
        # ================================================================
        # 9. BUILD SOURCES
        # ================================================================
        sources = _build_sources(filtered_chunks)
        logger.debug(f"[{session_id}] Built {len(sources)} sources")
        
        # ================================================================
        # 10. GENERATE SUGGESTIONS
        # ================================================================
        suggestion_engine = get_suggestion_engine()
        suggestions = suggestion_engine.generate(query, fallback=False)
        logger.debug(f"[{session_id}] Generated {len(suggestions)} suggestions")
        
        # ================================================================
        # 11. LOG SUCCESSFUL RESPONSE
        # ================================================================
        response_time_ms = int((time.time() - start_time) * 1000)
        
        query_logger = get_query_logger()
        query_logger.log_query(
            query=query,
            answer=answer,
            confidence=confidence,
            fallback=False,
            response_time_ms=response_time_ms,
            chunks_used=len(filtered_chunks),
            user_email=user_email,
            session_id=session_id,
            sources=sources
        )
        
        logger.info(f"[{session_id}] ✅ Response sent in {response_time_ms}ms")
        
        # ================================================================
        # 12. BUILD SUCCESS RESPONSE
        # ================================================================
        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 3),
            "fallback": False,
            "suggestions": suggestions,
            "meta": {
                "response_time_ms": response_time_ms,
                "chunks_used": len(filtered_chunks),
                "session_id": session_id
            }
        }
    
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error: {e}", exc_info=True)
        return {
            "error": True,
            "message": "Internal server error",
            "code": 500
        }


def _build_fallback_response(message: str = None,
                             confidence: float = 0.0,
                             response_time_ms: int = 0) -> dict:
    """Build standardized fallback response"""
    if message is None:
        message = "I couldn't find reliable information about that in my knowledge base. Please contact admissions for help."
    
    return {
        "answer": None,
        "fallback": True,
        "confidence": round(confidence, 3),
        "message": message,
        "contact": {
            "email": "admissions@theaims.ac.in",
            "phone": "+91-XXXXXXXXXX"  # To be filled in from config
        },
        "suggestions": [],
        "meta": {
            "response_time_ms": response_time_ms
        }
    }


def _build_sources(chunks: list) -> list:
    """Extract and build source citations from chunks"""
    sources = []
    seen_urls = set()  # Avoid duplicates
    
    for chunk in chunks[:3]:  # Top 3 sources
        if len(chunk) < 4:
            continue
        
        text, score, url, heading = chunk[0], chunk[1], chunk[2], chunk[3]
        
        # Skip if URL already added
        if url in seen_urls:
            continue
        
        sources.append({
            "title": heading or "AIMS Resource",
            "url": url or "https://www.theaims.ac.in"
        })
        seen_urls.add(url)
    
    return sources
