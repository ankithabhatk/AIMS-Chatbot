# app/services/intent_router.py
from typing import Optional
from app.services.intent_classifier import classify
from app.services.guided_flows import (
    GUIDED_INTENTS, advance_flow, get_active_flow, start_flow,
)

_EXIT_WORDS = {"stop", "cancel", "exit flow", "skip", "nevermind", "never mind", "quit"}


def route(query: str, session_id: str) -> Optional[dict]:
    """
    Returns a guided-flow response dict if a flow is active/triggered,
    or None to fall through to the RAG pipeline.
    """
    q_lower = query.strip().lower()

    # Allow user to cancel an active flow
    if any(w in q_lower for w in _EXIT_WORDS):
        from app.services.guided_flows import clear_flow
        clear_flow(session_id)
        return None

    # Continue active flow
    active = get_active_flow(session_id)
    if active:
        response = advance_flow(session_id, query)
        if response:
            return response
        # Flow complete — fall through to RAG with collected context
        return None

    # Detect intent and start guided flow if applicable
    result = classify(query)
    intent = result["intent"]
    confidence = result["confidence"]

    from app.services.analytics import record_conversation, record_flow_start
    record_conversation(intent)

    if intent in GUIDED_INTENTS and confidence >= 0.8:
        record_flow_start(intent)
        response = start_flow(session_id, intent)
        if response:
            return response

    return None  # RAG handles it
