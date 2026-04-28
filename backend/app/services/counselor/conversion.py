import re
import logging
from typing import Dict, Optional
from app.services.learning.optimizer import SYSTEM_TUNING

logger = logging.getLogger(__name__)

# -------------------------
# PATTERNS
# -------------------------
DECISION_PATTERNS = [
    r"\bi think\b",
    r"\bi'll go with\b",
    r"\bi will go with\b",
    r"\bseems good\b",
    r"\blooks good\b",
    r"\bbetter option\b",
    r"\bthis is better\b",
    r"\bi choose\b",
    r"\bi prefer\b",
    r"\bgoing with\b",
    r"\bbba is good\b",
    r"\bbcom is better\b",
    r"\bthis seems good\b",
    r"\bthat works\b",
    r"\bthis works\b",
    r"\byeah bca\b",
    r"\byeah bba\b",
    r"\bsounds right\b",
    r"\bsounds good\b",
    r"\bi'll do\b",
    r"\blet's go with\b",
    # Implicit decision patterns (real user language)
    r"\byeah\b", r"\bokay\b", r"\bok\b", r"\byes\b", r"\bfine\b", r"\bcool\b",
    r"\balright\b", r"\bsure\b", r"\byep\b", r"\byup\b",
    r"\bmakes sense\b", r"\bthat's good\b",
    r"\bgo with\b", r"\bgo for\b"
]

OBJECTION_PATTERNS = {
    "timing": [
        r"\blater\b",
        r"\bnot now\b",
        r"\bi'll think\b",
        r"\bafter some time\b"
    ],
    "uncertainty": [
        r"\bnot sure\b",
        r"\bconfused\b",
        r"\bmaybe\b",
        r"\bidk\b"
    ],
    "fees": [
        r"\bfees\b",
        r"\bcost\b",
        r"\bexpensive\b",
        r"\bbudget\b",
        r"\bafford\b"
    ]
}

PERMISSION_PATTERNS = [
    r"\byes\b",
    r"\bokay\b",
    r"\bok\b",
    r"\bhow\b",
    r"\bhow to apply\b",
    r"\bguide me\b",
    r"\bstart\b",
    r"\btell me\b",
    r"\bshow me\b",
    r"\bwhat next\b",
    r"\bwhat's next\b",
    r"\bsure\b",
    r"\bof course\b",
    r"\bplease\b",
]

# -------------------------
# SCORING
# -------------------------
def score_patterns(query: str, patterns: list) -> int:
    score = 0
    for p in patterns:
        if re.search(p, query.lower()):
            score += 1
    return score

LOW_INTENT_BLOCKERS = [
    "idk", "don't know", "confused", "not sure", "no idea"
]

def detect_decision_signal(query: str) -> bool:
    # Normalize query for robust detection
    q = query.lower().strip()
    if any(x in q for x in LOW_INTENT_BLOCKERS):
        return False
    score = score_patterns(q, DECISION_PATTERNS)
    return score >= 1

def detect_objection(query: str) -> Optional[str]:
    for key, patterns in OBJECTION_PATTERNS.items():
        if score_patterns(query, patterns) > 0:
            return key
    return None

def detect_permission(query: str) -> bool:
    return score_patterns(query, PERMISSION_PATTERNS) > 0

# -------------------------
# OBJECTION HANDLER
# -------------------------
def handle_objection(query: str) -> Optional[str]:
    obj = detect_objection(query)
    if not obj:
        # Detect salary objection specifically (not in OBJECTION_PATTERNS)
        if re.search(r"\bsalary\b.*\blow\b|\blow\b.*\bsalary\b", query.lower()):
            obj = "salary"
            
    if obj:
        from app.services.llm.minimax_service import get_minimax_service
        return get_minimax_service().handle_objection(obj, query)
    return None

# -------------------------
# CONVERSION STATE MACHINE
# -------------------------
CONVERSION_STAGE = [
    "none",
    "decision_confirmed",
    "visualized",
    "soft_transition",
    "permission_asked",
    "ready_to_close",
    "closed"
]

def run_conversion_flow(query: str, session: Dict, course: str) -> Optional[str]:
    from app.services.counselor.analytics import log_event
    stage = session.get("conversion_stage", "none")
    
    # CRITICAL: Respect locked course - never switch
    locked_course = session.get("locked_course")
    if locked_course:
        course = locked_course
        logger.info(f"[CONVERSION] Using locked course: {locked_course}")
    
    # STEP 1 — Decision detected
    if stage == "none" and detect_decision_signal(query):
        session["conversion_stage"] = "decision_confirmed"
        log_event("decision_hit", {"session_id": session.get("session_id", "unknown")})
        from app.services.llm.minimax_service import get_minimax_service
        return get_minimax_service().enhance_conversion("decision_confirmed", course)
        
    # STEP 2 — Visualization
    if stage == "decision_confirmed":
        session["conversion_stage"] = "visualized"
        return f"With {course}, you can move into roles like management, analytics, or marketing.\n\nDoes that direction feel right to you?"
        
    # STEP 3 — Soft transition
    if stage == "visualized":
        session["conversion_stage"] = "soft_transition"
        return "Great — then the next step is just understanding how to get started.\n\nI can walk you through the admission process step by step."
        
    # STEP 4 — Permission wait
    if stage == "soft_transition" and detect_permission(query):
        session["conversion_stage"] = "ready_to_close"
        log_event("permission_granted", {"session_id": session.get("session_id", "unknown")})
        from app.services.llm.minimax_service import get_minimax_service
        return get_minimax_service().enhance_conversion("ready_to_close", course)
        
    # STEP 5 — Close
    if stage == "ready_to_close":
        session["conversion_stage"] = "closed"
        log_event("conversion_complete", {"session_id": session.get("session_id", "unknown")})
        # Rule 4 & Rule 7
        return "I can stay with you and guide you while filling it — it only takes a few minutes."
        
    return None

def detect_conversion_intent(query: str) -> bool:
    q = query.lower()
    keywords = [
        "apply", "admission", "join", "enroll",
        "how to apply", "application process",
        "fees payment", "registration"
    ]
    return any(k in q for k in keywords)

def generate_cta(context: Dict) -> str:
    courses = context.get("courses", [])
    marks = context.get("marks")
    prefix = "Most students at this stage usually start their application to secure their preferred course.\n\n" if SYSTEM_TUNING.get("inject_social_proof") else ""
    if courses:
        return f"{prefix}You can start your application for {courses[0]} here: https://www.theaims.ac.in/admissions"
    if marks:
        return f"{prefix}Once you decide your course, I can guide you through the application step-by-step."
    return f"{prefix}I can help you with the admission process whenever you're ready."

def inject_informed_timing(response: str) -> str:
    return response + "\n\nAdmissions are currently open, so starting early can give you more flexibility in choosing your preferred course."

def guided_optional_close(course: str) -> str:
    prefix = "Most students at this stage usually start their application to secure their preferred course.\n" if SYSTEM_TUNING.get("inject_social_proof") else ""
    if SYSTEM_TUNING.get("cta_style") == "soft":
        return f"\n\n{prefix}If you feel confident about {course}, I can stay with you and guide you while filling it — it only takes a few minutes."
    return f"\n\n{prefix}If you feel confident about {course}, I can walk you through the admission process step by step."


# ─────────────────────────────────────────────
# GUIDANCE → ACTION BRIDGE (non-pushy)
# ─────────────────────────────────────────────
def is_decision_ready(guidance_output: Dict) -> bool:
    """Check if the guidance engine flagged a high-confidence decision.
    Uses the engine's own signal — no regex guessing."""
    return (
        guidance_output.get("decision_ready") is True
        and guidance_output.get("confidence", 0) >= 0.8
    )


def run_guidance_to_action(guidance_output: Dict, context: Dict) -> str:
    """
    Bridge response: converts a confident guidance recommendation
    into a personalized, explainable next-step offer.
    Uses ERL (reasoning.py) for transparent, data-backed explanation.
    No pressure. No links. Permission-gated.
    """
    from app.services.counselor.reasoning import build_full_bridge_response
    return build_full_bridge_response(guidance_output, context)



def run_next_step_info(query: str, course: str, context: Dict) -> str:
    """
    After micro-commitment is confirmed (yes/how/tell me),
    provide structured admission next steps.
    """
    q = query.lower()
    
    # 1. Document Request
    if any(word in q for word in ["document", "paper", "certificate", "id", "marksheet"]):
        docs = [
            f"**Required Documents for {course}:**",
            "  • 10th & 12th Standard Marksheets (Original + 2 copies)",
            "  • Transfer Certificate (TC) & Migration Certificate",
            "  • 5 Passport-size Photographs",
            "  • Valid ID Proof (Aadhar/Passport)",
            "  • Entrance Exam Scorecard (if applicable)",
            "",
            "Would you like me to send you the official document checklist PDF, or are you ready to see the application link?"
        ]
        return "\n".join(docs)

    # 2. Process/Procedure Request
    if any(word in q for word in ["process", "procedure", "how to", "steps", "guide"]):
        # REFINED: Action-first format (execution mode, not guidance)
        action_first = [
            f"Great! You're ready to apply for **{course}**.",
            "",
            f"👉 **Start here:** Visit our application portal and create your profile.",
            f"   (You can complete this in ~10 minutes)",
            "",
            f"📄 **You'll need:** 10th & 12th marks + ID proof",
            "",
            f"I can walk you through any step or answer document questions if needed."
        ]
        return "\n".join(action_first)

    # 3. Curriculum/Structure Request
    if any(word in q for word in ["structure", "subject", "curriculum", "syllabus"]):
        return (
            f"**{course} Course Structure:**\n"
            f"  • Duration: 3 years (6 semesters)\n"
            f"  • Core Focus: Industry-aligned curriculum with practical labs.\n"
            f"  • Internships: Mandatory 8-week internship in the final year.\n\n"
            f"Would you like to know about the eligibility requirements or the placement records for this course?"
        )

    # 4. Eligibility Request
    if any(word in q for word in ["eligib", "marks", "qualify", "requirement"]):
        from app.services.counselor.constraint_advisor import run_constraint
        result = run_constraint(query, context)
        return result.get("constraint", f"You typically need a minimum of 50% in your 12th standard to apply for {course}.")

    # Default: Action-first overview (when user asks general "how to apply")
    overview = [
        f"Perfect! You're ready to apply for **{course}**.",
        "",
        f"👉 **Next Step:** Start your application at our portal.",
        f"   Time needed: ~10 minutes",
        "",
        f"📋 **Required:** 10th & 12th marks + Valid ID",
        "",
        f"Let me know if you need help with any documents or have questions!"
    ]
    return "\n".join(overview)
