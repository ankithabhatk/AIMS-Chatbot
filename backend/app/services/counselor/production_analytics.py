"""
Production Analytics Layer

Tracks critical metrics for optimization:
1. Decision → Apply rate (conversion funnel)
2. Fallback trigger rate (system confusion)
3. Clarification frequency (confidence issues)
4. Stage transition patterns (user journey)
5. Drop-off points (where users leave)

This is what turns a working system into an optimizing machine.
"""

import logging
import time
from typing import Dict, Optional, List
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

# ============================================
# IN-MEMORY ANALYTICS STORE
# (In production: replace with Redis/PostgreSQL)
# ============================================
ANALYTICS_STORE = {
    "sessions": {},  # session_id → session data
    "metrics": defaultdict(int),  # metric_name → count
    "stage_transitions": defaultdict(int),  # stage_from→stage_to → count
    "drop_offs": defaultdict(int),  # stage → count
    "clarifications": [],  # list of clarification events
    "fallbacks": [],  # list of fallback events
    "sentiment_conflicts": [],  # list of sentiment conflict events
    "clarification_responses": [],  # list of clarification response events
    "locked_dropoffs": [],  # list of locked→apply dropoff events
}


# ============================================
# SESSION TRACKING
# ============================================
def init_session(session_id: str) -> Dict:
    """Initialize analytics for a new session"""
    ANALYTICS_STORE["sessions"][session_id] = {
        "session_id": session_id,
        "start_time": time.time(),
        "last_activity": time.time(),
        "stages": [],  # list of stages visited
        "decisions": [],  # list of decision events
        "clarifications": 0,
        "fallbacks": 0,
        "locked_course": None,
        "applied": False,
        "completed": False,
        "turn_count": 0,
        "awaiting_clarification": False,
        "clarification_turn": None,
        "locked_at": None,
        "apply_started": False,
    }
    return ANALYTICS_STORE["sessions"][session_id]


def get_session(session_id: str) -> Dict:
    """Get session analytics data"""
    if session_id not in ANALYTICS_STORE["sessions"]:
        return init_session(session_id)
    return ANALYTICS_STORE["sessions"][session_id]


def update_session_activity(session_id: str):
    """Update last activity timestamp"""
    session = get_session(session_id)
    session["last_activity"] = time.time()
    session["turn_count"] += 1


# ============================================
# STAGE TRACKING
# ============================================
def track_stage(session_id: str, stage: str, context: Dict = None):
    """Track stage transition"""
    session = get_session(session_id)
    context = context or {}
    
    # Get previous stage
    prev_stage = session["stages"][-1]["stage"] if session["stages"] else "start"
    
    # Record stage
    session["stages"].append({
        "stage": stage,
        "timestamp": time.time(),
        "context": {
            "marks": context.get("marks"),
            "interests": context.get("interests"),
            "locked_course": context.get("locked_course"),
        }
    })
    
    # Track transition
    transition = f"{prev_stage}→{stage}"
    ANALYTICS_STORE["stage_transitions"][transition] += 1
    ANALYTICS_STORE["metrics"][f"stage_{stage}"] += 1
    
    logger.info(f"[ANALYTICS] Session {session_id}: {transition}")


# ============================================
# DECISION TRACKING
# ============================================
def track_decision(session_id: str, decision_data: Dict):
    """
    Track decision event.
    
    decision_data = {
        "query": str,
        "confidence": float,
        "method": str,
        "course": str,
        "locked": bool,
        "clarification_needed": bool
    }
    """
    session = get_session(session_id)
    
    decision_event = {
        "timestamp": time.time(),
        **decision_data
    }
    
    session["decisions"].append(decision_event)
    
    # Track metrics
    ANALYTICS_STORE["metrics"]["decisions_total"] += 1
    
    if decision_data.get("locked"):
        ANALYTICS_STORE["metrics"]["decisions_locked"] += 1
        session["locked_course"] = decision_data.get("course")
    
    if decision_data.get("clarification_needed"):
        ANALYTICS_STORE["metrics"]["decisions_clarified"] += 1
    
    logger.info(f"[ANALYTICS] Decision: {decision_data.get('course')} (conf: {decision_data.get('confidence'):.2f})")


# ============================================
# CLARIFICATION TRACKING
# ============================================
def track_clarification(session_id: str, clarification_data: Dict):
    """
    Track clarification request.
    
    clarification_data = {
        "query": str,
        "confidence": float,
        "course": str,
        "reason": str
    }
    """
    session = get_session(session_id)
    session["clarifications"] += 1
    
    clarification_event = {
        "session_id": session_id,
        "timestamp": time.time(),
        **clarification_data
    }
    
    ANALYTICS_STORE["clarifications"].append(clarification_event)
    ANALYTICS_STORE["metrics"]["clarifications_total"] += 1
    
    logger.info(f"[ANALYTICS] Clarification requested: {clarification_data.get('reason')}")


# ============================================
# FALLBACK TRACKING
# ============================================
def track_fallback(session_id: str, fallback_data: Dict):
    """
    Track fallback trigger.
    
    fallback_data = {
        "query": str,
        "stage": str,
        "reason": str
    }
    """
    session = get_session(session_id)
    session["fallbacks"] += 1
    
    fallback_event = {
        "session_id": session_id,
        "timestamp": time.time(),
        **fallback_data
    }
    
    ANALYTICS_STORE["fallbacks"].append(fallback_event)
    ANALYTICS_STORE["metrics"]["fallbacks_total"] += 1
    
    logger.warning(f"[ANALYTICS] Fallback triggered: {fallback_data.get('reason')}")


# ============================================
# FAILURE CAPTURE LOOP (CRITICAL)
# ============================================
def track_sentiment_conflict(session_id: str, query: str, confidence: float, stage: str, bypassed: bool, outcome: str = "unknown"):
    """
    Track sentiment conflict event (explicit, countable).
    
    This is the ONLY way to know if we're over-blocking.
    
    outcome: "continued" | "dropped" | "converted" | "unknown"
    """
    session = get_session(session_id)
    
    event = {
        "session_id": session_id,
        "query": query,
        "confidence": confidence,
        "stage": stage,
        "bypassed": bypassed,
        "outcome": outcome,
        "timestamp": time.time()
    }
    
    ANALYTICS_STORE["sentiment_conflicts"].append(event)
    ANALYTICS_STORE["metrics"]["sentiment_conflicts_total"] += 1
    
    if bypassed:
        ANALYTICS_STORE["metrics"]["sentiment_conflicts_bypassed"] += 1
    
    logger.info(f"[FAILURE_CAPTURE] Sentiment conflict: bypassed={bypassed}, conf={confidence:.2f}, outcome={outcome}, query='{query}'")


def track_clarification_response(session_id: str, responded: bool, turns_taken: Optional[int] = None, outcome: str = "unknown"):
    """
    Track if user responded to clarification or dropped.
    
    This tells us if clarifications are annoying or helpful.
    
    outcome: "continued" | "dropped" | "converted" | "unknown"
    """
    session = get_session(session_id)
    
    event = {
        "session_id": session_id,
        "responded": responded,
        "turns_taken": turns_taken,
        "outcome": outcome,
        "timestamp": time.time()
    }
    
    ANALYTICS_STORE["clarification_responses"].append(event)
    ANALYTICS_STORE["metrics"]["clarification_responses_total"] += 1
    
    if responded:
        ANALYTICS_STORE["metrics"]["clarification_responses_responded"] += 1
    else:
        ANALYTICS_STORE["metrics"]["clarification_responses_dropped"] += 1
    
    logger.info(f"[FAILURE_CAPTURE] Clarification response: responded={responded}, turns={turns_taken}, outcome={outcome}")


def track_locked_dropoff(session_id: str, course: str, turns_since_lock: int, outcome: str = "dropped"):
    """
    Track when user drops off after locking course (never applies).
    
    This is the REAL conversion leak.
    
    outcome: "dropped" (default for this event)
    """
    session = get_session(session_id)
    
    event = {
        "session_id": session_id,
        "course": course,
        "turns_since_lock": turns_since_lock,
        "outcome": outcome,
        "timestamp": time.time()
    }
    
    ANALYTICS_STORE["locked_dropoffs"].append(event)
    ANALYTICS_STORE["metrics"]["locked_dropoffs_total"] += 1
    
    logger.warning(f"[FAILURE_CAPTURE] Locked dropoff: course={course}, turns_since_lock={turns_since_lock}, outcome={outcome}")


# ============================================
# CONVERSION TRACKING
# ============================================
def track_apply(session_id: str, course: str):
    """Track when user asks to apply"""
    session = get_session(session_id)
    session["applied"] = True
    session["apply_started"] = True
    
    ANALYTICS_STORE["metrics"]["apply_total"] += 1
    
    # Update outcome for previous events in this session
    _update_session_outcome(session_id, "converted")
    
    logger.info(f"[ANALYTICS] Apply triggered: {course}")


def _update_session_outcome(session_id: str, outcome: str):
    """
    Update outcome for all events in this session.
    
    This is called when we know the final outcome (converted, dropped, etc.)
    
    IMPORTANT: Outcomes are transitions, not end states.
    We append to outcome_history instead of overwriting.
    """
    # Update sentiment conflicts
    for event in ANALYTICS_STORE["sentiment_conflicts"]:
        if event["session_id"] == session_id:
            # Track outcome history (outcomes are transitions, not end states)
            if "outcome_history" not in event:
                event["outcome_history"] = [event.get("outcome", "unknown")]
            if outcome not in event["outcome_history"]:
                event["outcome_history"].append(outcome)
            event["outcome"] = outcome  # Current outcome
    
    # Update clarification responses
    for event in ANALYTICS_STORE["clarification_responses"]:
        if event["session_id"] == session_id:
            # Track outcome history
            if "outcome_history" not in event:
                event["outcome_history"] = [event.get("outcome", "unknown")]
            if outcome not in event["outcome_history"]:
                event["outcome_history"].append(outcome)
            event["outcome"] = outcome  # Current outcome
    
    logger.debug(f"[ANALYTICS] Updated session {session_id} outcome to: {outcome}")


def track_completion(session_id: str):
    """Track when user completes application"""
    session = get_session(session_id)
    session["completed"] = True
    
    ANALYTICS_STORE["metrics"]["completions_total"] += 1
    
    logger.info(f"[ANALYTICS] Application completed")


# ============================================
# DROP-OFF TRACKING
# ============================================
def detect_drop_off(session_id: str) -> bool:
    """
    Detect if user has dropped off.
    Drop-off = no activity for >5 minutes
    """
    session = get_session(session_id)
    
    time_since_activity = time.time() - session["last_activity"]
    
    if time_since_activity > 300:  # 5 minutes
        current_stage = session["stages"][-1]["stage"] if session["stages"] else "unknown"
        ANALYTICS_STORE["drop_offs"][current_stage] += 1
        
        # Determine final outcome
        if session.get("applied"):
            final_outcome = "converted"
        else:
            # Check if user engaged but didn't convert (hidden failure)
            if session["turn_count"] > 3:  # Engaged = more than 3 turns
                final_outcome = "engaged_no_conversion"
            else:
                final_outcome = "dropped"
        
        # Update outcome for all events in this session
        _update_session_outcome(session_id, final_outcome)
        
        # FAILURE CAPTURE: Check if user dropped after locking course
        if session.get("locked_at") is not None and not session.get("apply_started"):
            locked_course = session.get("locked_course", "unknown")
            turns_since_lock = session["turn_count"] - session["locked_at"]
            track_locked_dropoff(session_id, locked_course, turns_since_lock, outcome=final_outcome)
        
        # FAILURE CAPTURE: Check if user dropped after clarification
        if session.get("awaiting_clarification"):
            track_clarification_response(session_id, responded=False, turns_taken=None, outcome=final_outcome)
        
        logger.warning(f"[ANALYTICS] Drop-off detected at stage: {current_stage}, outcome: {final_outcome}")
        return True
    
    return False


# ============================================
# OUTCOME ANALYSIS (CRITICAL)
# ============================================
def analyze_sentiment_conflicts_by_outcome() -> Dict:
    """
    Analyze sentiment conflicts by outcome.
    
    This answers: Are we blocking good users?
    """
    conflicts = ANALYTICS_STORE["sentiment_conflicts"]
    
    if not conflicts:
        return {"total": 0, "converted": 0, "dropped": 0, "continued": 0, "engaged_no_conversion": 0, "unknown": 0}
    
    outcomes = {"converted": 0, "dropped": 0, "continued": 0, "engaged_no_conversion": 0, "unknown": 0}
    for event in conflicts:
        outcome = event.get("outcome", "unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    
    return {
        "total": len(conflicts),
        **outcomes,
        "conversion_rate": (outcomes["converted"] / len(conflicts) * 100) if len(conflicts) > 0 else 0,
        "hidden_failure_rate": (outcomes["engaged_no_conversion"] / len(conflicts) * 100) if len(conflicts) > 0 else 0
    }


def analyze_clarifications_by_outcome() -> Dict:
    """
    Analyze clarifications by outcome.
    
    This answers: Are clarifications helping or hurting?
    """
    clarifications = ANALYTICS_STORE["clarification_responses"]
    
    if not clarifications:
        return {"total": 0, "converted": 0, "dropped": 0, "continued": 0, "engaged_no_conversion": 0, "unknown": 0}
    
    outcomes = {"converted": 0, "dropped": 0, "continued": 0, "engaged_no_conversion": 0, "unknown": 0}
    for event in clarifications:
        outcome = event.get("outcome", "unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    
    return {
        "total": len(clarifications),
        **outcomes,
        "conversion_rate": (outcomes["converted"] / len(clarifications) * 100) if len(clarifications) > 0 else 0,
        "drop_rate": (outcomes["dropped"] / len(clarifications) * 100) if len(clarifications) > 0 else 0,
        "hidden_failure_rate": (outcomes["engaged_no_conversion"] / len(clarifications) * 100) if len(clarifications) > 0 else 0
    }


def analyze_locked_dropoffs_by_course() -> Dict:
    """
    Analyze locked dropoffs by course.
    
    This answers: Which courses have highest dropoff?
    """
    dropoffs = ANALYTICS_STORE["locked_dropoffs"]
    
    if not dropoffs:
        return {}
    
    by_course = defaultdict(int)
    for event in dropoffs:
        course = event.get("course", "unknown")
        by_course[course] += 1
    
    return dict(sorted(by_course.items(), key=lambda x: x[1], reverse=True))


# ============================================
# METRICS CALCULATION
# ============================================
def calculate_conversion_funnel() -> Dict:
    """
    Calculate conversion funnel metrics.
    
    Returns:
        {
            "guidance_to_decision": float,  # % who make decision
            "decision_to_locked": float,    # % who lock course
            "locked_to_apply": float,       # % who ask to apply
            "apply_to_complete": float      # % who complete
        }
    """
    metrics = ANALYTICS_STORE["metrics"]
    
    guidance_count = metrics.get("stage_guidance", 0)
    decision_count = metrics.get("decisions_total", 0)
    locked_count = metrics.get("decisions_locked", 0)
    apply_count = metrics.get("apply_total", 0)
    complete_count = metrics.get("completions_total", 0)
    
    return {
        "guidance_to_decision": (decision_count / guidance_count * 100) if guidance_count > 0 else 0,
        "decision_to_locked": (locked_count / decision_count * 100) if decision_count > 0 else 0,
        "locked_to_apply": (apply_count / locked_count * 100) if locked_count > 0 else 0,
        "apply_to_complete": (complete_count / apply_count * 100) if apply_count > 0 else 0,
    }


def calculate_fallback_rate() -> float:
    """Calculate fallback trigger rate (% of total queries)"""
    total_queries = sum(1 for s in ANALYTICS_STORE["sessions"].values() for _ in s["stages"])
    fallback_count = ANALYTICS_STORE["metrics"].get("fallbacks_total", 0)
    
    return (fallback_count / total_queries * 100) if total_queries > 0 else 0


def calculate_clarification_frequency() -> float:
    """Calculate clarification frequency (% of decisions)"""
    decision_count = ANALYTICS_STORE["metrics"].get("decisions_total", 0)
    clarification_count = ANALYTICS_STORE["metrics"].get("clarifications_total", 0)
    
    return (clarification_count / decision_count * 100) if decision_count > 0 else 0


# ============================================
# ADAPTIVE THRESHOLDS
# ============================================
def get_adaptive_threshold(session_id: str, base_threshold: float = 0.75) -> float:
    """
    Get adaptive confidence threshold based on interaction depth.
    
    Later in conversation = lower threshold (easier to lock)
    """
    session = get_session(session_id)
    interaction_depth = session["turn_count"]
    
    # Adjust threshold based on depth
    if interaction_depth > 5:
        # Deep conversation - user is engaged, lower threshold
        adjusted = base_threshold - 0.05
    elif interaction_depth > 3:
        # Medium conversation - slightly lower threshold
        adjusted = base_threshold - 0.02
    else:
        # Early conversation - keep base threshold
        adjusted = base_threshold
    
    logger.debug(f"[ADAPTIVE_THRESHOLD] Depth: {interaction_depth}, Threshold: {adjusted:.2f}")
    
    return max(adjusted, 0.65)  # Never go below 0.65


# ============================================
# INTEREST STABILIZATION
# ============================================
def stabilize_interest(session_id: str, new_interest: str, new_confidence: float, context: Dict) -> bool:
    """
    Prevent interest oscillation.
    
    Returns True if new interest should be accepted, False if should be ignored.
    """
    session = get_session(session_id)
    
    # Get locked interest from context
    locked_interest = context.get("locked_interest")
    locked_confidence = context.get("locked_interest_confidence", 0.0)
    
    if not locked_interest:
        # No locked interest yet, accept new one
        context["locked_interest"] = new_interest
        context["locked_interest_confidence"] = new_confidence
        return True
    
    # Check if new interest is strong enough to override
    if new_confidence > locked_confidence + 0.15:  # Needs to be significantly stronger
        logger.info(f"[INTEREST_STABILIZATION] Override: {locked_interest} → {new_interest} (conf: {new_confidence:.2f})")
        context["locked_interest"] = new_interest
        context["locked_interest_confidence"] = new_confidence
        return True
    else:
        logger.info(f"[INTEREST_STABILIZATION] Keeping: {locked_interest} (new conf too low: {new_confidence:.2f})")
        return False


# ============================================
# SILENT USER RE-ENGAGEMENT
# ============================================
def check_silent_user(session_id: str) -> Optional[str]:
    """
    Check if user has gone silent after conversion push.
    
    Returns nudge message if needed, None otherwise.
    """
    session = get_session(session_id)
    
    # Check if we're in a critical stage
    if not session["stages"]:
        return None
    
    current_stage = session["stages"][-1]["stage"]
    
    # Only nudge in decision_locked or after conversion push
    if current_stage not in ["decision_locked", "conversion"]:
        return None
    
    # Check time since last activity
    time_since_activity = time.time() - session["last_activity"]
    
    # If silent for 2-3 minutes, nudge
    if 120 < time_since_activity < 180:
        locked_course = session.get("locked_course", "your chosen course")
        
        nudges = [
            f"Just checking — do you want to proceed with {locked_course} admission or explore a bit more?",
            f"Still there? Let me know if you'd like to see the {locked_course} application steps.",
            f"No rush! Would you like me to walk you through the {locked_course} admission process?",
        ]
        
        import random
        return random.choice(nudges)
    
    return None


# ============================================
# ANALYTICS DASHBOARD
# ============================================
def get_analytics_dashboard() -> Dict:
    """
    Get complete analytics dashboard.
    
    Returns all key metrics for monitoring.
    """
    funnel = calculate_conversion_funnel()
    fallback_rate = calculate_fallback_rate()
    clarification_freq = calculate_clarification_frequency()
    
    # Get top drop-off stages
    drop_offs = sorted(ANALYTICS_STORE["drop_offs"].items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Get stage transition patterns
    transitions = sorted(ANALYTICS_STORE["stage_transitions"].items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Calculate failure capture metrics
    sentiment_conflicts_total = ANALYTICS_STORE["metrics"].get("sentiment_conflicts_total", 0)
    sentiment_conflicts_bypassed = ANALYTICS_STORE["metrics"].get("sentiment_conflicts_bypassed", 0)
    clarification_responses_total = ANALYTICS_STORE["metrics"].get("clarification_responses_total", 0)
    clarification_responses_responded = ANALYTICS_STORE["metrics"].get("clarification_responses_responded", 0)
    locked_dropoffs_total = ANALYTICS_STORE["metrics"].get("locked_dropoffs_total", 0)
    
    sentiment_conflict_rate = (sentiment_conflicts_total / ANALYTICS_STORE["metrics"].get("decisions_total", 1) * 100) if ANALYTICS_STORE["metrics"].get("decisions_total", 0) > 0 else 0
    clarification_response_rate = (clarification_responses_responded / clarification_responses_total * 100) if clarification_responses_total > 0 else 0
    locked_to_apply_rate = ((ANALYTICS_STORE["metrics"].get("apply_total", 0) / ANALYTICS_STORE["metrics"].get("decisions_locked", 1)) * 100) if ANALYTICS_STORE["metrics"].get("decisions_locked", 0) > 0 else 0
    
    return {
        "conversion_funnel": funnel,
        "fallback_rate": fallback_rate,
        "clarification_frequency": clarification_freq,
        "total_sessions": len(ANALYTICS_STORE["sessions"]),
        "total_decisions": ANALYTICS_STORE["metrics"].get("decisions_total", 0),
        "total_locked": ANALYTICS_STORE["metrics"].get("decisions_locked", 0),
        "total_applied": ANALYTICS_STORE["metrics"].get("apply_total", 0),
        "total_completed": ANALYTICS_STORE["metrics"].get("completions_total", 0),
        "top_drop_offs": drop_offs,
        "top_transitions": transitions,
        # FAILURE CAPTURE METRICS
        "sentiment_conflict_rate": sentiment_conflict_rate,
        "sentiment_conflicts_total": sentiment_conflicts_total,
        "sentiment_conflicts_bypassed": sentiment_conflicts_bypassed,
        "clarification_response_rate": clarification_response_rate,
        "clarification_responses_total": clarification_responses_total,
        "clarification_responses_responded": clarification_responses_responded,
        "locked_to_apply_rate": locked_to_apply_rate,
        "locked_dropoffs_total": locked_dropoffs_total,
    }


def print_analytics_dashboard():
    """Print analytics dashboard to console"""
    dashboard = get_analytics_dashboard()
    
    print("\n" + "=" * 60)
    print("PRODUCTION ANALYTICS DASHBOARD")
    print("=" * 60)
    
    print("\n📊 CONVERSION FUNNEL:")
    funnel = dashboard["conversion_funnel"]
    print(f"  Guidance → Decision: {funnel['guidance_to_decision']:.1f}%")
    print(f"  Decision → Locked:   {funnel['decision_to_locked']:.1f}%")
    print(f"  Locked → Apply:      {funnel['locked_to_apply']:.1f}%")
    print(f"  Apply → Complete:    {funnel['apply_to_complete']:.1f}%")
    
    print("\n⚠️ SYSTEM HEALTH:")
    print(f"  Fallback Rate:       {dashboard['fallback_rate']:.1f}%")
    print(f"  Clarification Freq:  {dashboard['clarification_frequency']:.1f}%")
    
    print("\n🔥 FAILURE CAPTURE (CRITICAL):")
    print(f"  Sentiment Conflict Rate:     {dashboard['sentiment_conflict_rate']:.1f}% (target: <30%)")
    print(f"  Sentiment Conflicts Bypassed: {dashboard['sentiment_conflicts_bypassed']}/{dashboard['sentiment_conflicts_total']}")
    print(f"  Clarification Response Rate:  {dashboard['clarification_response_rate']:.1f}% (target: >60%)")
    print(f"  Locked → Apply Rate:          {dashboard['locked_to_apply_rate']:.1f}% (target: >50%)")
    print(f"  Locked Dropoffs:              {dashboard['locked_dropoffs_total']}")
    
    # Outcome analysis
    sentiment_outcomes = analyze_sentiment_conflicts_by_outcome()
    clarification_outcomes = analyze_clarifications_by_outcome()
    
    if sentiment_outcomes["total"] > 0:
        print(f"\n  📊 Sentiment Conflicts by Outcome:")
        print(f"     Converted: {sentiment_outcomes['converted']} ({sentiment_outcomes['conversion_rate']:.1f}%)")
        print(f"     Dropped: {sentiment_outcomes['dropped']}")
        print(f"     Engaged (no conversion): {sentiment_outcomes['engaged_no_conversion']} ({sentiment_outcomes['hidden_failure_rate']:.1f}%) ⚠️")
        print(f"     Continued: {sentiment_outcomes['continued']}")
    
    if clarification_outcomes["total"] > 0:
        print(f"\n  📊 Clarifications by Outcome:")
        print(f"     Converted: {clarification_outcomes['converted']} ({clarification_outcomes['conversion_rate']:.1f}%)")
        print(f"     Dropped: {clarification_outcomes['dropped']} ({clarification_outcomes['drop_rate']:.1f}%)")
        print(f"     Engaged (no conversion): {clarification_outcomes['engaged_no_conversion']} ({clarification_outcomes['hidden_failure_rate']:.1f}%) ⚠️")
        print(f"     Continued: {clarification_outcomes['continued']}")
    
    print("\n📈 VOLUME:")
    print(f"  Total Sessions:      {dashboard['total_sessions']}")
    print(f"  Total Decisions:     {dashboard['total_decisions']}")
    print(f"  Total Locked:        {dashboard['total_locked']}")
    print(f"  Total Applied:       {dashboard['total_applied']}")
    print(f"  Total Completed:     {dashboard['total_completed']}")
    
    print("\n🚨 TOP DROP-OFF STAGES:")
    for stage, count in dashboard["top_drop_offs"]:
        print(f"  {stage}: {count}")
    
    print("\n🔄 TOP STAGE TRANSITIONS:")
    for transition, count in dashboard["top_transitions"][:5]:
        print(f"  {transition}: {count}")
    
    print("\n" + "=" * 60)


# ============================================
# EXPORT FOR EXTERNAL ANALYTICS
# ============================================
def export_analytics(filepath: str = "analytics_export.json"):
    """Export analytics data to JSON file"""
    export_data = {
        "dashboard": get_analytics_dashboard(),
        "sessions": {k: v for k, v in ANALYTICS_STORE["sessions"].items()},
        "clarifications": ANALYTICS_STORE["clarifications"],
        "fallbacks": ANALYTICS_STORE["fallbacks"],
        "sentiment_conflicts": ANALYTICS_STORE["sentiment_conflicts"],
        "clarification_responses": ANALYTICS_STORE["clarification_responses"],
        "locked_dropoffs": ANALYTICS_STORE["locked_dropoffs"],
        "timestamp": time.time(),
    }
    
    with open(filepath, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    logger.info(f"[ANALYTICS] Exported to {filepath}")


if __name__ == "__main__":
    # Test analytics
    print("Testing Analytics System...")
    
    # Simulate session
    session_id = "test_001"
    init_session(session_id)
    
    track_stage(session_id, "guidance", {"marks": 75})
    track_decision(session_id, {"query": "BCA sounds good", "confidence": 0.95, "method": "fuzzy", "course": "BCA", "locked": True, "clarification_needed": False})
    track_stage(session_id, "decision_locked", {"locked_course": "BCA"})
    track_apply(session_id, "BCA")
    
    print_analytics_dashboard()
