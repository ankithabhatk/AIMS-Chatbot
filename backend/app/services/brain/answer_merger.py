"""
Answer Merger - Intelligently combines structured and RAG answers.

Strategy:
- If both available: structured + RAG (best of both)
- If only structured: return structured (verified data)
- If only RAG: return RAG (synthesized)
- If neither: fallback
"""

import logging

logger = logging.getLogger(__name__)

def merge_answers(
    structured_answer: str = None, 
    rag_answer: str = None
) -> str:
    """
    Merge structured (verified) and RAG (retrieved) answers intelligently.
    
    Args:
        structured_answer: Answer from structured knowledge base
        rag_answer: Answer synthesized from RAG retrieval
        
    Returns:
        Merged answer or fallback
    """
    # Case 1: Both available - merge them
    if structured_answer and rag_answer:
        merged = f"{structured_answer}\n\n{rag_answer}"
        logger.info(f"[MERGER] Using hybrid answer (structured + rag)")
        return merged
    
    # Case 2: Only structured
    if structured_answer:
        logger.info(f"[MERGER] Using structured answer only")
        return structured_answer
    
    # Case 3: Only RAG
    if rag_answer:
        logger.info(f"[MERGER] Using RAG answer only")
        return rag_answer
    
    # Case 4: Neither (should be caught earlier but failsafe)
    logger.warning(f"[MERGER] No answer available, using fallback")
    return None
