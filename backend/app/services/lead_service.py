# app/services/lead_service.py
import threading
from typing import Dict, List, Optional
from app.models.lead import Lead

_lock = threading.Lock()
_leads: Dict[str, Lead] = {}  # session_id → Lead


def _find_by_contact(phone: Optional[str], email: Optional[str]):
    for sid, lead in _leads.items():
        if phone and lead.phone and lead.phone == phone:
            return sid, lead
        if email and lead.email and lead.email.lower() == (email or "").lower():
            return sid, lead
    return None, None


def create_lead(session_id: str, intent: str, course_interest: Optional[str] = None,
                phone: Optional[str] = None, email: Optional[str] = None) -> Lead:
    with _lock:
        old_sid, existing = _find_by_contact(phone, email)
        if existing:
            if old_sid and old_sid != session_id:
                del _leads[old_sid]  # remove stale key
            existing.session_id = session_id
            if course_interest:
                existing.course_interest = course_interest
            _leads[session_id] = existing
            return existing
        lead = Lead(session_id=session_id, intent=intent, course_interest=course_interest,
                    phone=phone, email=email)
        _leads[session_id] = lead
    return lead


def update_lead(session_id: str, **kwargs) -> Optional[Lead]:
    with _lock:
        lead = _leads.get(session_id)
        if not lead:
            return None
        for k, v in kwargs.items():
            if hasattr(lead, k) and v:
                setattr(lead, k, v)
    return lead


def get_lead_by_session(session_id: str) -> Optional[Lead]:
    with _lock:
        return _leads.get(session_id)


def get_all_leads() -> List[Lead]:
    with _lock:
        return list(_leads.values())


def leads_count() -> int:
    with _lock:
        return len(_leads)
