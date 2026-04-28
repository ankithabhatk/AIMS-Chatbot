"""
Constraint Advisor — Powered by real admission data (marks thresholds, eligibility).
"""
import json
from pathlib import Path
from typing import Optional

_GUIDANCE_DATA: Optional[dict] = None

def _load():
    global _GUIDANCE_DATA
    if _GUIDANCE_DATA is None:
        base = Path(__file__).resolve().parents[3] / "app" / "data"
        _GUIDANCE_DATA = json.loads((base / "course_guidance.json").read_text())

def run_constraint(query: str, context: dict = None) -> dict:
    _load()
    context = context or {}
    marks = context.get("marks")
    courses = context.get("courses", [])

    if marks is None:
        return {"constraint": "Could you share your board exam percentage? That'll help me check eligibility accurately."}

    eligible = []
    not_eligible = []

    for course, rules in _GUIDANCE_DATA.items():
        min_marks = rules.get("min_marks", 45)
        if marks >= min_marks:
            eligible.append((course, min_marks, rules.get("ideal_marks_range", "N/A")))
        else:
            not_eligible.append((course, min_marks))

    if not eligible:
        return {
            "constraint": (
                f"With {marks}%, options are limited. However, you may still be eligible for some diploma programs "
                "or can consider improving your score. Would you like guidance on what to explore next?"
            )
        }

    eligible_str = "\n".join(
        [f"✅ **{c}** (min {m}%, ideal {r})" for c, m, r in eligible]
    )

    # If specific course was asked about
    if courses:
        course = courses[0]
        rules = _GUIDANCE_DATA.get(course, {})
        min_req = rules.get("min_marks", 50)
        if marks >= min_req:
            return {
                "constraint": (
                    f"✅ With {marks}%, you **are eligible** for {course}.\n"
                    f"The minimum requirement is {min_req}% and your marks fall well within range.\n\n"
                    f"Ideal range for {course}: {rules.get('ideal_marks_range', 'N/A')}"
                )
            }
        else:
            gap = round(min_req - marks, 1)
            return {
                "constraint": (
                    f"⚠️ {course} requires a minimum of {min_req}%, and you currently have {marks}%.\n"
                    f"That's a gap of {gap}%. However, you are still eligible for:\n\n{eligible_str}"
                )
            }

    return {
        "constraint": (
            f"Based on your marks ({marks}%), here are the courses you're eligible for:\n\n"
            + eligible_str
            + "\n\nWould you like to explore any of these in detail?"
        )
    }
