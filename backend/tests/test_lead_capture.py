"""Tests: lead capture flow, validation, storage, analytics."""
from app.services.guided_flows import start_flow, advance_flow, get_active_flow, clear_flow
from app.services.lead_service import get_lead_by_session, leads_count
from app.services.analytics import get_stats, record_conversation

SID = "test-lead-session"


def setup_function():
    clear_flow(SID)


def _complete_admissions(sid):
    start_flow(sid, "admissions")
    advance_flow(sid, "PG")          # level
    advance_flow(sid, "MBA")         # program
    return advance_flow(sid, "Yes, send link")  # next_action → triggers lead capture


def test_lead_capture_prompt_after_flow():
    resp = _complete_admissions(SID)
    assert resp is not None
    assert resp["type"] == "lead_capture"
    assert resp["flow"] == "__lead__"
    assert "contact you" in resp["answer"].lower()


def test_lead_capture_decline():
    _complete_admissions(SID)
    resp = advance_flow(SID, "No, thanks")
    assert resp is None
    assert get_active_flow(SID) is None


def test_lead_capture_full_acceptance():
    _complete_admissions(SID)
    advance_flow(SID, "Yes, please")     # consent
    advance_flow(SID, "Ankitha")         # name
    done = advance_flow(SID, "9876543210")  # phone → complete
    assert done is None
    assert get_active_flow(SID) is None
    lead = get_lead_by_session(SID)
    assert lead is not None
    assert lead.phone == "9876543210"
    assert lead.name == "Ankitha"
    assert lead.intent == "admissions"


def test_invalid_contact_reprompts():
    _complete_admissions(SID)
    advance_flow(SID, "Yes, please")
    advance_flow(SID, "Ankitha")
    resp = advance_flow(SID, "notvalid")  # bad contact
    assert resp is not None
    assert "valid" in resp["answer"].lower()
    assert get_active_flow(SID) is not None  # still in flow


def test_email_accepted_as_contact():
    _complete_admissions(SID)
    advance_flow(SID, "Yes, please")
    advance_flow(SID, "Skip")
    advance_flow(SID, "user@example.com")
    lead = get_lead_by_session(SID)
    assert lead is not None
    assert lead.email == "user@example.com"


def test_analytics_records_leads():
    before = get_stats()["leads_captured"]
    _complete_admissions(SID)
    advance_flow(SID, "Yes, please")
    advance_flow(SID, "Skip")
    advance_flow(SID, "9123456789")
    assert get_stats()["leads_captured"] == before + 1
