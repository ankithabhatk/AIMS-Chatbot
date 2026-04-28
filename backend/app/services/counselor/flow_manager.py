from typing import Dict, List, Optional
from app.services.counselor.analytics import track_event

def add_hook(response: str, context: dict) -> str:
    """Forced micro-hook to keep user engaged."""
    if context.get("marks") and not context.get("courses"):
        return response + "\n\n👉 Tell me your interest (business / tech / finance), I’ll narrow it down for you."
    return response

def ask_commitment(context: dict) -> Optional[str]:
    if not context.get("goal"):
        return "👉 What’s your goal after studying — job, business, or higher studies?"
    if not context.get("interest"):
        return "👉 Which area excites you more — business, tech, or finance?"
    return None

def detect_intent_level(context: dict, query: str) -> str:
    q = query.lower()
    if any(x in q for x in ["apply", "admission", "join", "enroll"]):
        return "high"
    if any(x in q for x in ["which is better", "compare", "best course"]):
        return "mid"
    if any(x in q for x in ["confused", "what should i", "not sure"]):
        return "low"
    if context.get("goal") and context.get("interest"):
        return "mid"
    return "low"

def smart_followup(context: dict, level: str) -> Optional[str]:
    if level == "low":
        return "Want help exploring the best options for you?"
    if level == "mid":
        return "Do you want me to help you choose between these?"
    if level == "high":
        return "Shall we start your application process?"
    return None

def trust_loop() -> str:
    return "Feel free to take your time—I'm here to help you make the right decision, not rush you."

def gentle_followup(context: dict) -> Optional[str]:
    if not context.get("interest"):
        return "Would you like me to help narrow this down based on your interests?"
    return None

def generate_follow_up(context: Dict, last_intents: List[str]) -> str:
    """
    Smart follow-up generator based on user state + intents
    """
    marks = context.get("marks")
    courses = context.get("courses", [])
    
    # -------------------------
    # If user gave marks but no course
    # -------------------------
    if marks and not courses:
        follow_up = "Do you have any specific interest like business, tech, or finance?"
        track_event("follow_up_generated", {
            "question": follow_up,
            "session_id": context.get("session_id")
        })
        return follow_up
        
    # -------------------------
    # If comparing courses
    # -------------------------
    if "compare" in last_intents:
        follow_up = "Which one are you leaning towards so far?"
        track_event("follow_up_generated", {
            "question": follow_up,
            "session_id": context.get("session_id")
        })
        return follow_up
        
    # -------------------------
    # If guidance triggered
    # -------------------------
    if "guidance" in last_intents:
        follow_up = "Do you want me to narrow this down based on jobs or difficulty level?"
        track_event("follow_up_generated", {
            "question": follow_up,
            "session_id": context.get("session_id")
        })
        return follow_up
        
    # -------------------------
    # If career triggered
    # -------------------------
    if "career" in last_intents:
        follow_up = "Would you like me to suggest the best course to reach that career?"
        track_event("follow_up_generated", {
            "question": follow_up,
            "session_id": context.get("session_id")
        })
        return follow_up
        
    # -------------------------
    # Default
    # -------------------------
    follow_up = "Tell me a bit about what you're interested in, I’ll guide you better."
    
    track_event("follow_up_generated", {
        "question": follow_up,
        "session_id": context.get("session_id")
    })
    return follow_up
