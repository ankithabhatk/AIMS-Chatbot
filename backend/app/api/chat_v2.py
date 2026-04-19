"""
Phase 2: Retrieval Engine - Chat Endpoint with FAISS Integration

Flow:
1. Load FAISS index at startup
2. Embed user query
3. Search FAISS for relevant chunks
4. Return structured response with sources
5. Fallback logic for low confidence
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import time
import json
import os

from app.services.embeddings.embed_pipeline import EmbeddingPipeline
from app.services.retrieval.faiss_builder import FAISSIndexBuilder

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)


# ============================================================================
# GLOBALS - Loaded at startup
# ============================================================================

faiss_index: Optional[FAISSIndexBuilder] = None
embedding_pipeline: Optional[EmbeddingPipeline] = None
chunks_data: dict = {}  # {chunk_id: {content, url, heading, tokens}}


def initialize_retrieval():
    """Load FAISS index and embeddings at app startup"""
    global faiss_index, embedding_pipeline, chunks_data
    
    logger.info("Initializing retrieval engine...")
    
    # Load FAISS index
    faiss_index = FAISSIndexBuilder()
    if not faiss_index.load():
        logger.warning("FAISS index not found. System will have no knowledge base.")
        faiss_index = None
    else:
        logger.info(f"✓ FAISS index loaded ({faiss_index.index.ntotal} vectors)")
    
    # Load embedding pipeline
    embedding_pipeline = EmbeddingPipeline()
    logger.info("✓ Embedding pipeline ready")
    
    # Load chunks from checkpoint if available
    chunks_file = "/tmp/chatbot_ingest/chunks.json"
    if os.path.exists(chunks_file):
        try:
            with open(chunks_file, 'r') as f:
                chunks_list = json.load(f)
                for chunk in chunks_list:
                    chunk_id = f"{chunk['url']}#{chunk['chunk_index']}"
                    chunks_data[chunk_id] = chunk
            logger.info(f"✓ Loaded {len(chunks_data)} chunks from checkpoint")
        except Exception as e:
            logger.warning(f"Could not load chunks checkpoint: {e}")


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """User query request"""
    query: str
    session_id: Optional[str] = None
    k: int = 5  # Number of results to retrieve


class SourceInfo(BaseModel):
    """Source citation with snippet"""
    url: str
    heading: str
    chunk_index: int
    snippet: str
    relevance_score: float


class ChatResponse(BaseModel):
    """Structured response with sources"""
    answer: str
    sources: List[SourceInfo]
    is_fallback: bool
    fallback_reason: Optional[str] = None
    confidence: float
    chunks_found: int
    processing_time_ms: int


# ============================================================================
# Utility Functions
# ============================================================================

def _clean_snippet(text: str, max_chars: int = 300) -> str:
    """Clean and trim snippet for display"""
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(' ', 1)[0] + "..."
    return text


def _calculate_confidence(num_results: int, avg_distance: float) -> float:
    """
    Calculate confidence score based on:
    - Number of relevant results found
    - Average distance in vector space (0 = exact match, higher = less similar)
    """
    if num_results == 0:
        return 0.0
    
    # More results = higher confidence
    result_score = min(num_results / 5.0, 1.0)  # Max at 5 results
    
    # Lower distance = higher confidence
    # Distance typically 0-2 for meaningful matches
    distance_score = max(0, 1 - (avg_distance / 2.0))
    
    # Combined: 60% results, 40% distance
    confidence = (0.6 * result_score) + (0.4 * distance_score)
    
    return round(min(confidence, 1.0), 2)


def _format_answer(sources: List[SourceInfo], query: str) -> str:
    """
    Format answer from retrieved chunks
    
    Strategy (without LLM):
    1. Extract key sentences from top chunk
    2. Add context from other chunks if available
    3. Include source attribution
    """
    if not sources:
        return "I don't have information about that in my knowledge base."
    
    # Build answer from top chunk
    top_source = sources[0]
    answer = f"{_clean_snippet(top_source.snippet, 400)}"
    
    # Add reference
    if len(sources) > 1:
        answer += f"\n\n(Additional relevant content available from {len(sources)} sources)"
    
    return answer


# ============================================================================
# Main Chat Endpoint
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Retrieve relevant information from FAIMS knowledge base
    
    Process:
    1. Validate query
    2. Embed query
    3. Search FAISS
    4. Format response
    5. Apply fallback logic
    """
    start_time = time.time()
    
    # Step 1: Validate input
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if len(query) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")
    
    logger.info(f"Chat query: {query[:60]}...")
    
    # Step 2: Check if retrieval is available
    if not faiss_index or faiss_index.index.ntotal == 0:
        logger.warning("FAISS index not available")
        return ChatResponse(
            answer="The knowledge base is not initialized. Please try again later.",
            sources=[],
            is_fallback=True,
            fallback_reason="knowledge_base_not_ready",
            confidence=0.0,
            chunks_found=0,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
    
    try:
        # Step 3: Embed query
        query_embedding = embedding_pipeline.embed_text(query)
        
        # Step 4: Search FAISS
        search_results = faiss_index.search(query_embedding, k=min(request.k, 5))
        
        if not search_results:
            logger.warning(f"No results found for: {query}")
            return ChatResponse(
                answer="I don't have information about that in my knowledge base. Please contact admissions@theaims.ac.in for more information.",
                sources=[],
                is_fallback=True,
                fallback_reason="no_results_found",
                confidence=0.0,
                chunks_found=0,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # Step 5: Convert results to sources
        sources = []
        distances = []
        
        for result in search_results:
            distance = result['distance']
            distances.append(distance)
            url = result['url']
            heading = result['heading']
            chunk_index = result['chunk_index']
            
            # Get full chunk content
            chunk_id = f"{url}#{chunk_index}"
            chunk_data = chunks_data.get(chunk_id, {})
            snippet = chunk_data.get('content', '')
            
            # Calculate relevance for this result
            relevance = result['similarity_score']
            
            source = SourceInfo(
                url=url,
                heading=heading,
                chunk_index=chunk_index,
                snippet=_clean_snippet(snippet),
                relevance_score=round(relevance, 2)
            )
            sources.append(source)
        
        # Step 6: Calculate confidence
        avg_distance = sum(distances) / len(distances) if distances else 0
        confidence = _calculate_confidence(len(sources), avg_distance)
        
        # Step 7: Format answer
        answer = _format_answer(sources, query)
        
        # Step 8: Apply fallback logic (low confidence threshold)
        is_fallback = False
        fallback_reason = None
        
        if confidence < 0.3:
            logger.info(f"Low confidence score: {confidence}. Using fallback.")
            is_fallback = True
            fallback_reason = "low_confidence"
            answer = "I found some information but I'm not very confident. " + answer
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"✓ Response: {len(sources)} sources, confidence={confidence}, time={processing_time}ms")
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            confidence=confidence,
            chunks_found=len(sources),
            processing_time_ms=processing_time
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/health")
async def health_check():
    """Check if retrieval engine is ready"""
    
    if not faiss_index or faiss_index.index.ntotal == 0:
        return {
            "status": "degraded",
            "message": "Knowledge base not loaded",
            "faiss_vectors": 0,
            "chunks_loaded": len(chunks_data)
        }
    
    return {
        "status": "healthy",
        "message": "Retrieval engine ready",
        "faiss_vectors": faiss_index.index.ntotal,
        "chunks_loaded": len(chunks_data)
    }


@router.get("/stats")
async def retrieval_stats():
    """Get retrieval system statistics"""
    
    return {
        "faiss_index": {
            "vectors": faiss_index.index.ntotal if faiss_index else 0,
            "dimension": faiss_index.dimension if faiss_index else 0,
            "path": faiss_index.index_path if faiss_index else None
        },
        "chunks": {
            "total": len(chunks_data),
            "sources": len(set(c['url'] for c in chunks_data.values())) if chunks_data else 0
        },
        "embedding_model": "all-MiniLM-L6-v2"
    }
