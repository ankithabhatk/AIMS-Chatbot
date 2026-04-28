"""
Response Transformer - Convert text answers to UI-ready card structures

Transforms generic text answers into structured cards that frontends can render properly.
Examples:
- Fees answer → fees_card with structured data
- Placement answer → placement_card with stats
- Facilities answer → list_card with bullets
"""

import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from enum import Enum

logger = logging.getLogger(__name__)


class CardType(str, Enum):
    """Supported card types"""
    TEXT = "text"
    FEES = "fees_card"
    PLACEMENT = "placement_card"
    FACILITIES = "list_card"
    COMPARISON = "comparison_card"
    COURSE = "course_card"
    ADMISSION = "admission_card"


def detect_intent_from_answer(answer: str, query: str = "") -> CardType:
    """Detect what kind of card this answer should be"""
    answer_lower = answer.lower()
    query_lower = query.lower()
    
    # Placement detection
    if any(word in answer_lower for word in ["placement", "salary", "lpa", "package", "recruiter"]):
        if "vs" in query_lower or "compare" in query_lower:
            return CardType.COMPARISON
        return CardType.PLACEMENT
    
    # Fees detection
    if any(word in answer_lower for word in ["fee", "₹", "cost", "price", "tuition"]):
        return CardType.FEES
    
    # Facilities detection
    if any(word in answer_lower for word in ["facility", "hostel", "library", "campus", "infrastructure"]):
        return CardType.FACILITIES
    
    # Admission detection
    if any(word in answer_lower for word in ["admission", "eligible", "eligibility", "apply", "process"]):
        return CardType.ADMISSION
    
    # Course detection
    if any(word in answer_lower for word in ["course", "program", "mba", "bca", "degree"]):
        return CardType.COURSE
    
    return CardType.TEXT


def extract_fees_data(answer: str) -> Dict[str, Any]:
    """Extract structured fee information from answer text"""
    data = {
        "range": None,
        "min": None,
        "max": None,
        "note": None,
        "contact": None
    }
    
    # Extract fee range (₹50,000 – ₹1,00,000)
    range_pattern = r'₹([\d,]+)\s*(?:–|-)\s*₹([\d,]+)'
    match = re.search(range_pattern, answer)
    if match:
        min_val = match.group(1).replace(",", "")
        max_val = match.group(2).replace(",", "")
        data["min"] = min_val
        data["max"] = max_val
        data["range"] = f"₹{match.group(1)} – ₹{match.group(2)}"
    
    # Extract single fee amount
    if not data["range"]:
        single_fee = re.search(r'₹([\d,]+)', answer)
        if single_fee:
            amount = single_fee.group(1)
            data["range"] = f"₹{amount}"
            data["min"] = amount.replace(",", "")
    
    # Extract note/variation info
    if "varies" in answer.lower() or "depends" in answer.lower():
        note_match = re.search(r'(?:varies|depends)[^.]*', answer, re.IGNORECASE)
        if note_match:
            data["note"] = note_match.group(0)
    
    # Extract contact info
    if "admission@" in answer or "contact" in answer.lower():
        email_match = re.search(r'[\w.-]+@[\w.-]+', answer)
        if email_match:
            data["contact"] = email_match.group(0)
    
    return data


def extract_placement_data(answer: str) -> Dict[str, Any]:
    """Extract structured placement information"""
    data = {
        "highest_package": None,
        "average_package": None,
        "placement_rate": None,
        "recruiters": [],
        "highlights": []
    }
    
    # Extract highest package (₹23 LPA or ₹23 L)
    highest_match = re.search(r'highest[^.]*?₹([\d,\.]+)\s*(?:LPA|L|lakh)', answer, re.IGNORECASE)
    if highest_match:
        data["highest_package"] = f"₹{highest_match.group(1)} LPA"
    
    # Extract average package
    avg_match = re.search(r'average[^.]*?₹([\d,\.]+)\s*(?:LPA|L|lakh)', answer, re.IGNORECASE)
    if avg_match:
        data["average_package"] = f"₹{avg_match.group(1)} LPA"
    
    # Extract placement rate
    rate_match = re.search(r'(\d+)%\s*placement', answer, re.IGNORECASE)
    if rate_match:
        data["placement_rate"] = f"{rate_match.group(1)}%"
    
    # Extract recruiter names (known companies)
    known_recruiters = [
        "Deloitte", "EY", "Infosys", "Accenture", "TCS", "Wipro",
        "Amazon", "Microsoft", "Google", "IBM", "ICICI", "HDFC"
    ]
    for recruiter in known_recruiters:
        if recruiter.lower() in answer.lower():
            data["recruiters"].append(recruiter)
    
    # Extract key highlights (bullet points or key phrases)
    sentences = re.split(r'[.!?]', answer)
    for sent in sentences[:3]:  # Top 3 highlights
        sent = sent.strip()
        if len(sent) > 20 and len(sent) < 150:
            data["highlights"].append(sent)
    
    return data


def extract_facilities_data(answer: str) -> List[str]:
    """Extract facilities as bullet points"""
    facilities = []
    
    # Known facility keywords
    facility_keywords = [
        "hostel", "wifi", "wi-fi", "library", "lab", "laboratory",
        "sports", "ground", "gym", "cafeteria", "canteen",
        "classroom", "auditorium", "parking", "transport"
    ]
    
    # Split answer into sentences
    sentences = re.split(r'[.!?•\n-]', answer)
    
    for sent in sentences:
        sent = sent.strip()
        if not sent or len(sent) < 10:
            continue
        
        # Check if sentence mentions a facility
        is_facility = any(kw in sent.lower() for kw in facility_keywords)
        
        if is_facility:
            facilities.append(sent)
    
    # Fallback: if no specific facilities found, create generic list
    if not facilities:
        if "hostel" in answer.lower():
            facilities.append("Hostel with Wi-Fi")
        if "library" in answer.lower():
            facilities.append("Well-stocked library")
        if "sport" in answer.lower():
            facilities.append("Sports complex")
        if "lab" in answer.lower():
            facilities.append("Modern laboratories")
    
    return facilities[:5]  # Max 5 facilities


def extract_admission_data(answer: str) -> Dict[str, Any]:
    """Extract admission information"""
    data = {
        "process": [],
        "eligibility": None,
        "documents": [],
        "timeline": None
    }
    
    # Extract process steps (numbered or bulleted)
    steps = re.split(r'(?:\d+\.|•|-)\s+', answer)
    for step in steps[1:]:  # Skip first empty element
        step = step.strip().split('\n')[0]  # Get first line
        if step and len(step) < 150:
            data["process"].append(step)
    
    # Extract eligibility
    if "eligibility" in answer.lower():
        eligi_match = re.search(r'eligibility[^.]*(?:requirement[^.]*)?(?:criteria[^.]*)?[.!?]', answer, re.IGNORECASE)
        if eligi_match:
            data["eligibility"] = eligi_match.group(0)
    
    # Extract documents
    documents = ["application", "transcript", "certificate", "passport", "id", "photo"]
    found_docs = []
    for doc in documents:
        if doc in answer.lower():
            found_docs.append(doc.capitalize())
    if found_docs:
        data["documents"] = found_docs
    
    return data


def transform_to_card(
    answer: str,
    query: str = "",
    intent: str = ""
) -> Dict[str, Any]:
    """Transform answer text into UI card
    
    Args:
        answer: Text answer
        query: Original query (helps with context)
        intent: Detected intent
    
    Returns:
        Structured card dict suitable for frontend rendering
    """
    
    # Detect card type
    card_type = detect_intent_from_answer(answer, query)
    
    logger.debug(f"[TRANSFORMER] Detected card type: {card_type}")
    
    # Transform based on type
    if card_type == CardType.FEES:
        return {
            "type": "fees_card",
            "title": "Fee Structure",
            "data": extract_fees_data(answer),
            "raw_text": answer
        }
    
    elif card_type == CardType.PLACEMENT:
        return {
            "type": "placement_card",
            "title": "Placement Highlights",
            "data": extract_placement_data(answer),
            "raw_text": answer
        }
    
    elif card_type == CardType.FACILITIES:
        return {
            "type": "list_card",
            "title": "Campus Facilities",
            "items": extract_facilities_data(answer),
            "raw_text": answer
        }
    
    elif card_type == CardType.ADMISSION:
        return {
            "type": "admission_card",
            "title": "Admission Process",
            "data": extract_admission_data(answer),
            "raw_text": answer
        }
    
    else:
        # Default: text card
        return {
            "type": "text",
            "content": answer,
            "raw_text": answer
        }


def format_response_for_ui(
    answer: str,
    confidence: float = 0.7,
    intent: str = "",
    query: str = "",
    mode: str = "rag",
    suggestions: List[str] = None
) -> Dict[str, Any]:
    """Format complete response for frontend
    
    Args:
        answer: Main answer text
        confidence: Confidence score (0-1)
        intent: Detected intent
        query: Original query
        mode: How answer was generated (structured/rag/fallback)
        suggestions: List of suggestion strings
    
    Returns:
        Complete API response with card + metadata
    """
    
    card = transform_to_card(answer, query, intent)
    
    return {
        "message": card,
        "meta": {
            "confidence": confidence,
            "mode": mode,
            "intent": intent,
            "suggestions": suggestions or []
        }
    }
