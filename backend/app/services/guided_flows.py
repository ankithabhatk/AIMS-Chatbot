# app/services/guided_flows.py
import re
import threading
import time
from typing import Dict, Optional

_FLOW_TIMEOUT_SECS = 600  # 10 minutes

_lock = threading.Lock()
_state: Dict[str, dict] = {}  # session_id → {flow, step, data}

_FLOWS = {
    "admissions": [
        {
            "message": "Are you looking for UG or PG admissions?",
            "options": ["UG", "PG"],
            "key": "level",
        },
        {
            "message": "Which program are you interested in? (e.g. MBA, BBA, BCA, MCA)",
            "options": ["MBA", "BBA", "BCA", "MCA", "PGDM"],
            "key": "program",
        },
        {
            "message": "Would you like the direct application link for AIMS College?",
            "options": ["Yes, send link", "Tell me eligibility first"],
            "key": "next_action",
        },
    ],
    "fees": [
        {
            "message": "Which program's fee structure would you like to know?",
            "options": ["MBA", "BBA", "BCA", "MCA", "PGDM"],
            "key": "program",
        },
        {
            "message": "Would you also like information on scholarships or payment plans?",
            "options": ["Scholarships", "EMI / Payment Plans", "No, just fees"],
            "key": "fee_detail",
        },
    ],
    "courses": [
        {
            "message": "Are you looking for UG or PG courses?",
            "options": ["UG", "PG"],
            "key": "level",
        },
        {
            "message": "Which specialization interests you?",
            "options": ["Finance", "Marketing", "HR", "Operations", "IT", "General Management"],
            "key": "specialization",
        },
    ],
}

GUIDED_INTENTS = set(_FLOWS.keys())

_NEW_TOPIC_KEYWORDS = frozenset([
    "bca", "mca", "mba", "bba", "pgdm",
    "fees", "fee", "hostel", "admission",
    "placements", "placement", "courses",
    "salary", "scholarship",
])


def is_new_topic(query: str) -> bool:
    """Return True if the query clearly introduces a new subject."""
    q = query.lower()
    return any(k in q for k in _NEW_TOPIC_KEYWORDS)


_LEAD_STEPS = [
    {"key": "__consent__",
     "message": "Would you like us to contact you for personalized assistance?",
     "options": ["Yes, please", "No, thanks"]},
    {"key": "name",
     "message": "Please enter your name (or type Skip)",
     "options": ["Skip"]},
    {"key": "contact",
     "message": "Please enter your phone number or email (or type Skip)",
     "options": ["Skip"]},
]

def _valid_contact(value: str) -> bool:
    from app.models.lead import Lead
    return Lead.valid_phone(value) or Lead.valid_email(value)


def _make_response(step: dict, flow: str, step_num: int) -> dict:
    rtype = "lead_capture" if flow == "__lead__" else "guided"
    return {
        "type": rtype,
        "flow": flow,
        "step": step_num,
        "answer": step["message"],
        "options": step.get("options", []),
        "fallback": False,
        "confidence": 1.0,
        "sources": [],
    }


def _is_expired(state: dict) -> bool:
    return (time.time() - state.get("_ts", 0)) > _FLOW_TIMEOUT_SECS


def start_flow(session_id: str, flow: str) -> Optional[dict]:
    if flow not in _FLOWS:
        return None
    with _lock:
        _state[session_id] = {"flow": flow, "step": 0, "data": {"__orig_flow__": flow}, "_ts": time.time()}
    return _make_response(_FLOWS[flow][0], flow, 0)


def advance_flow(session_id: str, user_input: str) -> Optional[dict]:
    with _lock:
        state = _state.get(session_id)
        if not state:
            return None
        if _is_expired(state):
            del _state[session_id]
            return None
        # Secondary safety net: bail out if user changed topic
        if is_new_topic(user_input):
            del _state[session_id]
            return None
        # Loop prevention: same query twice → exit flow
        if state.get("last_query") == user_input.strip().lower():
            del _state[session_id]
            return None
        state["last_query"] = user_input.strip().lower()
        state["_ts"] = time.time()
        flow = state["flow"]
        step = state["step"]

        # ── Lead capture branch ───────────────────────────────────
        if flow == "__lead__":
            key = _LEAD_STEPS[step]["key"]

            if key == "__consent__":
                if "no" in user_input.lower():
                    del _state[session_id]
                    return None  # user declined
                state["data"][key] = "yes"

            elif key == "contact" and user_input.strip().lower() != "skip":
                if not _valid_contact(user_input.strip()):
                    return {
                        "type": "lead_capture",
                        "flow": "__lead__",
                        "step": step,
                        "answer": "Please enter a valid phone number or email (or type Skip)",
                        "options": ["Skip"],
                        "fallback": False,
                        "confidence": 1.0,
                        "sources": [],
                    }
                state["data"][key] = user_input.strip()
            else:
                if user_input.strip().lower() != "skip":
                    state["data"][key] = user_input.strip()

            next_step = step + 1
            if next_step >= len(_LEAD_STEPS):
                _flush_lead(session_id, state)
                return None  # lead capture complete
            state["step"] = next_step
            return _make_response(_LEAD_STEPS[next_step], "__lead__", next_step)

        # ── Main flow branch ──────────────────────────────────────
        steps = _FLOWS[flow]
        state["data"][steps[step]["key"]] = user_input
        next_step = step + 1
        if next_step >= len(steps):
            # Transition to lead capture instead of clearing
            state["flow"] = "__lead__"
            state["step"] = 0
            return _make_response(_LEAD_STEPS[0], "__lead__", 0)
        state["step"] = next_step
    return _make_response(steps[next_step], flow, next_step)


def _flush_lead(session_id: str, state: dict) -> None:
    from app.models.lead import Lead
    from app.services.lead_service import create_lead, update_lead
    from app.services.analytics import record_lead_captured
    data = state["data"]
    contact = data.get("contact", "")
    phone = contact if Lead.valid_phone(contact) else None
    email = contact if Lead.valid_email(contact) else None
    create_lead(
        session_id=session_id,
        intent=data.get("__orig_flow__", "unknown"),
        course_interest=data.get("program"),
        phone=phone,
        email=email,
    )
    update_lead(session_id, name=data.get("name"))
    record_lead_captured()
    del _state[session_id]


def get_active_flow(session_id: str) -> Optional[str]:
    with _lock:
        s = _state.get(session_id)
        return s["flow"] if s else None


def get_flow_data(session_id: str) -> dict:
    with _lock:
        s = _state.get(session_id)
        return dict(s["data"]) if s else {}


def clear_flow(session_id: str) -> None:
    with _lock:
        _state.pop(session_id, None)
