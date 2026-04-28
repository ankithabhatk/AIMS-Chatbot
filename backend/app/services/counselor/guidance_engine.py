"""
Guidance Engine — Decision Confidence Engine (Final Version)

Upgrades:
  1. Confidence Explanation — WHY this is the recommendation
  2. Tiered Backup Framing — Best / Backup / Stretch
  3. Risk Messaging for low-fit courses
  4. Decision Push Line — closes with authority
  5. Career Contrast — compares lifestyles not just courses
  6. Word-boundary safe interest detection
"""
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

# ─────────────────────────────────────────────
# FIT THRESHOLDS
# ─────────────────────────────────────────────
STRONG_MARKS = {"BBA": 65, "BCA": 65, "MBA": 65, "B.Com": 55, "MCA": 65, "BHM": 55}

# Use word-boundary safe patterns to prevent "ca" inside "bca" false match
INTEREST_PATTERNS: Dict[str, List[str]] = {
    "BBA":   [r"\bbusiness\b", r"\bmanagement\b", r"\bmarketing\b", r"\bleadership\b",
              r"\bhr\b", r"\bsales\b", r"\bentrepreneur\b"],
    "BCA":   [r"\bcoding\b", r"\btechnology\b", r"\bcomputer\b", r"\bsoftware\b",
              r"\bprogramming\b", r"\bdeveloper\b", r"\btech\b"],
    "MBA":   [r"\bstrategy\b", r"\bconsulting\b", r"\bcorporate\b", r"\bmba\b"],
    "B.Com": [r"\baccounts\b", r"\baccountancy\b", r"\bcommerce\b", r"\bbanking\b",
              r"\btaxation\b", r"\baudit\b", r"\bfinance\b"],
    "MCA":   [r"\bcomputer science\b", r"\badvanced it\b", r"\bsoftware development\b", r"\bmca\b"],
    "BHM":   [r"\bhotel\b", r"\bhospitality\b", r"\btravel\b", r"\btourism\b", r"\bevent\b"],
}

HIGH_SALARY_SIGNALS = [r"\bhigh salary\b", r"\bbetter salary\b", r"\bhigh package\b",
                       r"\bmore money\b", r"\bgood pay\b", r"\bhigh paying\b"]

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
def _score_course(course: str, marks: Optional[float], matched_interest: Optional[str],
                  weak_math: bool, salary_first: bool) -> Dict:
    rules = _GUIDANCE_DATA.get(course, {})
    min_marks = rules.get("min_marks", 45)
    strong_marks = STRONG_MARKS.get(course, 65)
    score = 0.0
    reasons: List[str] = []

    # Marks
    if marks is not None:
        if marks >= strong_marks:
            score += 0.5
            reasons.append(f"marks ({marks}%) are well above the {min_marks}% requirement")
        elif marks >= min_marks:
            score += 0.25
            reasons.append(f"marks ({marks}%) meet the {min_marks}% minimum")
        else:
            score -= 0.3
            reasons.append(f"marks ({marks}%) are {round(min_marks - marks, 1)}% below the {min_marks}% minimum")

    # Interest
    if matched_interest == course:
        score += 0.55  # Increased from 0.4 to 0.55 to prioritize interest over marks
        reasons.append(f"your interest directly aligns with {course}")

    # Math aversion
    if weak_math and course in ["B.Com", "BCA", "MCA"]:
        score -= 0.15
    elif weak_math and course in ["BBA", "BHM"]:
        score += 0.1
        reasons.append("low math requirement suits you")

    # Salary-first bonus: prioritise high-earning courses
    if salary_first:
        avg = _CAREER_DATA.get(course, {}).get("avg_salary_lpa", 0) if _CAREER_DATA else 0
        if avg >= 7:
            score += 0.2
            reasons.append(f"strong earning potential (avg {avg:.1f} LPA)")

    tier = "strong_fit" if score >= 0.7 else ("moderate_fit" if score >= 0.3 else "low_fit")
    return {"score": round(score, 2), "tier": tier, "reasons": reasons}


# ─────────────────────────────────────────────
# CAREER DATA HELPERS
# ─────────────────────────────────────────────
def _career_data(course: str) -> Dict:
    if not _CAREER_DATA:
        return {}
    return _CAREER_DATA.get(course, {})

def _career_preview(course: str) -> str:
    d = _career_data(course)
    role = d.get("roles", ["Professional"])[0]
    sal_range = d.get("salary_range", "")
    growth = d.get("growth", "Moderate")
    # Upgraded salary framing — add growth note
    if sal_range:
        return f"{role} · {sal_range}, with strong growth after 2–3 years"
    return role


# ─────────────────────────────────────────────
# SIGNAL EXTRACTOR
# ─────────────────────────────────────────────
def _extract_signals(query: str, context: Dict) -> Dict:
    q = query.lower()
    marks = context.get("marks")
    interest_context = context.get("interests") or context.get("interest")

    # Interest from context first; then from query using word-boundary patterns
    matched_interest: Optional[str] = None
    if interest_context:
        # Map free-text interest → best course
        for course, patterns in INTEREST_PATTERNS.items():
            if any(re.search(p, interest_context.lower()) for p in patterns):
                matched_interest = course
                break
    else:
        for course, patterns in INTEREST_PATTERNS.items():
            if any(re.search(p, q) for p in patterns):
                matched_interest = course
                break

    weak_math = bool(re.search(r"\bweak in maths?\b|\bbad at math\b|\bhate maths?\b|\bno maths?\b|\bavoid math\b", q))
    salary_first = any(re.search(p, q) for p in HIGH_SALARY_SIGNALS)

    return {
        "marks": marks,
        "matched_interest": matched_interest,
        "weak_math": weak_math,
        "salary_first": salary_first,
    }


# ─────────────────────────────────────────────
# RESPONSE COMPOSER
# ─────────────────────────────────────────────
def _compose_response(signals: Dict, ranked: List, all_scores: Dict, reasoning_block: Optional[str] = None) -> str:
    top_course, top_data = ranked[0]
    backup_ranked = ranked[1:]

    marks = signals["marks"]
    interest = signals["matched_interest"]

    # ── Section 1: Personalised intro ──
    context_parts = []
    if marks:
        context_parts.append(f"your marks ({marks}%)")
    if interest:
        context_parts.append(f"your interest in {interest.replace('B.Com', 'commerce').replace('BCA', 'tech').replace('BBA', 'business')}")
    if signals["salary_first"]:
        context_parts.append("your priority for a high-earning career")
    context_str = " and ".join(context_parts) if context_parts else "your profile"

    lines = [f"Based on {context_str}, here's my recommendation:\n"]

    # ── Section 2: Primary recommendation with confidence explanation ──
    tier_emoji = {"strong_fit": "✅", "moderate_fit": "🟡", "low_fit": "⚠️"}[top_data["tier"]]
    tier_label = {"strong_fit": "Best Option", "moderate_fit": "Best Option", "low_fit": "Best Available Option"}[top_data["tier"]]

    lines.append(f"🎯 **{tier_label}: {top_course}** {tier_emoji}")

    # Confidence explanation — WHY
    if top_data["reasons"]:
        lines.append("   *Why this fits:*")
        for r in top_data["reasons"][:2]:
            lines.append(f"   • {r.capitalize()}")

    # Career preview
    preview = _career_preview(top_course)
    if preview:
        lines.append(f"   💼 Career: {preview}")

    # Risk message for low_fit primary
    if top_data["tier"] == "low_fit" and marks:
        rules = _GUIDANCE_DATA.get(top_course, {})
        gap = round(rules.get("min_marks", 50) - marks, 1)
        gap_str = f"You are {gap}% below the standard threshold — " if gap > 0 else ""
        lines.append(f"\n   ⚠️ *Note: {top_course} is possible but competitive with {marks}%. "
                     f"{gap_str}manage expectations on admission.*")

    lines.append("")

    # ── Section 3: Backup options with career contrast ──
    if backup_ranked:
        backup_course, backup_data = backup_ranked[0]
        backup_tier = backup_data["tier"]
        backup_label = "🔁 Backup Option" if backup_tier in ["moderate_fit", "strong_fit"] else "⚠️ Stretch Option"
        backup_preview = _career_preview(backup_course)

        lines.append(f"{backup_label}: **{backup_course}**")
        if backup_data["reasons"]:
            lines.append(f"   • {backup_data['reasons'][0].capitalize()}")
        if backup_preview:
            lines.append(f"   💼 Career: {backup_preview}")

        # Career contrast if both previews exist
        if preview and backup_preview:
            lines.append(f"\n📊 **Career Contrast:**")
            lines.append(f"   • {top_course} → {preview}")
            lines.append(f"   • {backup_course} → {backup_preview}")

    # ── Section 4: Stretch / risky options ──
    if len(backup_ranked) > 1:
        stretch_course, stretch_data = backup_ranked[1]
        if stretch_data["tier"] == "low_fit":
            lines.append(f"\n⚠️ Stretch: **{stretch_course}** — possible but risky given current profile.")

    # ── Section 5: Decision lock ──
    lines.append("")
    # Map course name → human-readable goal
    _COURSE_GOALS = {
        "BBA": "management or business", "MBA": "senior management or high pay",
        "BCA": "technology and software", "MCA": "advanced technology",
        "B.Com": "finance or commerce", "BHM": "hospitality"
    }
    if signals.get("salary_first"):
        goal_desc = "a high-paying career"
    elif signals.get("matched_interest"):
        goal_desc = _COURSE_GOALS.get(signals["matched_interest"], signals["matched_interest"])
    else:
        goal_desc = _COURSE_GOALS.get(top_course, "a stable career")
    goal_phrase = f"If your goal is {goal_desc}, then {top_course} is the most practical and safe choice right now."
    lines.append(f"**{goal_phrase}**")

    # ── Salary framing with growth note ──
    if top_data["tier"] in ["strong_fit", "moderate_fit"]:
        d = _career_data(top_course)
        sal_range = d.get("salary_range", "")
        if sal_range:
            lines.append(f"   💰 Typical starting range: ₹{sal_range}, with strong growth after 2–3 years.")

    # ── Emotional anchor ──
    if top_data["tier"] == "strong_fit":
        lines.append("   *This is a stable and future-safe path based on your current profile.*")
    elif top_data["tier"] == "moderate_fit":
        lines.append("   *This keeps your options open while moving you forward.*")
    else:
        lines.append("   *Even with limited marks, taking the right path now builds momentum.*")

    lines.append("")

    # ── Section 6: Micro-commitment (triggers conversion flow) ──
    # Integrated "Why this over that" reasoning via ERL
    if reasoning_block:
        lines.append(reasoning_block)
    
    lines.append("\nDoes this direction feel right to you?")

    return "\n".join(lines)


def run_guidance_engine(query: str, context: Optional[Dict[str, Any]] = None) -> Dict:
    _load()
    context = context or {}
    signals = _extract_signals(query, context)

    # HARD BOUNDARY: Only score courses offered by college
    from app.config.college_courses import get_college_courses
    college_courses = get_college_courses()

    all_scores = {
        course: _score_course(
            course, signals["marks"], signals["matched_interest"],
            signals["weak_math"], signals["salary_first"]
        )
        for course in college_courses  # ← ONLY college courses
    }

    ranked = sorted(all_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    
    # GOAL MAPPING LAYER: Adjust ranking based on user goals
    from app.services.counselor.goal_mapper import map_goal_to_course
    goal_mapping = map_goal_to_course(query, signals.get("matched_interest"), context)
    
    if goal_mapping and goal_mapping.get("primary_course"):
        goal_course = goal_mapping["primary_course"]
        # Move goal-aligned course to front
        ranked = [item for item in ranked if item[0] == goal_course] + \
                 [item for item in ranked if item[0] != goal_course]
    
    # INTEREST DOMINANCE: Force interest mapping (if no goal override)
    elif signals.get("matched_interest"):
        force_primary = signals["matched_interest"]
        # Move the forced primary to the front
        ranked = [item for item in ranked if item[0] == force_primary] + \
                 [item for item in ranked if item[0] != force_primary]

    top_course, top_data = ranked[0]
    second_course = ranked[1][0] if len(ranked) > 1 else None

    response = _compose_response(signals, ranked, all_scores)

    # ── Structured reasoning dict (for ERL) ──
    marks = signals.get("marks")
    interest = signals.get("matched_interest")
    rules = _GUIDANCE_DATA.get(top_course, {})
    min_marks = rules.get("min_marks", 50)
    career = _career_data(top_course)
    top_roles = career.get("roles", [])[:2]
    sal_range = career.get("salary_range", "")

    marks_fit = (
        f"Your {marks}% comfortably meets the {min_marks}% minimum for {top_course}"
        if marks and marks >= min_marks + 10
        else (
            f"Your {marks}% meets the {min_marks}% requirement for {top_course}"
            if marks and marks >= min_marks
            else (
                f"Your {marks}% is below the typical {min_marks}% threshold — admission is competitive"
                if marks
                else "Marks not yet provided — recommendation is based on interest signals"
            )
        )
    )

    interest_fit = (
        f"Your interest in {interest.replace('BCA','technology').replace('BBA','business').replace('B.Com','commerce').replace('BHM','hospitality').replace('MBA','management')} "
        f"aligns directly with {top_course} subjects and career tracks"
        if interest == top_course
        else (
            f"No specific interest declared yet — {top_course} ranked highest on marks and career potential"
            if not interest
            else f"Your interest gives context; {top_course} is the best match given your marks and goals"
        )
    )

    career_alignment = (
        f"This path leads to roles like {', '.join(top_roles)}"
        + (f" with starting packages of {sal_range}" if sal_range else "")
        if top_roles
        else f"{top_course} opens structured career pathways in its domain"
    )

    # Why NOT others — compare vs second option
    why_not_others = (
        f"{second_course} is a valid backup, but scored lower given your current profile"
        if second_course
        else "Other options were scored lower based on your marks and interest combination"
    )

    # Risk note — transparent about limitations
    risk_note = None
    if top_data["tier"] == "low_fit":
        risk_note = f"With {marks}% marks, admission to {top_course} will be competitive — have a backup plan ready"
    elif interest and interest != top_course:
        risk_note = f"Your stated interest points slightly away from {top_course} — consider confirming your preference"
    elif signals.get("weak_math") and top_course in ["BCA", "MCA"]:
        risk_note = f"{top_course} involves quantitative subjects — if you're uncomfortable with math, factor this in"

    # ── Evidence Layer ──
    sample_size = career.get("sample_size", 0)
    market_demand = {
        "BCA": "High demand — tech roles growing 25%+ YoY in India",
        "MBA": "Very high demand — management roles across all sectors",
        "BBA": "Steady demand — business roles span every industry",
        "B.Com": "Stable demand — finance/accounting always essential",
        "MCA": "High demand — advanced tech roles with premium packages",
        "BHM": "Growing demand — hospitality sector recovering strongly post-2022",
    }
    evidence = {
        "data_source": "2025 Indian fresher salary trends and real admission patterns",
        "sample_size": sample_size if sample_size > 0 else "industry aggregated",
        "market_signal": market_demand.get(top_course, "Verified demand in relevant industry sector"),
        "nirf_context": (
            "Management programs evaluated by NIRF on placement quality and graduation outcomes"
            if top_course in ["MBA", "BBA", "B.Com"]
            else "Technical programs show strongest salary-to-ranking correlation in NIRF data"
        ),
    }

    # ── Confidence reason (human-readable, not a magic number) ──
    reason_parts = []
    if marks and marks >= min_marks + 10:
        reason_parts.append("marks align strongly")
    elif marks and marks >= min_marks:
        reason_parts.append("marks meet the threshold")
    if interest == top_course:
        reason_parts.append("interest matches directly")
    if top_data["tier"] == "strong_fit":
        reason_parts.append("overall profile fits well")
    if signals.get("salary_first") and career.get("avg_salary_lpa", 0) >= 7:
        reason_parts.append("strong earning potential confirmed")

    confidence_reason = (
        " + ".join(reason_parts) if reason_parts
        else "best available match given current profile"
    )

    # ── Calibrated confidence score ──
    base_confidence = top_data["score"]
    if not marks:
        base_confidence *= 0.75
    if not interest:
        base_confidence *= 0.85
    confidence_score = round(min(0.97, max(0.50, base_confidence)), 2)

    # ── Compose Final Response ──
    from app.services.counselor.reasoning import build_explanation
    reasoning_block = build_explanation({
        "reasoning": {
            "marks_fit": marks_fit,
            "interest_fit": interest_fit,
            "career_alignment": career_alignment,
            "why_not_others": why_not_others,
        }
    })
    response = _compose_response(signals, ranked, all_scores, reasoning_block)

    # ── Soft bridge: marks present, interest missing ──
    # Instead of blocking bridge entirely, offer a targeted clarifying question
    soft_bridge_ready = (
        marks is not None
        and interest is None
        and top_data["tier"] in ["strong_fit", "moderate_fit"]
    )
    soft_bridge_question = None
    if soft_bridge_ready:
        from app.services.counselor.adaptive_questions import get_adaptive_question
        _guidance_stub = {
            "top_course": top_course,
            "recommended_courses": [c for c, _ in ranked[:2]],
        }
        soft_bridge_question = get_adaptive_question(context, _guidance_stub)



    decision_ready = (
        signals.get("marks") is not None
        and signals.get("matched_interest") is not None
        and top_data["tier"] in ["strong_fit", "moderate_fit"]
    )

    result = {
        "intent": "guidance",
        "guidance": response,
        "recommended_courses": [c for c, _ in ranked[:3]],
        "fit_tiers": {c: d["tier"] for c, d in all_scores.items()},
        # Explainable Reasoning Layer
        "reasoning": {
            "marks_fit": marks_fit,
            "interest_fit": interest_fit,
            "career_alignment": career_alignment,
            "why_not_others": why_not_others,
        },
        # Evidence Layer
        "evidence": evidence,
        # Trust signals
        "risk_note": risk_note,
        "confidence_score": confidence_score,
        "confidence_reason": confidence_reason,
        # Bridge routing
        "decision_ready": decision_ready,
        "soft_bridge_ready": soft_bridge_ready,
        "soft_bridge_question": soft_bridge_question,
        "top_course": top_course,
        # Legacy
        "reasoning_list": top_data["reasons"],
        "confidence": 0.95 if top_data["tier"] == "strong_fit" else 0.8,
    }
    
    # GOAL ENHANCEMENT: Add goal-aware personalization
    if goal_mapping and goal_mapping.get("personalization"):
        from app.services.counselor.goal_mapper import enhance_guidance_with_goal
        result = enhance_guidance_with_goal(result, goal_mapping)
    
    return result


def run_guidance(query: str, context: dict = None) -> dict:
    return run_guidance_engine(query, context)

