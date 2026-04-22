"""
Summary Engine — Rule-Based + Predictive Scoring
==================================================
Generates student intelligence profiles from chat history.
No LLM required → deterministic, instant, reliable.

Architecture:
  Chat history
    → keyword extraction (courses, intents, sentiment)
    → lead scoring    (intent weights + message depth + breadth)
    → predictive layer (conversion timeline + next query prediction)
    → structured summary (6–8 lines, presentable to management)
"""

from typing import List, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD MAPS
# ─────────────────────────────────────────────────────────────────────────────

_COURSE_KEYWORDS = {
    "MBA":   ["mba", "master of business", "post graduate", "pgdm"],
    "BBA":   ["bba", "bachelor of business", "under graduate", "ug", "aviation management"],
    "MCA":   ["mca", "master of computer", "computer applications"],
    "BCA":   ["bca", "bachelor of computer"],
    "B.Com": ["b.com", "commerce", "accounting", "bcom"],
    "PhD":   ["phd", "doctoral", "research programme"],
}

# Keywords that must NOT immediately precede a Fees keyword
# e.g. "hostel fee" should NOT fire Fees Inquiry, only Campus/Hostel
_FEES_EXCLUSION_CONTEXT = ["hostel fee", "hostel fees", "hostel cost"]

_INTENT_KEYWORDS = {
    "Fees Inquiry": [
        "fee structure", "total cost", "annual fee", "how much does",
        "tuition fee", "course fee", "mba fee", "bba fee", "bca fee",
        "fees kya", "how much is", "cost of", "afford", "price",
        "lakh", "rupee", "payment plan", "scholarship", "loan", "emi",
        "financial aid", "fee after", "total fee",
    ],
    "Admission Inquiry": [
        "admission", "apply", "apply online", "eligibility", "eligible",
        "entrance", "cat", "mat", "xat", "cmat", "pgcet", "document",
        "last date", "deadline", "when does admission", "how to join",
        "registration", "application form",
    ],
    "Placement Interest": [
        "placement", "package", "lpa", "salary", "recruiter", "hiring",
        "job", "career", "company", "deloitte", "accenture", "highest package",
        "average salary", "placement record", "placement stats", "ctc",
        "placement percentage", "companies visit", "companies come",
        "who recruits", "average ctc", "international recruiter",
    ],
    "Campus / Hostel": [
        "hostel", "campus", "facility", "lab", "library", "sports",
        "canteen", "accommodation", "infrastructure", "wifi", "mess",
        "room", "living", "hostel fee", "hostel fees", "hostel cost",
    ],
    "Program Details": [
        "specialization", "subject", "curriculum", "semester", "syllabus",
        "duration", "course", "program", "what courses", "difference between",
        "which course", "pgdm vs mba",
    ],
}

_SENTIMENT_SIGNALS = {
    "Serious":   ["i want", "i am planning", "confirm", "when does", "how soon",
                  "deadline", "i have decided", "apply now", "i will apply",
                  "planning to join", "want to enrol"],
    "Exploring": ["tell me", "what are", "can you explain", "just want to know",
                  "curious", "what is", "just checking"],
    "Confused":  ["i don't understand", "still not clear", "repeat",
                  "what does that mean", "clarify", "confused", "not sure"],
}

# Lead score weights per intent (higher = stronger buying signal)
_LEAD_WEIGHTS = {
    "Fees Inquiry":       4,   # Student evaluating affordability → decision stage
    "Admission Inquiry":  3,   # Strong intent to apply
    "Placement Interest": 2,   # Career-driven, likely serious
    "Campus / Hostel":    2,   # Logistics → thinking about joining
    "Program Details":    1,   # Still exploring options
}

# ─────────────────────────────────────────────────────────────────────────────
# PREDICTIVE TABLES
# ─────────────────────────────────────────────────────────────────────────────

# What intents typically follow a given primary intent
_NEXT_QUERY_MAP: Dict[str, List[str]] = {
    "Fees Inquiry":       ["scholarship availability", "EMI / payment plans", "hostel fees"],
    "Admission Inquiry":  ["fee structure", "entrance exam cut-off", "document checklist"],
    "Placement Interest": ["average / highest salary", "companies that visit campus", "placement percentage"],
    "Campus / Hostel":    ["hostel fee", "campus facilities tour", "library / lab access"],
    "Program Details":    ["fee structure", "admission eligibility", "placement record"],
    "General Inquiry":    ["available programs", "admission process", "fee structure"],
}

# Conversion timeline prediction based on intent combination
_CONVERSION_TIMELINE: Dict[frozenset, str] = {
    frozenset(["Fees Inquiry", "Admission Inquiry"]):                "Likely to convert within 3–7 days",
    frozenset(["Fees Inquiry", "Placement Interest"]):               "Likely to convert within 7–14 days",
    frozenset(["Fees Inquiry", "Admission Inquiry",
               "Campus / Hostel"]):                                  "Likely to convert within 1–3 days",
    frozenset(["Placement Interest", "Admission Inquiry"]):          "Likely to convert within 7–14 days",
    frozenset(["Campus / Hostel", "Admission Inquiry"]):             "Likely to convert within 14–21 days",
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _user_text(chat_history: List[Dict]) -> str:
    """Concatenate all user messages into a single lowercase string."""
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
    return [c for c, kws in _COURSE_KEYWORDS.items() if any(kw in text for kw in kws)] or ["General"]


def _detect_intents(text: str) -> List[str]:
    """
    Detect intents using phrase-priority matching.
    Fees Inquiry excludes hostel-fee context to prevent false positives.
    Returns each intent at most once (deduped — repetition doesn't inflate score).
    """
    found = set()

    # Strip hostel-fee compound phrases before testing Fees Inquiry
    fees_text = text
    for excl in _FEES_EXCLUSION_CONTEXT:
        fees_text = fees_text.replace(excl, "[hostel-cost]")

    for intent_label, keywords in _INTENT_KEYWORDS.items():
        search_text = fees_text if intent_label == "Fees Inquiry" else text
        if any(kw in search_text for kw in keywords):
            found.add(intent_label)

    return list(found) or ["General Inquiry"]


def _detect_sentiment(text: str) -> str:
    for sentiment, signals in _SENTIMENT_SIGNALS.items():
        if any(s in text for s in signals):
            return sentiment
    return "Exploring"


# ─────────────────────────────────────────────────────────────────────────────
# LEAD SCORING
# ─────────────────────────────────────────────────────────────────────────────

def _lead_score(intents: List[str], message_count: int = 0, user_text: str = "") -> Dict:
    """
    Score is based on intent PRESENCE (each intent counted once),
    plus bonuses for breadth and message depth.
    Normalized to a 0–10 display scale.
    """
    # Base: each unique intent contributes its weight exactly once
    raw = sum(_LEAD_WEIGHTS.get(i, 0) for i in intents)

    # Breadth bonus: 3+ distinct topics = serious exploration (+2)
    if len(intents) >= 3:
        raw += 2

    # Depth bonus: more messages = stronger commitment signal
    if message_count >= 9:
        raw += 3
    elif message_count >= 6:
        raw += 2
    elif message_count >= 4:
        raw += 1

    # Normalize to 0–10 scale (max raw ≈ 14 for all intents + breadth + depth)
    score = round(min(raw * 10 / 14, 10.0), 1)

    # Intent-combination fast-path: Fees+Admission together = serious buyer
    has_fees      = "Fees Inquiry"      in intents
    has_admission = "Admission Inquiry" in intents
    has_placement = "Placement Interest" in intents
    combo_boost   = has_fees and has_admission

    # Scholarship-only dampener:
    # If Fees is driven purely by scholarship/loan keywords (no fee-amount terms),
    # the student is researching financial aid, not ready to enrol → cap at High
    _FEE_AMOUNT_TERMS = ["fee structure", "total fee", "annual fee", "tuition fee",
                         "course fee", "how much does", "how much is", "cost of",
                         "fees kya", "fee after", "total cost"]
    has_fee_amount_term = any(t in user_text for t in _FEE_AMOUNT_TERMS)
    scholarship_only = has_fees and not has_admission and not has_fee_amount_term


    # Thresholds on normalized 0–10 scale (calibrated against 10-conversation audit)
    if scholarship_only and score >= 6.5:
        # Cap scholarship-only sessions — not yet decision-ready
        probability = "High"
        action      = "📧 Send scholarship + fee-waiver details"
        priority    = 2
    elif score >= 6.5 or (combo_boost and score >= 5.0):
        probability = "Very High"
        action      = "📞 Contact immediately — high-intent student ready to enrol"
        priority    = 1
    elif score >= 5.0:
        probability = "High"
        action      = "📧 Send admission brochure + fee structure within 24 hrs"
        priority    = 2
    elif score >= 1.5 or (has_placement and message_count >= 3):
        # Placement-only boost: 3+ placement questions = active researcher → Moderate
        probability = "Moderate"
        action      = "📋 Add to nurture list — follow up in 3–5 days"
        priority    = 3
    else:
        probability = "Low"
        action      = "🔔 Monitor — student is still in early exploration"
        priority    = 4

    return {
        "score":                  score,
        "raw_score":              raw,
        "conversion_probability": probability,
        "recommended_action":     action,
        "priority":               priority,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PREDICTIVE LAYER
# ─────────────────────────────────────────────────────────────────────────────

def _predict_conversion_timeline(intents: List[str], score: int, message_count: int) -> str:
    """
    Rule-based timeline prediction using intent combinations.
    Falls back to score-based estimate when no exact match exists.
    """
    intent_set = frozenset(intents)

    # Try exact combination match first
    for combo, timeline in _CONVERSION_TIMELINE.items():
        if combo.issubset(intent_set):
            return timeline

    # Score-based fallback
    if score >= 8:
        return "Likely to convert within 1–5 days"
    elif score >= 5:
        return "Likely to convert within 7–14 days"
    elif score >= 3:
        return "Possibly converting in 2–4 weeks — nurture needed"
    else:
        return "No clear conversion signal yet — early exploration stage"


def _predict_next_queries(primary_intent: str, intents: List[str]) -> List[str]:
    """
    Predict what the student will ask next based on their primary intent
    and already-covered topics. Filters out topics already asked.
    """
    candidates = _NEXT_QUERY_MAP.get(primary_intent, _NEXT_QUERY_MAP["General Inquiry"])

    # Heuristic: remove suggestions that seem already covered
    covered_keywords = {
        "Fees Inquiry":       ["fee", "cost", "scholarship"],
        "Admission Inquiry":  ["admission", "document", "deadline"],
        "Placement Interest": ["placement", "salary", "package"],
        "Campus / Hostel":    ["hostel", "campus", "facility"],
        "Program Details":    ["program", "course", "syllabus"],
    }
    already_asked = set()
    for intent in intents:
        already_asked.update(covered_keywords.get(intent, []))

    # Return up to 3 most-likely next questions
    filtered = [q for q in candidates if not any(kw in q.lower() for kw in already_asked)]
    return (filtered or candidates)[:3]


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY TEXT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _build_summary_text(
    courses: List[str],
    intents: List[str],
    sentiment: str,
    prediction: Dict,
    message_count: int,
    primary_intent: str,
    conversion_timeline: str,
    next_queries: List[str],
) -> str:
    """
    Produces a structured 7–9 line intelligence summary.
    Presentable to college management — max 10 lines even for 50-message sessions.
    """
    courses_str = ", ".join(courses) if courses else "General"
    intents_str = ", ".join(intents) if intents else "General Inquiry"
    score       = prediction["score"]
    prob        = prediction["conversion_probability"]
    action      = prediction["recommended_action"]
    next_q_str  = " | ".join(next_queries) if next_queries else "N/A"

    if message_count >= 9:
        depth = "deep engagement"
    elif message_count >= 5:
        depth = "moderate engagement"
    elif message_count >= 2:
        depth = "initial engagement"
    else:
        depth = "single-message contact"

    lines = [
        f"Course Interest    : {courses_str}",
        f"Primary Intent     : {primary_intent}",
        f"Topics Covered     : {intents_str}",
        f"Sentiment          : {sentiment} ({depth}, {message_count} messages)",
        f"Lead Score         : {score:.1f}/10  |  Conversion: {prob}",
        f"Conversion Timeline: {conversion_timeline}",
        f"Next Expected Query: {next_q_str}",
        f"Recommended Action : {action}",
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
          summary, courses, primary_intent, all_intents, sentiment,
          lead_score, conversion_probability, recommended_action, priority,
          conversion_timeline, next_expected_queries, messages, topics_covered
        }
    """
    if not chat_history:
        return {
            "summary":                "No messages recorded.",
            "courses":                [],
            "primary_intent":         "Unknown",
            "all_intents":            [],
            "sentiment":              "Unknown",
            "lead_score":             0,
            "conversion_probability": "Low",
            "recommended_action":     "No action needed",
            "conversion_timeline":    "No signal yet",
            "next_expected_queries":  [],
            "priority":               5,
            "messages":               0,
            "topics_covered":         0,
        }

    user_text     = _user_text(chat_history)
    message_count = len(chat_history)

    courses       = _detect_courses(user_text)
    intents       = _detect_intents(user_text)
    sentiment     = _detect_sentiment(user_text)
    prediction    = _lead_score(intents, message_count, user_text)

    # Determine primary (highest-weight) intent
    primary_intent = max(
        intents,
        key=lambda i: _LEAD_WEIGHTS.get(i, 0),
        default="General Inquiry",
    )

    # Predictive layer
    conversion_timeline = _predict_conversion_timeline(
        intents, prediction["score"], message_count
    )
    next_queries = _predict_next_queries(primary_intent, intents)

    summary_text = _build_summary_text(
        courses, intents, sentiment, prediction,
        message_count, primary_intent,
        conversion_timeline, next_queries,
    )

    return {
        "summary":                summary_text,
        "courses":                courses,
        "primary_intent":         primary_intent,
        "all_intents":            intents,
        "sentiment":              sentiment,
        "lead_score":             prediction["score"],
        "conversion_probability": prediction["conversion_probability"],
        "recommended_action":     prediction["recommended_action"],
        "conversion_timeline":    conversion_timeline,
        "next_expected_queries":  next_queries,
        "priority":               prediction["priority"],
        "messages":               message_count,
        "topics_covered":         len(intents),
    }
