"""Tests: dedup, validation, timeout, conversion rate, CSV export."""
import time
import os
from app.services.lead_service import create_lead, get_lead_by_session, get_all_leads, leads_count
from app.services.analytics import record_flow_start, record_lead_captured, get_conversion_rate, get_stats
from app.models.lead import Lead
from app.services.guided_flows import start_flow, advance_flow, get_active_flow, clear_flow, _FLOW_TIMEOUT_SECS, _state

SID1 = "dedup-session-1"
SID2 = "dedup-session-2"


def setup_function():
    from app.services import lead_service
    with lead_service._lock:
        lead_service._leads.clear()
    clear_flow(SID1)
    clear_flow(SID2)


# ── Dedup ─────────────────────────────────────────────────────────

def test_duplicate_phone_updates_existing():
    create_lead(SID1, "admissions", phone="9876543210")
    before = leads_count()
    create_lead(SID2, "fees", phone="9876543210")
    assert leads_count() == before  # no new entry
    lead = get_lead_by_session(SID2)
    assert lead.session_id == SID2   # session updated


def test_duplicate_email_updates_existing():
    create_lead(SID1, "admissions", email="a@b.com")
    create_lead(SID2, "fees", email="A@B.COM")  # case-insensitive
    assert leads_count() == leads_count()
    assert get_lead_by_session(SID2).email == "a@b.com"


# ── Validation ────────────────────────────────────────────────────

def test_valid_phone_10_digits():
    assert Lead.valid_phone("9876543210") is True
    assert Lead.valid_phone("98765")      is False
    assert Lead.valid_phone("abcdefghij") is False


def test_valid_email():
    assert Lead.valid_email("user@example.com") is True
    assert Lead.valid_email("notanemail")       is False
    assert Lead.valid_email("@nodomain")        is False


# ── Timeout ───────────────────────────────────────────────────────

def test_expired_flow_returns_none():
    start_flow(SID1, "fees")
    from app.services.guided_flows import _state as fs
    fs[SID1]["_ts"] = time.time() - _FLOW_TIMEOUT_SECS - 1
    result = advance_flow(SID1, "MBA")
    assert result is None
    assert get_active_flow(SID1) is None


# ── Conversion Rate ───────────────────────────────────────────────

def test_conversion_rate():
    from app.services import analytics
    with analytics._lock:
        analytics._data["flows_started"] = 4
        analytics._data["leads_captured"] = 2
    assert get_conversion_rate() == 0.5


def test_conversion_rate_zero_flows():
    from app.services import analytics
    with analytics._lock:
        analytics._data["flows_started"] = 0
        analytics._data["leads_captured"] = 0
    assert get_conversion_rate() == 0.0


# ── CSV Export ────────────────────────────────────────────────────

def test_csv_export_creates_file():
    create_lead(SID1, "admissions", phone="9000000001", email="test@aims.com")
    from app.utils.export import export_leads_to_csv
    path = export_leads_to_csv("/tmp/test_leads.csv")
    assert os.path.exists(path)
    with open(path) as f:
        content = f.read()
    assert "9000000001" in content or "test@aims.com" in content
