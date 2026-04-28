import time
import re
from typing import Dict

# In-memory store (later → Redis / DB)
SESSION_MEMORY = {}

# -------------------------
# GET PROFILE
# -------------------------
def get_student_profile(session_id: str) -> Dict:
    return SESSION_MEMORY.get(session_id, {
        "marks": None,
        "courses": [],
        "interests": None,
        "locked_course": None,
        "turn_count": 0,
        "conversion_stage": "none",
        "confusion_count": 0,
        "last_seen": time.time(),
        "session_id": session_id
    })

# -------------------------
# UPDATE PROFILE
# -------------------------
CONFUSION_PATTERNS = [
    r"\bwhat should i do\b",
    r"\bnot sure\b",
    r"\bconfused\b",
    r"\bidk\b"
]

def update_student_profile(session_id: str, entities: Dict, query: str = "", increment_turn: bool = True):
    profile = get_student_profile(session_id)
    profile["last_seen"] = time.time()
    
    if query:
        q = query.lower()
        for p in CONFUSION_PATTERNS:
            if re.search(p, q):
                profile["confusion_count"] = profile.get("confusion_count", 0) + 1
                if profile["confusion_count"] >= 2:
                    from app.services.counselor.analytics import log_event
                    log_event("confusion_loop", {"session_id": session_id, "count": profile["confusion_count"]})
                break
    
    # update marks with validation
    if entities.get("marks"):
        try:
            marks_val = float(entities["marks"])
            if 0 <= marks_val <= 100:
                profile["marks"] = marks_val
            elif profile.get("marks") and profile["marks"] > 100:
                profile.pop("marks")
        except (ValueError, TypeError):
            pass
            
    # update courses (merge unique)
    if entities.get("courses"):
        existing = set(profile.get("courses", []))
        new = set(entities["courses"])
        profile["courses"] = list(existing.union(new))

    # update interests
    if entities.get("interests"):
        profile["interests"] = entities["interests"]

    # update locked course
    if entities.get("locked_course"):
        profile["locked_course"] = entities["locked_course"]

    # Reset confusion if new specific info is provided
    if entities.get("marks") or entities.get("interests") or entities.get("courses"):
        profile["confusion_count"] = 0

    # update conversion stage
    if entities.get("conversion_stage"):
        profile["conversion_stage"] = entities["conversion_stage"]
    
    # update confusion count
    if entities.get("confusion_count"):
        profile["confusion_count"] = entities["confusion_count"]

    # update bridge stage
    if entities.get("bridge_stage"):
        profile["bridge_stage"] = entities["bridge_stage"]
        
    if entities.get("bridge_course"):
        profile["bridge_course"] = entities["bridge_course"]

    # update asked questions
    if entities.get("_asked_questions"):
        existing = profile.get("_asked_questions", [])
        for q in entities["_asked_questions"]:
            if q not in existing:
                existing.append(q)
        profile["_asked_questions"] = existing

    if increment_turn:
        profile["turn_count"] = profile.get("turn_count", 0) + 1
    
    # Update fallback escalation state
    if "_consecutive_fallbacks" in entities:
        profile["_consecutive_fallbacks"] = entities["_consecutive_fallbacks"]
    
    if "_escalated_once" in entities:
        profile["_escalated_once"] = entities["_escalated_once"]
        
    # Memory Size Control (avoid OOM in prod)
    MAX_SESSIONS = 1000
    if len(SESSION_MEMORY) > MAX_SESSIONS:
        # Remove oldest session (Python dict maintains insertion order)
        oldest_key = next(iter(SESSION_MEMORY))
        del SESSION_MEMORY[oldest_key]
        
    SESSION_MEMORY[session_id] = profile
    return profile

# -------------------------
# MERGE INTO CONTEXT
# -------------------------
def enrich_context_with_memory(context: Dict, session_id: str):
    profile = get_student_profile(session_id)
    
    # Only fill missing fields (do NOT override fresh query)
    if not context.get("marks"):
        context["marks"] = profile.get("marks")
        
    if not context.get("courses"):
        context["courses"] = profile.get("courses")

    if not context.get("interests"):
        context["interests"] = profile.get("interests")

    # Carry forward asked questions list for dedup
    if "_asked_questions" not in context:
        context["_asked_questions"] = profile.get("_asked_questions", [])
        
    # Carry forward state machine fields
    if "conversion_stage" not in context:
        context["conversion_stage"] = profile.get("conversion_stage", "none")
        
    if "confusion_count" not in context:
        context["confusion_count"] = profile.get("confusion_count", 0)
        
    if "bridge_stage" not in context:
        context["bridge_stage"] = profile.get("bridge_stage", "none")

    if "bridge_course" not in context:
        context["bridge_course"] = profile.get("bridge_course")

    if "locked_course" not in context:
        context["locked_course"] = profile.get("locked_course")

    # Carry forward fallback escalation state
    if "_consecutive_fallbacks" not in context:
        context["_consecutive_fallbacks"] = profile.get("_consecutive_fallbacks", 0)
    
    if "_escalated_once" not in context:
        context["_escalated_once"] = profile.get("_escalated_once", False)

    context["turn_count"] = profile.get("turn_count", 0)
    context["session_id"] = session_id
        
    return context


# -------------------------
# ADAPTIVE QUESTION MEMORY
# -------------------------
def store_last_question(session_id: str, question: str) -> None:
    """Store the last adaptive question asked for deduplication."""
    profile = get_student_profile(session_id)
    asked = profile.setdefault("_asked_questions", [])
    if question not in asked:
        asked.append(question)
    # Keep last 10 questions only
    profile["_asked_questions"] = asked[-10:]
    SESSION_MEMORY[session_id] = profile


def avoid_repeat(question: str, session: Dict) -> str:
    """If this question was already asked, return a gentle fallback."""
    asked = session.get("_asked_questions", [])
    if question in asked:
        return "Tell me a bit more about your interests so I can guide you better."
    return question
