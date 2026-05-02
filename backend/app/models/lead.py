# app/models/lead.py
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

_PHONE_RE = re.compile(r"^\d{10}$")
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


@dataclass
class Lead:
    session_id: str
    intent: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    course_interest: Optional[str] = None

    def is_valid(self) -> bool:
        return bool(self.phone or self.email)

    @staticmethod
    def valid_phone(v: str) -> bool:
        return bool(v and _PHONE_RE.match(re.sub(r"\D", "", v)) and len(re.sub(r"\D", "", v)) == 10)

    @staticmethod
    def valid_email(v: str) -> bool:
        return bool(v and _EMAIL_RE.match(v.strip()))
