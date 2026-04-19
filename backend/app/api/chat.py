"""Chat Endpoint - RAG-based Query Processing"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import logging
import time

from app.services.embeddings.embedding_service import embed_text
from app.services.retrieval.faiss_index import get_index
from app.services.llm.response_generator import get_generator

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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - RAG Pipeline
    
    Flow:
    1. Embed query using sentence-transformers
    2. Search FAISS index for similar chunks
    3. Generate response from top chunks
    4. Return with sources and confidence
    """
    try:
        # Validate input
        query = request.query.strip()
        if len(query) < 3:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 3 characters"
            )
        
        start_time = time.time()
        
        logger.info(f"Chat query: {query[:50]}... (session: {request.session_id})")
        
        # 1. Embed query
        query_embedding = embed_text(query)
        
        # 2. Search FAISS index
        index = get_index()
        retrieved_chunks = index.search(query_embedding, k=5)
        
        if not retrieved_chunks:
            logger.warning(f"No results found for: {query}")
            return ChatResponse(
                response="I don't have information about that in my knowledge base. Please contact admissions@theaims.ac.in",
                confidence_score=0.0,
                sources=[],
                is_fallback=True,
                fallback_reason="no_results_found",
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # 3. Generate response
        generator = get_generator(use_openai=False)  # Use template mode
        response_text, confidence, is_fallback = generator.generate(query, retrieved_chunks)
        
        # 4. Build sources
        sources = [
            SourceCitation(
                url=chunk[2],
                heading=chunk[3],
                snippet=chunk[0][:200]  # First 200 chars
            )
            for chunk in retrieved_chunks[:3]  # Top 3
        ]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"Response generated. Confidence: {confidence:.2f}, Time: {processing_time}ms")
        
        return ChatResponse(
            response=response_text,
            confidence_score=confidence,
            sources=sources,
            recommendations=[],
            is_fallback=is_fallback,
            processing_time_ms=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
