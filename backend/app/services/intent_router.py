# app/services/intent_router.py
from typing import Optional
from app.services.intent_classifier import classify
from app.services.guided_flows import (
    GUIDED_INTENTS, advance_flow, clear_flow, get_active_flow, start_flow,
)

_EXIT_WORDS = {"stop", "cancel", "exit flow", "nevermind", "never mind", "quit"}

# Hard-override topic keywords — any match instantly exits an active flow
_TOPIC_KEYWORDS = frozenset([
    "bca", "mca", "mba", "bba", "bcom",
    "fees", "fee", "hostel", "admission",
    "placements", "placement", "courses", "course",
    "salary", "scholarship", "recruiter",
])

# Conversation-switch phrases that signal topic change mid-flow
_SWITCH_PHRASES = ("what about", "tell me", "compare", "difference", "vs", "or")


def has_strong_topic(query: str) -> bool:
    """True when query contains an unambiguous AIMS subject keyword."""
    q = query.lower()
    return any(k in q for k in _TOPIC_KEYWORDS)


def should_continue_flow(query: str, intent: str, confidence: float) -> bool:
    """
    False → exit the current flow; True → keep going.
    Checks are intentionally explicit per spec.
    """
    q = query.lower()

    if has_strong_topic(q):
        return False

    if any(p in q for p in _SWITCH_PHRASES):
        return False

    # Program names mid-flow always mean topic change
    if any(k in q for k in ("mca", "mba", "bca", "bba", "pgdm")):
        return False

    # Only exit on a confident topic shift — not when intent is 'general'
    # (short flow answers like 'UG', 'Yes', 'No' all return general/0.4)
    if intent != "general" and confidence > 0.6:
        return False

    return True


def route(query: str, session_id: str) -> Optional[dict]:
    """
    Priority order (per spec):
      1. Comparison intent
      2. Hard override (topic keyword → clear flow)
      3. Guided flow validation
      4. Guided flow execution
      5. RAG fallback (return None)
    Single classify() call per request.
    """
    q_lower = query.strip().lower()

    # Explicit cancellation — before classify to keep it fast
    if any(w in q_lower for w in _EXIT_WORDS):
        clear_flow(session_id)
        return None

    # Classify ONCE — result reused throughout
    result = classify(query)
    intent = result["intent"]
    confidence = result["confidence"]

    # ── 1. COMPARISON (highest priority) ────────────────────────────────────
    if intent == "comparison":
        from app.services.comparison_handler import handle_comparison
        clear_flow(session_id)          # always exit any active flow
        return handle_comparison(query) # None → falls through to RAG

    # ── 2. HARD OVERRIDE (topic keyword → clear flow immediately) ───────────
    if has_strong_topic(query):
        clear_flow(session_id)

    # ── 3+4. GUIDED FLOW VALIDATE + EXECUTE ─────────────────────────────────
    active = get_active_flow(session_id)
    if active:
        if not should_continue_flow(query, intent, confidence):
            clear_flow(session_id)
            # Fall through to RAG with the new question
        else:
            response = advance_flow(session_id, query)
            if response:
                return response
            return None  # flow finished normally

    # ── 5. START NEW FLOW OR RAG ─────────────────────────────────────────────
    from app.services.analytics import record_conversation, record_flow_start
    record_conversation(intent)

    # Don't start a flow if query names a specific program — RAG answers directly
    # e.g. "tell me about mca" → RAG; "I want to apply" → admissions flow
    _specific_program_in_query = any(
        p in query.lower() for p in ("mca", "mba", "bca", "bba", "bcom", "pgdm")
    )
    if intent in GUIDED_INTENTS and confidence >= 0.8 and not _specific_program_in_query:
        record_flow_start(intent)
        response = start_flow(session_id, intent)
        if response:
            return response

    return None  # RAG handles it
