"""
Stage Controller - Conversation Flow Control

This is the BRAIN that decides what runs and what is blocked.
Sits at the TOP of the system, before any other logic.

Stage Priority (Highest to Lowest):
1. APPLY - User wants to apply → Structured steps (no personality)
2. DECISION_LOCKED - Course locked → No re-ranking, only deepening
3. DECISION - User confirmed choice → Lock course, move to conversion
4. GUIDANCE - User exploring options → Run guidance engine
5. CONFUSION - User stuck → Simplify and redirect

Rules:
- Higher stage ALWAYS overrides lower stage
- Once locked, NEVER unlock (unless explicit reset)
- Apply intent = immediate execution (no soft talk)
- Fallback ONLY when no signal exists
"""

from typing import Dict, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

# ============================================
# STAGE DEFINITIONS
# ============================================
class Stage:
    APPLY = "apply"
    DECISION_LOCKED = "decision_locked"
    DECISION = "decision"
    GUIDANCE = "guidance"
    CONFUSION = "confusion"
    FALLBACK = "fallback"

# Stage priority (higher number = higher priority)
STAGE_PRIORITY = {
    Stage.APPLY: 100,
    Stage.DECISION_LOCKED: 90,
    Stage.DECISION: 80,
    Stage.GUIDANCE: 50,
    Stage.CONFUSION: 30,
    Stage.FALLBACK: 0
}

# ============================================
# STAGE DETECTION PATTERNS
# ============================================
APPLY_PATTERNS = [
    r"\bapply\b", r"\bapplication\b", r"\bhow to apply\b",
    r"\badmission process\b", r"\bsteps\b", r"\bprocedure\b",
    r"\bdocuments\b", r"\bform\b", r"\benroll\b",
    r"\bjoin\b", r"\bregister\b", r"\bstart application\b"
]

DECISION_PATTERNS = [
    r"\bi think\b", r"\bi'll go with\b", r"\bseems good\b",
    r"\blooks good\b", r"\bthat works\b", r"\bthis works\b",
    r"\bsounds good\b", r"\bsounds right\b", r"\bi choose\b",
    r"\bi prefer\b", r"\bgoing with\b", r"\blet's go with\b",
    r"\byeah\b.*\bgood\b", r"\bokay\b.*\bgood\b",
    # Implicit decision patterns (real user language)
    r"\byeah\b", r"\bokay\b", r"\bok\b", r"\byes\b", r"\bfine\b", r"\bcool\b",
    r"\balright\b", r"\bsure\b", r"\byep\b", r"\byup\b",
    r"\bmakes sense\b", r"\bsounds right\b", r"\bthat's good\b",
    r"\bi'll do\b", r"\blet's do\b", r"\bgo with\b", r"\bgo for\b"
]

CONFUSION_PATTERNS = [
    r"\bconfused\b", r"\bnot sure\b", r"\bidk\b",
    r"\bwhat should i do\b", r"\bdon't know\b", r"\bhelp\b"
]

# ============================================
# STAGE DETECTION
# ============================================
def detect_stage(query: str, context: Dict) -> str:
    """
    Detect current conversation stage.
    Returns highest priority stage that applies.
    """
    # Normalize query for robust detection
    query_lower = query.lower().strip()
    
    # ╔════════════════════════════════════════════════════════════╗
    # ║ PRIORITY 1: APPLY (MUST CHECK FIRST - OVERRIDES ALL)       ║
    # ║ If user asks about application, IMMEDIATELY switch to apply ║
    # ╚════════════════════════════════════════════════════════════╝
    if any(re.search(p, query_lower) for p in APPLY_PATTERNS):
        logger.info("[STAGE] APPLY detected - switching to structured mode (HIGHEST PRIORITY)")
        return Stage.APPLY
    
    # PRIORITY 2: DECISION_LOCKED
    # If course is already locked, stay locked
    if context.get("locked_course"):
        logger.info(f"[STAGE] DECISION_LOCKED - course: {context['locked_course']}")
        return Stage.DECISION_LOCKED
    
    # PRIORITY 3-4: DECISION & GUIDANCE (based on commitment signal)
    # HARD RULE: Explicit course mention WITH commitment signal = decision
    # Commitment: "I want BCA", "I'll go with BCA", "I choose BCA"
    # NOT commitment: "Tell me about BCA", "BCA vs BBA", "Which is better?"
    entities = context.get("_entities") or context
    extracted_courses = entities.get("courses", [])
    
    # Check for commitment signal
    has_commitment = any(word in query_lower for word in [
        "i want", "i will", "i choose", "i'm choosing",
        "i think", "i'll go with", "going with", "decided"
    ])
    
    if extracted_courses and has_commitment and not context.get("locked_course"):
        logger.info(f"[STAGE] DECISION detected - course + commitment: {extracted_courses[0]}")
        context["_decision_confidence"] = 0.95
        context["_explicit_course_mention"] = True
        return Stage.DECISION
    elif extracted_courses and not context.get("locked_course"):
        logger.info(f"[STAGE] GUIDANCE - course mentioned but no commitment: {extracted_courses[0]}")
        return Stage.GUIDANCE
    
    # STAGE 3: DECISION
    # User confirmed a choice → lock it
    # Use production decision detector with confidence
    from app.services.counselor.decision_detector import detect_decision as detect_decision_confident
    
    decision_result = detect_decision_confident(query_lower, context)
    if decision_result["is_decision"] and decision_result["confidence"] >= 0.75:
        logger.info(f"[STAGE] DECISION detected - confidence: {decision_result['confidence']:.2f}, method: {decision_result['method']}")
        
        # Store decision confidence in context for analytics
        context["_decision_confidence"] = decision_result["confidence"]
        
        # If low confidence (0.75-0.85), may need clarification
        if decision_result["needs_clarification"]:
            context["_needs_decision_clarification"] = True
        
        return Stage.DECISION
    
    # STAGE 4: GUIDANCE
    # User has marks OR interest OR goal → run guidance
    has_marks = context.get("marks") is not None or re.search(r'\d{2}\s*%', query_lower) or re.search(r'got\s+\d{2}', query_lower)
    has_interest = context.get("interests") is not None
    has_courses = bool(context.get("courses"))
    has_goal_signal = any(word in query_lower for word in ["salary", "job", "abroad", "mba", "business", "coding", "finance", "hotel", "commerce"])
    
    has_signal = has_marks or has_interest or has_courses or has_goal_signal
    
    if has_signal:
        logger.info("[STAGE] GUIDANCE - user has signal")
        return Stage.GUIDANCE
    
    # STAGE 5: CONFUSION
    # User explicitly confused
    if any(re.search(p, query_lower) for p in CONFUSION_PATTERNS):
        logger.info("[STAGE] CONFUSION detected")
        return Stage.CONFUSION
    
    # STAGE 6: FALLBACK (Lowest Priority)
    # No signal, no context, no idea what user wants
    logger.info("[STAGE] FALLBACK - no signal detected")
    return Stage.FALLBACK


def should_block_stage(current_stage: str, requested_stage: str) -> bool:
    """
    Check if requested stage should be blocked by current stage.
    Higher priority stages block lower priority stages.
    """
    current_priority = STAGE_PRIORITY.get(current_stage, 0)
    requested_priority = STAGE_PRIORITY.get(requested_stage, 0)
    
    return current_priority > requested_priority


# ============================================
# DECISION LOCKING
# ============================================
def lock_decision(context: Dict, course: str) -> Dict:
    """
    Lock a course decision.
    After this, system CANNOT switch courses.
    """
    context["locked_course"] = course
    context["lock_timestamp"] = __import__("time").time()
    context["conversion_stage"] = "decision_confirmed"
    
    logger.info(f"[LOCK] Course locked: {course}")
    return context


def is_decision_locked(context: Dict) -> bool:
    """Check if a decision is locked"""
    return context.get("locked_course") is not None


def get_locked_course(context: Dict) -> Optional[str]:
    """Get the locked course (if any)"""
    return context.get("locked_course")


# ============================================
# GOAL-INTEREST COMPATIBILITY CHECK
# ============================================
GOAL_INTEREST_COMPATIBILITY = {
    "salary": {
        "compatible": ["BCA", "MBA", "MCA"],  # High-paying courses
        "incompatible": ["BHM"]  # Lower salary range
    },
    "job": {
        "compatible": ["BCA", "BBA", "B.Com", "BHM"],  # All have placements
        "incompatible": []
    },
    "abroad": {
        "compatible": ["BCA", "MBA", "MCA"],  # Tech/management travel well
        "incompatible": ["BHM"]  # Hospitality is location-specific
    },
    "entrepreneurship": {
        "compatible": ["BBA", "MBA"],  # Business-focused
        "incompatible": []
    },
    "higher_studies": {
        "compatible": ["BCA", "BBA", "B.Com"],  # All have postgrad paths
        "incompatible": []
    },
    "stability": {
        "compatible": ["B.Com", "BBA", "BCA"],  # Stable careers
        "incompatible": []
    }
}


def check_goal_interest_compatibility(goal: str, interest_course: str) -> Dict:
    """
    Check if goal and interest are compatible.
    
    Returns:
        {
            "compatible": bool,
            "conflict": str or None,
            "clarification_needed": bool
        }
    """
    if not goal or not interest_course:
        return {"compatible": True, "conflict": None, "clarification_needed": False}
    
    goal_compat = GOAL_INTEREST_COMPATIBILITY.get(goal, {})
    compatible_courses = goal_compat.get("compatible", [])
    incompatible_courses = goal_compat.get("incompatible", [])
    
    # Check incompatibility first
    if interest_course in incompatible_courses:
        return {
            "compatible": False,
            "conflict": f"Your interest suggests {interest_course}, but your goal ({goal}) typically aligns better with other courses.",
            "clarification_needed": True
        }
    
    # Check compatibility
    if compatible_courses and interest_course not in compatible_courses:
        return {
            "compatible": False,
            "conflict": f"Your interest suggests {interest_course}, but your goal ({goal}) might be better served by {compatible_courses[0]}.",
            "clarification_needed": True
        }
    
    return {"compatible": True, "conflict": None, "clarification_needed": False}


def generate_clarification_question(goal: str, interest_course: str, goal_course: str) -> str:
    """
    Generate clarification question when goal and interest conflict.
    """
    goal_names = {
        "salary": "high salary",
        "job": "quick placement",
        "abroad": "working abroad",
        "entrepreneurship": "starting a business",
        "higher_studies": "pursuing higher studies",
        "stability": "career stability"
    }
    
    goal_text = goal_names.get(goal, goal)
    
    return (
        f"I notice you're interested in **{interest_course}** but your goal is **{goal_text}**.\n\n"
        f"Would you prefer:\n"
        f"1. **{interest_course}** (following your interest)\n"
        f"2. **{goal_course}** (optimized for {goal_text})\n\n"
        f"Which matters more to you right now?"
    )


# ============================================
# STAGE EXECUTION ROUTER
# ============================================
def route_by_stage(stage: str, query: str, context: Dict) -> Dict:
    """
    Route execution based on stage.
    This is the MAIN CONTROL FUNCTION.
    
    Returns:
        {
            "action": "apply" | "guidance" | "clarify" | "fallback",
            "data": {...},
            "block_lower_stages": bool
        }
    """
    
    # STAGE 1: APPLY (Structured Execution)
    if stage == Stage.APPLY:
        locked_course = get_locked_course(context)
        if not locked_course:
            # No course locked yet, need to guide first
            return {
                "action": "clarify",
                "data": {
                    "message": "Which course would you like to apply for? Let me know and I'll walk you through the steps."
                },
                "block_lower_stages": True
            }
        
        return {
            "action": "apply",
            "data": {
                "course": locked_course,
                "mode": "structured"  # NOT conversational
            },
            "block_lower_stages": True
        }
    
    # STAGE 2: DECISION_LOCKED (Stay Locked)
    if stage == Stage.DECISION_LOCKED:
        locked_course = get_locked_course(context)
        
        return {
            "action": "deepening",
            "data": {
                "course": locked_course,
                "message": f"You've chosen **{locked_course}**. What would you like to know more about?",
                "options": ["Fees", "Placement", "Curriculum", "Admission Process"]
            },
            "block_lower_stages": True
        }
    
    # STAGE 3: DECISION (Lock Course)
    if stage == Stage.DECISION:
        # Need to determine which course to lock
        # This requires running guidance first to get top course
        return {
            "action": "lock_and_guide",
            "data": {
                "lock_after_guidance": True
            },
            "block_lower_stages": False
        }
    
    # STAGE 4: GUIDANCE (Run Guidance Engine)
    if stage == Stage.GUIDANCE:
        return {
            "action": "guidance",
            "data": {},
            "block_lower_stages": False
        }
    
    # STAGE 5: CONFUSION (Simplify)
    if stage == Stage.CONFUSION:
        return {
            "action": "simplify",
            "data": {
                "message": "Let's simplify this. Tell me:\n1. Your 12th marks (%)\n2. What you're interested in (business/tech/finance/hospitality)"
            },
            "block_lower_stages": True
        }
    
    # STAGE 6: FALLBACK (Last Resort)
    return {
        "action": "fallback",
        "data": {
            "message": "I can help you choose the right course at AIMS. Tell me about your marks or interests to get started."
        },
        "block_lower_stages": False
    }


# ============================================
# MAIN STAGE CONTROLLER
# ============================================
def execute_stage_control(query: str, context: Dict) -> Dict:
    """
    Main stage controller function.
    This is called FIRST, before any other logic.
    
    Returns:
        {
            "stage": str,
            "action": str,
            "data": dict,
            "should_run_guidance": bool,
            "should_lock": bool,
            "locked_course": str or None
        }
    """
    # Detect current stage
    stage = detect_stage(query, context)
    
    # Route by stage
    routing = route_by_stage(stage, query, context)
    
    # Build response
    result = {
        "stage": stage,
        "action": routing["action"],
        "data": routing["data"],
        "should_run_guidance": routing["action"] in ["guidance", "lock_and_guide"],
        "should_lock": routing["action"] == "lock_and_guide",
        "locked_course": get_locked_course(context),
        "block_lower_stages": routing["block_lower_stages"]
    }
    
    logger.info(f"[STAGE_CONTROL] Stage: {stage} | Action: {routing['action']} | Locked: {result['locked_course']}")
    
    return result


# ============================================
# TESTING
# ============================================
def test_stage_controller():
    """Test stage controller logic"""
    print("Testing Stage Controller...")
    
    test_cases = [
        # Apply intent (highest priority)
        ({"query": "how to apply", "context": {}}, Stage.APPLY),
        ({"query": "application process", "context": {}}, Stage.APPLY),
        
        # Decision locked (stays locked)
        ({"query": "what about fees", "context": {"locked_course": "BCA"}}, Stage.DECISION_LOCKED),
        ({"query": "tell me about placement", "context": {"locked_course": "BBA"}}, Stage.DECISION_LOCKED),
        
        # Decision (will lock)
        ({"query": "BCA sounds good", "context": {}}, Stage.DECISION),
        ({"query": "I'll go with BBA", "context": {}}, Stage.DECISION),
        
        # Guidance (has signal)
        ({"query": "I got 70%", "context": {}}, Stage.GUIDANCE),
        ({"query": "I like coding", "context": {}}, Stage.GUIDANCE),
        
        # Confusion
        ({"query": "I'm confused", "context": {}}, Stage.CONFUSION),
        
        # Fallback
        ({"query": "hello", "context": {}}, Stage.FALLBACK),
    ]
    
    for test_input, expected_stage in test_cases:
        query = test_input["query"]
        context = test_input["context"]
        
        result = execute_stage_control(query, context)
        detected_stage = result["stage"]
        
        status = "✅" if detected_stage == expected_stage else "❌"
        print(f"{status} '{query}' → {detected_stage} (expected: {expected_stage})")


if __name__ == "__main__":
    test_stage_controller()
