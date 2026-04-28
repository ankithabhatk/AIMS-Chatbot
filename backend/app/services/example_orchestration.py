"""
WORKING EXAMPLE - Complete orchestration with all 3 optimizations integrated

This is NOT a replacement for your engine.py - it's a reference implementation
showing how everything fits together. Copy the pattern, not the entire function.
"""

import time
import logging
from typing import Dict, Any, List, Optional

# Imports needed
from app.services.structured_knowledge import get_structured_response
from app.services.retrieval.faiss_index import get_index
from app.services.response_debate import debate_gate, run_debate, is_reasoning_query
from app.services.response_transformer import format_response_for_ui, transform_to_card
from app.services.query_router import (
    select_execution_path,
    optimize_retrieval_config,
    should_skip_layer,
    log_execution_metrics
)

logger = logging.getLogger(__name__)


def execute_orchestration_optimized(
    query: str,
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    🚀 OPTIMIZED ORCHESTRATION with debate + UI cards + latency control
    
    This integrates all 3 modules:
    1. Query router for latency optimization
    2. Debate system for intelligent decisions
    3. UI transformer for card-based responses
    """
    
    # TIME TRACKING
    start_time = time.time()
    
    # ============ STEP 1: EARLY RETURNS (FAST PATH) ============
    
    # Check structured KB first (fastest)
    structured_response = get_structured_response(query)
    if structured_response and structured_response.get("answer"):
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"[FAST_PATH] Structured hit in {latency_ms:.0f}ms")
        
        # Transform for UI immediately
        return format_response_for_ui(
            answer=structured_response["answer"],
            confidence=0.95,
            intent="structured",
            query=query,
            mode="structured",
            suggestions=structured_response.get("suggestions", [])
        )
    
    # ============ STEP 2: SELECT EXECUTION PATH ============
    
    exec_config = select_execution_path(query, base_confidence=0.7, mode="rag")
    logger.info(f"[ROUTER] Selected path: {exec_config['path']}")
    
    # ============ STEP 3: OPTIMIZED RAG RETRIEVAL ============
    
    retrieval_config = optimize_retrieval_config(query, base_confidence=0.7)
    rag_chunks = []
    
    if not retrieved_chunks:
        try:
            index = get_index()
            if index and index.validate_integrity():
                # Use optimized top_k based on query complexity
                rag_chunks = index.keyword_search(
                    query,
                    k=retrieval_config["top_k"]
                )
                logger.debug(f"[RAG] Retrieved {len(rag_chunks)} chunks (k={retrieval_config['top_k']})")
        except Exception as e:
            logger.warning(f"[RAG] Retrieval failed: {e}")
            rag_chunks = []
    else:
        rag_chunks = retrieved_chunks
    
    # ============ STEP 4: CHECK DATA QUALITY ============
    
    def has_meaningful_chunks(chunks, min_score=0.3):
        """Check if chunks have sufficient quality"""
        if not chunks:
            return False
        for c in chunks:
            text = c[0] if isinstance(c, tuple) else c.get("content", "")
            score = c[1] if isinstance(c, tuple) else c.get("score", 0.0)
            if len(text.strip()) > 50 and score >= min_score:
                return True
        return False
    
    if has_meaningful_chunks(rag_chunks, min_score=retrieval_config.get("min_score", 0.35)):
        
        # ============ STEP 5: GENERATE ANSWER ============
        
        def format_rag_response_with_style(chunks, style="balanced"):
            """Generate answer with optional style variation"""
            # Your existing format_rag_response logic
            answer = "Based on retrieved data:\n"
            for chunk in chunks[:3]:
                text = chunk[0] if isinstance(chunk, tuple) else chunk.get("content", "")
                if text:
                    answer += f"• {text[:200]}\n"
            
            # Apply style
            if style == "critical":
                answer = "⚠️ Note: " + answer
            elif style == "optimistic":
                answer = "✓ Positive aspects: " + answer
            
            return answer
        
        initial_answer = format_rag_response_with_style(rag_chunks, style="balanced")
        initial_confidence = 0.7
        
        # ============ STEP 6: OPTIONAL DEBATE (EXPENSIVE LAYER) ============
        
        if exec_config["use_debate"]:
            logger.info("[DEBATE] Running multi-candidate debate...")
            
            final_answer, final_confidence, winning_style = run_debate(
                query=query,
                chunks=rag_chunks,
                generate_answer_fn=format_rag_response_with_style,
                base_confidence=initial_confidence
            )
        else:
            final_answer = initial_answer
            final_confidence = initial_confidence
            logger.debug("[DEBATE] Skipped (high confidence or simple query)")
        
        # ============ STEP 7: OPTIONAL VERIFICATION ============
        
        if exec_config["use_verification"] and not should_skip_layer("verification", final_confidence):
            logger.debug("[VERIFICATION] Checking answer grounding...")
            # Simple verification: check if answer mentions key data
            chunk_text = " ".join([c[0] if isinstance(c, tuple) else c.get("content", "") for c in rag_chunks])
            
            # If answer has specific numbers, verify they're in chunks
            import re
            numbers = re.findall(r'₹[\d,]+|\d+%', final_answer)
            verified = 0
            for num in numbers:
                if num in chunk_text:
                    verified += 1
            
            if numbers and verified / len(numbers) < 0.5:
                logger.warning("[VERIFICATION] Answer not well-grounded, using safer version")
                final_answer = initial_answer
                final_confidence = 0.6
        
        # ============ STEP 8: TRANSFORM TO UI CARD ============
        
        ui_response = format_response_for_ui(
            answer=final_answer,
            confidence=final_confidence,
            intent="rag",
            query=query,
            mode="rag",
            suggestions=["Learn more", "Other courses", "Fees structure"]
        )
        
        latency_ms = (time.time() - start_time) * 1000
        log_execution_metrics(query, exec_config, latency_ms)
        
        return ui_response
    
    # ============ STEP 9: FALLBACK (ONLY IF NO DATA) ============
    
    logger.info("[FALLBACK] No data found, using fallback response")
    
    fallback_answer = (
        "I can help you with information about AIMS programs, fees, admission, "
        "placements, and campus facilities. What would you like to know?"
    )
    
    latency_ms = (time.time() - start_time) * 1000
    log_execution_metrics(query, exec_config, latency_ms)
    
    return format_response_for_ui(
        answer=fallback_answer,
        confidence=0.3,
        intent="fallback",
        query=query,
        mode="fallback",
        suggestions=["MBA fees", "BCA admission", "Placements", "Hostel facilities"]
    )


# ============ EXAMPLE USAGE ============

if __name__ == "__main__":
    # Test queries
    test_queries = [
        ("MBA fees", "Fast path - direct answer"),
        ("placements", "RAG path - transform to placement_card"),
        ("Is MBA worth it?", "Deep path - debate runs"),
        ("Compare MBA and BBA", "Deep path - comparison debate"),
    ]
    
    for query, description in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Expected: {description}")
        print(f"{'='*60}")
        
        response = execute_orchestration_optimized(query)
        
        print(f"Response type: {response['message']['type']}")
        print(f"Confidence: {response['meta']['confidence']:.2f}")
        print(f"Mode: {response['meta']['mode']}")
        print(f"Answer preview: {str(response['message']).split('raw_text')[0][:200]}...")
