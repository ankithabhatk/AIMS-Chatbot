"""
Chat Endpoint - Production Grade RAG API (Phase 4)

POST /api/v1/chat
- Input: query, user (name/email/phone), context (session_id)
- Output: answer, sources, confidence, fallback flag, suggestions
- Features: Real-time RAG, confidence calibration, fallback safety, analytics logging
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
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
from app.services.conversation_brain import preprocess_query, postprocess_response

router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)

# Constants
FAISS_K = 20
MAX_ANSWER_LENGTH = 800
CONFIDENCE_THRESHOLD = 0.45  # Lowered from 0.55 — placements/hostel content scores ~0.50–0.55
RERANK_MIN_SCORE = 0.65
MIN_QUERY_LENGTH = 3
MIN_SCORE_FILTER = 0.3


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
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
        # ================================================================
        # 1. VALIDATE INPUT & SESSION
        # ================================================================
        query = request.query.strip()
        
        # Extract context
        session_id = None
        if request.context and request.context.session_id:
            session_id = request.context.session_id
        else:
            session_id = str(uuid.uuid4())  # Generate if not provided
            
        from app.services.lead_handler import (
            get_or_create_session, update_session_on_query, 
            handle_gated_capture, get_gate_invitation, FEES_DISCLAIMER
        )
        from app.services.database.supabase_client import get_lead_store
        
        # Base session context
        session = get_or_create_session(session_id)
        
        # ================================================================
        # 2. SENSITIVE DATA PROTECTION (Moved to Orchestration Layer)
        # ================================================================
        # Blanket interception of "fee" queries is removed here.
        # The Orchestration layer (SelfHealingEngine) now distinguishes between
        # informational queries and lead-intent queries.
        
        # ================================================================
        # 3. MANDATORY GATE INTERCEPT (Hard Block)
        # ================================================================
        if session["gate_active"] and not session["has_lead"]:
            # ── Gate escape hatch ──────────────────────────────────────
            # Only treat input as a form response if it looks like one
            # (contains @, phone digits, or comma-separated name pattern).
            # This prevents regular questions from looping in email-validation.
            import re as _re
            _looks_like_form = bool(
                _re.search(r'@', query) or                          # email
                _re.search(r'\d{7,}', query) or                     # phone
                (_re.search(r',', query) and len(query) > 8)        # "Name, email, course"
            )
            if not _looks_like_form:
                # Reminder — not an error loop
                reminder = (
                    "I'd love to help! Before I can share those details, "
                    "could you please provide your **Name, Email, and Course of interest**?\n\n"
                    "*(Example: John Doe, john@gmail.com, MBA)*"
                )
                return {
                    "answer":      reminder,
                    "status":      "lock",
                    "fallback":    False,
                    "confidence":  1.0,
                    "sources":     [],
                    "suggestions": ["Share my details", "What programs are offered?"],
                    "meta": {"intent": "gate_reminder", "session_id": session_id},
                }
            # Looks like a real form submission — process it
            capture_result = handle_gated_capture(session_id, query)

            if capture_result.get("lead_ready"):
                try:
                    lead_data = capture_result["data"]
                    lead_store = get_lead_store()
                    import asyncio
                    await lead_store.create_lead(
                        name=lead_data.get("name"),
                        email=lead_data.get("email"),
                        phone=lead_data.get("phone"),
                        interest=lead_data.get("course"),
                        source="chatbot_gated"
                    )
                    logger.info(f"[{session_id}] Lead saved to Supabase: {lead_data.get('email')}")
                except Exception as e:
                    logger.error(f"[{session_id}] Failed to save lead: {e}")
            
            # Log gated queries to in-memory admin system
            try:
                from app.services.chat_logger import log_chat as _log_chat
                _log_chat(session_id, query, capture_result.get("answer", "[Gated]"),
                          confidence=1.0, intent="GATED", status="lock")
            except Exception:
                pass
            # Persist to Supabase
            from app.services.database.db_logger import persist_chat_turn as _persist
            background_tasks.add_task(
                _persist,
                session_id=session_id, query=query,
                response=capture_result.get("answer", "[Gated]"),
                intent="GATED", confidence_score=1.0,
                processing_time_ms=0, status="lock", is_fallback=False,
            )
            return {
                "answer": capture_result["answer"],
                "status": capture_result.get("status", "lock"),
                "fallback": False,
                "confidence": 1.0,
                "sources": [],
                "suggestions": ["Tell me about placements", "Admission last date"],
                "meta": {"intent": "lead_capture_intercept", "session_id": session_id}
            }

        # SURGICAL GATE FIX: Update session ONLY AFTER gate and fees checks pass.
        # This ensures the first question flows to RAG, and Turn 2 is the one that gets gated.
        update_session_on_query(session_id, query)

        # ================================================================
        # 2.5 CONVERSATION BRAIN (Context Intelligence - Safe Layer)
        # ================================================================
        # Pre-process query using conversation context
        # This handles: follow-ups, corrections, query expansion
        # Returns: (processed_query, brain_instruction)
        original_query = query
        query, brain_instruction = preprocess_query(query, session_id)
        
        if brain_instruction and brain_instruction.get("type") == "correction":
            # User rejected last answer - retry with same query
            logger.info(f"[{session_id}] Correction detected, retrying with last query")
        
        if brain_instruction and brain_instruction.get("type") == "affirmation":
            # User was satisfied - provide follow-up options
            return {
                "answer": "Glad I could help! Is there anything else you'd like to know about AIMS?",
                "status": "unlock",
                "fallback": False,
                "confidence": 1.0,
                "sources": [],
                "suggestions": ["Admission requirements", "Campus facilities", "Placement record"],
                "meta": {"intent": "affirmation", "session_id": session_id}
            }

        # Use Input Intelligence to classify intent (GREETING/EXIT/NONSENSE/QUESTION)
        from app.services.input_handler import classify_intent
        intent = classify_intent(query)
        
        logger.info(f"[{session_id}] Detected Intent: {intent}")
        
        # Branch based on intent
        if intent == "GREETING":
            return {
                "answer": "Hello! I'm the AIMS admissions assistant. How can I help you today?",
                "status": "unlock",
                "fallback": False,
                "confidence": 1.0,
                "sources": [],
                "suggestions": ["What programs do you offer?", "Tell me about MBA", "Hostel facilities?"],
                "meta": {"intent": "greeting", "session_id": session_id}
            }
        
        elif intent == "EXIT":
            return {
                "answer": "You're welcome! Feel free to ask anytime. Have a great day!",
                "fallback": False,
                "confidence": 1.0,
                "suggestions": [],
                "meta": {"intent": "exit", "session_id": session_id}
            }
        
        elif intent == "NONSENSE":
            return {
                "answer": "I didn't quite understand that. Could you please rephrase your question about AIMS college?",
                "fallback": True,
                "confidence": 0.0,
                "suggestions": ["Admission process", "Placements", "Contact info"],
                "meta": {"intent": "nonsense", "session_id": session_id}
            }
            
        # Continue with QUESTION flow
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
        
        logger.info(f"[{session_id}] Processing Question: {query[:60]}...")
        
        # ================================================================
        # 1.5 ORCHESTRATION LAYER (Decision Engine)
        # ================================================================
        from app.services.orchestration.self_healing_engine import SelfHealingEngine
        from app.services.orchestration.engine import get_structured_response_for_intent
        
        engine = SelfHealingEngine()
        decision = engine.decide(query)
        
        if decision.mode == "structured":
            # Pass session_id in context for the structured handler
            structured_res = get_structured_response_for_intent(
                decision.intent, query, {"session_id": session_id}
            )
            if structured_res:
                logger.info(f"[{session_id}] Structured response found for intent: {decision.intent}")
                
                # If the structured handler says it's a lock (gate), respect it
                status = structured_res.get("status", "unlock")
                if status == "lock":
                    session["gate_active"] = True
                
                response_time_ms = int((time.time() - start_time) * 1000)
                
                # Persist turn
                from app.services.database.db_logger import persist_chat_turn as _p
                background_tasks.add_task(
                    _p,
                    session_id=session_id, query=query, response=structured_res["answer"],
                    intent=decision.intent, confidence_score=structured_res.get("confidence", 1.0),
                    processing_time_ms=response_time_ms, status=status, is_fallback=False,
                )
                
                return {
                    "answer": structured_res["answer"],
                    "status": status,
                    "fallback": False,
                    "confidence": structured_res.get("confidence", 1.0),
                    "sources": [],
                    "suggestions": structured_res.get("suggestions", ["Admission process", "Placements"]),
                    "meta": {
                        "intent": decision.intent, 
                        "mode": "structured", 
                        "session_id": session_id,
                        "response_time_ms": response_time_ms
                    }
                }
        
        # ================================================================
        # 2. REWRITE QUERY (Only for Questions)
        # ================================================================
        from app.services.query_rewriter import rewrite_with_context
        
        original_query = query
        rewritten_query = rewrite_with_context(query, session_id)
        
        logger.info(f"[{session_id}] Original:  '{original_query}'")
        logger.info(f"[{session_id}] Rewritten: '{rewritten_query}'")

        # ================================================================
        # 2.1 INTENT ROUTING (Guided Flows)
        # ================================================================
        from app.services.intent_router import route as intent_route
        guided = intent_route(original_query, session_id)
        if guided:
            guided.setdefault("meta", {})["session_id"] = session_id
            logger.info(f"[{session_id}] Guided flow: {guided.get('flow')} step {guided.get('step')}")
            return guided

        # ================================================================
        # 3. EMBED QUERY
        # ================================================================
        try:
            query_embedding = embed_text(rewritten_query)
            logger.debug(f"[{session_id}] Embedded query (dim={len(query_embedding)})")
        except Exception as e:
            logger.error(f"[{session_id}] Embedding failed: {e}")
            return {
                "error": True,
                "message": "Failed to process query",
                "code": 500
            }
        
        # ================================================================
        # 4. CHECK FAISS INDEX HEALTH
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
        # 5. RERANK RESULTS (Model-based: ~20 docs → top 5)
        # ================================================================
        from app.services.reranker import get_reranker
        
        # Convert FAISS tuples to dicts for reranker
        # Format: (text, score, url, heading, doc_id, source, priority, course, topic, importance)
        candidate_dicts = [
            {
                "content": c[0],
                "score": c[1],
                "url": c[2],
                "heading": c[3],
                "id": c[4] if len(c) > 4 else None,
                "source": c[5] if len(c) > 5 else "web",
                "priority": c[6] if len(c) > 6 else 1.0,
            } for c in retrieved_chunks
        ]
        
        logger.info(f"[{session_id}] Reranking: {len(candidate_dicts)} candidates → top 5")
        
        # Model-based re-ranking: picks top 5 by relevance
        # Falls back to TF-IDF or heuristic automatically if model unavailable
        reranked_dicts = get_reranker().rerank(rewritten_query, candidate_dicts, top_k=5)
        
        # ================================================================
        # 5.1 DOMAIN-SPECIFIC BOOSTING (Heuristic precision)
        # ================================================================
        query_lower = query.lower()
        
        # Boost placements
        if any(kw in query_lower for kw in ["placement", "job", "career", "recruit"]):
            reranked_dicts = sorted(
                reranked_dicts, 
                key=lambda x: any(kw in x["content"].lower() for kw in ["placement", "recruit", "company"]), 
                reverse=True
            )
            
        # Boost admissions
        if any(kw in query_lower for kw in ["admission", "apply", "enrol", "eligibility"]):
            reranked_dicts = sorted(
                reranked_dicts, 
                key=lambda x: any(kw in x["content"].lower() for kw in ["admission", "process", "apply", "requirement"]), 
                reverse=True
            )
            
        # Boost hostel/facilities
        if any(kw in query_lower for kw in ["hostel", "room", "stay", "accommodation", "facility"]):
            reranked_dicts = sorted(
                reranked_dicts, 
                key=lambda x: any(kw in x["content"].lower() for kw in ["hostel", "facility", "accommodation", "campus"]), 
                reverse=True
            )
        
        # Convert back to tuples for compatibility with downstream services
        filtered_chunks = [
            (r["content"], r["score"], r["url"], r["heading"], r["id"])
            for r in reranked_dicts
        ]
        
        logger.info(f"[{session_id}] Reranked: {len(retrieved_chunks)} → {len(filtered_chunks)} chunks")
        
        # ================================================================
        # 5.5 BOOST FAQ RESULTS (If Present)
        # ================================================================
        # Prioritize FAQ chunks if any exist - they tend to directly answer common questions
        faq_chunks = []
        non_faq_chunks = []
        
        for chunk in filtered_chunks:
            # chunk format: (content, score, url, heading, id)
            # Try to detect if this is a FAQ (by content pattern or explicit metadata)
            content = chunk[0].lower()
            if "q:" in content and "a:" in content:
                # Likely a FAQ based on content pattern
                faq_chunks.append(chunk)
            else:
                non_faq_chunks.append(chunk)
        
        # Reorder: FAQs first (if any), then regular content
        if faq_chunks:
            logger.info(f"[{session_id}] Boosting {len(faq_chunks)} FAQ chunks to top")
            filtered_chunks = faq_chunks + non_faq_chunks
        
        # ================================================================
        # 6. CALCULATE CONFIDENCE
        # ================================================================
        confidence = calculate_confidence(rewritten_query, filtered_chunks) if filtered_chunks else 0.0
        logger.info(f"[{session_id}] Confidence: {confidence:.3f}")
        
        # ================================================================
        # 7. BRANCHING LOGIC: FALLBACK vs. ANSWER
        # ================================================================
        is_fallback = confidence < CONFIDENCE_THRESHOLD
        
        if is_fallback:
            logger.warning(f"[{session_id}] Low confidence ({confidence:.3f}) -> Smart Fallback")
            
            # Construct Smart Fallback Message
            fallback_msg = (
                "I want to make sure I give you the most accurate information. "
                "For this query, I recommend connecting with the AIMS admissions team who can guide you in detail."
            )
            
            # Log fallback
            query_logger = get_query_logger()
            query_logger.log_query(
                query=query,
                answer=fallback_msg,
                confidence=confidence,
                fallback=True,
                response_time_ms=int((time.time() - start_time) * 1000),
                chunks_used=len(filtered_chunks),
                user_email=user_email,
                session_id=session_id
            )
            
            fallback_response_ms = int((time.time() - start_time) * 1000)
            # Persist fallback turn to Supabase
            from app.services.database.db_logger import persist_chat_turn as _p, persist_session_summary as _s
            background_tasks.add_task(
                _p,
                session_id=session_id, query=query, response=fallback_msg,
                intent=intent, confidence_score=confidence,
                processing_time_ms=fallback_response_ms,
                status="fallback", is_fallback=True,
            )
            background_tasks.add_task(_s, session_id)

            return {
                "answer": fallback_msg,
                "sources": [],
                "confidence": round(confidence, 3),
                "confidence_label": _get_confidence_label(confidence),
                "fallback": True,
                "suggestions": ["Admission requirements", "Available programs", "Campus facilities"],
                "meta": {"response_time_ms": fallback_response_ms, "session_id": session_id}
            }

        # ================================================================
        # 8. SYNTHESIZE ANSWER (High/Medium Confidence)
        # ================================================================
        answer_gen = get_answer_generator()
        answer = answer_gen.synthesize(query, filtered_chunks)

        # Safety net: if synthesis returns empty but we have chunks, use top chunk text
        if (not answer or not answer.strip()) and filtered_chunks:
            top_chunk = filtered_chunks[0][0] if isinstance(filtered_chunks[0], (list, tuple)) else str(filtered_chunks[0])
            answer = top_chunk.strip()[:1200]
            logger.warning(f"[{session_id}] Synthesis returned empty — using top chunk as fallback answer")
        
        # ================================================================
        # 8.5 POST-PROCESS ANSWER (Apply Brain Modifications)
        # ================================================================
        answer = postprocess_response(
            original_query=original_query,
            processed_query=query,
            answer=answer,
            confidence=confidence,
            session_id=session_id,
            brain_instruction=brain_instruction
        )
        
        # Add disclaimer if confidence is in the medium range
        if confidence < CONFIDENCE_THRESHOLD:
            logger.info(f"[{session_id}] Medium confidence disclaimer added")
            answer += "\n\nFor more specific details or verification, please contact the AIMS admissions office."
        
        # ================================================================
        # 9. GATE INVITATION (On first 'free' turn)
        # ================================================================
        from app.services.lead_handler import get_gate_invitation
        
        if session["query_count"] == 1 and not session["has_lead"]:
            logger.info(f"[{session_id}] Appending gate invitation to first answer")
            answer = f"{answer}\n\n{get_gate_invitation()}"
        
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

        from app.services.logger import log_event as _structured_log
        background_tasks.add_task(
            _structured_log,
            session_id=session_id,
            query=original_query,
            rewritten_query=rewritten_query,
            intent=intent,
            chunks=filtered_chunks,
            confidence=confidence,
            response=answer,
            response_time_ms=response_time_ms,
        )

        logger.info(f"[{session_id}] ✅ Response sent in {response_time_ms}ms")
        
        # ================================================================
        # 13. BUILD SUCCESS RESPONSE
        # ================================================================
        status = "unlock"
        # Turn counting (query_count increments before this check):
        #   T1 = free answer + gate invite
        #   T2 = free (first follow-up — natural conversation)
        #   T3 = free (second follow-up / context expansion)
        #   T4+ = gate fires (user has had 3 free exchanges)
        if intent not in ["GREETING", "EXIT"] and session["query_count"] >= 4 and not session["has_lead"]:
            status = "lock"
            session["gate_active"] = True
            logger.info(f"[{session_id}] Turn {session['query_count']} - Activating lead gate")

        # ── Log this turn — in-memory (admin API) + Supabase (persistent) ──
        try:
            from app.services.chat_logger import log_chat as _log_chat
            _log_chat(
                session_id  = session_id,
                user_message= query,
                bot_response= answer,
                confidence  = confidence,
                intent      = intent,
                status      = status,
            )
        except Exception as _log_err:
            logger.debug(f"[{session_id}] In-memory log skipped: {_log_err}")

        # Supabase persistent log — retry-safe, visible errors, never blocks response
        from app.services.database.db_logger import persist_chat_turn as _persist
        background_tasks.add_task(
            _persist,
            session_id         = session_id,
            query              = query,
            response           = answer,
            intent             = intent,
            confidence_score   = confidence,
            processing_time_ms = response_time_ms,
            status             = status,
            is_fallback        = False,
        )
        # Background task 2: update session intelligence summary in Supabase
        from app.services.database.db_logger import persist_session_summary as _summarise
        background_tasks.add_task(_summarise, session_id)
        # ─────────────────────────────────────────────────────────────────

        return {
            "answer": answer,
            "status": status,
            "fallback": False,
            "confidence": round(confidence, 3),
            "confidence_label": _get_confidence_label(confidence),
            "sources": sources,
            "suggestions": suggestions,
            "meta": {
                "response_time_ms": response_time_ms,
                "chunks_used": len(filtered_chunks),
                "session_id": session_id
            }
        }

    
    except Exception as e:
        logger.error(f"[{session_id}] Unexpected error: {e}", exc_info=True)
        try:
            from app.services.logger import log_event as _structured_log
            _structured_log(
                session_id=session_id or "",
                query=getattr(request, "query", ""),
                error=str(e),
                response_time_ms=int((time.time() - start_time) * 1000),
            )
        except Exception:
            pass
        return {
            "error": True,
            "message": "Internal server error",
            "code": 500,
            "status": "unlock"
        }


def _get_confidence_label(confidence: float) -> str:
    """Generate human-readable confidence label"""
    if confidence >= 0.65:
        return "✔ Verified Information"
    elif confidence >= 0.55:
        return "⚠️ General Guidance"
    else:
        return "📩 Connect for Details"


def _build_fallback_response(message: str = None,
                             confidence: float = 0.0,
                             response_time_ms: int = 0) -> dict:
    """Build standardized fallback response"""
    if message is None:
        message = "I want to make sure I give you the most accurate information. For this query, I recommend connecting with the AIMS admissions team who can guide you in detail."
    
    return {
        "answer": None,
        "status": "unlock",
        "fallback": True,
        "confidence": round(confidence, 3),
        "confidence_label": _get_confidence_label(confidence),
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
