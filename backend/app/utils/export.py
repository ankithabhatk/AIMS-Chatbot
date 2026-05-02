# app/utils/export.py
import csv
import os
from typing import Optional

_EXPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "leads_export.csv")
_FIELDS = ["session_id", "name", "phone", "email", "course_interest", "intent", "timestamp"]


def export_leads_to_csv(path: Optional[str] = None) -> str:
    from app.services.lead_service import get_all_leads
    out = os.path.abspath(path or _EXPORT_PATH)
    leads = get_all_leads()
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            writer.writerow({
                "session_id":    lead.session_id,
                "name":          lead.name or "",
                "phone":         lead.phone or "",
                "email":         lead.email or "",
                "course_interest": lead.course_interest or "",
                "intent":        lead.intent,
                "timestamp":     lead.timestamp,
            })
    return out
