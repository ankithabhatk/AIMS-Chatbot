"""
Goal Mapper - Personal Decision Layer

Maps user goals to course recommendations within college boundary.
This layer sits BETWEEN interest mapping and guidance engine.

Architecture:
User Input → Interest Mapper → Goal Mapper → Guidance Engine → Decision

Goals Supported:
1. Job (immediate employment)
2. Higher Studies (MBA, MCA, etc.)
3. Salary (high-paying career)
4. Abroad (international opportunities)
5. Entrepreneurship (start own business)
6. Stability (safe, predictable career)
"""

from typing import Dict, Optional, List
import re

# ============================================
# GOAL SIGNAL PATTERNS
# ============================================
GOAL_PATTERNS = {
    "job": [
        r"\bjob\b", r"\bemployment\b", r"\bwork\b", r"\bplacement\b",
        r"\bget placed\b", r"\bget a job\b", r"\bstart working\b",
        r"\bcareer\b", r"\bjoin company\b"
    ],
    "higher_studies": [
        r"\bmba\b", r"\bmca\b", r"\bmaster\b", r"\bphd\b",
        r"\bhigher studies\b", r"\bfurther studies\b", r"\bpost.?grad\b",
        r"\bcontinue studying\b", r"\badvanced degree\b"
    ],
    "salary": [
        r"\bhigh salary\b", r"\bgood salary\b", r"\bhigh.?pay\b",
        r"\bpackage\b", r"\bearning\b", r"\bmoney\b",
        r"\bhigh.?income\b", r"\blucrative\b"
    ],
    "abroad": [
        r"\babroad\b", r"\bforeign\b", r"\binternational\b",
        r"\boverseas\b", r"\bus\b", r"\buk\b", r"\bcanada\b",
        r"\baustralia\b", r"\beurope\b", r"\bwork abroad\b"
    ],
    "entrepreneurship": [
        r"\bbusiness\b", r"\bstartup\b", r"\bentrepreneur\b",
        r"\bown business\b", r"\bstart.?up\b", r"\bself.?employed\b",
        r"\bcompany\b.*\bstart\b"
    ],
    "stability": [
        r"\bstable\b", r"\bsecure\b", r"\bsafe\b", r"\breliable\b",
        r"\bpredictable\b", r"\bsteady\b", r"\blong.?term\b"
    ]
}

# ============================================
# GOAL → COURSE PRIORITY MAPPING
# ============================================
GOAL_COURSE_PRIORITY = {
    "job": {
        # Courses ranked by immediate employability
        "priority": ["BCA", "BBA", "B.Com", "BHM", "MBA", "MCA"],
        "reasoning": {
            "BCA": "Strong placement record in tech companies, immediate job opportunities",
            "BBA": "Business roles available across industries, good entry-level positions",
            "B.Com": "Accounting and finance roles always in demand",
            "BHM": "Hospitality sector has immediate openings"
        }
    },
    "higher_studies": {
        # Courses with strong postgrad pathways
        "priority": ["BCA", "BBA", "B.Com", "MBA", "MCA", "BHM"],
        "reasoning": {
            "BCA": "Natural path to MCA for advanced tech roles",
            "BBA": "Strong foundation for MBA programs",
            "B.Com": "Gateway to M.Com, CA, or MBA in Finance"
        }
    },
    "salary": {
        # Courses with highest earning potential
        "priority": ["BCA", "MBA", "MCA", "BBA", "B.Com", "BHM"],
        "reasoning": {
            "BCA": "Tech roles offer 4-8 LPA starting packages",
            "MBA": "Management roles command premium salaries",
            "MCA": "Senior tech positions with 6-12 LPA packages"
        }
    },
    "abroad": {
        # Courses with international mobility
        "priority": ["BCA", "MBA", "MCA", "BBA", "B.Com", "BHM"],
        "reasoning": {
            "BCA": "Tech skills are globally transferable, strong visa prospects",
            "MBA": "International business programs widely recognized",
            "MCA": "Advanced tech roles in demand worldwide"
        }
    },
    "entrepreneurship": {
        # Courses that prepare for business ownership
        "priority": ["BBA", "MBA", "BCA", "B.Com", "BHM", "MCA"],
        "reasoning": {
            "BBA": "Core business skills for running a company",
            "MBA": "Strategic management and leadership training",
            "BCA": "Tech entrepreneurship and product development"
        }
    },
    "stability": {
        # Courses with predictable career paths
        "priority": ["B.Com", "BBA", "BCA", "BHM", "MBA", "MCA"],
        "reasoning": {
            "B.Com": "Accounting and finance roles are recession-proof",
            "BBA": "Management skills always needed",
            "BCA": "Tech sector continues to grow steadily"
        }
    }
}

# ============================================
# GOAL EXTRACTION
# ============================================
def extract_goal_from_query(query: str) -> Optional[str]:
    """
    Extract primary goal from user query.
    Returns: goal name or None
    """
    query_lower = query.lower()
    
    # Score each goal
    scores = {goal: 0 for goal in GOAL_PATTERNS}
    
    for goal, patterns in GOAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                scores[goal] += 1
    
    # Return goal with highest score
    best_goal = max(scores, key=scores.get)
    if scores[best_goal] > 0:
        return best_goal
    
    return None


def extract_multiple_goals(query: str) -> List[str]:
    """
    Extract all goals mentioned in query.
    Example: "I want a high salary job abroad" → ["salary", "job", "abroad"]
    """
    query_lower = query.lower()
    goals = []
    
    for goal, patterns in GOAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                goals.append(goal)
                break  # Only count each goal once
    
    return goals


# ============================================
# GOAL-AWARE COURSE RANKING
# ============================================
def rank_courses_by_goal(goal: str, base_course: Optional[str] = None) -> Dict:
    """
    Rank courses based on user goal.
    
    Args:
        goal: Primary goal (job, salary, abroad, etc.)
        base_course: Course from interest mapping (optional)
    
    Returns:
        {
            "primary": "BCA",
            "alternatives": ["BBA", "B.Com"],
            "reasoning": "...",
            "goal_alignment": 0.95
        }
    """
    if goal not in GOAL_COURSE_PRIORITY:
        # No specific goal, return base course
        return {
            "primary": base_course,
            "alternatives": [],
            "reasoning": "Based on your interests",
            "goal_alignment": 0.7
        }
    
    goal_data = GOAL_COURSE_PRIORITY[goal]
    priority_list = goal_data["priority"]
    reasoning_map = goal_data["reasoning"]
    
    # If base_course exists and is in priority list, boost it
    if base_course and base_course in priority_list:
        primary = base_course
        alternatives = [c for c in priority_list if c != base_course][:2]
        reasoning = reasoning_map.get(base_course, f"{base_course} aligns with your {goal} goal")
        alignment = 0.95
    else:
        # Use goal priority
        primary = priority_list[0]
        alternatives = priority_list[1:3]
        reasoning = reasoning_map.get(primary, f"{primary} is best for {goal}")
        alignment = 0.9
    
    return {
        "primary": primary,
        "alternatives": alternatives,
        "reasoning": reasoning,
        "goal_alignment": alignment,
        "goal": goal
    }


def rank_courses_by_multiple_goals(goals: List[str], base_course: Optional[str] = None) -> Dict:
    """
    Handle multiple goals (e.g., "high salary job abroad").
    Uses weighted scoring across all goals.
    """
    if not goals:
        return rank_courses_by_goal(None, base_course)
    
    # Score each course across all goals
    try:
        from app.config.college_courses import get_college_courses
        college_courses = get_college_courses()
    except:
        # Fallback for testing
        college_courses = ["BBA", "BCA", "MBA", "B.Com", "MCA", "BHM"]
    
    course_scores = {course: 0 for course in college_courses}
    
    for goal in goals:
        if goal in GOAL_COURSE_PRIORITY:
            priority_list = GOAL_COURSE_PRIORITY[goal]["priority"]
            # Higher priority = higher score
            for i, course in enumerate(priority_list):
                if course in course_scores:
                    course_scores[course] += (len(priority_list) - i)
    
    # Boost base_course if provided
    if base_course and base_course in course_scores:
        course_scores[base_course] += 10
    
    # Sort by score
    ranked = sorted(course_scores.items(), key=lambda x: x[1], reverse=True)
    
    primary = ranked[0][0]
    alternatives = [c for c, _ in ranked[1:3]]
    
    # Build reasoning
    goal_descriptions = {
        "job": "immediate employment",
        "salary": "high earning potential",
        "abroad": "international opportunities",
        "higher_studies": "postgraduate pathways",
        "entrepreneurship": "business ownership",
        "stability": "career security"
    }
    
    goal_text = " and ".join([goal_descriptions.get(g, g) for g in goals[:2]])
    reasoning = f"{primary} offers the best combination of {goal_text}"
    
    return {
        "primary": primary,
        "alternatives": alternatives,
        "reasoning": reasoning,
        "goal_alignment": 0.92,
        "goals": goals
    }


# ============================================
# MAIN GOAL MAPPING FUNCTION
# ============================================
def map_goal_to_course(query: str, interest_course: Optional[str] = None, context: Optional[Dict] = None) -> Dict:
    """
    Main goal mapping function.
    
    Args:
        query: User query
        interest_course: Course from interest mapping
        context: Additional context (marks, etc.)
    
    Returns:
        {
            "primary_course": "BCA",
            "alternative_courses": ["BBA", "B.Com"],
            "goal": "salary",
            "reasoning": "...",
            "confidence": 0.95,
            "personalization": "Based on your goal of high salary..."
        }
    """
    context = context or {}
    
    # Extract goals
    goals = extract_multiple_goals(query)
    
    if not goals:
        # No explicit goal, use interest-based course
        return {
            "primary_course": interest_course,
            "alternative_courses": [],
            "goal": None,
            "reasoning": "Based on your interests",
            "confidence": 0.75,
            "personalization": None
        }
    
    # Rank courses by goals
    if len(goals) == 1:
        ranking = rank_courses_by_goal(goals[0], interest_course)
    else:
        ranking = rank_courses_by_multiple_goals(goals, interest_course)
    
    # Build personalization message
    goal_names = {
        "job": "getting placed quickly",
        "salary": "earning a high salary",
        "abroad": "working abroad",
        "higher_studies": "pursuing higher studies",
        "entrepreneurship": "starting your own business",
        "stability": "having a stable career"
    }
    
    if len(goals) == 1:
        goal_text = goal_names.get(goals[0], goals[0])
        personalization = f"Since your goal is **{goal_text}**, {ranking['primary']} is your best path."
    else:
        goal_list = [goal_names.get(g, g) for g in goals[:2]]
        goal_text = " and ".join(goal_list)
        personalization = f"Since you want **{goal_text}**, {ranking['primary']} gives you the best of both."
    
    return {
        "primary_course": ranking["primary"],
        "alternative_courses": ranking["alternatives"],
        "goal": goals[0] if len(goals) == 1 else "multiple",
        "goals": goals,
        "reasoning": ranking["reasoning"],
        "confidence": ranking["goal_alignment"],
        "personalization": personalization
    }


# ============================================
# GOAL-AWARE RESPONSE ENHANCEMENT
# ============================================
def enhance_guidance_with_goal(guidance_output: Dict, goal_mapping: Dict) -> Dict:
    """
    Enhance guidance engine output with goal-aware personalization.
    
    This is called AFTER guidance engine runs, to add goal context.
    """
    if not goal_mapping or not goal_mapping.get("personalization"):
        return guidance_output
    
    # Prepend goal personalization to guidance
    original_guidance = guidance_output.get("guidance", "")
    goal_intro = goal_mapping["personalization"]
    
    enhanced_guidance = f"{goal_intro}\n\n{original_guidance}"
    
    guidance_output["guidance"] = enhanced_guidance
    guidance_output["goal_context"] = {
        "goal": goal_mapping.get("goal"),
        "goals": goal_mapping.get("goals", []),
        "goal_reasoning": goal_mapping.get("reasoning")
    }
    
    return guidance_output


# ============================================
# TESTING
# ============================================
def test_goal_mapper():
    """Test goal mapping functionality"""
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    
    print("Testing Goal Mapper...")
    
    test_cases = [
        ("I want a high salary job", "BCA", ["salary", "job"]),
        ("I want to study MBA after graduation", "BBA", ["higher_studies"]),
        ("I want to work abroad", "BCA", ["abroad"]),
        ("I want to start my own business", "BBA", ["entrepreneurship"]),
        ("I want a stable career", "B.Com", ["stability"]),
        ("I got 70% and like coding, want high salary", "BCA", ["salary"]),
    ]
    
    for query, expected_course, expected_goals in test_cases:
        result = map_goal_to_course(query, expected_course)
        
        status = "✅" if result["primary_course"] == expected_course else "❌"
        print(f"{status} '{query}' → {result['primary_course']} (Goal: {result.get('goal')})")
        print(f"   Personalization: {result.get('personalization')}")


if __name__ == "__main__":
    test_goal_mapper()
