import re
from typing import Dict, List, Optional

# -------------------------
# COURSE LIST (College Boundary)
# -------------------------
from app.config.college_courses import COLLEGE_COURSES

# Only extract courses we actually offer
KNOWN_COURSES = [v["code"] for v in COLLEGE_COURSES.values()]

# -------------------------
# COURSE NORMALIZATION
# -------------------------
def normalize_course(course: str) -> str:
    course = course.lower().replace(".", "").strip()
    mapping = {
        "bcom": "B.Com",
        "bba": "BBA",
        "bca": "BCA",
        "mba": "MBA",
        "mca": "MCA",
        "mcom": "M.Com",
        "bsc": "B.Sc",
        "bhm": "BHM"
    }
    return mapping.get(course, course.upper())

# -------------------------
# EXTRACT COURSES
# -------------------------
def extract_courses(query: str) -> List[str]:
    q = query.lower()
    found = []
    
    for course in KNOWN_COURSES:
        clean = course.replace(".", "")
        if clean in q.replace(".", ""):
            found.append(normalize_course(clean))
            
    return list(set(found))

# -------------------------
# EXTRACT MARKS
# -------------------------
def extract_marks(query: str) -> Optional[int]:
    """
    Extracts percentage like:
    - 60%
    - 75 percent
    """
    # 60%
    match = re.search(r'(\d{2})\s*%', query)
    if match:
        return int(match.group(1))
        
    # 75 percent
    match = re.search(r'(\d{2})\s*(percent|percentage)', query.lower())
    if match:
        return int(match.group(1))
        
    return None

# -------------------------
# EXTRACT INTERESTS
# -------------------------
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

def extract_interests(query: str) -> Optional[str]:
    """
    Extract interest and map to college course.
    Uses production-grade signal-based mapping.
    """
    from app.services.counselor.interest_mapper import map_interest_to_course, extract_interest_from_query
    
    # Try to extract interest from query
    interest_text = extract_interest_from_query(query)
    
    if not interest_text:
        # Fallback: check if query contains any interest signals directly
        q = query.lower()
        for course, patterns in INTEREST_PATTERNS.items():
            if any(re.search(p, q) for p in patterns):
                return course
        return None
    
    # Map interest to course using signal-based mapper
    mapping = map_interest_to_course(interest_text)
    
    if mapping["is_direct_match"]:
        return mapping["course"]
    
    return None

# -------------------------
# MAIN FUNCTION
# -------------------------
def extract_entities(query: str) -> Dict:
    return {
        "courses": extract_courses(query),
        "marks": extract_marks(query),
        "interests": extract_interests(query)
    }
