"""
College Course Boundary - Single Source of Truth

This file defines the ONLY courses offered by AIMS.
All system logic MUST respect this boundary.

If a course is not in this list, the system CANNOT recommend it.
"""

# ============================================
# COLLEGE COURSES (Single Source of Truth)
# ============================================
COLLEGE_COURSES = {
    "BBA": {
        "code": "bba",
        "display": "BBA",
        "full_name": "Bachelor of Business Administration"
    },
    "BCA": {
        "code": "bca",
        "display": "BCA",
        "full_name": "Bachelor of Computer Applications"
    },
    "MBA": {
        "code": "mba",
        "display": "MBA",
        "full_name": "Master of Business Administration"
    },
    "B.Com": {
        "code": "bcom",
        "display": "B.Com",
        "full_name": "Bachelor of Commerce"
    },
    "MCA": {
        "code": "mca",
        "display": "MCA",
        "full_name": "Master of Computer Applications"
    },
    "BHM": {
        "code": "bhm",
        "display": "BHM",
        "full_name": "Bachelor of Hotel Management"
    }
}


def get_college_courses():
    """Get list of all courses offered by college"""
    return list(COLLEGE_COURSES.keys())


def is_valid_college_course(course: str) -> bool:
    """Check if course is offered by college"""
    course_upper = course.upper().replace(".", "")
    return course_upper in COLLEGE_COURSES or course_upper in [v["code"].upper() for v in COLLEGE_COURSES.values()]


def normalize_course_name(course: str) -> str:
    """Normalize course name to standard format"""
    course_clean = course.upper().replace(".", "").strip()
    
    # Direct match
    if course_clean in COLLEGE_COURSES:
        return course_clean
    
    # Code match
    for key, value in COLLEGE_COURSES.items():
        if value["code"].upper() == course_clean:
            return key
    
    return None


def enforce_course_boundary(course_list: list) -> list:
    """
    GLOBAL GUARD: Ensures only college courses pass through.
    Use this everywhere courses are processed.
    """
    allowed = set(COLLEGE_COURSES.keys())
    return [c for c in course_list if c in allowed]
