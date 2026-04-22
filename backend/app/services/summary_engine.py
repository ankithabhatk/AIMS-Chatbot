"""
Summary Engine — Rule-Based + Predictive Scoring
==================================================
Generates student intelligence profiles from chat history.
No LLM required → instant, reliable for demo.

Architecture:
  Chat history → keyword extraction → intent scoring → lead prediction
"""

from typing import List, Dict


# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD MAPS
# ─────────────────────────────────────────────────────────────────────────────

_COURSE_KEYWORDS = {
    "MBA":              ["mba", "master of business", "post graduate", "pgdm"],
    "BBA":              ["bba", "bachelor of business", "under graduate", "ug", "aviation management"],
    "MCA":              ["mca", "master of computer", "computer applications"],
    "BCA":              ["bca", "bachelor of computer"],
    "B.Com":            ["b.com", "commerce", "accounting", "bcom"],
    "PhD":              ["phd", "doctoral", "research programme"],
}

_INTENT_KEYWORDS = {
    "Fees Inquiry":        [
        "fee", "fees", "cost", "tuition", "afford", "price", "lakh", "rupee",
        "payment", "scholarship", "loan", "how much", "expensive", "financial",
        "fee structure", "total cost", "annual fee",
    ],
    "Admission Inquiry":   [
        "admission", "apply", "apply online", "eligibility", "eligible",
        "entrance", "cat", "mat", "xat", "cmat", "pgcet", "document",
        "last date", "deadline", "when does admission", "how to join",
        "registration", "application form",
    ],
    "Placement Interest":  [
        "placement", "package", "lpa", "salary", "recruiter", "hiring",
        "job", "career", "company", "deloitte", "accenture", "highest package",
        "average salary", "placement record", "placement stats", "ctc",
        "placement percentage", "companies visit",
    ],
    "Campus / Hostel":     [
        "hostel", "campus", "facility", "lab", "library", "sports",
        "canteen", "accommodation", "infrastructure", "wifi", "mess",
        "room", "living",
    ],
    "Program Details":     [
        "specialization", "subject", "curriculum", "semester", "syllabus",
        "duration", "course", "program", "what courses",
    ],
}

_SENTIMENT_SIGNALS = {
    "Serious":     ["i want", "i am planning", "confirm", "when does", "how soon", "deadline", "i have decided", "apply now"],
    "Exploring":   ["tell me", "what are", "can you explain", "just want to know", "curious", "what is"],
    "Confused":    ["i don't understand", "still not clear", "repeat", "what does that mean", "clarify", "confused"],
}

# Lead score weights per intent
_LEAD_WEIGHTS = {
    "Fees Inquiry":        4,   # Highest — student is evaluating affordability (decision stage)
    "Admission Inquiry":   3,   # Strongly signal intent to apply
    "Placement Interest":  2,   # Career-driven student, likely serious
    "Campus / Hostel":     2,   # Logistics inquiry — thinking about joining
    "Program Details":     1,   # Still exploring
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _user_text(chat_history: List[Dict]) -> str:
    """Concatenate all user messages into lowercase string."""
    return " ".join(c.get("user", "") for c in chat_history).lower()


def _all_text(chat_history: List[Dict]) -> str:
    return " ".join(
        c.get("user", "") + " " + c.get("bot", "")
        for c in chat_history
    ).lower()


# ─────────────────────────────────────────────────────────────────────────────
# DETECTORS
# ─────────────────────────────────────────────────────────────────────────────

def _detect_courses(text: str) -> List[str]:
    found = []
    for course, keywords in _COURSE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(course)
    return found or ["General"]


def _detect_intents(text: str) -> List[str]:
    found = []
    for intent_label, keywords in _INTENT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(intent_label)
    return found or ["General Inquiry"]


def _detect_sentiment(text: str) -> str:
    for sentiment, signals in _SENTIMENT_SIGNALS.items():
        if any(s in text for s in signals):
            return sentiment
    return "Exploring"  # default


def _lead_score(intents: List[str], message_count: int = 0) -> Dict:
    score = 0
    for intent in intents:
        score += _LEAD_WEIGHTS.get(intent, 0)

    # Breadth bonus: asking 3+ distinct topics signals serious exploration
    if len(intents) >= 3:
        score += 2

    # Depth bonus: more messages = stronger engagement signal
    # 4–5 msgs = +1, 6–8 msgs = +2, 9+ msgs = +3
    if message_count >= 9:
        score += 3
    elif message_count >= 6:
        score += 2
    elif message_count >= 4:
        score += 1

    if score >= 8:
        probability = "Very High"
        action = "📞 Contact immediately — high-intent student ready to enrol"
        priority = 1
    elif score >= 5:
        probability = "High"
        action = "📧 Send admission brochure + fee structure within 24 hrs"
        priority = 2
    elif score >= 3:
        probability = "Moderate"
        action = "📋 Add to nurture list — follow up in 3–5 days"
        priority = 3
    else:
        probability = "Low"
        action = "🔔 Monitor — student is still in early exploration"
        priority = 4

    return {
        "score": score,
        "conversion_probability": probability,
        "recommended_action": action,
        "priority": priority,
    }


def _build_summary_text(
    courses: List[str],
    intents: List[str],
    sentiment: str,
    prediction: Dict,
    message_count: int,
    primary_intent: str,
) -> str:
    """
    Produces a structured 5–7 line intelligence summary.
    Max 10 lines even for 50-message sessions.
    """
    courses_str  = ", ".join(courses) if courses else "General"
    intents_str  = ", ".join(intents) if intents else "General Inquiry"
    score        = prediction['score']
    prob         = prediction['conversion_probability']
    action       = prediction['recommended_action']

    # Depth label
    if message_count >= 9:
        depth = "deep engagement"
    elif message_count >= 5:
        depth = "moderate engagement"
    elif message_count >= 2:
        depth = "initial engagement"
    else:
        depth = "single-message contact"

    lines = [
        f"Course Interest  : {courses_str}",
        f"Primary Intent   : {primary_intent}",
        f"Topics Covered   : {intents_str}",
        f"Sentiment        : {sentiment} ({depth}, {message_count} messages)",
        f"Lead Score       : {score}/10+  |  Conversion: {prob}",
        f"Recommended Action: {action}",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_summary(chat_history: List[Dict]) -> Dict:
    """
    Generate a full intelligence profile from a session's chat history.

    Returns:
        {
          summary, courses, primary_intent, all_intents,
          sentiment, lead_score, conversion_probability,
          recommended_action, priority, messages, topics_covered
        }
    """
    if not chat_history:
        return {
            "summary": "No messages recorded.",
            "courses": [],
            "primary_intent": "Unknown",
            "all_intents": [],
            "sentiment": "Unknown",
            "lead_score": 0,
            "conversion_probability": "Low",
            "recommended_action": "No action needed",
            "priority": 5,
            "messages": 0,
            "topics_covered": 0,
        }

    user_text = _user_text(chat_history)
    message_count = len(chat_history)

    courses  = _detect_courses(user_text)
    intents  = _detect_intents(user_text)
    sentiment = _detect_sentiment(user_text)
    prediction = _lead_score(intents, message_count)  # pass depth

    # Determine primary (highest-weight) intent
    primary_intent = max(
        intents,
        key=lambda i: _LEAD_WEIGHTS.get(i, 0),
        default="General Inquiry"
    )

    summary_text = _build_summary_text(
        courses, intents, sentiment, prediction, message_count, primary_intent
    )

    return {
        "summary":               summary_text,
        "courses":               courses,
        "primary_intent":        primary_intent,
        "all_intents":           intents,
        "sentiment":             sentiment,
        "lead_score":            prediction["score"],
        "conversion_probability": prediction["conversion_probability"],
        "recommended_action":    prediction["recommended_action"],
        "priority":              prediction["priority"],
        "messages":              len(chat_history),
        "topics_covered":        len(intents),
    }
