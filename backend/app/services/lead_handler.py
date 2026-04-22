# backend/app/services/lead_handler.py

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Authoritative Lead states
# START -> COLLECTING_DETAILS -> COMPLETED
LEAD_SESSIONS: Dict[str, Any] = {}

FEES_DISCLAIMER = (
    "Fee structures vary depending on the program and admission cycle. "
    "Fee details are shared by our admissions team to ensure accuracy and provide you with the most up-to-date information."
)

def get_or_create_session(session_id: str) -> Dict[str, Any]:
    """Retrieve or initialize session state"""
    if session_id not in LEAD_SESSIONS:
        LEAD_SESSIONS[session_id] = {
            "query_count": 0,
            "has_lead": False,
            "gate_active": False,
            "last_active": datetime.now(),
            "data": {}
        }
    return LEAD_SESSIONS[session_id]

def parse_details(text: str) -> Dict[str, Any]:
    """
    Robust parser for lead details.
    Supports: 
    - Labeled: "Name: John Doe, Email: john@gmail.com, Course: MBA, Phone: 9876543210"
    - Delimited: "John Doe, john@gmail.com, MBA, 9876543210"
    """
    # 1. Extract Email and Phone via Regex (highest reliability)
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone_match = re.search(r'\b[6-9]\d{9}\b', text)
    
    email = email_match.group(0) if email_match else None
    phone = phone_match.group(0) if phone_match else None
    
    # 2. Cleanup labels if present
    clean_text = re.sub(r'(Name:|Email:|Course:|Phone:)', '', text, flags=re.IGNORECASE)
    
    # 3. Split by commas or pipes
    parts = [p.strip() for p in re.split(r'[,|]', clean_text)]
    
    # 4. Extract Name and Course
    # We assume Name is usually the first part if not labeled
    name = parts[0] if len(parts) > 0 else None
    
    # Look for common course keywords in any part
    course = None
    for p in parts:
        lower_p = p.lower()
        if any(c in lower_p for c in ["mba", "bba", "bca", "mca", "mcom", "bcom"]):
            # Use the original case/string for course
            course = p
            break
            
    # Remove email/phone from potential name if they leaked in
    if name and (name == email or name == phone):
        name = parts[1] if len(parts) > 1 else None

    return {
        "name": name,
        "email": email,
        "phone": phone or "N/A",
        "course": course
    }

def validate_details(data: Dict[str, Any]) -> Optional[str]:
    """Strict validation for lead data. Returns error message or None."""
    if not data["name"] or len(data["name"]) < 2:
        return "Please enter your full name."
    
    if not data["email"]:
        return "That email doesn't look right. Please provide a valid email (example: name@gmail.com)."
    
    if not data["course"]:
        return "Please mention the course you're interested in (e.g., MBA, BBA)."
    
    return None

def handle_gated_capture(session_id: str, user_input: str) -> Dict[str, Any]:
    """
    Handle the mandatory gate loop.
    Returns a dict with 'answer' and 'status' (lock|unlock).
    """
    session = get_or_create_session(session_id)
    
    data = parse_details(user_input)
    error = validate_details(data)
    
    if error:
        return {
            "answer": f"{error}\n\nFormat: Name, Email, Course, Phone (optional)",
            "status": "lock"
        }
    
    # Success - Save data to session
    session["data"] = data
    session["has_lead"] = True
    session["gate_active"] = False
    
    return {
        "answer": f"Thank you, {data['name']}! I've shared your interest in {data['course']} with our admissions team. How else can I help you today?",
        "status": "unlock",
        "lead_ready": True,
        "data": data
    }

def update_session_on_query(session_id: str, query: str):
    """Increment count and update last active timestamp"""
    session = get_or_create_session(session_id)
    session["query_count"] += 1
    session["last_active"] = datetime.now()

def get_gate_invitation() -> str:
    """The mandatory block message"""
    return (
        "I'd love to help you with that! Before we continue, could you please share a few details so I can guide you better?\n\n"
        "Please provide your: **Name, Email, and Course**\n"
        "(Example: John Doe, john@example.com, MBA)"
    )
