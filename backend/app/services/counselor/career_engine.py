"""
Career Engine — Powered by real Indian salary/role data (cleaned from Kaggle).
"""
import json
from pathlib import Path
from typing import Optional

_CAREER_DATA: Optional[dict] = None
_COLLEGE_DATA: Optional[dict] = None

def _load():
    global _CAREER_DATA, _COLLEGE_DATA
    if _CAREER_DATA is None:
        base = Path(__file__).resolve().parents[3] / "app" / "data"
        _CAREER_DATA = json.loads((base / "career_paths.json").read_text())
        _COLLEGE_DATA = json.loads((base / "college_stats.json").read_text())

def run_career(query: str, context: dict = None) -> dict:
    _load()
    context = context or {}
    q = query.lower()
    courses = context.get("courses", [])

    # Try to infer course from query if not in context
    for course in _CAREER_DATA:
        if course.lower() in q:
            courses = [course]
            break

    if not courses:
        # Generic multi-course summary
        lines = []
        for course, data in _CAREER_DATA.items():
            top_role = data["roles"][0] if data["roles"] else "Industry Professional"
            lines.append(f"• **{course}** → {top_role}, avg {data['avg_salary_lpa']} LPA")
        return {
            "career": (
                "Here's a quick salary snapshot across AIMS courses:\n\n"
                + "\n".join(lines)
                + "\n\nWould you like career details for a specific course?"
            )
        }

    course = courses[0]
    data = _CAREER_DATA.get(course)
    college_info = _COLLEGE_DATA.get("aims_stats", {}).get(course, {})

    if not data:
        return {"career": f"I have career data for BBA, BCA, MBA, B.Com, MCA, and BHM. Which one would you like to explore?"}

    roles_str = ", ".join(data["roles"][:4])
    skills_str = ", ".join(data["top_skills"][:5])
    package = college_info.get("avg_package", data.get("salary_range", "N/A"))

    response = (
        f"**Career Outlook — {course}**\n\n"
        f"💼 **Common Roles:** {roles_str}\n"
        f"💰 **Salary Range:** {package}\n"
        f"🛠 **Key Skills:** {skills_str}\n"
        f"📈 **Growth:** {data.get('growth', 'Good')}\n"
    )

    return {"career": response}
