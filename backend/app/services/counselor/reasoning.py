"""
Explainable Reasoning Layer (ERL)
==================================
Converts structured guidance output into human-readable, personalized
explanations. Used by the guidance → action bridge.

Design principle:
  • Every line references the student's actual input (marks / interest / goals)
  • Confidence score is shown only at high-intent stage (never trivially)
  • Risk note is included when present — honesty builds trust
"""
from typing import Dict, Optional


def build_explanation(guidance: Dict) -> str:
    """
    Convert the structured reasoning dict from run_guidance_engine()
    into a clean, personalised explanation block.
    Uses MiniMaxService for persuasive rewriting if available.

    Returns a formatted multi-line string ready to embed in a response.
    """
    r = guidance.get("reasoning", {})
    
    # Use MiniMax for enhanced explanation
    from app.services.llm.minimax_service import get_minimax_service
    enhanced = get_minimax_service().rewrite_explanation(r)
    if enhanced:
        return enhanced
        
    # Fallback to structured if MiniMax fails or is disabled
    marks_fit      = r.get("marks_fit", "")
    interest_fit   = r.get("interest_fit", "")
    career_align   = r.get("career_alignment", "")
    why_not_others = r.get("why_not_others", "")

    lines = ["**Here's why this fits your profile:**"]

    if marks_fit:
        lines.append(f"  • {marks_fit}.")
    if interest_fit:
        lines.append(f"  • {interest_fit}.")
    if career_align:
        lines.append(f"  • {career_align}.")

    if why_not_others:
        lines.append(f"\n**Compared to other options:**")
        lines.append(f"  • {why_not_others}.")

    return "\n".join(lines)


def build_confidence_note(guidance: Dict, show_threshold: float = 0.80) -> str:
    """
    Returns a soft, human-readable confidence sentence that includes WHY —
    not just a number. Only shown when score is above threshold.
    """
    score = guidance.get("confidence_score", 0.0)
    reason = guidance.get("confidence_reason", "")
    if score < show_threshold:
        return ""
    pct = int(score * 100)
    reason_str = f" ({reason})" if reason else ""
    return f"This recommendation matches your profile with approximately {pct}% confidence{reason_str}."


def build_evidence_note(guidance: Dict) -> str:
    """
    Subtle trust-builder: tells the student this isn't a random AI answer.
    Kept short — one line max. Never salesy.
    """
    e = guidance.get("evidence", {})
    if not e:
        return ""
    source = e.get("data_source", "")
    signal = e.get("market_signal", "")
    lines = []
    if source:
        lines.append(f"Based on {source}.")
    if signal:
        lines.append(f"Market context: {signal}.")
    return "_(" + " ".join(lines) + ")_" if lines else ""


def build_full_bridge_response(guidance: Dict, context: Dict) -> str:
    """
    Complete bridge response injecting ERL explanation + evidence note
    + confidence reason + role preview + permission-gated next steps.
    No pressure. No links.
    """
    import json
    from pathlib import Path

    top_course = guidance.get("top_course", "this course")

    # Career role preview from data
    try:
        base = Path(__file__).resolve().parents[3] / "app" / "data"
        career_paths = json.loads((base / "career_paths.json").read_text())
        career = career_paths.get(top_course, {})
        roles = career.get("roles", [])[:2]
        sal_range = career.get("salary_range", "")
    except Exception:
        roles, sal_range = [], ""

    role_preview = ""
    if roles:
        role_str = ", ".join(roles)
        sal_str  = f" with starting packages of {sal_range}" if sal_range else ""
        role_preview = f"Students in this path typically move into roles like **{role_str}**{sal_str}."

    # Core ERL explanation block
    explanation = build_explanation(guidance)

    # Confidence note with human-readable reason (only if score ≥ 0.80)
    confidence_note = build_confidence_note(guidance)

    # Evidence note (subtle credibility anchor, always shown)
    evidence_note = build_evidence_note(guidance)

    lines = [
        f"Based on everything you've shared, **{top_course}** looks like a strong choice for you.",
        "",
        explanation,
    ]

    if role_preview:
        lines += ["", role_preview]

    if confidence_note:
        lines += ["", f"_{confidence_note}_"]

    lines += [
        "",
        "If you'd like, I can help you with:",
        "  • What the course structure looks like",
        "  • Eligibility and admission steps",
        "  • How to prepare before joining",
        "",
        "What would you like to explore next?",
    ]

    risk_note = guidance.get("risk_note")
    if risk_note:
        lines += [
            "",
            "Just to be transparent:",
            f"  • {risk_note}",
        ]

    if evidence_note:
        lines += ["", evidence_note]

    return "\n".join(lines)
