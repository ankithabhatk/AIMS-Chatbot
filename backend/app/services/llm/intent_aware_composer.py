"""
Intent-Aware Response Composer - Clean Pipeline

Replaces answer_generator.synthesize() with structured output:
- Detect intent
- Filter docs by relevance + topic
- Deduplicate
- Extract points (not sentences)
- Return structured sections + CTAs

This fixes the "data dumping" problem.
"""

import logging
from typing import List, Tuple, Dict, Any
import re
from rapidfuzz.fuzz import partial_ratio

logger = logging.getLogger(__name__)


def detect_intent(query: str) -> str:
    """Detect query intent with fuzzy matching"""
    q = query.lower()
    
    # FIRST: Specific keywords - RAG handles these
    if any(kw in q for kw in ["subjects", "skills", "syllabus", "curriculum", "topics", "learn"]):
        return "curriculum"
    
    if any(kw in q for kw in ["hostel", "room", "accommodation", "campus", "facility"]):
        return "campus"
    
    keyword_map = {
        "fees": ["fee", "fees", "cost", "costs", "tuition", "price", "scholarship", "financial", "finaid"],
        "admission": ["admission", "admissions", "apply", "aply", "enrol", "eligibility", "eligible", "requirement", "process", "admisn"],
        "placements": ["placement", "placements", "job", "jobs", "recruit", "recruitment", "package", "salary", "lpa", "company", "internship"],
        "campus": ["hostel", "hostels", "room", "stay", "accommodation", "facility", "facilities", "campus"],
        "courses": ["course", "courses", "program", "programs", "mba", "mca", "bba", "bca", "specialization", "corses"],
    }
    
    for intent, keywords in keyword_map.items():
        for kw in keywords:
            if partial_ratio(q, kw) > 80:
                return intent
    
    return "general"


def clean_docs(docs: List[Tuple], intent: str = "general", query: str = "") -> List[Tuple]:
    """
    Filter low-relevance docs + deduplicate + type filter + program-aware filtering
    
    Input: [(text, score, url, heading, doc_id, ...), intent, query]
    Output: Unique docs with score > 0.30, max 3
    
    Now includes program filtering for curriculum queries
    """
    # First: Apply program-aware filtering for specific queries
    program_filter = None
    query_lower = query.lower() if query else ""
    
    # Detect which program from query for targeted filtering
    programs = {"mca": "mca", "mba": "mba", "bca": "bca", "bba": "bba", "bcom": "bcom", "bhm": "bhm"}
    for prog, keyword in programs.items():
        if prog in query_lower:
            program_filter = prog
            break
    
    # Type filters by intent
    type_prefs = {
        "placements": ["placement", "recruit", "company", "job", "salary", "lpa"],
        "campus": ["hostel", "facility", "campus", "lab", "accommodation"],
        "admission": ["admission", "apply", "process", "eligibility", "form"],
        "courses": ["program", "course", "mba", "mca", "degree"],
        "fees": ["fee", "cost", "scholarship", "loan"],
        "curriculum": ["python", "machine learning", "data", "statistics", "skills", "cyber", "full stack", "cloud"],
    }
    
    preferred = type_prefs.get(intent, [])
    
    # First pass: filter by score threshold
    filtered = [d for d in docs if len(d) > 1 and float(d[1]) > 0.30]
    
    # Second pass: program-aware filtering (if detected)
    if program_filter and intent == "curriculum":
        program_matched = []
        other_docs = []
        for d in filtered:
            url = d[2].lower() if len(d) > 2 else ""
            # Check if doc URL matches the program
            if program_filter in url:
                program_matched.append(d)
            else:
                other_docs.append(d)
        
        # Prioritize matching program docs
        if program_matched:
            filtered = program_matched + other_docs
        # If no exact match, still use all but demote others
    
    # Priority: docs matching intent keywords first
    def score_doc(doc):
        text_lower = doc[0].lower() if doc else ""
        score = 0
        for kw in preferred:
            if kw in text_lower:
                score += 1
        # Bonus for program match
        if program_filter:
            url = doc[2].lower() if len(doc) > 2 else ""
            if program_filter in url:
                score += 2
        return -score  # Negative so matching docs come first
    
    filtered.sort(key=score_doc)
    
    seen_keys = set()
    unique = []
    
    for doc in filtered:
        key = doc[0][:150]
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(doc)
    
    return unique[:3]


# Boilerplate/intro phrases that look like content but are just section titles or nav text
_SKIP_PATTERNS = (
    "frequently asked",
    "faq",
    "contact us",
    "for more information",
    "click here",
    "home |",
    "| home",
    "skip to",
    "all rights reserved",
    "copyright",
    "privacy policy",
    "terms of",
    "follow us",
    "connect with us",
    "share this",
    "read more",
)


def extract_points(docs: List[Tuple], keywords: List[str], require_keyword_in_content: bool = True) -> List[str]:
    """
    Extract intelligent bullet points from docs that match keywords.

    Filters out:
    - Blank lines
    - Q:/A: prefixed lines
    - Lines shorter than 15 chars
    - Lines that are sub-headings (end with ":" after stripping)
    - Known boilerplate intro phrases
    - Generic lines without specific course/program info
    
    Priority: Lines with actual course names (MBA, MCA, etc.) or technical skills come first
    """
    clean = []
    course_names = ["MBA", "MCA", "BBA", "BCA", "M.Com", "B.Com", "BHM", "B.Sc", "M.Sc"]
    technical_keywords = ["Python", "Machine Learning", "Data Science", "Cyber Security", "Full Stack", "Cloud", "AI", "ML"]
    skip_phrases = ["facilities for boys", "management quota", "personal interview", 
                  "entrance exam", "pgcet", "academic merit", "commute from home"]

    # Sort docs: program list docs first
    program_list_docs = []
    other_docs = []
    course_keywords = ['program', 'offered', 'list', 'postgraduate', 'undergraduate']
    
    for doc in docs:
        text = doc[0]
        text_lower = text.lower()
        if any(kw in text_lower for kw in keywords):
            if any(pk in text_lower for pk in course_keywords):
                program_list_docs.append(doc)
            else:
                other_docs.append(doc)
    
    ordered_docs = program_list_docs + other_docs

    for doc in ordered_docs:
        text = doc[0]

        for line in text.split("\n"):
            line = line.strip()

            if not line:
                continue

            if line.lower().startswith(("q:", "a:", "q -", "a -", "question:", "answer:")):
                continue

            if len(line) < 15:
                continue

            if line.endswith(":"):
                continue

            line_lower = line.lower()
            if any(pat in line_lower for pat in _SKIP_PATTERNS):
                continue
            
            # Skip generic lines that aren't about specific courses/programs or technical skills
            has_course = any(cn in line for cn in course_names)
            has_technical = any(tkw.lower() in line_lower for tkw in technical_keywords)
            
            if not has_course and not has_technical:
                if any(sp in line_lower for sp in skip_phrases):
                    continue
                # Skip generic lines without content
                continue
            
            # Technical skills lines go to front for technical queries, courses for general
            if has_technical:
                clean.insert(0, line)
            elif has_course:
                clean.append(line)
            else:
                clean.append(line)

            if len(clean) >= 4:
                break

        if len(clean) >= 4:
            break

    return clean[:4]


def format_section(title: str, items: List[str]) -> Dict[str, Any]:
    """Format a response section"""
    if not items:
        return None
    
    return {
        "type": "list",
        "title": title,
        "items": items[:4]  # Max 4 items per section
    }


def build_structured_answer(intent: str, docs: List[Tuple]) -> Dict[str, Any]:
    """
    Core composer: Turn intent + docs → structured response
    """
    
    # 🚨 IF NO DATA: Redirect
    if not docs:
        return {
            "answer": (
                "I couldn't find specific information for this.\n\n"
                "📞 For accurate details, please connect with our admissions team.\n"
                "• Email: admissions@aims.ac.in\n"
                "• Phone: +91-XXXXXXXXXX"
            ),
            "mode": "fallback",
            "sections": None,
            "ctas": [
                {"label": "Talk to counselor", "action": "apply"}
            ],
            "intent": intent
        }
    
    # ================================================================
    # FEES
    # ================================================================
    if intent == "fees":
        fee_points = extract_points(docs, ["fee", "cost", "lakh", "tuition", "price", "scholarship"])
        
        # ❌ NO FEE DATA FOUND → HONEST REDIRECT (don't hallucinate)
        if not fee_points:
            logger.info("No fee data found in retrieved documents - returning redirect")
            return {
                "answer": (
                    "💰 **Fee Information**\n\n"
                    "I don't have detailed fee information in my knowledge base. "
                    "For accurate, up-to-date fee details, please contact our admissions team directly:\n\n"
                    "📞 **Admissions Office**\n"
                    "📧 admissions@aims.ac.in\n"
                    "📱 +91-XXXXXXXXXX"
                ),
                "mode": "redirect",
                "sections": None,
                "ctas": [
                    {"label": "Talk to Counselor", "action": "contact_counselor"}
                ],
                "intent": intent
            }
        
        # ✅ FEE DATA FOUND → Return structured response
        sections = [
            format_section("💰 Fees Overview", fee_points),
        ]
        
        return {
            "answer": None,  # Use sections instead
            "mode": "structured",
            "sections": [s for s in sections if s],
            "ctas": [
                {"label": "Check Eligibility", "action": "eligibility"},
                {"label": "Apply Now", "action": "apply"}
            ],
            "intent": intent
        }
    
    # ================================================================
    # ADMISSION
    # ================================================================
    elif intent == "admission":
        admission_points = extract_points(
            docs, 
            ["admission", "apply", "process", "eligibility", "requirement", "form"]
        )
        
        if not admission_points:
            return {
                "answer": (
                    "📝 For admission details:\n\n"
                    "📞 Contact Admissions\n"
                    "• admissions@aims.ac.in\n"
                    "• +91-XXXXXXXXXX"
                ),
                "mode": "redirect",
                "sections": None,
                "ctas": [
                    {"label": "Talk to counselor", "action": "apply"}
                ],
                "intent": intent
            }
        
        sections = [
            format_section("📝 Admission Process", admission_points),
        ]
        
        return {
            "answer": None,
            "mode": "structured",
            "sections": [s for s in sections if s],
            "ctas": [
                {"label": "Check Eligibility", "action": "eligibility"},
                {"label": "Apply Now", "action": "apply"}
            ],
            "intent": intent
        }
    
    # ================================================================
    # PLACEMENTS
    # ================================================================
    elif intent == "placements":
        placement_points = extract_points(
            docs,
            ["placement", "recruit", "company", "package", "salary", "lpa", "job"]
        )
        
        if not placement_points:
            return {
                "answer": (
                    "📈 For placement details:\n\n"
                    "📞 Contact Admissions\n"
                    "• admissions@aims.ac.in\n"
                    "• +91-XXXXXXXXXX"
                ),
                "mode": "redirect",
                "sections": None,
                "ctas": [
                    {"label": "Talk to counselor", "action": "apply"}
                ],
                "intent": intent
            }
        
        sections = [
            format_section("💼 Placements Overview", placement_points),
        ]
        
        return {
            "answer": None,
            "mode": "structured",
            "sections": [s for s in sections if s],
            "ctas": [
                {"label": "Courses Offered", "action": "courses"},
                {"label": "Apply Now", "action": "apply"}
            ],
            "intent": intent
        }
    
    # ================================================================
    # CAMPUS / FACILITIES
    # ================================================================
    elif intent == "campus":
        campus_points = extract_points(
            docs,
            ["hostel", "facility", "campus", "lab", "accommodation", "facility"]
        )
        
        if not campus_points:
            return {
                "answer": (
                    "🏫 For campus details:\n\n"
                    "📞 Contact Admissions\n"
                    "• admissions@aims.ac.in\n"
                    "• +91-XXXXXXXXXX"
                ),
                "mode": "redirect",
                "sections": None,
                "ctas": [
                    {"label": "Talk to counselor", "action": "apply"}
                ],
                "intent": intent
            }
        
        sections = [
            format_section("🏫 Campus & Facilities", campus_points),
        ]
        
        return {
            "answer": None,
            "mode": "structured",
            "sections": [s for s in sections if s],
            "ctas": [
                {"label": "Placements", "action": "placements"},
                {"label": "Apply Now", "action": "apply"}
            ],
            "intent": intent
        }
    
    # ================================================================
    # COURSES / PROGRAMS
    # ================================================================
    elif intent == "courses":
        course_points = extract_points(
            docs,
            ["course", "program", "mba", "mca", "specialization", "degree", "bba", "bca"],
            require_keyword_in_content=False
        )
        
        # Check if we got valid course info (not just admission boilerplate)
        has_valid_courses = any(cn in " ".join(course_points) for cn in ["MBA", "MCA", "BBA", "BCA", "M.Com", "BHM"])
    
    # ================================================================
    # CURRICULUM / SUBJECTS
    # ================================================================
    elif intent == "curriculum":
        curriculum_points = extract_points(
            docs,
            ["python", "machine learning", "data science", "statistics", "cyber security", "full stack", "cloud", "skills", "programming"]
        )
        
        # Fallback: if extraction is too short or generic, add helpful context
        if not curriculum_points or len(curriculum_points) < 2:
            # Try to detect program from query
            program = None
            for p in ["mca", "mba", "bca", "bba"]:
                if p in query.lower():
                    program = p.upper()
                    break
            
            program_name = f"{program} program" if program else "This program"
            curriculum_points = [
                f"Core technical skills are part of the {program_name} curriculum",
                "Specific subject details available upon admission",
                "Contact admissions@theaims.ac.in for complete syllabus"
            ]
        
        sections = [
            format_section("📚 Curriculum & Skills", curriculum_points),
        ]
        
        return {
            "answer": None,
            "mode": "structured",
            "sections": [s for s in sections if s],
            "ctas": [
                {"label": "Admission Process", "action": "admission"},
                {"label": "Apply Now", "action": "apply"}
            ],
            "intent": intent
        }
        
        if not course_points or not has_valid_courses:
            return {
                "answer": (
                    "AIMS Institutes offers a range of programs:\n\n"
                    "• MBA (Master of Business Administration)\n"
                    "• MCA (Master of Computer Applications)\n"
                    "• BBA (Bachelor of Business Administration)\n"
                    "• BCA (Bachelor of Computer Applications)\n"
                    "• M.Com / B.Com\n\n"
                    "For detailed fee structure and specializations, please contact our admissions team:\n"
                    "• admissions@aims.ac.in"
                ),
                "mode": "structured",
                "sections": None,
                "ctas": [
                    {"label": "Admission Process", "action": "admission"},
                    {"label": "Apply Now", "action": "apply"}
                ],
                "intent": intent
            }
        
        sections = [
            format_section("📚 Courses Offered", course_points),
        ]
        
        return {
            "answer": None,
            "mode": "structured",
            "sections": [s for s in sections if s],
            "ctas": [
                {"label": "Admission Process", "action": "admission"},
                {"label": "Apply Now", "action": "apply"}
            ],
            "intent": intent
        }
    
    # ================================================================
    # GENERAL / FALLBACK
    # ================================================================
    else:
        general_points = extract_points(docs, ["college", "course", "program", "aims"])
        
        if not general_points:
            return {
                "answer": (
                    "📌 For more information:\n\n"
                    "📞 Contact Admissions\n"
                    "• admissions@aims.ac.in\n"
                    "• +91-XXXXXXXXXX"
                ),
                "mode": "fallback",
                "sections": None,
                "ctas": [
                    {"label": "Talk to counselor", "action": "apply"}
                ],
                "intent": intent
            }
        
        sections = [
            format_section("📌 Information", general_points),
        ]
        
        return {
            "answer": None,
            "mode": "structured",
            "sections": [s for s in sections if s],
            "ctas": [
                {"label": "Explore Courses", "action": "courses"},
                {"label": "Apply Now", "action": "apply"}
            ],
            "intent": intent
        }


def compose(query: str, docs: List[Tuple]) -> Dict[str, Any]:
    """Main entry point: query + docs → structured response"""
    intent = detect_intent(query)
    
    cleaned = clean_docs(docs, intent, query)
    
    result = build_structured_answer(intent, cleaned)
    
    return result

