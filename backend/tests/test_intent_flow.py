"""Tests: intent classification, guided flow start/advance, routing."""
from app.services.intent_classifier import classify
from app.services.guided_flows import start_flow, advance_flow, get_active_flow, clear_flow
from app.services.intent_router import route

SID = "test-flow-session"


def setup_function():
    clear_flow(SID)


# ── Classifier ────────────────────────────────────────────────────

def test_admissions_intent():
    assert classify("I want to apply")["intent"] == "admissions"

def test_fees_intent():
    assert classify("what are the mba fees")["intent"] == "fees"

def test_hostel_intent():
    assert classify("hostel facility")["intent"] == "hostel"

def test_placement_intent():
    assert classify("placement packages")["intent"] == "placements"

def test_general_fallback():
    assert classify("tell me something")["intent"] == "general"


# ── Guided Flow ───────────────────────────────────────────────────

def test_admissions_flow_starts():
    resp = start_flow(SID, "admissions")
    assert resp["type"] == "guided"
    assert resp["step"] == 0
    assert "UG" in resp["options"]

def test_admissions_flow_advances():
    start_flow(SID, "admissions")
    resp = advance_flow(SID, "PG")
    assert resp is not None
    assert resp["step"] == 1
    assert "MBA" in resp["options"]

def test_flow_completes_after_last_step():
    start_flow(SID, "fees")       # 2 steps
    advance_flow(SID, "MBA")      # step 0 → 1
    done = advance_flow(SID, "Scholarships")  # step 1 → complete
    assert done is None
    assert get_active_flow(SID) is None


# ── Router ────────────────────────────────────────────────────────

def test_router_triggers_guided_flow():
    resp = route("I want to apply for admission", SID)
    assert resp is not None
    assert resp["type"] == "guided"

def test_router_returns_none_for_general():
    clear_flow(SID)
    resp = route("who is the founder of AIMS?", SID)
    assert resp is None  # falls through to RAG

def test_router_cancel_clears_flow():
    start_flow(SID, "admissions")
    resp = route("cancel", SID)
    assert resp is None
    assert get_active_flow(SID) is None
