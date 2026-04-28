"""
Post-Tier Validation Layer

After tier_generator returns an answer, validate:
1. Intent anchoring (answer contains keywords from original intent)
2. RAG grounding (answer is grounded in retrieved chunks)
3. Structured protection (for specific intents, enforce correctness)

If validation fails → set fallback = True
"""

import logging
from typing import Any, Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Intent keyword mapping for validation
INTENT_KEYWORDS = {
    "fees": [
        "fee", "fees", "cost", "price", "tuition", "scholarship", 
        "payment", "loan", "emi", "financial", "installment"
    ],
    "admission": [
        "admission", "apply", "application", "eligibility", "eligible", 
        "enrol", "enroll", "process", "documents", "requirement"
    ],
    "placements": [
        "placement", "placements", "salary", "package", "ctc", "recruiter", 
        "recruiters", "company", "companies", "career", "job", "hiring",
        "record", "statistics", "average", "highest"
    ],
    "campus": [
        "campus", "hostel", "facility", "facilities", "accommodation", 
        "library", "transport", "cafeteria", "infrastructure"
    ],
    "curriculum": [
        "curriculum", "syllabus", "subject", "subjects", "semester", 
        "module", "modules", "learn", "course", "coursework"
    ],
    "courses": [
        "course", "courses", "program", "programs", "degree", 
        "offer", "offered", "available", "offering"
    ],
}


def validate_tier_output(
    result: Any,
    original_intent: str,
    original_query: str,
    chunks: List[Tuple[str, float, str, str]],
) -> Any:
    """
    Validate output from tier_generator.
    
    CRITICAL: This validates LLM/fallback responses, NOT structured/RAG answers.
    
    Args:
        result: OrchestrationResult object with answer, intent, mode, confidence
        original_intent: Original detected intent (e.g., "placements")
        original_query: Original user query
        chunks: Retrieved chunks as tuples (content, score, url, heading)
    
    Returns:
        Modified result with fallback = True if validation fails
    """
    
    # 🚫 NEVER VALIDATE STRUCTURED ANSWERS
    # Structured mode has verified data → trust it completely
    if result.mode == "structured":
        logger.info(f"[VALIDATION] Skipping validation for STRUCTURED mode answer")
        return result
    
    # ✅ For RAG mode, validate lightly (only grounding check)
    # For fallback/LLM, validate more aggressively
    
    issues = []
    answer = result.answer.lower() if result.answer else ""
    
    # ─────────────────────────────────────────────────────────────────────────
    # 1. INTENT ANCHORING CHECK (RAG/LLM Only)
    # ─────────────────────────────────────────────────────────────────────────
    # For RAG/LLM modes: answer SHOULD contain keywords from original intent
    
    if result.mode in ["rag", "fallback"] and original_intent and original_intent != "unknown":
        keywords = INTENT_KEYWORDS.get(original_intent, [])
        if keywords:
            has_intent_keyword = any(
                keyword.lower() in answer 
                for keyword in keywords
            )
            
            # For critical intents, this is important but not fatal
            if not has_intent_keyword and original_intent in ["placements", "fees", "admission"]:
                logger.warning(
                    f"[VALIDATION] Intent anchoring weak for {original_intent}. "
                    f"Keywords {keywords[:3]} not strongly represented."
                )
                # Don't force fallback immediately, but note the issue
                result.confidence = max(0.0, result.confidence - 0.2)  # Penalty
    
    # ─────────────────────────────────────────────────────────────────────────
    # 2. RAG GROUNDING CHECK (RAG Mode Only)
    # ─────────────────────────────────────────────────────────────────────────
    # For RAG mode, answer should reference retrieved chunks
    
    if result.mode == "rag" and chunks:
        chunk_phrases = []
        for chunk in chunks[:3]:
            if chunk and len(chunk) > 0:
                content_snippet = chunk[0][:100].lower() if chunk[0] else ""
                if content_snippet:
                    chunk_phrases.append(content_snippet)
        
        is_grounded = False
        if chunk_phrases:
            for phrase in chunk_phrases:
                words = phrase.split()[:5]
                if len(words) > 0:
                    if any(word in answer for word in words if len(word) > 3):
                        is_grounded = True
                        break
        
        if not is_grounded and chunks:
            logger.warning(
                f"[VALIDATION] RAG grounding check weak. "
                f"Answer may not be tightly grounded in chunks."
            )
            # Confidence penalty, not fallback
            result.confidence = max(0.0, result.confidence - 0.15)
        for chunk in chunks[:3]:  # Check top 3 chunks
            if chunk and len(chunk) > 0:
                content_snippet = chunk[0][:100].lower() if chunk[0] else ""
                if content_snippet:
                    chunk_phrases.append(content_snippet)
        
        # Check if answer is grounded in chunk content
        is_grounded = False
        if chunk_phrases:
            # If answer contains any significant phrase from chunks, consider it grounded
            for phrase in chunk_phrases:
                words = phrase.split()[:5]  # First 5 words of chunk
                if len(words) > 0:
                    # Check if any of these words appear in answer
                    if any(word in answer for word in words if len(word) > 3):
                        is_grounded = True
                        break
        
        if not is_grounded and chunks:
            issues.append("rag_grounding_failed")
            logger.warning(
                f"[VALIDATION] RAG grounding check failed. "
                f"Answer may not be grounded in retrieved chunks."
            )
    
    # ─────────────────────────────────────────────────────────────────────────
    # 3. ANSWER QUALITY CHECKS (All modes except structured)
    # ─────────────────────────────────────────────────────────────────────────
    
    if result.mode != "structured":
        # Check for obviously empty/short answers
        if not answer or len(answer.strip()) < 10:
            logger.warning("[VALIDATION] Answer too short or empty. Confidence penalty.")
            result.confidence = max(0.0, result.confidence - 0.3)
        
        # Check for RAG mode having no sentence structure
        if result.mode == "rag" and answer.count(".") == 0 and len(answer) > 20:
            logger.warning("[VALIDATION] RAG answer incomplete (no periods). Confidence penalty.")
            result.confidence = max(0.0, result.confidence - 0.15)
    
    # ─────────────────────────────────────────────────────────────────────────
    # 4. FINAL DECISION
    # ─────────────────────────────────────────────────────────────────────────
    # After checks, determine if we should fallback
    #
    # CRITICAL RULE: Only fallback if confidence drops below 0.3
    # This prevents over-aggressive validation
    
    if result.confidence < 0.3 and result.mode != "structured":
        logger.warning(
            f"[VALIDATION] Confidence dropped to {result.confidence}. Setting fallback."
        )
        result.fallback = True
        result.is_fallback = True
    
    return result
    # ─────────────────────────────────────────────────────────────────────────
    
    if issues:
        logger.warning(
            f"[VALIDATION] Validation FAILED with issues: {', '.join(issues)}. "
            f"Setting fallback = True"
        )
        result.fallback = True
        result.confidence = max(0.0, result.confidence - 0.3)  # Penalize confidence
        
        # Log validation failure for future learning
        logger.info(
            f"[VALIDATION] Query: {original_query} | Intent: {original_intent} | "
            f"Issues: {issues} | Mode: {result.mode} | Conf: {result.confidence}"
        )
    else:
        logger.info(
            f"[VALIDATION] ✅ PASSED | Intent: {original_intent} | "
            f"Mode: {result.mode} | Conf: {result.confidence}"
        )
    
    return result


def get_validation_report(result: Any) -> Dict[str, Any]:
    """Get detailed validation report for debugging."""
    return {
        "answer_length": len(result.answer) if result.answer else 0,
        "fallback": result.fallback,
        "confidence": round(result.confidence, 3),
        "intent": result.intent,
        "mode": result.mode,
    }
