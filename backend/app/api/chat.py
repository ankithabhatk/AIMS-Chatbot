"""Production chat endpoint for the local retrieval-first AIMS assistant."""

from __future__ import annotations

import asyncio
import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.models.schemas import ChatRequest, ChatResponseSuccess, SourceCitation
from app.services.conversation_store import get_conversation_store
from app.services.intelligence_layer import get_intelligence_layer
from app.services.lead_handler import (
    FEES_DISCLAIMER,
    get_gate_invitation,
    get_or_create_session,
    handle_gated_capture,
    update_session_on_query,
)
from app.services.query_cache import get_query_response_cache
from app.services.response.confidence import calculate_confidence, get_confidence_label
from app.services.retrieval.faiss_index import get_index
from app.services.retrieval.hybrid_retriever import get_hybrid_retriever
from app.services.suggestions.engine import get_suggestion_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])

CONFIDENCE_THRESHOLD = 0.48
LOW_CONFIDENCE_THRESHOLD = 0.32


@router.post("/chat", response_model=ChatResponseSuccess)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Answer user queries using local preprocessing, hybrid retrieval, and extractive synthesis."""
    start_time = time.time()
    session_id = _resolve_session_id(request)
    session = get_or_create_session(session_id)

    query = request.query.strip()
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="Query too short")

    intel = get_intelligence_layer()
    query_data = intel.process_query(query, session_id)
    update_session_on_query(session_id, query)

    if session["gate_active"] and not session["has_lead"]:
        response = await _handle_lead_capture(session_id, session, query, query_data)
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
        )
        return response

    if query_data.get("needs_clarification"):
        response = _build_clarification_response(query_data, session_id, start_time)
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
        )
        return response

    if query_data["intent"] in {"greeting", "exit"}:
        final_data = intel.synthesize_response(query_data, [], 1.0)
        response = ChatResponseSuccess(
            answer=final_data["answer"],
            sources=[],
            confidence=1.0,
            status="unlock",
            intent=final_data["intent"],
            course=final_data["course"],
            fallback=False,
            suggestions=_default_suggestions_for_intent(final_data["intent"]),
            meta={
                "response_time_ms": int((time.time() - start_time) * 1000),
                "session_id": session_id,
                "original_query": query_data.get("original_query"),
                "corrected_query": query_data.get("corrected_query"),
                "confidence_label": "high",
                "retrieved_chunks": 0,
                "control_tokens": query_data.get("control_tokens", []),
                "memory_notes": query_data.get("memory_notes", []),
            },
        )
        get_query_response_cache().set(
            get_query_response_cache().make_key(query_data),
            _response_to_cache_payload(response),
        )
        _log_interaction(
            session_id=session_id,
            query=query,
            answer=response.answer,
            confidence=response.confidence,
            intent=response.intent,
            status=response.status,
        )
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
        )
        return response

    if _is_sensitive_query(query_data) and not session["has_lead"]:
        session["gate_active"] = True
        response = ChatResponseSuccess(
            answer=f"{FEES_DISCLAIMER}\n\n{get_gate_invitation()}",
            sources=[],
            confidence=1.0,
            status="lock",
            intent="Lead Capture",
            course=query_data.get("course") or "General",
            suggestions=["Programs offered", "Campus life", "Admission process"],
            meta={
                "session_id": session_id,
                "gated": True,
                "original_query": query_data.get("original_query"),
                "corrected_query": query_data.get("corrected_query"),
                "control_tokens": query_data.get("control_tokens", []),
            },
        )
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
        )
        return response

    cache = get_query_response_cache()
    cache_key = cache.make_key(query_data)
    cached_payload = cache.get(cache_key)
    if cached_payload:
        response = _build_cached_response(
            cached_payload,
            session_id=session_id,
            query_data=query_data,
            processing_time=int((time.time() - start_time) * 1000),
            session=session,
        )
        _log_interaction(
            session_id=session_id,
            query=query,
            answer=response.answer,
            confidence=response.confidence,
            intent=response.intent,
            status=response.status,
        )
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
        )
        return response

    index = get_index()
    if not index.validate_integrity():
        logger.error("FAISS index integrity check failed")
        response = _build_fallback(
            session_id,
            start_time,
            message="System maintenance is in progress. Please try again shortly.",
            query_data=query_data,
        )
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
        )
        return response

    retriever = get_hybrid_retriever()
    retrieval_results = await asyncio.to_thread(retriever.search, query_data, 8, 16, 16)
    confidence = calculate_confidence(query_data["query"], retrieval_results, query_data=query_data)
    chunk_tuples = retriever.to_chunk_tuples(retrieval_results)

    if not retrieval_results:
        response = _build_fallback(
            session_id,
            start_time,
            message="I could not find a matching AIMS record for that yet. Please try mentioning the course or topic.",
            query_data=query_data,
        )
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
        )
        return response

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        response = _build_best_snippet_response(
            session_id=session_id,
            query_data=query_data,
            retrieval_results=retrieval_results,
            confidence=confidence,
            start_time=start_time,
            message_prefix="",
        )
        cache.set(cache_key, _response_to_cache_payload(response))
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
            retrieval_results=retrieval_results,
        )
        return response

    try:
        final_data = await asyncio.to_thread(intel.synthesize_response, query_data, chunk_tuples, confidence)
    except Exception:
        logger.exception("Response synthesis failed, falling back to extractive snippet")
        response = _build_best_snippet_response(
            session_id=session_id,
            query_data=query_data,
            retrieval_results=retrieval_results,
            confidence=confidence,
            start_time=start_time,
            message_prefix="",
        )
        cache.set(cache_key, _response_to_cache_payload(response))
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
            retrieval_results=retrieval_results,
        )
        return response

    if confidence < CONFIDENCE_THRESHOLD:
        response = _build_best_snippet_response(
            session_id=session_id,
            query_data=query_data,
            retrieval_results=retrieval_results,
            confidence=confidence,
            start_time=start_time,
            message_prefix="",
        )
        cache.set(cache_key, _response_to_cache_payload(response))
        _queue_persistence(
            background_tasks,
            request=request,
            session_id=session_id,
            user_query=query,
            response=response,
            query_data=query_data,
            retrieval_results=retrieval_results,
        )
        return response

    sources = _build_sources(retrieval_results)
    suggestions = get_suggestion_engine().generate(query_data.get("query", ""), fallback=False)
    processing_time = int((time.time() - start_time) * 1000)
    status = _derive_status(session, query_data["intent"])

    response = ChatResponseSuccess(
        answer=final_data["answer"],
        sources=sources,
        confidence=round(confidence, 3),
        status=status,
        intent=final_data["intent"],
        course=final_data["course"],
        fallback=False,
        suggestions=suggestions,
        meta={
            "response_time_ms": processing_time,
            "session_id": session_id,
            "original_query": query_data.get("original_query"),
            "corrected_query": query_data.get("corrected_query"),
            "confidence_label": get_confidence_label(confidence),
            "retrieved_chunks": len(retrieval_results),
            "control_tokens": query_data.get("control_tokens", []),
            "memory_notes": query_data.get("memory_notes", []),
        },
    )

    _log_interaction(
        session_id=session_id,
        query=query,
        answer=response.answer,
        confidence=confidence,
        intent=query_data["intent"],
        status=status,
    )
    cache.set(cache_key, _response_to_cache_payload(response))
    _queue_persistence(
        background_tasks,
        request=request,
        session_id=session_id,
        user_query=query,
        response=response,
        query_data=query_data,
        retrieval_results=retrieval_results,
    )
    return response


@router.get("/chat/history")
async def get_chat_history(
    user_email: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Return persisted chat sessions, optionally filtered by user email."""
    store = get_conversation_store()
    sessions = store.list_sessions(user_email=user_email, limit=limit)
    return {"sessions": sessions, "count": len(sessions)}


@router.get("/chat/history/{session_id}")
async def get_chat_session(session_id: str):
    """Return one persisted chat session."""
    session = get_conversation_store().get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def _handle_lead_capture(session_id: str, session: Dict, query: str, query_data: Dict) -> ChatResponseSuccess:
    capture_result = handle_gated_capture(session_id, query)
    if capture_result.get("lead_ready"):
        try:
            from app.services.database.supabase_client import get_lead_store

            lead_data = capture_result["data"]
            lead_store = get_lead_store()
            await lead_store.create_lead(
                name=lead_data.get("name"),
                email=lead_data.get("email"),
                phone=lead_data.get("phone"),
                interest=lead_data.get("course"),
                source="chatbot_gated",
            )
        except Exception as exc:
            logger.error("Lead saving failed: %s", exc)

    return ChatResponseSuccess(
        answer=capture_result["answer"],
        sources=[],
        confidence=1.0,
        status=capture_result.get("status", "lock"),
        intent="Lead Capture",
        course=query_data.get("course") or "General",
        suggestions=["Tell me about placements", "Admission dates"],
        meta={"session_id": session_id, "lead_capture": True},
    )


def _build_clarification_response(query_data: Dict, session_id: str, start_time: float) -> ChatResponseSuccess:
    suggestions = []
    if not query_data.get("course"):
        suggestions = ["MBA fees", "BBA placements", "MBA hostel"]

    return ChatResponseSuccess(
        answer=query_data.get("clarification_message")
        or "Could you rephrase that with the course or topic you need?",
        sources=[],
        confidence=0.0,
        status="unlock",
        intent="clarification",
        course=query_data.get("course") or "General",
        fallback=True,
        suggestions=suggestions,
        meta={
            "session_id": session_id,
            "response_time_ms": int((time.time() - start_time) * 1000),
            "original_query": query_data.get("original_query"),
            "corrected_query": query_data.get("corrected_query"),
            "control_tokens": query_data.get("control_tokens", []),
        },
    )


def _build_best_snippet_response(
    session_id: str,
    query_data: Dict,
    retrieval_results: List[Dict],
    confidence: float,
    start_time: float,
    message_prefix: str,
) -> ChatResponseSuccess:
    top_result = retrieval_results[0]
    snippet = _extract_snippet(top_result.get("content", ""))
    answer = f"{message_prefix}\n\n{snippet}".strip()
    processing_time = int((time.time() - start_time) * 1000)

    _log_interaction(
        session_id=session_id,
        query=query_data.get("original_query", ""),
        answer=answer,
        confidence=confidence,
        intent="fallback",
        status="unlock",
    )

    return ChatResponseSuccess(
        answer=answer,
        sources=_build_sources(retrieval_results),
        confidence=round(confidence, 3),
        status="unlock",
        intent="fallback",
        course=query_data.get("course") or "General",
        fallback=True,
        suggestions=["Mention the course name", "Ask for a detailed answer", "Try another topic"],
        meta={
            "session_id": session_id,
            "response_time_ms": processing_time,
            "original_query": query_data.get("original_query"),
            "corrected_query": query_data.get("corrected_query"),
            "confidence_label": get_confidence_label(confidence),
            "retrieved_chunks": len(retrieval_results),
            "control_tokens": list(query_data.get("control_tokens", [])) + ["<FALLBACK>"],
        },
    )


def _build_fallback(session_id: str, start_time: float, message: str, query_data: Dict | None = None) -> ChatResponseSuccess:
    meta = {
        "session_id": session_id,
        "response_time_ms": int((time.time() - start_time) * 1000),
    }
    if query_data:
        meta.update(
            {
                "original_query": query_data.get("original_query"),
                "corrected_query": query_data.get("corrected_query"),
                "control_tokens": list(query_data.get("control_tokens", [])) + ["<FALLBACK>"],
            }
        )

    return ChatResponseSuccess(
        answer=message,
        sources=[],
        confidence=0.0,
        status="unlock",
        intent="fallback",
        course=query_data.get("course") if query_data else "General",
        fallback=True,
        suggestions=["Mention the course name", "Ask about admissions", "Ask about placements"],
        meta=meta,
    )


def _resolve_session_id(request: ChatRequest) -> str:
    if request.context and request.context.session_id:
        return request.context.session_id
    if request.session_id:
        return request.session_id
    return str(uuid.uuid4())


def _derive_status(session: Dict[str, Any], intent: str) -> str:
    if intent not in {"greeting", "exit"} and session["query_count"] >= 2 and not session["has_lead"]:
        session["gate_active"] = True
        return "lock"
    return "unlock"


def _response_to_cache_payload(response: ChatResponseSuccess) -> Dict[str, Any]:
    meta = dict(response.meta or {})
    meta.pop("session_id", None)
    meta.pop("response_time_ms", None)
    meta.pop("cache_hit", None)
    return {
        "answer": response.answer,
        "sources": _serialize_sources(response.sources),
        "confidence": float(response.confidence),
        "intent": response.intent,
        "course": response.course,
        "fallback": bool(response.fallback),
        "suggestions": list(response.suggestions or []),
        "meta": meta,
    }


def _build_cached_response(
    cached_payload: Dict[str, Any],
    *,
    session_id: str,
    query_data: Dict[str, Any],
    processing_time: int,
    session: Dict[str, Any],
) -> ChatResponseSuccess:
    confidence = float(cached_payload.get("confidence", 0.0))
    fallback = bool(cached_payload.get("fallback", False))
    intent = cached_payload.get("intent", "factual")
    status = cached_payload.get("status", "unlock")
    if not fallback:
        status = _derive_status(session, intent)

    meta = dict(cached_payload.get("meta", {}))
    meta.update(
        {
            "session_id": session_id,
            "response_time_ms": processing_time,
            "original_query": query_data.get("original_query"),
            "corrected_query": query_data.get("corrected_query"),
            "confidence_label": get_confidence_label(confidence),
            "cache_hit": True,
        }
    )
    if "control_tokens" not in meta:
        meta["control_tokens"] = query_data.get("control_tokens", [])

    return ChatResponseSuccess(
        answer=cached_payload.get("answer", ""),
        sources=[SourceCitation(**source) for source in cached_payload.get("sources", [])],
        confidence=round(confidence, 3),
        status=status,
        intent=intent,
        course=cached_payload.get("course") or query_data.get("course") or "General",
        fallback=fallback,
        suggestions=list(cached_payload.get("suggestions", [])),
        meta=meta,
    )


def _queue_persistence(
    background_tasks: BackgroundTasks,
    *,
    request: ChatRequest,
    session_id: str,
    user_query: str,
    response: ChatResponseSuccess,
    query_data: Optional[Dict[str, Any]] = None,
    retrieval_results: Optional[List[Dict[str, Any]]] = None,
) -> None:
    user_name = request.user.name if request.user else None
    user_email = request.user.email if request.user else None
    control_tokens = list((response.meta or {}).get("control_tokens", []))

    background_tasks.add_task(
        get_conversation_store().append_turn,
        session_id=session_id,
        user_query=user_query,
        assistant_answer=response.answer,
        user_email=user_email,
        user_name=user_name,
        confidence=float(response.confidence),
        status=response.status,
        intent=response.intent,
        fallback=bool(response.fallback),
        response_time_ms=int((response.meta or {}).get("response_time_ms", 0)),
        original_query=(query_data or {}).get("original_query", user_query),
        corrected_query=(query_data or {}).get("corrected_query", user_query),
        control_tokens=control_tokens,
        retrieved_chunks=_serialize_retrieval_results(retrieval_results),
        sources=_serialize_sources(response.sources),
        suggestions=list(response.suggestions or []),
        active_course=(query_data or {}).get("course") or response.course,
        active_topic=(query_data or {}).get("topic"),
        last_intent=(query_data or {}).get("intent") or response.intent,
    )
    background_tasks.add_task(
        _persist_remote_log,
        session_id=session_id,
        query=user_query,
        response=response.answer,
        intent=response.intent,
        confidence_score=float(response.confidence),
        processing_time_ms=int((response.meta or {}).get("response_time_ms", 0)),
        status=response.status,
        is_fallback=bool(response.fallback),
    )


def _persist_remote_log(
    *,
    session_id: str,
    query: str,
    response: str,
    intent: str,
    confidence_score: float,
    processing_time_ms: int,
    status: str,
    is_fallback: bool,
) -> None:
    try:
        from app.services.database.db_logger import persist_chat_turn

        persist_chat_turn(
            session_id=session_id,
            query=query,
            response=response,
            intent=intent,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            status=status,
            is_fallback=is_fallback,
        )
    except Exception:
        logger.debug("Remote chat logging skipped", exc_info=True)


def _serialize_sources(sources: List[SourceCitation]) -> List[Dict[str, str]]:
    serialized: List[Dict[str, str]] = []
    for source in sources:
        serialized.append({"title": source.title, "url": source.url})
    return serialized


def _serialize_retrieval_results(results: Optional[List[Dict[str, Any]]], limit: int = 5) -> List[Dict[str, Any]]:
    if not results:
        return []

    serialized: List[Dict[str, Any]] = []
    for result in results[:limit]:
        serialized.append(
            {
                "doc_id": result.get("doc_id"),
                "heading": result.get("heading"),
                "url": result.get("url"),
                "score": round(float(result.get("score", 0.0)), 4),
                "course": result.get("course"),
                "topic": result.get("topic"),
            }
        )
    return serialized


def _default_suggestions_for_intent(intent: str) -> List[str]:
    if intent == "greeting":
        return ["MBA fees", "BBA placements", "MBA admission process"]
    return []


def _extract_snippet(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    filtered = [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 18]
    return "\n".join(f"- {sentence}" for sentence in filtered[:3]) or text[:320]


def _build_sources(retrieval_results: List[Dict]) -> List[SourceCitation]:
    seen = set()
    sources: List[SourceCitation] = []
    for result in retrieval_results:
        url = result.get("url") or ""
        title = result.get("heading") or "Source"
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        sources.append(SourceCitation(title=title, url=url))
        if len(sources) >= 2:
            break
    return sources


def _is_sensitive_query(query_data: Dict) -> bool:
    topic = query_data.get("topic")
    keywords = set(query_data.get("keyword_terms", []))
    if topic in {"fees", "placements"}:
        return True
    return bool({"fee", "fees", "placement", "placements", "salary", "package"} & keywords)


def _log_interaction(session_id: str, query: str, answer: str, confidence: float, intent: str, status: str) -> None:
    try:
        from app.services.chat_logger import log_chat

        log_chat(
            session_id,
            query,
            answer,
            confidence=confidence,
            intent=intent,
            status=status,
        )
    except Exception:
        logger.debug("In-memory chat logging skipped", exc_info=True)
