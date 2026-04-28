"""
Adaptive Questioning Layer
===========================
Asks the right question at the right time — not generic, not repetitive.

Question priority:
  1. Interest (highest — needed to unlock decision)
  2. Goal  (salary vs growth vs study path)
  3. Constraint (budget / location)
  4. Fallback

Every question is:
  • context-aware  (based on top_course + known signals)
  • stage-aware    (earlier questions unlock later decisions)
  • memory-aware   (never repeats last asked question)
  • tone-wrapped   (feels like a counselor, not a form)
"""
import random
from typing import Dict, Optional, List

# ─────────────────────────────────────────────
# QUESTION BUCKETS
# ─────────────────────────────────────────────

INTEREST_QUESTIONS: Dict[str, List[str]] = {
    "business": [
        "Do you see yourself in management and strategy roles, or working more with numbers like finance and accounts?",
        "Would you enjoy leading teams and building products, or analyzing financial data and audits more?",
        "Are you drawn more to marketing and sales, or to accounting and banking?"
    ],
    "tech": [
        "Have you tried coding or programming before — even basic projects?",
        "Do you enjoy problem-solving on a computer, or is it more of a curiosity you want to explore?",
        "Would you prefer building software, or using technology in a business/data context?"
    ],
    "hospitality": [
        "Do you enjoy working with people in dynamic environments like hotels or events?",
        "Are you more interested in the operational side of hospitality, or customer-facing roles?"
    ],
    "commerce": [
        "Is your interest more in accountancy and taxation, or in banking and financial services?",
        "Do you plan to pursue professional certifications like CA, or prefer a corporate finance path?"
    ],
    "general": [
        "What kind of work do you see yourself enjoying daily — desk-based analysis, working with people, or building things?",
        "Do you prefer practical, applied work or more theoretical/academic learning?",
        "Are you more comfortable with numbers, words, or technology?"
    ]
}

GOAL_QUESTIONS: List[str] = [
    "Are you aiming for a job right after graduation, or are you planning for higher studies like MBA or M.Com?",
    "Is your priority a high starting salary quickly, or building expertise for long-term career growth?",
    "Are you looking to stay close to home, or open to opportunities in metro cities?",
    "Do you see yourself specializing in one domain, or preferring a broad business/management role?"
]

CONSTRAINT_QUESTIONS: List[str] = [
    "Do you have any budget constraints I should factor into the recommendation?",
    "Are you looking at a 3-year undergraduate program, or are you open to 2-year postgraduate options as well?",
    "Is there a specific city or region you're targeting for college?"
]

# ─────────────────────────────────────────────
# COURSE → INTEREST DOMAIN MAPPING
# ─────────────────────────────────────────────
COURSE_INTEREST_DOMAIN: Dict[str, str] = {
    "BBA":   "business",
    "MBA":   "business",
    "BCA":   "tech",
    "MCA":   "tech",
    "B.Com": "commerce",
    "BHM":   "hospitality",
}

# ─────────────────────────────────────────────
# TONE WRAPPER
# ─────────────────────────────────────────────
_TONE_PREFIXES = [
    "To guide you better, just help me with this:\n",
    "One quick thing that'll sharpen this recommendation:\n",
    "Before I refine this further:\n",
    "This'll help me narrow it down for you:\n",
]

def _wrap_tone(question: str) -> str:
    """Wrap a question with a counselor-tone prefix to avoid interrogative feel."""
    prefix = random.choice(_TONE_PREFIXES)
    return f"{prefix}{question}"


# ─────────────────────────────────────────────
# MEMORY-AWARE DEDUP
# ─────────────────────────────────────────────
def _is_repeat(question: str, context: Dict) -> bool:
    """Check if this exact question was already asked in this session."""
    asked = context.get("_asked_questions", [])
    return question in asked


def _mark_asked(question: str, context: Dict) -> None:
    """Record the question as asked (modifies context in-place)."""
    asked = context.setdefault("_asked_questions", [])
    if question not in asked:
        asked.append(question)
    # Also write to SESSION_MEMORY if session_id available
    session_id = context.get("session_id")
    if session_id:
        try:
            from app.services.counselor.memory import store_last_question
            store_last_question(session_id, question)
        except ImportError:
            pass


def _pick_fresh(bucket: List[str], context: Dict) -> str:
    """Pick a random question from a bucket that hasn't been asked yet."""
    asked = context.get("_asked_questions", [])
    fresh = [q for q in bucket if q not in asked]
    
    if not fresh:
        # All questions in this bucket were asked. 
        # To avoid immediate repeat, pick any EXCEPT the last one if possible
        last_q = asked[-1] if asked else None
        alternates = [q for q in bucket if q != last_q]
        return random.choice(alternates) if alternates else random.choice(bucket)
        
    return random.choice(fresh)


# ─────────────────────────────────────────────
# MAIN ADAPTIVE SELECTOR
# ─────────────────────────────────────────────
def get_adaptive_question(context: Dict, guidance: Dict) -> str:
    """
    Return the single most useful question to ask right now.

    Priority:
      1. Interest (unlocks decision)
      2. Goal (refines recommendation)
      3. Constraint (personalises further)
      4. Fallback

    Returns a tone-wrapped, non-repeated question.
    """
    marks    = context.get("marks")
    interest = context.get("interests") or context.get("interest")
    goal     = context.get("goal")
    budget   = context.get("budget")
    top_course = guidance.get("top_course", "")
    top2_courses: list = guidance.get("recommended_courses", [])[:2]

    # ── Priority 1: Missing interest ──
    # Switch to goal if we've asked 2 interest questions and still no interest
    asked_interest_count = len([q for q in context.get("_asked_questions", []) if any(q in b for b in INTEREST_QUESTIONS.values())])
    
    if not interest and asked_interest_count < 2:
        domain = COURSE_INTEREST_DOMAIN.get(top_course, "general")
        bucket = INTEREST_QUESTIONS.get(domain, INTEREST_QUESTIONS["general"])
        question = _pick_fresh(bucket, context)
        _mark_asked(question, context)

        # Build contextual lead-in using top 2 courses
        if len(top2_courses) >= 2:
            a, b = top2_courses[0], top2_courses[1]
            lead = (
                f"Based on your marks, **{a}** and **{b}** are both strong options.\n\n"
                f"{_wrap_tone(question)}"
            )
        else:
            lead = _wrap_tone(question)
        return lead

    # ── Priority 2: Missing goal ──
    if not goal:
        question = _pick_fresh(GOAL_QUESTIONS, context)
        _mark_asked(question, context)
        return _wrap_tone(question)

    # ── Priority 3: Missing constraint ──
    if not budget and not context.get("location"):
        question = _pick_fresh(CONSTRAINT_QUESTIONS, context)
        _mark_asked(question, context)
        return _wrap_tone(question)

    # ── Priority 4: Fallback ──
    return "What would you like to explore next — course structure, career paths, or admission steps?"


# ─────────────────────────────────────────────
# STAGE-AWARE UPGRADE
# ─────────────────────────────────────────────
def get_pre_decision_question(context: Dict, guidance: Dict) -> Optional[str]:
    """
    For students who are almost decision-ready (soft bridge stage).
    Asks the single question that unlocks full decision_ready=True.
    Returns None if all signals are already complete.
    """
    marks    = context.get("marks")
    interest = context.get("interests") or context.get("interest")
    goal     = context.get("goal")
    top_course = guidance.get("top_course", "")

    if not marks:
        return _wrap_tone(
            "What were your board exam marks? That'll make this recommendation much more precise."
        )
        
    asked_interest_count = len([q for q in context.get("_asked_questions", []) if any(q in b for b in INTEREST_QUESTIONS.values())])
    
    if not interest and asked_interest_count < 2:
        domain = COURSE_INTEREST_DOMAIN.get(top_course, "general")
        bucket = INTEREST_QUESTIONS.get(domain, INTEREST_QUESTIONS["general"])
        question = _pick_fresh(bucket, context)
        _mark_asked(question, context)
        return _wrap_tone(question)
        
    if not goal:
        question = _pick_fresh(GOAL_QUESTIONS, context)
        _mark_asked(question, context)
        return _wrap_tone(question)

    return None  # all signals complete → trigger hard bridge
