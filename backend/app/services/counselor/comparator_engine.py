import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

_GUIDANCE_DATA: Optional[dict] = None
_CAREER_DATA: Optional[dict] = None

def _load():
    global _GUIDANCE_DATA, _CAREER_DATA
    if _GUIDANCE_DATA is None:
        base = Path(__file__).resolve().parents[3] / "app" / "data"
        _GUIDANCE_DATA = json.loads((base / "course_guidance.json").read_text())
        _CAREER_DATA = json.loads((base / "career_paths.json").read_text())

def run_comparator(query: str, context: dict = None) -> dict:
    """
    Compares two or more courses based on marks, interests, and career goals.
    """
    _load()
    context = context or {}
    
    # 1. Extract courses to compare
    from app.services.counselor.entity_extractor import extract_entities
    entities = extract_entities(query)
    courses_to_compare = entities.get("courses", [])
    
    # Fallback: if no courses in query, use context
    if not courses_to_compare:
        context_courses = context.get("courses", [])
        if len(context_courses) >= 2:
            courses_to_compare = context_courses[:2]
        elif len(context_courses) == 1:
            # Compare context course with a logical alternative
            primary = context_courses[0]
            alternatives = {
                "BBA": "B.Com",
                "BCA": "MCA",
                "MBA": "BBA",
                "B.Com": "BBA",
                "MCA": "BCA",
                "BHM": "BBA"
            }
            courses_to_compare = [primary, alternatives.get(primary, "BBA")]
        else:
            # Default comparison
            courses_to_compare = ["BBA", "BCA"]

    # Ensure unique courses
    courses_to_compare = list(dict.fromkeys(courses_to_compare))
    if len(courses_to_compare) < 2:
        # Add a default if only one found
        courses_to_compare.append("BBA" if courses_to_compare[0] != "BBA" else "BCA")

    # 2. Get data for each course
    comparison_data = []
    marks = context.get("marks")
    interests = context.get("interests", "")
    interests = interests.lower() if interests else ""

    for course in courses_to_compare[:3]: # Max 3 for clarity
        g_data = _GUIDANCE_DATA.get(course, {})
        c_data = _CAREER_DATA.get(course, {})
        
        # Calculate fit
        fit_score = 0
        reasons = []
        
        if marks:
            min_m = g_data.get("min_marks", 50)
            if marks >= min_m + 10:
                fit_score += 2
                reasons.append("Marks well above threshold")
            elif marks >= min_m:
                fit_score += 1
                reasons.append("Meets marks requirement")
            else:
                fit_score -= 1
                reasons.append("Below marks threshold")
                
        if interests:
            tags = g_data.get("tags", [])
            if any(tag in interests for tag in tags):
                fit_score += 2
                reasons.append("Strong interest alignment")

        comparison_data.append({
            "name": course,
            "fit_score": fit_score,
            "reasons": reasons,
            "salary": c_data.get("avg_salary_lpa", "N/A"),
            "growth": c_data.get("growth", "N/A"),
            "duration": g_data.get("duration", "N/A"),
            "difficulty": g_data.get("difficulty", "N/A"),
            "roles": c_data.get("roles", [])[:2]
        })

    # 3. Compose response
    lines = [f"### Comparing {', '.join(courses_to_compare)}\n"]
    
    # Header Row
    lines.append("| Feature | " + " | ".join([f"**{c['name']}**" for c in comparison_data]) + " |")
    lines.append("| :--- | " + " | ".join([":---" for _ in comparison_data]) + " |")
    
    # Salary Row
    lines.append("| **Avg Salary** | " + " | ".join([f"₹{c['salary']} LPA" if isinstance(c['salary'], (int, float)) else c['salary'] for c in comparison_data]) + " |")
    
    # Growth Row
    lines.append("| **Growth** | " + " | ".join([c['growth'] for c in comparison_data]) + " |")
    
    # Difficulty Row
    lines.append("| **Difficulty** | " + " | ".join([c['difficulty'].capitalize() for c in comparison_data]) + " |")
    
    # Roles Row
    lines.append("| **Top Roles** | " + " | ".join([", ".join(c['roles']) for c in comparison_data]) + " |")
    
    lines.append("\n**Why choose one over the other?**")
    
    # Comparison Logic
    c1, c2 = comparison_data[0], comparison_data[1]
    
    # Marks-based logic
    if marks:
        if c1['fit_score'] > c2['fit_score']:
            lines.append(f"- Based on your {marks}%, **{c1['name']}** is a safer and more realistic choice.")
        elif c2['fit_score'] > c1['fit_score']:
            lines.append(f"- Based on your {marks}%, **{c2['name']}** aligns better with your current score.")
            
    # Salary-based logic
    try:
        s1 = float(c1['salary']) if isinstance(c1['salary'], (int, float)) else 0
        s2 = float(c2['salary']) if isinstance(c2['salary'], (int, float)) else 0
        if s1 > s2 + 1:
            lines.append(f"- If your priority is **salary**, {c1['name']} typically offers higher starting packages (₹{c1['salary']} LPA).")
        elif s2 > s1 + 1:
            lines.append(f"- For higher **earning potential**, {c2['name']} is the stronger contender.")
    except: pass

    # Interest-based logic
    if interests:
        lines.append(f"- Your interest in '{interests}' suggests a natural fit for the curriculum in **{c1['name'] if c1['fit_score'] >= c2['fit_score'] else c2['name']}**.")

    lines.append(f"\nDoes this comparison help you narrow it down, or should we look at another option?")

    return {
        "answer": "\n".join(lines),
        "courses": courses_to_compare,
        "comparison": comparison_data
    }
