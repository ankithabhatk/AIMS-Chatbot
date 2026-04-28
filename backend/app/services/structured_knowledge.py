"""
Structured Knowledge Base - Hardcoded authoritative data
for high-precision intents (courses, fees, contact, etc.)
Bypasses RAG entirely for enumeration questions.
"""

import re
from difflib import SequenceMatcher


def partial_ratio(value: str, pattern: str) -> int:
    """Small local replacement for fuzzy keyword checks.

    The structured router only needs coarse intent matching for short keywords,
    so avoid requiring a separate runtime package in the API process.
    """
    value = (value or "").lower()
    pattern = (pattern or "").lower()

    if not value or not pattern:
        return 0
    if pattern in value or value in pattern:
        return 100

    shorter, longer = (value, pattern) if len(value) <= len(pattern) else (pattern, value)
    best = 0.0
    for start in range(0, len(longer) - len(shorter) + 1):
        candidate = longer[start:start + len(shorter)]
        best = max(best, SequenceMatcher(None, shorter, candidate).ratio())

    return int(best * 100)

COURSES = {
    "postgraduate": [
        {"name": "MBA", "full": "Master of Business Administration", "duration": "2 years", "specializations": "Finance, Marketing, HR, Business Analytics"},
        {"name": "MCA", "full": "Master of Computer Applications", "duration": "2 years", "eligibility": "BCA / B.Sc (CS/IT/Maths) / B.Com with Maths"},
        {"name": "M.Com", "full": "Master of Commerce", "duration": "2 years"},
    ],
    "undergraduate": [
        {"name": "BBA", "full": "Bachelor of Business Administration", "duration": "3 years"},
        {"name": "BBA Aviation", "full": "BBA in Aviation Management", "duration": "3 years"},
        {"name": "BCA", "full": "Bachelor of Computer Applications", "duration": "3 years"},
        {"name": "B.Com", "full": "Bachelor of Commerce", "duration": "3 years"},
        {"name": "BHM", "full": "Bachelor of Hotel Management", "duration": "3 years"},
    ]
}

FEES = {
    "MBA": {"annual": "₹50,000 - ₹1,00,000", "note": "Varies by specialization. Contact admissions for exact figures."},
    "MCA": {"annual": "₹40,000 - ₹80,000", "note": "Contact admissions for exact figures."},
    "BBA": {"annual": "₹30,000 - ₹60,000", "note": "Contact admissions for exact figures."},
    "BCA": {"annual": "₹30,000 - ₹60,000", "note": "Contact admissions for exact figures."},
    "B.Com": {"annual": "₹20,000 - ₹40,000", "note": "Contact admissions for exact figures."},
    "M.Com": {"annual": "₹30,000 - ₹50,000", "note": "Contact admissions for exact figures."},
    "BHM": {"annual": "₹40,000 - ₹80,000", "note": "Varies by specialization. Contact admissions for exact figures."},
}

PROGRAM_ALIASES = {
    "MBA": ["mba", "master of business administration"],
    "MCA": ["mca", "master of computer applications"],
    "BBA": ["bba", "bachelor of business administration"],
    "BCA": ["bca", "bachelor of computer applications"],
    "B.Com": ["b.com", "bcom", "bachelor of commerce"],
    "M.Com": ["m.com", "mcom", "master of commerce"],
    "BHM": ["bhm", "bachelor of hotel management"],
}

CONTACT = {
    "email": "admission@theaims.ac.in",
    "phone": "+91-815-000-1994",
    "website": "www.theaims.ac.in",
    "address": "#1, Pipeline Road, Hesaraghatta Main Road, Bangalore - 560090",
    "landmark": "Near Peenya, Bangalore",
}

ADMISSION_STEPS = [
    "Fill out the application form",
    "Submit academic records (10th, 12th, Graduation)",
    "Shortlist based on merit",
    "Personal Interview",
    "Admission confirmation & fee payment",
]

ADMISSION_DOCUMENTS = [
    "10th mark sheet / SSLC certificate",
    "12th mark sheet / PUC certificate",
    "Graduation mark sheets and degree certificate for PG programs",
    "Entrance exam score card if applicable",
    "Transfer certificate and migration certificate if required",
    "Passport-size photographs and valid ID proof",
]

ELIGIBILITY = {
    "MBA": "Graduation with 50% marks (any discipline)",
    "MCA": "BCA / B.Sc with Mathematics",
    "BBA": "10+2 with 50% marks",
    "BCA": "10+2 with Mathematics or Computer Science",
    "B.Com": "10+2 with 50% marks",
}

PLACEMENT_STATS = {
    "highest_overall": "₹27 LPA",
    "highest_current": "₹16.5 LPA",
    "average": "₹8 LPA",
    "placement_rate": "84% of eligible students placed",
    "ppo_conversion": "70% internship-to-PPO conversion",
    "recruiters": "300+ corporate tie-ups and 100+ annual recruiters",
    "companies": "Deloitte, EY, KPMG, Accenture, Amazon, Infosys, Wipro, TCS, Cognizant, Capgemini, HDFC Bank, Axis Bank, ICICI Bank",
}

HOSTEL_FACILITIES = [
    "Separate hostel facilities for boys and girls",
    "Fully furnished single, double, and triple occupancy rooms",
    "24/7 security with CCTV surveillance and biometric entry",
    "Wi-Fi in hostel rooms",
    "Mess facility with breakfast, lunch, and dinner",
    "Laundry, common room, recreation, medical room, and emergency support",
]

ENTRANCE_EXAMS = {
    "MBA": "CAT, MAT, ATMA, and CMAT are accepted for MBA admissions.",
    "MCA": "NIMCET is accepted for MCA admissions.",
}

SCHOLARSHIP_INFO = [
    "Scholarships are available based on merit and category.",
    "Eligibility depends on the program, admission cycle, and applicable category rules.",
    "Contact admissions for current scholarship criteria and documentation.",
]

# NEW: Institution-level knowledge
ABOUT_AIMS = {
    "overview": "AIMS Institutes is a premier educational institution in Bangalore offering undergraduate and postgraduate programs in management, commerce, computer applications, and hospitality. Founded with a vision to provide industry-oriented education, AIMS focuses on holistic student development and employability.",
    "established": "AIMS has been serving students for over a decade with a commitment to academic excellence and practical learning.",
    "location": "Located in Bangalore, a major IT and business hub, AIMS provides students with access to industry opportunities and networking.",
    "mission": "To provide quality education that bridges the gap between academic learning and industry requirements.",
}

WHY_AIMS = [
    "Industry-integrated curriculum designed with input from leading companies",
    "Strong placement support with 300+ corporate tie-ups",
    "Experienced faculty with industry and academic backgrounds",
    "Focus on soft skills, personality development, and professional readiness",
    "Modern campus facilities with Wi-Fi, smart classrooms, and labs",
    "Internship opportunities with leading organizations",
    "Holistic development through co-curricular activities and clubs",
    "Affordable fees with scholarship opportunities",
]

AIMS_FEATURES = [
    "Smart classrooms with modern teaching aids",
    "Well-equipped computer labs and specialized labs",
    "Central library with extensive digital and physical resources",
    "Wi-Fi enabled campus for seamless connectivity",
    "Separate hostel facilities for boys and girls with 24/7 security",
    "Sports facilities including indoor and outdoor courts",
    "Cafeteria with diverse food options",
    "Medical support and counseling services",
    "Seminar halls and auditorium for events and seminars",
    "ATM and banking facilities on campus",
    "Active student clubs and societies",
    "Regular industry interactions and guest lectures",
]


def _find_course_record(program: str = None):
    if not program:
        return None

    normalized = (program or "").replace(".", "").lower()
    for level_courses in COURSES.values():
        for course in level_courses:
            course_name = course["name"].replace(".", "").lower()
            if course_name == normalized:
                return course
    return None


def get_courses_structured(program: str = None) -> dict:
    """Return structured course list as grouped, deterministic facts."""
    course = _find_course_record(program)
    if course:
        details = [f"Duration: {course['duration']}"]
        if course.get("specializations"):
            details.append(f"Specializations: {course['specializations']}")
        if course.get("eligibility"):
            details.append(f"Eligibility: {course['eligibility']}")
        return {
            "answer": f"Yes, AIMS offers {course['name']} ({course['full']}).\n" + "\n".join(details),
            "sections": [
                {"type": "info", "title": course["name"], "items": details},
            ],
            "ctas": [
                {"label": f"{course['name']} fees", "action": "fees"},
                {"label": "Admission process", "action": "admission"},
            ],
            "sources": [{"title": "Programs at AIMS", "url": "https://www.theaims.ac.in"}],
        }

    pg = ", ".join(course["name"] for course in COURSES["postgraduate"])
    ug = ", ".join(course["name"] for course in COURSES["undergraduate"])
    return {
        "answer": (
            "Courses offered:\n"
            f"Postgraduate: {pg}\n"
            f"Undergraduate: {ug}\n"
            "MBA specializations: Finance, Marketing, HR, Business Analytics"
        ),
        "sections": [
            {"type": "info", "title": "Postgraduate programs", "items": [pg]},
            {"type": "info", "title": "Undergraduate programs", "items": [ug]},
            {
                "type": "info",
                "title": "MBA specializations",
                "items": ["Finance, Marketing, HR, Business Analytics"],
            },
        ],
        "ctas": [
            {"label": "Admission process", "action": "admission"},
            {"label": "MBA fees", "action": "fees"}
        ],
        "sources": [{"title": "Programs at AIMS", "url": "https://www.theaims.ac.in"}],
    }


def get_fees_structured(program: str = None) -> dict:
    """Return structured fee information from the local authoritative fee table."""
    program_key = (program or "").replace(".", "").upper()
    fee_key = next((key for key in FEES if key.replace(".", "").upper() == program_key), None)

    if fee_key:
        fee_info = FEES[fee_key]
        return {
            "answer": (
                f"{fee_key} fee structure:\n"
                f"Annual fee: {fee_info['annual']}\n"
                f"{fee_info['note']}\n"
                f"Contact: {CONTACT['email']}"
            ),
            "sections": [
                {
                    "type": "info",
                    "title": f"{fee_key} fee details",
                    "items": [
                        f"Annual fee: {fee_info['annual']}",
                        fee_info["note"],
                        f"Contact: {CONTACT['email']}",
                    ],
                }
            ],
            "ctas": [{"label": "Admission process", "action": "admission"}],
            "sources": [{"title": "Admissions", "url": "https://www.theaims.ac.in"}],
        }

    fee_lines = [f"{program_name}: {info['annual']}" for program_name, info in FEES.items()]
    return {
        "answer": (
            "Fee structure:\n"
            + "\n".join(fee_lines)
            + f"\nContact admissions for exact figures: {CONTACT['email']}"
        ),
        "sections": [
            {
                "type": "info",
                "title": "Fee structure",
                "items": fee_lines + [f"Contact admissions for exact figures: {CONTACT['email']}"],
            }
        ],
        "ctas": [{"label": "Contact Admissions", "action": "contact"}],
        "sources": [{"title": "Admissions", "url": "https://www.theaims.ac.in"}],
    }


def get_admission_structured(program: str = None, documents_only: bool = False) -> dict:
    """Return structured admission process."""
    if documents_only:
        return {
            "answer": "Documents required for admission:\n" + "\n".join(ADMISSION_DOCUMENTS),
            "sections": [
                {"type": "list", "title": "Required documents", "items": ADMISSION_DOCUMENTS},
            ],
            "ctas": [{"label": "Admission process", "action": "admission"}],
            "sources": [{"title": "Admissions", "url": "https://www.theaims.ac.in"}],
        }

    if program and program.replace(".", "").upper() == "MBA":
        mba_items = [
            "Eligibility: Bachelor's degree with 50%+ marks",
            ENTRANCE_EXAMS["MBA"],
            "Selection includes GD/PI after application and document submission",
            "Confirm admission by completing fee payment after selection",
        ]
        return {
            "answer": "MBA admission process:\n" + "\n".join(mba_items),
            "sections": [
                {"type": "list", "title": "MBA admission steps", "items": mba_items},
            ],
            "ctas": [{"label": "MBA fees", "action": "fees"}],
            "sources": [{"title": "Admissions", "url": "https://www.theaims.ac.in"}],
        }

    return {
        "answer": "Admission process:\n" + "\n".join(ADMISSION_STEPS),
        "sections": [
            {"type": "list", "title": "Admission steps", "items": ADMISSION_STEPS},
        ],
        "ctas": [{"label": "Apply Online", "action": "apply"}],
        "sources": [{"title": "Admissions", "url": "https://www.theaims.ac.in"}],
    }


def get_placements_structured(program: str = None) -> dict:
    """Return structured placement information from the local placement summary."""
    if program and program.replace(".", "").upper() == "MBA":
        return {
            "answer": (
                "MBA placement highlights:\n"
                "Average package: ₹6–8 LPA\n"
                "Highest package: ₹15–20 LPA\n"
                "Top recruiters: Deloitte, Amazon, ICICI Bank"
            ),
            "sections": [
                {
                    "type": "info",
                    "title": "MBA placement highlights",
                    "items": [
                        "Average package: ₹6–8 LPA",
                        "Highest package: ₹15–20 LPA",
                        "Top recruiters: Deloitte, Amazon, ICICI Bank",
                    ],
                }
            ],
            "ctas": [{"label": "MBA admission", "action": "admission"}],
            "sources": [{"title": "AIMS Placement", "url": "https://www.theaims.ac.in/placement"}],
        }

    return {
        "answer": (
            "Placement highlights:\n"
            f"Highest package (current): {PLACEMENT_STATS['highest_current']}\n"
            f"Highest package (overall): {PLACEMENT_STATS['highest_overall']}\n"
            f"Average package: {PLACEMENT_STATS['average']}\n"
            f"Placement rate: {PLACEMENT_STATS['placement_rate']}\n"
            f"Recruiter base: {PLACEMENT_STATS['recruiters']}"
        ),
        "sections": [
            {
                "type": "info",
                "title": "Placement highlights",
                "items": [
                    f"Highest package (current): {PLACEMENT_STATS['highest_current']}",
                    f"Highest package (overall): {PLACEMENT_STATS['highest_overall']}",
                    f"Average package: {PLACEMENT_STATS['average']}",
                    f"Placement rate: {PLACEMENT_STATS['placement_rate']}",
                    f"Recruiter base: {PLACEMENT_STATS['recruiters']}",
                ],
            }
        ],
        "ctas": [
            {"label": "Contact Admissions", "action": "contact"},
        ],
        "sources": [{"title": "AIMS Placement", "url": "https://www.theaims.ac.in/placement"}],
    }


def get_hostel_structured() -> dict:
    """Return official hostel and campus facilities overview."""
    return {
        "answer": (
            "AIMS Hostel & Campus Facilities\n\n"
            + "\n".join(f"• {item}" for item in HOSTEL_FACILITIES)
            + "\n\nThe campus also includes smart classrooms, computer labs, Wi-Fi, central library, seminar halls, sports facilities, ATM, cafeteria, and medical support."
        ),
        "sections": None,
        "ctas": [
            {"label": "Campus facilities", "action": "campus"},
            {"label": "Contact Admissions", "action": "contact"},
        ],
        "sources": [{"title": "AIMS Student Information Zone", "url": "https://www.theaims.ac.in/student-information-zone"}],
    }


def get_location_structured() -> dict:
    """Return official campus location and contact details."""
    return {
        "answer": (
            "AIMS Institutes campus is located at "
            f"{CONTACT['address']}. {CONTACT['landmark']}.\n\n"
            f"Admissions office: {CONTACT['phone']} | {CONTACT['email']}"
        ),
        "sections": [
            {
                "type": "info",
                "title": "Campus location",
                "items": [
                    CONTACT["address"],
                    CONTACT["landmark"],
                    f"Phone: {CONTACT['phone']}",
                    f"Email: {CONTACT['email']}",
                ],
            }
        ],
        "ctas": [
            {"label": "Contact Admissions", "action": "contact"},
            {"label": "Campus facilities", "action": "campus"},
        ],
        "sources": [{"title": "AIMS Campus", "url": "https://www.theaims.ac.in"}],
    }


def get_exam_structured(program: str = None) -> dict:
    """Return deterministic entrance exam information."""
    if program:
        program_key = program.replace(".", "").upper()
        exam_key = next((key for key in ENTRANCE_EXAMS if key.replace(".", "").upper() == program_key), None)
        if exam_key:
            exam = ENTRANCE_EXAMS[exam_key]
            return {
                "answer": f"{exam_key} entrance exams: {exam}",
                "sections": [
                    {"type": "info", "title": f"{exam_key} entrance exams", "items": [exam]},
                ],
                "ctas": [{"label": f"{exam_key} admission", "action": "admission"}],
                "sources": [{"title": "Admissions", "url": "https://www.theaims.ac.in"}],
            }

    items = [f"{program_name}: {exam}" for program_name, exam in ENTRANCE_EXAMS.items()]
    return {
        "answer": "Entrance exams accepted:\n" + "\n".join(items),
        "sections": [{"type": "info", "title": "Entrance exams", "items": items}],
        "ctas": [{"label": "Admission process", "action": "admission"}],
        "sources": [{"title": "Admissions", "url": "https://www.theaims.ac.in"}],
    }


def get_scholarship_structured() -> dict:
    """Return deterministic scholarship information."""
    return {
        "answer": "Scholarship information:\n" + "\n".join(SCHOLARSHIP_INFO),
        "sections": [{"type": "info", "title": "Scholarships", "items": SCHOLARSHIP_INFO}],
        "ctas": [{"label": "Contact Admissions", "action": "contact"}],
        "sources": [{"title": "Admissions", "url": "https://www.theaims.ac.in"}],
    }


def get_about_aims_structured() -> dict:
    """Return information about AIMS institution."""
    return {
        "answer": (
            f"About AIMS Institutes\n\n"
            f"{ABOUT_AIMS['overview']}\n\n"
            f"Location: {ABOUT_AIMS['location']}\n"
            f"Mission: {ABOUT_AIMS['mission']}"
        ),
        "sections": [
            {
                "type": "info",
                "title": "About AIMS",
                "items": [
                    ABOUT_AIMS["overview"],
                    f"Location: {ABOUT_AIMS['location']}",
                    f"Mission: {ABOUT_AIMS['mission']}",
                ],
            }
        ],
        "ctas": [
            {"label": "Why choose AIMS?", "action": "why_aims"},
            {"label": "Campus facilities", "action": "aims_features"},
            {"label": "Contact Admissions", "action": "contact"},
        ],
        "sources": [{"title": "About AIMS", "url": "https://www.theaims.ac.in/about"}],
    }


def get_why_aims_structured() -> dict:
    """Return reasons to choose AIMS."""
    return {
        "answer": (
            "Why choose AIMS Institutes?\n\n"
            + "\n".join(f"• {item}" for item in WHY_AIMS)
        ),
        "sections": [
            {
                "type": "list",
                "title": "Why AIMS?",
                "items": WHY_AIMS,
            }
        ],
        "ctas": [
            {"label": "Campus facilities", "action": "aims_features"},
            {"label": "Placement record", "action": "placements"},
            {"label": "Apply now", "action": "apply"},
        ],
        "sources": [{"title": "Why AIMS", "url": "https://www.theaims.ac.in"}],
    }


def get_aims_features_structured() -> dict:
    """Return AIMS campus features and facilities."""
    return {
        "answer": (
            "AIMS Campus Features & Facilities\n\n"
            + "\n".join(f"• {item}" for item in AIMS_FEATURES)
        ),
        "sections": [
            {
                "type": "list",
                "title": "Campus features",
                "items": AIMS_FEATURES,
            }
        ],
        "ctas": [
            {"label": "Hostel facilities", "action": "hostel"},
            {"label": "Contact Admissions", "action": "contact"},
        ],
        "sources": [{"title": "Campus", "url": "https://www.theaims.ac.in/campus"}],
    }


def detect_program(query: str) -> str:
    """Detect a program key from a user query."""
    q = query.lower()
    for program, aliases in PROGRAM_ALIASES.items():
        if any(alias in q for alias in aliases):
            return program
    return None


def get_program_intent(query: str) -> tuple:
    """If program is detected but no explicit intent, return courses intent.
    
    Example: "bca!!!" → program=BCA, intent=courses
    """
    program = detect_program(query)
    if program:
        # Program mentioned → user is asking about that course
        return ("courses", 0.8)
    return (None, 0.0)


def is_structured_intent(query: str) -> tuple:
    """🚀 RESTRICTED INTENT MATCHING
    
    STRUCTURED ONLY for:
    - fees (exact amounts)
    - admission (process steps, documents)
    - scholarship (eligibility)
    - courses (what's offered)
    - contact (phone, email)
    - about_aims (institution info)
    - why_aims (differentiation)
    - aims_features (campus facilities)
    
    FORCE TO RAG for:
    - placements (dynamic data)
    - campus (descriptive)
    - hostel (facility details)
    
    This fixes the routing bug where RAG never runs.
    """
    q = query.lower()

    def has_any(terms):
        return any(
            re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", q)
            for term in terms
        )

    # 🟢 STRUCTURED INTENTS (return with high confidence)
    if has_any(["fee", "fees", "cost", "price", "tuition"]):
        return ("fees", 1.0)
    if has_any(["scholarship", "scholarships", "financial aid", "fee waiver"]):
        return ("scholarship", 1.0)
    if has_any(["course", "courses", "program", "programs", "specialization", "specializations"]):
        return ("courses", 1.0)
    # IMPORTANT: Don't claim "admission" if it's a location or apply-only query (→ TOOL layer)
    if has_any(["admission", "eligibility"]) or (
        has_any(["application"]) and has_any(["document", "requirement", "criteria"])
    ):
        if not has_any(["location", "where", "distance", "how far", "directions", "map", "address"]):
            return ("admission", 1.0)
    if has_any(["document", "documents", "certificate", "mark sheet", "marksheet", "score card", "scorecard"]):
        return ("admission", 1.0)
    # IMPORTANT: Don't claim "contact" if it's a location query (→ TOOL layer)
    if has_any(["contact", "phone", "email"]) and not has_any(["placement", "campus", "hostel", "location", "where", "distance"]):
        return ("contact", 1.0)
    
    # NEW: Institution-level intents
    if has_any(["about aims", "what is aims", "tell me about aims", "aims overview", "aims introduction"]):
        return ("about_aims", 1.0)
    if has_any(["why aims", "why choose aims", "why should i join aims", "advantages of aims", "benefits of aims"]):
        return ("why_aims", 1.0)
    if has_any(["features", "facilities", "campus facilities", "infrastructure", "what facilities"]):
        return ("aims_features", 1.0)
    
    # ⛔ NOT STRUCTURED (force RAG instead)
    # These are descriptive/dynamic and should go through RAG
    if has_any(["placement", "placements", "salary", "package", "salary package", "recruiter", "recruiting"]):
        return (None, 0)  # Force to RAG
    if has_any(["hostel", "accommodation", "facility", "facilities"]):
        return (None, 0)  # Force to RAG
    if has_any(["campus"]):
        return (None, 0)  # Force to RAG

    return (None, 0)


def get_structured_response(query: str) -> dict:
    """Get structured response for known intents. Returns None if not applicable.
    
    Routing rules:
    - program detected + fees keywords → program-specific fees
    - confidence >= 0.8: Structured (broad queries)
    - confidence < 0.8: None (RAG handles specifics)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    q = query.lower()
    
    out_of_scope = ["weather", "iit bombay", "delhi university", "iim", "harvard"]
    if any(x in q for x in out_of_scope):
        logger.info(f"[structured] Out-of-scope: {query}")
        return None
    
    intent, confidence = is_structured_intent(query)
    logger.info(f"[structured] Query: '{query}' → intent={intent}, confidence={confidence}")
    
    program = detect_program(query)
    
    if not intent and program and len(q.split()) <= 2:
        return {
            **get_courses_structured(program),
            "intent": "courses",
            "confidence": 0.85,
            "mode": "structured",
        }
    
    if confidence < 0.8:
        return None
    
    if intent == "courses":
        return {
            **get_courses_structured(program),
            "intent": intent,
            "confidence": 1.0,
            "mode": "structured",
        }
    
    if intent == "fees":
        return {**get_fees_structured(program), "intent": intent, "confidence": 1.0, "mode": "structured"}
    
    if intent == "admission":
        documents_only = any(term in q for term in ["document", "documents", "certificate", "mark sheet", "marksheet", "score card", "scorecard"])
        return {
            **get_admission_structured(program=program, documents_only=documents_only),
            "intent": intent,
            "confidence": 0.9,
            "mode": "structured",
        }
    
    if intent == "placements":
        return {**get_placements_structured(program), "intent": intent, "confidence": 0.95, "mode": "structured"}
    
    if intent == "hostel":
        return {**get_hostel_structured(), "intent": intent, "confidence": 0.95, "mode": "structured"}

    if intent == "location":
        return {**get_location_structured(), "intent": intent, "confidence": 0.95, "mode": "structured"}

    if intent == "exam":
        return {**get_exam_structured(program), "intent": intent, "confidence": 0.95, "mode": "structured"}

    if intent == "scholarship":
        return {**get_scholarship_structured(), "intent": intent, "confidence": 0.95, "mode": "structured"}
    
    if intent == "contact":
        return {
            "answer": f"Contact Admissions\n\nEmail: {CONTACT['email']}\nPhone: {CONTACT['phone']}\nWebsite: {CONTACT['website']}",
            "intent": "contact",
            "confidence": 1.0,
            "mode": "structured",
            "sections": None,
            "ctas": [{"label": "Visit Website", "action": "website"}],
        }
    
    if intent == "about_aims":
        return {
            **get_about_aims_structured(),
            "intent": intent,
            "confidence": 1.0,
            "mode": "structured",
        }
    
    if intent == "why_aims":
        return {
            **get_why_aims_structured(),
            "intent": intent,
            "confidence": 1.0,
            "mode": "structured",
        }
    
    if intent == "aims_features":
        return {
            **get_aims_features_structured(),
            "intent": intent,
            "confidence": 1.0,
            "mode": "structured",
        }
    
    return None
