import logging
from typing import Optional, List, Dict, Any, Tuple
from symspellpy import SymSpell, Verbosity
import re
import json
from pathlib import Path

from app.services.counselor.router import detect_intents, handle_ambiguity
from app.services.counselor.composer import compose_response
from app.services.counselor.guidance_engine import run_guidance_engine as run_guidance
from app.services.counselor.comparator_engine import run_comparator
from app.services.counselor.career_engine import run_career
from app.services.counselor.constraint_advisor import run_constraint
from app.services.counselor.life_assistant import run_life
from app.services.counselor.unavailable_handler import run_unavailable
from app.services.counselor.entity_extractor import extract_entities
from app.services.counselor.memory import update_student_profile, enrich_context_with_memory
from app.services.counselor.persona import apply_hybrid_behavior
from app.services.counselor.flow_manager import generate_follow_up, ask_commitment, gentle_followup, detect_intent_level, smart_followup, trust_loop
from app.services.counselor.analytics import track_event
from app.services.counselor.conversion import detect_conversion_intent, generate_cta, inject_informed_timing, guided_optional_close, handle_objection, run_conversion_flow
from app.services.learning.optimizer import apply_tuning, SYSTEM_TUNING
from app.services.learning.reinforcement import reinforce_response
from app.config.college_courses import COLLEGE_COURSES, enforce_course_boundary
from app.services.orchestration.deployment_logger import log_deployment_event

# College course boundary
VALID_COURSES = set([v["code"] for v in COLLEGE_COURSES.values()] + list(COLLEGE_COURSES.keys()))

# PHASE 2 FIX: Protected words that should NOT be spell-corrected
# These are critical domain terms that must be preserved exactly
PROTECTED_WORDS = {
    "bca", "bcom", "btech", "ba", "bsc",  # Degree codes
    "mca", "mba", "mtech", "ma", "msc",   # Master codes
    "aims", "aiims",                       # Institution names
    "placement", "placements",             # Key terms
    "fees", "fee",                         # Key terms
    "admission", "admissions",             # Key terms
    "hostel", "campus",                    # Key terms
}

# ═══════════════════════════════════════════════════════════════════════════
# ENRICHED DATA INJECTION (MICRO FIX - STEP 1)
# Load enriched dataset with decision-support fields
# ═══════════════════════════════════════════════════════════════════════════

def _load_enriched_dataset() -> List[Dict[str, Any]]:
    """Load enriched course dataset with decision-support fields."""
    try:
        # Path from backend/app/services/orchestration/engine.py → /data/processed/
        # Go up 4 levels: engine.py → orchestration → services → app → backend
        # Then go to parent (project root) → data/processed/
        enriched_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "processed" / "courses_enriched.json"
        
        if enriched_path.exists():
            with open(enriched_path, "r") as f:
                courses_data = json.load(f)
            logger = logging.getLogger(__name__)
            logger.info(f"[ENRICHMENT] Loaded {len(courses_data)} enriched course records from {enriched_path}")
            return courses_data
        else:
            logging.getLogger(__name__).warning(f"[ENRICHMENT] Enriched dataset not found at {enriched_path}")
            return []
    except Exception as e:
        logging.getLogger(__name__).error(f"[ENRICHMENT] Failed to load enriched data: {e}")
        return []

# Load enriched data once at startup
ENRICHED_COURSES = _load_enriched_dataset()

def _get_course_enrichment(course_name: str) -> Optional[Dict[str, Any]]:
    """Get enrichment data for a course (decision-support fields)."""
    if not course_name or not ENRICHED_COURSES:
        return None
    
    course_upper = course_name.upper().replace(".", "").strip()
    
    for course_record in ENRICHED_COURSES:
        record_course = course_record.get("course_name", "").upper().replace(".", "").strip()
        if record_course == course_upper:
            return course_record
    
    return None

def _build_enrichment_block(course_enrichment: Dict[str, Any]) -> str:
    """Build text block with enriched course information."""
    if not course_enrichment:
        return ""
    
    blocks = []
    
    # Add career paths if available
    if course_enrichment.get("career_paths"):
        careers = ", ".join(course_enrichment["career_paths"][:3])  # Top 3
        blocks.append(f"Career paths: {careers}")
    
    # Add average salary if available
    if course_enrichment.get("avg_salary_range"):
        blocks.append(f"Average salary: {course_enrichment['avg_salary_range']}")
    
    # Add difficulty if available
    if course_enrichment.get("difficulty_level"):
        blocks.append(f"Difficulty level: {course_enrichment['difficulty_level']}")
    
    # Join with newlines and add separator
    if blocks:
        enrichment_text = "\n".join(blocks)
        return "\n\n" + enrichment_text
    
    return ""

def normalize_course(course: str):
    return course.lower().replace(".", "").strip()

def is_valid_course(course):
    return normalize_course(course) in VALID_COURSES

def ultimate_fallback():
    intros = [
        "I want to make sure I guide you correctly.",
        "Let's make sure we're on the right track with your planning.",
        "I want to be as helpful as possible with your career choice.",
        "To give you the best advice, I need to understand your query better."
    ]
    import random
    intro = random.choice(intros)
    return (
        f"{intro}\n\n"
        "You can ask me about:\n"
        "• Courses (BBA, BCA, B.Com, etc.)\n"
        "• Fees & Scholarships\n"
        "• Placements & Salary\n"
        "• Admission process\n\n"
        "What would you like to explore?"
    )

def generate_course_specific_fallback(user_course: str, query: str) -> Optional[str]:
    """Generate course-specific fallback when user queries their own course."""
    if not user_course:
        return None
    
    # Map courses to structured knowledge
    course_info = {
        "MBA": "Master of Business Administration (MBA) - A 2-year postgraduate program focusing on business fundamentals, strategy, and leadership.",
        "MCA": "Master of Computer Applications (MCA) - A 2-year postgraduate program in computer science and applications.",
        "BCA": "Bachelor of Computer Applications (BCA) - A 3-year undergraduate program in computer science and IT.",
        "BBA": "Bachelor of Business Administration (BBA) - A 3-year undergraduate program in business and management.",
        "B.Com": "Bachelor of Commerce (B.Com) - A 3-year undergraduate program in commerce and accounting.",
        "M.Com": "Master of Commerce (M.Com) - A 2-year postgraduate program in advanced commerce and finance.",
        "BHM": "Bachelor of Hotel Management (BHM) - A 3-year undergraduate program in hospitality and hotel management.",
    }
    
    # Find matching course
    user_course_upper = user_course.upper().replace(".", "")
    matching_info = None
    for course_key, description in course_info.items():
        if course_key.replace(".", "") == user_course_upper:
            matching_info = description
            break
    
    if not matching_info:
        return None
    
    # Generate context-aware response
    if "fee" in query.lower() or "cost" in query.lower():
        return f"You're interested in {user_course}. To provide accurate fee information, I'd like to connect you with our admissions team. They can give you the exact fee structure and payment options for {user_course}."
    elif "admission" in query.lower() or "apply" in query.lower() or "eligible" in query.lower():
        return f"For {user_course} admission details, I recommend contacting our admissions team. They can walk you through eligibility criteria, application process, and required documents."
    elif "placement" in query.lower() or "job" in query.lower() or "salary" in query.lower():
        return f"Great interest in {user_course}! For detailed placement statistics and salary information specific to {user_course}, our career services team would have the most current data."
    elif "semester" in query.lower() or "duration" in query.lower() or "syllabus" in query.lower():
        return f"{matching_info}. For detailed curriculum and semester breakdown of {user_course}, I can connect you with our academic advisor."
    else:
        # Generic course-specific response
        return f"{matching_info}\n\nI'd be happy to provide more specific information about {user_course}. What would you like to know - fees, admission process, placements, or curriculum details?"

# Import structured knowledge for deterministic responses
from app.services.structured_knowledge import (
    get_structured_response as get_structured_knowledge_response,
    get_courses_structured,
    get_fees_structured,
    get_admission_structured,
    get_placements_structured,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== INTENT SCORING CONFIGURATION =====
CLARIFICATION_THRESHOLD = 0.82  # FIX #3: Increased from 0.75 to reduce wrong answers
MAX_EDIT_DISTANCE = 1  # FIX #2: Reduced from 2 to prevent meaning corruption

# SymSpell dictionary path - download from symspellpy
# https://github.com/charlesnchr/SymSpell/blob/master/frequency_dictionary_en_82_765.txt
DEFAULT_DICTIONARY = "/Users/maneeth/Desktop/Chat-Bot/backend/app/services/orchestration/frequency_dictionary_en_82_765.txt"

TOOL_INTENT_WEIGHTS = {
    "location": {
        "keywords": ["where", "location", "map", "directions", "reach", "distance", "campus", "address", "place"],
        "weight": 0.7
    },
    "contact": {
        "keywords": ["phone", "email", "contact", "call", "reach", "number", "mobile", "whatsapp"],
        "weight": 0.5
    }
}

STRUCTURED_INTENTS = {
    "fees": {"weight": 0.9, "priority": 1},
    "admission": {"weight": 0.85, "priority": 2},
    "courses": {"weight": 0.95, "priority": 3},
    "placements": {"weight": 0.8, "priority": 4},
    "exam": {"weight": 0.8, "priority": 5},
    "scholarship": {"weight": 0.8, "priority": 6},
    "hostel": {"weight": 0.75, "priority": 7},
    "about_aims": {"weight": 1.0, "priority": 8},
    "why_aims": {"weight": 1.0, "priority": 9},
    "aims_features": {"weight": 0.9, "priority": 10}
}

# Tool intents NOT handled by structured - these go to tool ONLY
TOOL_ONLY_INTENTS = ["contact", "location", "apply"]

def compute_intent_scores(query: str) -> Dict[str, float]:
    """Compute intent scores for routing decisions using weighted scoring."""
    q = query.lower()
    scores = {}
    
    # Tool intent scoring
    for intent, config in TOOL_INTENT_WEIGHTS.items():
        score = 0.0
        matches = 0
        for keyword in config["keywords"]:
            if keyword in q:
                matches += 1
        if matches > 0:
            score = config["weight"] * min(matches, 2) / 2  # Normalize
        scores[intent] = score
    
    # Structured intent scoring
    for intent, config in STRUCTURED_INTENTS.items():
        match_words = {
            "fees": ["fee", "fees", "cost", "price", "charges", "structure"],
            "admission": ["admission", "admissions", "apply", "apply process", "eligibility", "eligible", "criteria", "how to apply"],
            "courses": ["course", "courses", "program", "programs", "degree", "available"],
            "placements": ["placement", "placements", "placed", "jobs", "recruit", "salary", "package"],
            "exam": ["exam", "entrance", "exam"],
            "scholarship": ["scholarship", "scholarships", "financial aid"],
            "hostel": ["hostel", "accommodation", "housing", "dorm", "price"],
            # Improved: Match "what is" + "aims" for about_aims
            "about_aims": ["what is aims", "about aims", "tell me about aims", "aims overview", "aims introduction", "who is aims", "what does aims"],
            # Improved: Match "why" + "aims" for why_aims
            "why_aims": ["why aims", "why choose aims", "why should i join aims", "advantages of aims", "benefits of aims", "why aims better"],
            "aims_features": ["features", "facilities", "campus facilities", "infrastructure", "what facilities", "campus", "smart classroom", "labs", "library"],
        }
        matches = sum(1 for word in match_words.get(intent, []) if word in q)
        
        # Special handling for about_aims: if query has "what" and "aims", it's likely about_aims
        if intent == "about_aims" and "what" in q and "aims" in q and matches == 0:
            matches = 1
        
        # Special handling for why_aims: if query has "why" and "aims", it's likely why_aims
        if intent == "why_aims" and "why" in q and "aims" in q and matches == 0:
            matches = 1
        
        if matches > 0:
            scores[intent] = config["weight"] * min(matches, 2) / 2
        else:
            scores[intent] = 0.0
    
    return scores

def detect_tool_intent(query: str) -> Tuple[Optional[str], float]:
    """Detect if query should go to tool layer (returns intent, score)."""
    scores = compute_intent_scores(query)
    
    tool_scores = {k: v for k, v in scores.items() if k in TOOL_INTENT_WEIGHTS}
    if not tool_scores:
        return None, 0.0
    
    best_intent = max(tool_scores, key=tool_scores.get)
    best_score = tool_scores[best_intent]
    
    if best_score >= 0.3:
        return best_intent, best_score
    return None, 0.0

def detect_structured_intent(query: str) -> Tuple[Optional[str], float]:
    """Detect if query should use structured layer."""
    scores = compute_intent_scores(query)
    
    structured_scores = {k: v for k, v in scores.items() if k in STRUCTURED_INTENTS}
    if not structured_scores:
        return None, 0.0
    
    best_intent = max(structured_scores, key=structured_scores.get)
    best_score = structured_scores[best_intent]
    
    if best_score >= 0.4:
        return best_intent, best_score
    return None, 0.0


def detect_multiple_intents(query: str) -> List[Tuple[str, float]]:
    """Detect multiple intents in a single query.
    
    PHASE 1: Simple multi-intent detection (no aggressive splitting).
    Detects all intents present in the query without breaking natural language.
    
    IMPORTANT: Preserves query order for natural response ordering.
    """
    scores = compute_intent_scores(query)
    
    # Get all structured intents with score >= 0.4
    # Filter to only include intents that are clearly present
    multi_intents = [
        (intent, score)
        for intent, score in scores.items()
        if intent in STRUCTURED_INTENTS and score >= 0.4
    ]
    
    # PHASE 3 FIX: Post-process intents to remove conflicts and add forced detections
    multi_intents = _post_process_intents(query, multi_intents)
    
    # PHASE 2 FIX: Preserve query order instead of sorting by score
    # This makes responses feel natural, not robotic
    # Find position of each intent keyword in query
    query_lower = query.lower()
    intents_with_position = []
    
    for intent, score in multi_intents:
        # Get keywords for this intent
        intent_keywords = INTENT_KEYWORDS.get(intent, [])
        
        # Find earliest position of any keyword for this intent
        min_position = len(query)
        for keyword in intent_keywords:
            pos = query_lower.find(keyword.lower())
            if pos != -1 and pos < min_position:
                min_position = pos
        
        intents_with_position.append((intent, score, min_position))
    
    # PHASE 3 FIX: Sort by position first, then by confidence score (descending)
    # This ensures query order is preserved, but higher confidence intents appear first within same position
    intents_with_position.sort(key=lambda x: (x[2], -x[1]))
    
    # Return without position (for backward compatibility)
    multi_intents = [(intent, score) for intent, score, _ in intents_with_position]
    
    if len(multi_intents) > 1:
        logger.info(f"[MULTI_INTENT] Detected {len(multi_intents)} intents (query order): {[i[0] for i in multi_intents]}")
    
    return multi_intents


def _post_process_intents(query: str, intents: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
    """Post-process intents to remove conflicts and add forced detections.
    
    PHASE 3 FIX: Control rules for intent behavior
    """
    intent_names = [intent for intent, score in intents]
    query_lower = query.lower()
    
    # RULE 1: Intent conflict resolution
    # If why_aims is detected, remove about_aims (they conflict)
    if "why_aims" in intent_names and "about_aims" in intent_names:
        intents = [(i, s) for i, s in intents if i != "about_aims"]
        logger.debug(f"[INTENT_CONFLICT] Removed about_aims (why_aims takes priority)")
    
    # RULE 2: Forced detection for critical intents
    # If "hostel" keyword is present, force hostel intent even if score is low
    hostel_keywords = ["hostel", "accommodation", "stay", "dorm", "housing"]
    if any(kw in query_lower for kw in hostel_keywords):
        if "hostel" not in intent_names:
            intents.append(("hostel", 0.9))
            logger.debug(f"[FORCED_DETECTION] Added hostel intent (keyword match)")
    
    # RULE 3: Remove duplicate intents
    seen = set()
    unique_intents = []
    for intent, score in intents:
        if intent not in seen:
            unique_intents.append((intent, score))
            seen.add(intent)
    
    return unique_intents

# Legacy compatibility
LOCATION_KEYWORDS = TOOL_INTENT_WEIGHTS["location"]["keywords"]
CONTACT_KEYWORDS = TOOL_INTENT_WEIGHTS["contact"]["keywords"]

# PHASE 2 FIX: Intent keywords for query order preservation
INTENT_KEYWORDS = {
    "fees": ["fee", "fees", "cost", "price", "charges", "structure"],
    "admission": ["admission", "admissions", "apply", "apply process", "eligibility"],
    "placements": ["placement", "placements", "placed", "jobs", "salary", "package"],
    "courses": ["course", "courses", "program", "programs", "study", "degree"],
    "hostel": ["hostel", "accommodation", "housing", "dorm"],
    "exam": ["exam", "exams", "test", "entrance"],
    "scholarship": ["scholarship", "scholarships", "financial aid"],
    "about_aims": ["what is aims", "about aims", "aims institutes", "institution"],
    "why_aims": ["why aims", "why choose", "choose aims", "benefits"],
    "aims_features": ["facilities", "campus", "infrastructure", "features"],
}

# ===== DATA STRUCTURES =====
class OrchestrationResult:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# ===== UTILITY FUNCTIONS =====
def edit_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance"""
    if len(s1) < len(s2):
        return edit_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = previous_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def correct_query_typos(query: str) -> Tuple[str, str]:
    """Correct query typos using SymSpell with safety checks.
    
    FIX #2: Enhanced to prevent meaning corruption.
    """
    # Guardrail: skip short queries
    if len(query) < 3:
        return query, query
    
    # Guardrail: skip if contains non-alphabetic (except spaces)
    if not query.replace(" ", "").isalpha():
        return query, query
    
    try:
        sym_spell = SymSpell(max_dictionary_edit_distance=1, prefix_length=7)
        
        # Try to load custom dictionary first
        dict_loaded = False
        if DEFAULT_DICTIONARY:
            try:
                dict_loaded = sym_spell.load_dictionary(DEFAULT_DICTIONARY, term_index=0, count_index=1)
            except Exception as e:
                logger.debug(f"[SYMSPELL] Dictionary load failed: {e}")
        
        # Guardrail: if no dictionary, skip correction
        if not dict_loaded:
            logger.debug(f"[SYMSPELL] No dictionary, skipping correction")
            return query, query
            
        suggestions = sym_spell.lookup(query, Verbosity.CLOSEST, max_edit_distance=1)
        if not suggestions:
            return query, query
            
        best_suggestion = suggestions[0].term
        edit_dist = edit_distance(query.lower(), best_suggestion.lower())
        
        # Guardrail: Only correct if meaningful change
        # - edit_dist must be > 0 (actually different)
        # - edit_dist must be <= 1 (prevent major changes)
        # - Word count shouldn't increase (prevents garbage like "location job cost lab")
        word_increase = len(best_suggestion.split()) - len(query.split())
        
        if 0 < edit_dist <= 1 and word_increase <= 0:
            corrected_query = best_suggestion
            logger.debug(f"[TYPO_CORRECTION] '{query}' -> '{corrected_query}' (edit_dist: {edit_dist})")
            return corrected_query, query
        else:
            logger.debug(f"[TYPO_CORRECTION] No correction for '{query}' (edit_dist: {edit_dist}, word_increase: {word_increase})")
            return query, query
            
    except Exception as e:
        logger.warning(f"[TYPO_CORRECTION] Failed with error: {e}")
        return query, query  # Safe fallback


def validate_query(query: str) -> Tuple[bool, str]:
    """Validate query before processing.
    
    PHASE 1: Input validation - prevents garbage input.
    """
    if not query:
        return False, "Please ask a question."
    
    cleaned = query.strip()
    
    # Check minimum length
    if len(cleaned) < 3:
        return False, "Your question is too short. Try: 'What is AIMS?' or 'BCA fees'"
    
    # Check for pure garbage (no alphanumeric characters)
    # Allow numbers because users may type "BCA fees 2024"
    if not any(c.isalnum() for c in cleaned):
        return False, "I didn't understand that. You can ask about:\n• What is AIMS?\n• BCA fees\n• Admission process"
    
    return True, cleaned


def correct_query_typos_word_level(query: str) -> Tuple[str, str]:
    """Correct query typos at WORD LEVEL using SymSpell.
    
    PHASE 1: Word-level correction - safer than sentence-level.
    Corrects individual words while preserving sentence structure.
    
    PHASE 2 FIX: Protects critical domain terms from over-correction.
    """
    if len(query) < 3:
        return query, query
    
    try:
        sym_spell = SymSpell(max_dictionary_edit_distance=1, prefix_length=7)
        
        # Load dictionary
        dict_loaded = False
        if DEFAULT_DICTIONARY:
            try:
                dict_loaded = sym_spell.load_dictionary(DEFAULT_DICTIONARY, term_index=0, count_index=1)
            except Exception as e:
                logger.debug(f"[SYMSPELL] Dictionary load failed: {e}")
        
        if not dict_loaded:
            return query, query
        
        # Split into words and correct each one
        words = query.split()
        corrected_words = []
        corrections_made = []
        
        for word in words:
            # PHASE 2 FIX: Skip protected words (critical domain terms)
            if word.lower() in PROTECTED_WORDS:
                corrected_words.append(word)
                logger.debug(f"[TYPO_WORD] Skipped protected word: {word}")
                continue
            
            # Skip very short words (less likely to be typos)
            if len(word) < 3:
                corrected_words.append(word)
                continue
            
            # Look up word
            suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=1)
            
            if suggestions:
                suggestion = suggestions[0].term
                edit_dist = edit_distance(word.lower(), suggestion.lower())
                
                # Only correct if edit distance is 1 (single typo)
                if 0 < edit_dist <= 1:
                    corrected_words.append(suggestion)
                    corrections_made.append(f"'{word}' → '{suggestion}'")
                    logger.debug(f"[TYPO_WORD] {word} → {suggestion}")
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
        
        corrected_query = " ".join(corrected_words)
        
        if corrections_made:
            logger.info(f"[TYPO_CORRECTIONS] {', '.join(corrections_made)}")
            return corrected_query, query
        
        return query, query
        
    except Exception as e:
        logger.warning(f"[SYMSPELL_WORD_LEVEL] Failed: {e}")
        return query, query

def is_meaningful_chunk(chunk: Any) -> bool:
    """Check if a chunk contains meaningful information"""
    if isinstance(chunk, tuple) and len(chunk) > 0:
        return bool(chunk[0])
    elif isinstance(chunk, dict):
        return bool(chunk.get('text', ''))
    elif isinstance(chunk, str):
        return bool(chunk.strip())
    return False

def has_meaningful_chunks(chunks: List[Any]) -> bool:
    """Check if we have meaningful chunks after filtering"""
    return any(is_meaningful_chunk(chunk) for chunk in chunks)

# ===== INTENT DETECTION =====
def parse_query(query: str):
    """Parse query into intents and entities"""
    query_lower = query.lower()
    intents = []
    entities = {}
    
    FEES_KEYWORDS = ['fee', 'fees', 'cost', 'price', 'fees structure']
    ADMISSION_KEYWORDS = ['admission', 'admissions', 'apply', 'apply process']
    PLACEMENT_KEYWORDS = ['placement', 'placements', 'placed', 'jobs', 'jobs record']
    COURSE_KEYWORDS = ['course', 'courses', 'program', 'programs', 'study', 'degree']
    PLACEMENT_RANKING_KEYWORDS = ['ranking', 'rank', 'top', 'best']
    REASONING_KEYWORDS = ['worth', 'better', 'compare', 'vs', 'versus', 'which is', 'which']
    LOCATION_KEYWORDS = ['location', 'where', 'place', 'address', 'campus', 'map', 'direction', 'how to reach', 'how to get']
    
    if any(word in query_lower for word in REASONING_KEYWORDS):
        intents.append('reasoning')
        entities['comparison_type'] = 'value'
    
    if any(word in query_lower for word in FEES_KEYWORDS):
        intents.append('fees')
    if any(word in query_lower for word in ADMISSION_KEYWORDS):
        intents.append('admission')
    if any(word in query_lower for word in PLACEMENT_KEYWORDS):
        intents.append('placement')
    if any(word in query_lower for word in COURSE_KEYWORDS):
        intents.append('course')
    if any(word in query_lower for word in PLACEMENT_RANKING_KEYWORDS):
        intents.append('ranking')
    if any(word in query_lower for word in LOCATION_KEYWORDS):
        intents.append('location')
    
    # Extract course entity if mentioned
    course_matches = re.findall(r'\b(MBA|BCA|BBA|MCA|B.Tech|B.Sc|B.Com)\b', query.upper())
    if course_matches:
        entities['course'] = course_matches[0].upper()
    
    return intents, entities

# ===== CONTEXT INJECTION =====
def _inject_course_context(query: str, entities: Dict) -> str:
    """Inject course context into query for RAG retrieval"""
    course = entities.get("course", "").strip()
    if course:
        return f"{query} about {course}"
    return query

# ===== TOOL LAYER (CONVERSATIONAL) =====
TOOL_RESPONSES = {
    "location": {
        "primary": (
            "AIMS Institutes is located in Bangalore, Karnataka. "
            "The campus is situated at #1, Pipeline Road, Hesaraghatta Main Road, "
            "Near Peenya, Bangalore - 560090."
        ),
        "maps_link": "https://www.google.com/maps?q=AIMS+Institutes+Bangalore",
        "cta": "Get Directions"
    },
    "contact": {
        "primary": (
            "For admissions inquiries, you can reach us at:"
        ),
        "phone": "+91-815-000-1994",
        "email": "admission@theaims.ac.in",
        "website": "www.theaims.ac.in",
        "cta": "Visit Website"
    }
}

def get_conversational_tool_response(intent: str, query: str = "") -> Optional[OrchestrationResult]:
    """Get conversational tool response - human style."""
    response_data = TOOL_RESPONSES.get(intent)
    if not response_data:
        return None
    
    q_lower = query.lower()
    
    if intent == "location":
        # Check if user is asking for directions specifically
        if any(word in q_lower for word in ["how to reach", "directions", "distance", "travel"]):
            answer = (
                f"{response_data['primary']}\n\n"
                f"📍 Get directions: {response_data['maps_link']}\n\n"
                "If you share your current location, I can help estimate the travel time!"
            )
        else:
            answer = (
                f"{response_data['primary']}\n\n"
                f"📍 View on map: {response_data['maps_link']}\n\n"
                "Would you like directions from a specific location?"
            )
        
        return OrchestrationResult(
            answer=answer,
            intent="location",
            confidence=0.95,
            mode="tool",
            fallback=False,
            suggestions=["Campus facilities", "Admission process", "Hostel"]
        )
    
    if intent == "contact":
        # Check if user is asking specifically about phone/email
        if any(word in q_lower for word in ["phone", "call", "number", "mobile"]):
            answer = (
                f"📞 You can call us at: {response_data['phone']}\n\n"
                "Our admissions team is available during working hours."
            )
        elif any(word in q_lower for word in ["email", "mail"]):
            answer = (
                f"📧 Email: {response_data['email']}\n\n"
                "We typically respond within 24 hours."
            )
        else:
            answer = (
                f"{response_data['primary']}\n\n"
                f"📞 Phone: {response_data['phone']}\n"
                f"📧 Email: {response_data['email']}\n"
                f"🌐 Website: {response_data['website']}\n\n"
                "Which would you prefer?"
            )
        
        return OrchestrationResult(
            answer=answer,
            intent="contact",
            confidence=0.95,
            mode="tool",
            fallback=False,
            suggestions=["Admission process", "Fees"]
        )
    
    return None

def handle_tool_query_by_intent(query: str) -> Optional[OrchestrationResult]:
    """Route query to tool responses using intent detection."""
    intent, score = detect_tool_intent(query)
    if intent and score >= 0.3:
        return get_conversational_tool_response(intent, query)
    return None

# ===== STRUCTURED LAYER (Delegates to structured_knowledge.py) =====
# FIX #1: Single source of truth - all structured logic in one place

def get_structured_response_for_intent(intent: Optional[str], query: str, context: Optional[Dict] = None) -> Optional[Dict]:
    """Route structured request using intent scoring results.
    
    FIX #1: Force intent, don't re-detect. Call specific functions directly.
    FIX #2: Use user's selected course from context if not mentioned in query.
    """
    if not intent:
        return None
    
    # Remove tool intents from structured handling
    if intent in TOOL_ONLY_INTENTS:
        return None
    
    # Use structured_knowledge for these intents
    structured_intents = ["fees", "admission", "courses", "placements", "hostel", "exam", "scholarship", "about_aims", "why_aims", "aims_features"]
    if intent not in structured_intents:
        return None
    
    # Extract program from query if present, otherwise use user's selected course from context
    program = None
    query_lower = query.lower()
    for prog in ["mba", "bba", "mca", "bca", "b.com", "m.com", "bhm"]:
        if prog.replace(".", "") in query_lower.replace(" ", ""):
            program = prog.replace(".", "").upper()
            break
    
    # If no program found in query, use user's selected course from context
    if not program and context:
        user_course = context.get("course", "").strip()
        if user_course:
            program = user_course.replace(".", "").upper()
            logger.info(f"[STRUCTURED] Using user's selected course from context: {program}")
    
    try:
        response = None
        # FORCE INTENT - call specific function, don't re-detect
        if intent == "fees":
            response = get_fees_structured(program)
        elif intent == "admission":
            response = get_admission_structured(program=program)
        elif intent == "courses":
            response = get_courses_structured(program)
        elif intent == "placements":
            response = get_placements_structured(program)
        elif intent == "hostel":
            from app.services.structured_knowledge import get_hostel_structured
            response = get_hostel_structured()
        elif intent == "exam":
            from app.services.structured_knowledge import get_exam_structured
            response = get_exam_structured(program)
        elif intent == "scholarship":
            from app.services.structured_knowledge import get_scholarship_structured
            response = get_scholarship_structured()
        elif intent == "about_aims":
            from app.services.structured_knowledge import get_about_aims_structured
            response = get_about_aims_structured()
        elif intent == "why_aims":
            from app.services.structured_knowledge import get_why_aims_structured
            response = get_why_aims_structured()
        elif intent == "aims_features":
            from app.services.structured_knowledge import get_aims_features_structured
            response = get_aims_features_structured()
        
        if response:
            answer_text = response.get("answer", "")
            if answer_text:
                return {
                    "answer": answer_text,
                    "intent": intent,  # Use enforced intent, not detected
                    "confidence": response.get("confidence", 0.95),
                    "mode": "structured",
                    "suggestions": response.get("suggestions", [])
                }
    except Exception as e:
        logger.warning(f"[STRUCTURED_ERROR] {e}")
    
    return None

# ===== TOOL LAYER =====
def handle_tool_query(query: str) -> Optional[OrchestrationResult]:
    """Handle tool-based queries like location and contact using intent detection.
    
    This function is called when we detect tool-specific intents (location, contact).
    It uses conversational tool responses defined in TOOL_RESPONSES.
    """
    # Route to tool layer using intent detection
    return handle_tool_query_by_intent(query)

# ===== RAG RESPONSE =====
def format_rag_response(chunks: List) -> str:
    """Format RAG response from chunks"""
    texts = []
    for chunk in chunks:
        if isinstance(chunk, dict) and 'text' in chunk:
            texts.append(chunk['text'])
        elif isinstance(chunk, str):
            texts.append(chunk)
        elif isinstance(chunk, tuple) and len(chunk) > 0:
            texts.append(str(chunk[0]))
    if not texts:
        return "I couldn't find relevant information."
    return "\n\n".join(f"Source {i+1}:\n{text}" for i, text in enumerate(texts))

# ===== CONFIDENCE CALCULATION =====
def _compute_rag_confidence(chunks: List[Any], intents: List[str], query: str) -> float:
    intent_score = 0.35 if intents and intents[0] != "general" else 0.15
    chunk_score = 0.0
    if chunks:
        best_score = 0.0
        meaningful_count = 0
        for c in chunks:
            score = c[1] if isinstance(c, tuple) and len(c) > 1 else c.get("score", 0.5)
            best_score = max(best_score, score)
            if score >= 0.3:
                meaningful_count += 1
        if best_score >= 0.5 and meaningful_count >= 2:
            chunk_score = 0.4
        elif best_score >= 0.3:
            chunk_score = 0.25
        else:
            chunk_score = 0.1
    specificity = 0.1 if any(term in query.lower() for term in ["fees", "admission", "placement", "course", "worth", "better", "compare"]) else 0.0
    return min(intent_score + chunk_score + specificity, 0.95)

# ===== CLARIFICATION =====
def generate_clarification_response(query: str, parsed_intents: List[str]) -> OrchestrationResult:
    intent_map = {
        "fees": "Fees", "placements": "Placements", "courses": "Courses", 
        "admission": "Admission", "campus": "Campus Facilities", 
        "scholarship": "Scholarships", "contact": "Contact Info", 
        "reasoning": "Reasoning/Comparison"
    }
    options = []
    for intent in parsed_intents:
        if intent in intent_map and intent_map[intent] not in options:
            options.append(intent_map[intent])
    all_options = ["Fees", "Placements", "Courses", "Admission", "Reasoning"]
    for opt in all_options:
        if opt not in options:
            options.append(opt)
        if len(options) >= 5:
            break
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    return OrchestrationResult(
        answer=(
            "I want to make sure I understood correctly. "
            "Are you asking about:\n\n"
            f"{options_text}\n\n"
            "Please reply with the number or topic you're interested in."
        ),
        intent="clarification",
        confidence=0.5,
        mode="clarification",
        fallback=False,
        suggestions=options,
    )

def calculate_similarity(a: str, b: str) -> float:
    """Simple character-based similarity for loop detection."""
    if not a or not b:
        return 0.0
    a_start = a[:100].lower()
    b_start = b[:100].lower()
    
    # Check for exact prefix overlap
    if a_start == b_start:
        return 1.0
        
    # Check for word overlap
    words_a = set(a_start.split())
    words_b = set(b_start.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a.intersection(words_b)
    return len(intersection) / max(len(words_a), len(words_b))

def calculate_progression(old_context: dict, new_context: dict, query: str) -> float:
    """
    Calculates if the conversation is moving forward.
    Score: 0.0 to 1.0
    """
    score = 0.0
    
    # 1. New information extracted?
    old_marks = old_context.get("marks")
    new_marks = new_context.get("marks")
    if new_marks and new_marks != old_marks:
        score += 0.4
        
    old_interest = old_context.get("interests")
    new_interest = new_context.get("interests")
    if new_interest and new_interest != old_interest:
        score += 0.4
        
    # 2. Stage progression?
    old_stage = old_context.get("conversion_stage", "none")
    new_stage = new_context.get("conversion_stage", "none")
    if old_stage != new_stage:
        score += 0.3
        
    # 3. New question asked?
    old_asked = len(old_context.get("_asked_questions", []))
    new_asked = len(new_context.get("_asked_questions", []))
    if new_asked > old_asked:
        score += 0.2
        
    return min(score, 1.0)

# ===== NEW COUNSELOR PIPELINE =====
def _execute_counselor_pipeline(query: str, context: dict = None, session_id: str = None, increment_turn: bool = True):
    """
    Full counselor flow:
    stage_controller → router → engines → composer → formatter
    """

    context = context or {}
    entities = extract_entities(query)
    
    # FAILURE CAPTURE: Check if user responded to clarification
    if context.get("awaiting_clarification"):
        session_id_for_tracking = session_id or context.get("session_id")
        if session_id_for_tracking:
            from app.services.counselor.production_analytics import track_clarification_response
            turns_taken = context.get("turn_count", 0) - context.get("clarification_turn", 0)
            # Outcome will be updated later when we know if they converted or continued
            track_clarification_response(session_id_for_tracking, responded=True, turns_taken=turns_taken, outcome="continued")
        context["awaiting_clarification"] = False
    
    # Update memory (initial state update)
    if session_id:
        update_student_profile(session_id, entities, query=query, increment_turn=increment_turn)
    
    # Merge entities into context for engines
    context.update(entities)
    context["_entities"] = entities  # Store for stage controller
    
    # Enrich context with memory
    if session_id:
        context = enrich_context_with_memory(context, session_id)
    
    # Snapshot of context for progression tracking
    old_context_snapshot = context.copy()
    last_answer = context.get("last_answer", "")
    
    # ============================================
    # STAGE CONTROLLER (NEW - HIGHEST PRIORITY)
    # ============================================
    from app.services.counselor.stage_controller import execute_stage_control, lock_decision
    from app.services.counselor.production_analytics import (
        track_stage, update_session_activity, get_adaptive_threshold,
        stabilize_interest, check_silent_user, track_fallback
    )
    
    # Update session activity
    if session_id:
        update_session_activity(session_id)
    
    stage_control = execute_stage_control(query, context)
    stage = stage_control["stage"]
    action = stage_control["action"]
    
    # Track stage transition
    if session_id:
        track_stage(session_id, stage, context)
    
    # Store stage control result in context for later use
    context["_stage_control"] = stage_control
    
    logger.info(f"[STAGE_CONTROL] Stage: {stage} | Action: {action}")
    
    # STAGE ACTION: APPLY (Structured Mode - EXECUTION ONLY)
    if action == "apply":
        from app.services.counselor.conversion import run_next_step_info
        locked_course = stage_control["locked_course"]
        if not locked_course:
            return {"answer": "Which course would you like to apply for? Let me know and I'll walk you through the steps.", "mode": "clarification", "intents": ["apply"], "confidence": 1.0}
        
        # Track apply event
        if session_id:
            from app.services.counselor.production_analytics import track_apply
            track_apply(session_id, locked_course)
        
        # BALANCED APPLY MODE: Structured but responsive
        # Allow quick info queries (fees, hostel, placement) but stay in apply context
        quick_info_keywords = ["fee", "cost", "hostel", "placement", "salary"]
        is_quick_info = any(word in query.lower() for word in quick_info_keywords) and len(query.split()) <= 5
        
        if is_quick_info:
            # Answer briefly then return to apply steps
            from app.services.counselor.guidance_engine import run_guidance_engine
            guidance_result = run_guidance_engine(query, context)
            brief_answer = guidance_result.get("explanation", "")[:200]  # Keep it brief
            
            return {
                "answer": f"{brief_answer}\n\n**Ready to apply for {locked_course}?**\n\n{run_next_step_info('how to apply', locked_course, context)}",
                "mode": "apply",
                "intents": ["apply"],
                "confidence": 1.0
            }
        
        # HARD GUARD: Block exploratory questions (course switching attempts)
        exploratory_keywords = ["better", "compare", "vs", "which", "should i", "what about"]
        if any(word in query.lower() for word in exploratory_keywords):
            return {
                "answer": f"You've already chosen **{locked_course}**. Let's focus on getting you enrolled.\n\n{run_next_step_info(query, locked_course, context)}",
                "mode": "apply",
                "intents": ["apply"],
                "confidence": 1.0
            }
        
        # Default: Show structured apply steps
        answer = run_next_step_info(query, locked_course, context)
        return {"answer": answer, "mode": "apply", "intents": ["apply"], "confidence": 1.0}
    
    # STAGE ACTION: DECISION_LOCKED (Stay Locked)
    if action == "decision_locked":
        locked_course = stage_control["locked_course"]
        # Continue with normal flow but ensure course stays locked
        logger.info(f"[DECISION_LOCKED] Course: {locked_course} - staying locked")
    
    # STAGE ACTION: LOCK_AND_GUIDE (Explicit Course Mention)
    # User said "I want to do BCA" - this is a decision, lock it immediately
    if action == "lock_and_guide":
        # Get the course from entities
        extracted_courses = entities.get("courses", [])
        if extracted_courses and not context.get("locked_course"):
            course_to_lock = extracted_courses[0]
            
            # Lock immediately (bypass confidence gate for explicit mentions)
            from app.services.counselor.stage_controller import lock_decision
            context = lock_decision(context, course_to_lock)
            context["locked_at"] = context.get("turn_count", 0)
            
            if session_id:
                update_student_profile(session_id, {"locked_course": course_to_lock}, increment_turn=False)
                
                # Track decision
                from app.services.counselor.production_analytics import track_decision
                track_decision(session_id, {
                    "query": query,
                    "confidence": 0.95,
                    "method": "explicit_course_mention",
                    "course": course_to_lock,
                    "locked": True,
                    "clarification_needed": False,
                    "skip_reason": "explicit_mention"
                })
            
            logger.info(f"[EXPLICIT_LOCK] Course LOCKED: {course_to_lock} (explicit mention)")
            
            # Now run guidance to provide course-specific information
            from app.services.counselor.guidance_engine import run_guidance_engine
            guidance_result = run_guidance_engine(query, context)
            
            return {
                "answer": guidance_result.get("explanation", f"Great choice! {course_to_lock} is locked. What would you like to know?"),
                "mode": "guidance",
                "intents": ["guidance"],
                "confidence": 0.95
            }
    
    # STAGE ACTION: DECISION_LOCKED (Stay Locked)
    if action == "deepening":
        locked_course = stage_control["locked_course"]
        
        # Check for multi-intent queries
        from app.services.counselor.decision_detector import detect_multi_intent
        multi_intent = detect_multi_intent(query)
        
        # Run guidance engine in LOCKED mode (no course switching)
        from app.services.counselor.guidance_engine import run_guidance_engine
        guidance_result = run_guidance_engine(query, context)
        
        # Force top_course to be locked_course (no switching allowed)
        guidance_result["top_course"] = locked_course
        guidance_result["recommended_courses"] = [locked_course]
        
        # Compose response focused on deepening knowledge
        answer = guidance_result.get("explanation", f"You've chosen **{locked_course}**. What would you like to know more about?")
        
        # Handle multi-intent: answer all parts
        if multi_intent["is_multi"]:
            logger.info(f"[MULTI_INTENT] Detected secondary intents: {multi_intent['intents']}")
            # Answer is already comprehensive from guidance engine
            # Just ensure we address all parts
        
        # CONVERSION PUSH: After answering, push toward apply
        # Check if user is asking about apply-related topics
        apply_related = any(word in query.lower() for word in ["fee", "cost", "salary", "placement", "job", "eligibility", "admission"])
        
        if apply_related and "apply" not in query.lower():
            # Add conversion push after answer
            push_messages = [
                f"\n\nSince you're aligned with {locked_course}, would you like to see how the admission process works?",
                f"\n\nYou seem ready for {locked_course}. Want me to walk you through the application steps?",
                f"\n\nGlad that helps! Should I show you the next steps to apply for {locked_course}?"
            ]
            import random
            answer += random.choice(push_messages)
        
        return {"answer": answer, "mode": "locked", "intents": ["locked"], "confidence": 1.0, "locked_course": locked_course}
    
    # STAGE ACTION: SIMPLIFY (Confusion)
    if action == "simplify":
        message = stage_control["data"]["message"]
        return {"answer": message, "mode": "confusion", "intents": ["confusion"], "confidence": 1.0}
    
    # STAGE ACTION: CLARIFY
    if action == "clarify":
        message = stage_control["data"]["message"]
        return {"answer": message, "mode": "clarification", "intents": ["clarification"], "confidence": 1.0}
    
    # STAGE ACTION: FALLBACK (Last Resort)
    # STAGE ACTION: FALLBACK (Last Resort)
    if action == "fallback" and not stage_control["should_run_guidance"]:
        # Track consecutive fallbacks
        fallback_count = context.get("_consecutive_fallbacks", 0)
        
        # Check if user is engaged (not noise)
        is_engaged = (
            context.get("marks") is not None or
            context.get("interests") is not None or
            bool(context.get("courses")) or
            len(query.split()) >= 3  # Minimal real signal (filters noise)
        )
        
        # ESCALATION: After 2 consecutive fallbacks with engaged user
        if fallback_count >= 2 and is_engaged and not context.get("_escalated_once"):
            context["_escalated_once"] = True
            
            # Track escalation
            if session_id:
                from app.services.counselor.production_analytics import track_fallback
                track_fallback(session_id, {
                    "query": query,
                    "stage": stage,
                    "reason": "escalation_triggered"
                })
            
            # Save context BEFORE returning (so escalation flag persists)
            if session_id:
                update_student_profile(session_id, context, increment_turn=False)
            
            return {
                "answer": "Got it — let me narrow this down.\n\nAre you looking for:\n1️⃣ Courses\n2️⃣ Fees\n3️⃣ Admission process\n4️⃣ Placements",
                "mode": "escalation",
                "intents": ["escalation"],
                "confidence": 0.6,
                "stage_control": stage_control
            }
        
        # Increment fallback counter
        context["_consecutive_fallbacks"] = fallback_count + 1
        
        # Track fallback
        if session_id:
            from app.services.counselor.production_analytics import track_fallback
            track_fallback(session_id, {
                "query": query,
                "stage": stage,
                "reason": "no_signal"
            })
        
        # Save context BEFORE returning (so counter persists)
        if session_id:
            update_student_profile(session_id, context, increment_turn=False)
        
        return {"answer": ultimate_fallback(), "mode": "fallback", "intents": ["fallback"], "confidence": 0.0, "stage_control": stage_control}
    
    # ============================================
    # CONTINUE WITH GUIDANCE (if allowed by stage)
    # ============================================
    if not stage_control["should_run_guidance"]:
        # Stage blocked guidance, return early
        return {"answer": "Processing...", "mode": "blocked", "intents": ["blocked"], "confidence": 0.5}
    
    # --- HARD STAGE ENFORCEMENT (Legacy - now handled by stage controller) ---
    # Keeping for backward compatibility but stage controller takes precedence
    apply_keywords = ["apply", "admission", "process", "documents", "how to join", "procedure", "steps", "join", "link"]
    query_lower = query.lower()
    if any(word in query_lower for word in apply_keywords):
        logger.info(f"[DEBUG] Hard Stage Enforcement triggered for query: '{query}'")
        from app.services.counselor.conversion import run_next_step_info
        top_course = context.get("locked_course") or (context.get("courses", [""])[0] if context.get("courses") else "your chosen course")
        answer = run_next_step_info(query, top_course, context)
        return {"answer": answer, "mode": "conversion", "intents": ["apply"], "confidence": 1.0}

    logger.info(f"[DEBUG] turn_count={context.get('turn_count')} | query='{query}' | entities={entities}")
    
    ambiguity = handle_ambiguity(query)
    if ambiguity:
        return {"answer": ambiguity, "mode": "clarification", "intents": ["clarification"], "confidence": 1.0}
        
    # 2. INTENT DETECTION
    intents = detect_intents(query)
    
    # --- RESPONSE VARIATION ENGINE ---
    # Rotate opening phrases to avoid "soft-looping"
    OPENING_PHRASES = [
        "Let’s simplify this.",
        "Here’s the real picture.",
        "Based on what you’ve told me so far,",
        "Looking at your profile,",
        "To give you a clear direction,",
        "Here's how we should approach this."
    ]
    import random
    opening = random.choice(OPENING_PHRASES)
    context["opening_variation"] = opening

    logger.info(f"[DEBUG] detected intents: {intents} for query: '{query}'")
    if not intents:
        logger.error(f"[DEBUG] No intents detected for query: '{query}' - checking for escalation")
        
        # Track consecutive fallbacks
        fallback_count = context.get("_consecutive_fallbacks", 0)
        logger.info(f"[ESCALATION_CHECK] fallback_count={fallback_count}, query='{query}'")
        
        # Check if user is engaged (not noise)
        is_engaged = (
            context.get("marks") is not None or
            context.get("interests") is not None or
            bool(context.get("courses")) or
            len(query.split()) >= 3  # Minimal real signal (filters noise)
        )
        logger.info(f"[ESCALATION_CHECK] is_engaged={is_engaged}, marks={context.get('marks')}, interests={context.get('interests')}, courses={context.get('courses')}, words={len(query.split())}")
        
        # ESCALATION: After 2 consecutive fallbacks with engaged user
        if fallback_count >= 2 and is_engaged and not context.get("_escalated_once"):
            logger.info(f"[ESCALATION_TRIGGERED] Escalating after {fallback_count} fallbacks")
            context["_escalated_once"] = True
            
            # Track escalation
            if session_id:
                from app.services.counselor.production_analytics import track_fallback
                track_fallback(session_id, {
                    "query": query,
                    "stage": stage,
                    "reason": "escalation_triggered"
                })
            
            # Save context BEFORE returning (so escalation flag persists)
            if session_id:
                update_student_profile(session_id, context, increment_turn=False)
            
            return {
                "answer": "Got it — let me narrow this down.\n\nAre you looking for:\n1️⃣ Courses\n2️⃣ Fees\n3️⃣ Admission process\n4️⃣ Placements",
                "mode": "escalation",
                "intents": ["escalation"],
                "confidence": 0.6,
                "stage_control": stage_control
            }
        
        # Increment fallback counter
        context["_consecutive_fallbacks"] = fallback_count + 1
        logger.info(f"[ESCALATION_CHECK] Incremented fallback counter to {fallback_count + 1}")
        
        # Track fallback
        if session_id:
            from app.services.counselor.production_analytics import track_fallback
            track_fallback(session_id, {
                "query": query,
                "stage": stage,
                "reason": "no_intent_detected"
            })
        
        # Save context BEFORE returning (so counter persists)
        if session_id:
            update_student_profile(session_id, context, increment_turn=False)
        
        # Check if user queried their own course - use course-specific fallback instead
        fallback_answer = ultimate_fallback()
        # Use the local variables that were extracted earlier in the function
        if query_mentions_user_course and user_course:
            course_specific = generate_course_specific_fallback(user_course, working_query)
            if course_specific:
                logger.info(f"[COURSE_AWARE_FALLBACK] User queried their course ({user_course}) - using course-specific fallback")
                fallback_answer = course_specific
        
        return {"answer": fallback_answer, "mode": "fallback", "intents": ["unknown"], "confidence": 0.0, "stage_control": stage_control}
        
    top_intent, top_score = intents[0]
    logger.info(f"[DEBUG] top_intent='{top_intent}' score={top_score}")
    if top_score < 0.6:
        # Rule 8 - Router Failure Fix
        return {"answer": "I want to guide you correctly — are you looking for courses, fees, or career options?", "mode": "clarification", "intents": ["clarification"], "confidence": top_score}

    # 3. CONVERSION FALLBACK (Turn-based logic)
    if context.get("turn_count", 0) > 8:
        # Bypass summary if user provides fresh info (marks, interests, etc)
        has_new_info = bool(entities.get("marks") or entities.get("courses") or entities.get("interests"))
        
        # Or if it's a very specific intent (compare, career, etc)
        # Lowered threshold to 0.7 to catch career/salary queries
        is_specific = any(i[0] not in ["conversion", "unknown", "guidance"] and i[1] >= 0.7 for i in intents)
        
        # Special check for high salary intent which routes to guidance but is very specific
        is_salary_query = any(re.search(p, query.lower()) for p in ["salary", "package", "money", "earn"])
        
        logger.info(f"[DEBUG] turn_count={context.get('turn_count')} has_new_info={has_new_info} is_specific={is_specific} is_salary={is_salary_query} intents={intents}")
        
        if not (has_new_info or is_specific or is_salary_query):
            logger.info("[DEBUG] Triggering conversion fallback summary")
            
            # Diversified intros to avoid loop detection
            intros = [
                "It’s completely normal to feel unsure at this stage—most students explore a few options before deciding.",
                "I want to make sure we're on the right track with your planning.",
                "Let’s take a step back and simplify things based on our conversation so far.",
                "Deciding on a career takes time, and it's good that you're asking these questions."
            ]
            import random
            summary_intro = random.choice(intros)
            
            marks_val = context.get('marks')
            if marks_val:
                summary_intro += f"\n\nBased on your {marks_val}%, here’s a quick summary:"
            else:
                summary_intro += "\n\nHere is where we stand:"
            
            conversion_stage = context.get("conversion_stage", "none")
            top_course = context.get("courses", [""])[0] if context.get("courses") else None
            if not top_course:
                from app.services.counselor.guidance_engine import run_guidance_engine
                guidance = run_guidance_engine(query, context)
                top_course = guidance.get("top_course", "a professional degree")

            if conversion_stage == "decision_confirmed":
                from app.services.counselor.conversion import run_next_step_info
                res = {"answer": f"{summary_intro}\n\n{run_next_step_info(query, top_course, context)}", "mode": "conversion", "intents": ["conversion"], "confidence": 1.0}
            elif conversion_stage == "ready_to_close":
                res = {"answer": f"{summary_intro}\n\nYou have all the information you need to proceed. Let me know if you want the application link, or if there's any final question on your mind.", "mode": "conversion", "intents": ["conversion"], "confidence": 1.0}
            else:
                res = {
                    "answer": f"{summary_intro}\n\n"
                              f"We've looked at {top_course} as a potential path. "
                              f"Would you like to see the admission steps or compare it with another option?",
                    "mode": "summary",
                    "intents": ["summary"],
                    "confidence": 1.0
                }
            
            if session_id:
                update_student_profile(session_id, context, increment_turn=False)
            return res

    # Rule 2 - Fix Confusion Loops
    # Only trigger if they are ACTUALLY still confused and we have no better intent
    is_confusion_query = any(re.search(p, query.lower()) for p in ["confused", "not sure", "idk", "what to do"])
    if context.get("confusion_count", 0) >= 2 and (is_confusion_query or top_intent == "unknown"):
        # Use actual guidance instead of hardcoded BBA/B.Com
        from app.services.counselor.guidance_engine import run_guidance_engine
        guidance = run_guidance_engine(query, context)
        top_course = guidance.get("top_course", "BBA")
        second_course = guidance.get("recommended_courses", ["BBA", "B.Com"])[1] if len(guidance.get("recommended_courses", [])) > 1 else "B.Com"
        
        return {
            "answer": f"Let’s simplify this.\nBased on what you’ve told me so far, {top_course} or {second_course} seem like your strongest starting points.\n\nWould you like to look at the fees for these, or discuss which one fits your salary goals better?",
            "mode": "guidance", 
            "intents": ["guidance"], 
            "confidence": 1.0
        }

    # 1. HANDLE OBJECTION FIRST (Rule 3)
    objection_response = handle_objection(query)
    if objection_response:
        track_event("objection_handled", {"session_id": session_id})
        return {"answer": objection_response, "mode": "conversion", "intents": ["objection"], "confidence": 1.0}
        
    # 2. RUN CONVERSION FLOW STATE MACHINE (Rule 1 & 4)
    course_name = context.get("locked_course") or (entities.get("courses", [""])[0] if entities.get("courses") else "that course")
    conversion_response = run_conversion_flow(query, context, course_name)
    if conversion_response:
        track_event("conversion_flow_advanced", {"session_id": session_id, "stage": context.get("conversion_stage")})
        
        # CRITICAL: If we just confirmed a decision and have a course, lock it
        if context.get("conversion_stage") == "decision_confirmed" and not context.get("locked_course"):
            # Extract course from entities or run guidance to get top course
            course_to_lock = None
            if entities.get("courses"):
                course_to_lock = entities["courses"][0]
            else:
                # Run guidance to get top course
                from app.services.counselor.guidance_engine import run_guidance_engine
                guidance = run_guidance_engine(query, context)
                course_to_lock = guidance.get("top_course")
            
            if course_to_lock:
                context = lock_decision(context, course_to_lock)
                if session_id:
                    update_student_profile(session_id, {"locked_course": course_to_lock}, increment_turn=False)
                logger.info(f"[CONVERSION_LOCK] Course LOCKED: {course_to_lock}")
        
        return {"answer": conversion_response, "mode": "conversion", "intents": ["conversion"], "confidence": 1.0}

    # ── BRIDGE: check permission/next-step if in bridge stage ──
    bridge_stage = context.get("bridge_stage", "none")
    if bridge_stage == "action_offered" and detect_permission(query):
        from app.services.counselor.conversion import run_next_step_info
        bridge_course = context.get("bridge_course", "your course")
        context["bridge_stage"] = "next_step_given"
        track_event("micro_commitment_confirmed", {"session_id": session_id, "course": bridge_course})
        return {
            "answer": run_next_step_info(query, bridge_course, context),
            "mode": "bridge",
            "intents": ["next_step"],
            "confidence": 1.0
        }

    # Course validation gate
    if entities.get("courses"):
        invalid_courses = [c for c in entities["courses"] if not is_valid_course(c)]
        if invalid_courses:
             return {"answer": f"We don't offer {invalid_courses[0]}. We offer BBA, BCA, MBA, B.Com, MCA, and BHM.\n\nWould you like to explore any of these?", "mode": "unavailable", "intents": ["unavailable"], "confidence": 1.0}
        
    track_event("counselor_used", {
        "intents": [i[0] for i in intents],
        "session_id": session_id
    })
    
    # Check for conversion signals
    if "apply" in query.lower() or "admission" in query.lower():
        track_event("conversion_signal", {
            "type": "admission_interest",
            "courses": entities.get("courses", []),
            "session_id": session_id
        })
    
    logger.info(f"[COUNSELOR] intents={intents} | entities={entities}")
    results = {}
    for intent, score in intents:
        if intent == "guidance":
            guidance_result = run_guidance(query, context)
            results["guidance"] = guidance_result

            # --- STRONG DECISION LOCK ---
            # Lock the course when stage controller signals it (stage="decision")
            stage_control = context.get("_stage_control", {})
            if stage_control.get("should_lock") and not context.get("locked_course"):
                # GUARD: Never lock without explicit course signal
                extracted_courses = context.get("_entities", {}).get("courses", [])
                if not extracted_courses:
                    # Block lock - no explicit course mentioned
                    logger.info("[LOCK_GUARD] Blocking lock - no explicit course signal")
                    stage_control["should_lock"] = False
                    stage_control["reason"] = "no_explicit_course"
                else:
                    top_course = guidance_result.get("top_course")
                    if top_course:
                        # Use adaptive threshold based on interaction depth
                        from app.services.counselor.production_analytics import (
                            get_adaptive_threshold, track_decision, track_clarification
                        )
                        from app.services.counselor.confidence_gate import should_interrupt_for_confirmation
                    
                    adaptive_threshold = get_adaptive_threshold(session_id) if session_id else 0.75
                    
                    # Get decision confidence from stage controller
                    decision_confidence = context.get("_decision_confidence", 0.85)
                    
                    # CONTEXT-AWARE CONFIDENCE GATE
                    # Don't interrupt if user has action intent or multi-intent
                    should_interrupt, interrupt_reason = should_interrupt_for_confirmation(
                        query, decision_confidence, context
                    )
                    
                    if should_interrupt and decision_confidence < adaptive_threshold + 0.10:
                        # Ask for confirmation before locking (ONLY for short idle replies)
                        from app.services.counselor.decision_detector import generate_clarification
                        clarification = generate_clarification(query, {"top_course": top_course})
                        
                        # Store pending lock
                        context["_pending_lock_course"] = top_course
                        
                        # FAILURE CAPTURE: Mark awaiting clarification
                        context["awaiting_clarification"] = True
                        context["clarification_turn"] = context.get("turn_count", 0)
                        
                        # Track clarification
                        if session_id:
                            track_clarification(session_id, {
                                "query": query,
                                "confidence": decision_confidence,
                                "course": top_course,
                                "reason": interrupt_reason
                            })
                        
                        logger.info(f"[CONFIDENCE_GATE] Asking confirmation - reason: {interrupt_reason}")
                        
                        return {
                            "answer": clarification,
                            "mode": "clarification",
                            "intents": ["clarification"],
                            "confidence": decision_confidence
                        }
                    else:
                        # High confidence OR action intent - lock immediately
                        context = lock_decision(context, top_course)
                        
                        # FAILURE CAPTURE: Track locked_at for dropoff detection
                        context["locked_at"] = context.get("turn_count", 0)
                        
                        if session_id:
                            update_student_profile(session_id, {"locked_course": top_course}, increment_turn=False)
                            
                            # Track decision
                            track_decision(session_id, {
                                "query": query,
                                "confidence": decision_confidence,
                                "method": "stage_controller",
                                "course": top_course,
                                "locked": True,
                                "clarification_needed": False,
                                "skip_reason": interrupt_reason if not should_interrupt else None
                            })
                        
                        logger.info(f"[STAGE_LOCK] Course LOCKED: {top_course} (reason: {interrupt_reason})")

            
            # Legacy lock for backward compatibility
            elif context.get("conversion_stage") == "decision_confirmed" and not context.get("locked_course"):
                top_course = guidance_result.get("top_course")
                if top_course:
                    context["locked_course"] = top_course
                    if session_id:
                        update_student_profile(session_id, {"locked_course": top_course}, increment_turn=False)
                    logger.info(f"[LEGACY_LOCK] Course LOCKED: {top_course}")

            # ── GUIDANCE → ACTION BRIDGE ──
            # Trigger when engine flags decision_ready OR user text signals decision
            from app.services.counselor.conversion import (
                is_decision_ready, run_guidance_to_action, detect_decision_signal
            )
            text_signal = detect_decision_signal(query)
            engine_signal = is_decision_ready(guidance_result)

            if engine_signal or text_signal:
                bridge_response = run_guidance_to_action(guidance_result, context)
                context["bridge_stage"] = "action_offered"
                context["bridge_course"] = guidance_result.get("top_course", "")
                track_event("guidance_bridge_triggered", {
                    "session_id": session_id,
                    "course": context["bridge_course"],
                    "trigger": "engine" if engine_signal else "text",
                })
                return {
                    "answer": bridge_response,
                    "mode": "bridge",
                    "intents": ["guidance"],
                    "confidence": 1.0
                }

            # ── SOFT BRIDGE: marks only, no interest → ask clarifying question ──
            # Keeps momentum instead of dead-ending
            if guidance_result.get("soft_bridge_ready") and guidance_result.get("soft_bridge_question"):
                track_event("soft_bridge_triggered", {
                    "session_id": session_id,
                    "top_course": guidance_result.get("top_course"),
                })
                return {
                    "answer": guidance_result["soft_bridge_question"],
                    "mode": "soft_bridge",
                    "intents": ["guidance"],
                    "confidence": 0.9
                }

        elif intent == "compare":
            results["compare"] = run_comparator(query, context)
        elif intent == "career":
            results["career"] = run_career(query, context)
        elif intent == "constraint":
            results["constraint"] = run_constraint(query, context)
        elif intent == "life":
            results["life"] = run_life(query, context)
        elif intent == "unavailable":
            results["unavailable"] = run_unavailable(query, context)
        elif intent in ["about_aims", "why_aims", "aims_features"]:
            # NEW: Institution-level intents - route to structured knowledge
            structured_response = get_structured_response_for_intent(intent, query, context)
            if structured_response:
                return OrchestrationResult(
                    answer=structured_response.get("answer", ""),
                    intent=intent,
                    confidence=structured_response.get("confidence", 0.95),
                    mode="structured",
                    suggestions=structured_response.get("suggestions", []),
                    stage_control=stage_control
                )
            
    if not results:
        return None
        
    raw_answer = compose_response(results, query, context)
    intent_level = detect_intent_level(context, query)
    final_answer = apply_hybrid_behavior(raw_answer, context, intent_level)
    
    # Trust loop injection (every few turns conceptually, or conditionally)
    # Since we can't easily track exact turns here, we add it to 'mid' intents or when exploring
    if intent_level == "mid":
        final_answer += f"\n\n{trust_loop()}"
    
    # -------------------------
    # Flow & Momentum Layer
    # -------------------------
    # Try commitment escalation first
    follow_up = ask_commitment(context)
    if not follow_up:
        follow_up = smart_followup(context, intent_level)
    if not follow_up:
        follow_up = generate_follow_up(context, [i[0] for i in intents])
        
    # Rule 9 - High Exit After First Message (Hook Fix)
    if context.get("turn_count", 0) == 0:
        final_answer = "Before I suggest anything — what are you most confused about right now?\n\n" + final_answer
        
    final_answer = f"{final_answer}\n\n👉 {follow_up}"
    
    # -------------------------
    # Response Fatigue Log & Rule 3 (Length Control)
    # -------------------------
    words = final_answer.split()
    if len(words) > 150:
        track_event("long_response", {
            "session_id": session_id,
            "message_length": len(words)
        })
    if len(words) > 120:
        # Trim to roughly 120 words and add prompt
        trimmed_answer = " ".join(words[:120])
        final_answer = trimmed_answer + "...\n\nWant a quick summary or full details?"
        
    # -------------------------
    # Conversion Layer
    # -------------------------
            
    # 2. Hard push if explicit conversion intent
    if detect_conversion_intent(query):
        course_name = context.get("courses", [""])[0] if context.get("courses") else ""
        cta = guided_optional_close(course_name) if course_name else generate_cta(context)
        final_answer = f"{final_answer}\n\n🚀 {cta}"
        track_event("cta_shown", {
            "type": "hard_push",
            "courses": context.get("courses"),
            "session_id": session_id
        })
    else:
        # Passive conversion (soft push)
        if context.get("courses"):
            final_answer = inject_informed_timing(final_answer)
            track_event("cta_shown", {
                "type": "soft_push",
                "courses": context.get("courses"),
                "session_id": session_id
            })
            
    # Gentle followup instead of momentum trap
    gf = gentle_followup(context)
    if gf and not final_answer.strip().endswith("?"):
        final_answer += f"\n\n👉 {gf}"
            
    # -------------------------
    # System Tuning Application
    # -------------------------
    final_answer = apply_tuning(final_answer, context)
    
    # -------------------------
    # LLM Reinforcement Layer
    # -------------------------
    data_for_llm = {
        "conversion_stage": context.get("conversion_stage", "none"),
        "course": context.get("courses", [""])[0] if context.get("courses") else "unknown",
        "user_marks": context.get("marks", "unknown")
    }
    final_answer = reinforce_response(final_answer, data_for_llm, SYSTEM_TUNING)
    
    # -------------------------
    # Metrics & Loop Risk Logging
    # -------------------------
    similarity = calculate_similarity(final_answer, last_answer)
    progression = calculate_progression(old_context_snapshot, context, query)
    
    if similarity > 0.8:
        logger.warning(f"[LOOP RISK] Similarity={similarity:.2f} | turn={context.get('turn_count')} | query='{query}'")
    
    logger.info(f"[METRICS] similarity={similarity:.2f} | progression={progression:.2f} | turn={context.get('turn_count')}")
    
    # Store last answer for next turn similarity check
    context["last_answer"] = final_answer
    
    # Reset fallback counter on successful response (but NOT if we're in fallback mode)
    # This allows the counter to accumulate across consecutive fallbacks
    if stage_control.get("action") != "fallback":
        context["_consecutive_fallbacks"] = 0
    
    if session_id:
        update_student_profile(session_id, context, increment_turn=False)

    return {
        "answer": final_answer,
        "mode": "counselor",
        "intents": [i[0] for i in intents],
        "confidence": 0.95,
        "stage_control": stage_control,
        "metrics": {
            "similarity": similarity,
            "progression": progression
        }
    }

def run_counselor_pipeline(query: str, context: dict = None, session_id: str = None):
    # Retry and self-healing wrapper
    for i in range(2):
        try:
            # Only increment turn on the first attempt
            return _execute_counselor_pipeline(query, context, session_id, increment_turn=(i == 0))
        except Exception as e:
            logger.error(f"[COUNSELOR ENGINE CRASH] {e}")
            continue
            
    return {"answer": ultimate_fallback(), "mode": "fallback", "intents": ["error"], "confidence": 0.0}

# ===== MAIN ORCHESTRATION FUNCTION =====
def execute_orchestration(
    query: str,
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    session_id: str = None,
    context: dict = None
) -> OrchestrationResult:
    print("🔥 ORCHESTRATE FUNCTION CALLED")
    
    # ===== PHASE 1: INPUT VALIDATION =====
    is_valid, validation_msg = validate_query(query)
    if not is_valid:
        logger.warning(f"[VALIDATION] Query rejected: {validation_msg}")
        return OrchestrationResult(
            answer=validation_msg,
            intent="invalid_input",
            confidence=0.0,
            mode="fallback",
            fallback=True,
            suggestions=["What is AIMS?", "BCA fees", "Admission process"]
        )
    
    # ===== PHASE 1: WORD-LEVEL SYMSPELL CORRECTION =====
    corrected_query, original_query = correct_query_typos_word_level(query)
    working_query = corrected_query if corrected_query != original_query else query
    if corrected_query != original_query:
        logger.info(f"[TYPO_CORRECTION] '{original_query}' -> '{corrected_query}'")
    
    # Extract user course from context for intelligent matching
    user_course = (context or {}).get("course", "").strip()
    if user_course:
        logger.info(f"[USER_CONTEXT] User course: {user_course}")
    
    # Check if query mentions user's course - if so, boost confidence and avoid fallback
    query_mentions_user_course = False
    if user_course:
        # Normalize course names for matching
        course_variations = [
            user_course.lower(),
            user_course.upper(),
            user_course.replace(".", ""),
            user_course.lower().replace(".", "")
        ]
        query_lower = working_query.lower()
        query_mentions_user_course = any(var in query_lower for var in course_variations if var)
        if query_mentions_user_course:
            logger.info(f"[COURSE_MATCH] Query mentions user's course: {user_course}")
    
    if _is_out_of_domain(working_query):
        return OrchestrationResult(
            answer="I can only provide information about AIMS Institutes. Please contact that institution directly for your query.",
            intent="out_of_scope",
            confidence=0.0,
            mode="fallback",
            fallback=True,
            suggestions=["AIMS courses", "AIMS fees", "AIMS admission"]
        )
    
    intents, entities = parse_query(working_query)
    logger.info(f"[PARSED] intents={intents} | entities={entities}")
    
    REASONING_KEYWORDS = ['worth', 'better', 'compare', 'vs', 'versus', 'which is', 'which']
    if any(word in working_query.lower() for word in REASONING_KEYWORDS):
        intents = ['reasoning']
        logger.info("[REASONING_OVERRIDE] Detected reasoning intent")
    
    # ===== APPLY INTENT CHECK (HIGHEST PRIORITY) =====
    # Check if stage controller detects APPLY intent
    # This must run BEFORE structured/tool layers
    from app.services.counselor.stage_controller import execute_stage_control
    stage_check = execute_stage_control(working_query, context or {})
    
    if stage_check["stage"] == "apply":  # Check stage, not action
        # Stage controller says APPLY - execute immediately
        logger.info("[APPLY_PRIORITY] Stage controller detected APPLY - bypassing structured/tool layers")
        from app.services.counselor.conversion import run_next_step_info
        locked_course = (context or {}).get("locked_course")
        if not locked_course:
            # Extract course from entities
            locked_course = entities.get("course")
        
        if not locked_course:
            return OrchestrationResult(
                answer="Which course would you like to apply for? Let me know and I'll walk you through the steps.",
                intent="apply",
                confidence=1.0,
                mode="apply",
                fallback=False,
                suggestions=[]
            )
        
        answer = run_next_step_info(working_query, locked_course, context or {})
        return OrchestrationResult(
            answer=answer,
            intent="apply",
            confidence=1.0,
            mode="apply",
            fallback=False,
            suggestions=[]
        )
    
    # ===== UNIFIED MULTI-INTENT DETECTION (FIX: Detect ALL intents FIRST) =====
    # CRITICAL: Detect all significant intents BEFORE committing to any layer
    # This prevents early returns that skip secondary intents
    
    tool_intent, tool_score = detect_tool_intent(working_query)
    structured_intent, struct_score = detect_structured_intent(working_query)
    multi_intents = detect_multiple_intents(working_query)  # Get ALL structured intents
    
    logger.info(f"[ROUTING_UNIFIED] tool=({tool_intent}, {tool_score:.2f}) | struct=({structured_intent}, {struct_score:.2f}) | multi={[(i, f'{s:.2f}') for i, s in multi_intents]}")
    
    has_tool_intent = tool_intent and tool_score >= 0.3
    has_structured_intent = structured_intent and struct_score >= 0.4
    has_multiple_structured = len(multi_intents) > 1
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ROUTING LOGIC: Order of precedence:
    # 1. Multi-intent (2+ structured intents) → Process ALL in parallel
    # 2. Tool + Structured (both significant) → Hybrid response
    # 3. Tool only (dominates) → Tool response
    # 4. Single structured intent → Structured response
    # 5. Counselor pipeline (guidance, comparison, etc.)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # CASE 1: Multiple structured intents detected (e.g., "fees AND placements AND hostel")
    if has_multiple_structured:
        logger.info(f"[ROUTING] CASE 1: Multi-intent mode - {len(multi_intents)} intents")
        responses = []
        
        for intent, score in multi_intents:
            # Fetch response for each intent
            resp = get_structured_response_for_intent(intent, working_query, context)
            if resp and resp.get("answer"):
                # Build natural, flowing response (no bold labels if just 2-3 intents)
                if len(multi_intents) <= 3:
                    responses.append(resp["answer"])
                else:
                    responses.append(f"**{intent.upper()}:**\n{resp['answer']}")
        
        if responses:
            # Merge responses naturally
            combined_answer = "\n\n".join(responses)
            logger.info(f"[MULTI_INTENT_HANDLER] Combined {len(responses)} responses from {len(multi_intents)} intents")
            return OrchestrationResult(
                answer=combined_answer,
                intent="multi_intent",
                confidence=0.9,
                mode="structured",
                fallback=False,
                suggestions=[]
            )
    
    # CASE 2: Both tool and structured intents significant and close → Hybrid
    if has_tool_intent and has_structured_intent:
        score_diff = abs(tool_score - struct_score)
        
        # If one dominates by > 0.30, skip hybrid and go to CASE 3 or 4
        if struct_score > tool_score + 0.30:
            logger.info(f"[ROUTING] CASE 2 SKIP: Structured dominates ({struct_score:.2f} vs {tool_score:.2f})")
            # Fall through to CASE 4
        elif tool_score > struct_score + 0.30:
            logger.info(f"[ROUTING] CASE 2 SKIP: Tool dominates ({tool_score:.2f} vs {struct_score:.2f})")
            # Fall through to CASE 3
        else:
            # Both are close enough for hybrid
            logger.info(f"[ROUTING] CASE 2: Hybrid - tool={tool_intent} + struct={structured_intent}")
            
            struct_resp = get_structured_response_for_intent(structured_intent, working_query, context)
            tool_resp = get_conversational_tool_response(tool_intent, working_query)
            
            if tool_resp and struct_resp:
                # Merge: tool primary + structured secondary
                answer = tool_resp.answer
                struct_answer = struct_resp.get("answer", "")
                
                if struct_answer and struct_answer not in answer:
                    answer = answer.rstrip()
                    if not answer.endswith("\n"):
                        answer += "\n\n"
                    answer += f"📌 Additional details: {struct_answer}"
                
                return OrchestrationResult(
                    answer=answer,
                    intent=f"{structured_intent}+{tool_intent}",
                    confidence=0.95,
                    mode="hybrid",
                    fallback=False,
                    suggestions=struct_resp.get("suggestions", [])
                )
    
    # CASE 3: Tool intent only (or dominates structured)
    if has_tool_intent and tool_score > struct_score:
        logger.info(f"[ROUTING] CASE 3: Tool only - {tool_intent} ({tool_score:.2f})")
        tool_response = get_conversational_tool_response(tool_intent, working_query)
        if tool_response:
            return tool_response
    
    # CASE 4: Single structured intent (or structured dominates tool)
    if has_structured_intent:
        logger.info(f"[ROUTING] CASE 4: Single structured - {structured_intent} ({struct_score:.2f})")
        structured_response = get_structured_response_for_intent(structured_intent, working_query, context)
        if structured_response:
            return OrchestrationResult(
                answer=structured_response["answer"],
                intent=structured_response.get("intent", "structured"),
                confidence=structured_response.get("confidence", 0.9),
                mode=structured_response.get("mode", "structured"),
                fallback=False,
                suggestions=structured_response.get("suggestions", [])
            )
    
    # ===== PROGRAM FALLBACK INTENT =====
    # If no structured intent but program detected, treat as courses inquiry
    from app.services.structured_knowledge import get_program_intent
    program_intent, program_score = get_program_intent(working_query)
    if program_intent and program_score >= 0.7:
        logger.info(f"[PROGRAM_FALLBACK] Program detected, treating as '{program_intent}' intent")
        program_response = get_structured_response_for_intent(program_intent, working_query, context)
        if program_response:
            return OrchestrationResult(
                answer=program_response["answer"],
                intent=program_intent,
                confidence=program_score,
                mode="structured",
                fallback=False,
                suggestions=program_response.get("suggestions", []),
            )
    
    # ===== COUNSELOR LAYER (Guidance, Comparison, Career Advice) =====
    # Only called if structured/tool layers didn't handle the query
    # Pass the existing context to maintain continuity
    # Pass course matching flags through context for fallback logic
    context_with_course_flags = (context or {}).copy()
    context_with_course_flags["_query_mentions_user_course"] = query_mentions_user_course
    context_with_course_flags["_user_course"] = user_course
    
    counselor_response = run_counselor_pipeline(working_query, context=context_with_course_flags, session_id=session_id)
    if counselor_response:
        # Use mode from counselor pipeline (fallback, escalation, etc.) instead of hardcoding
        response_mode = counselor_response.get("mode", "counselor")
        is_fallback = response_mode in ["fallback", "blocked"]
        answer = counselor_response["answer"]
        
        # ═════════════════════════════════════════════════════════════════════════════
        # ENRICHED DATA INJECTION (MICRO FIX - STEP 3e) - Counselor Pipeline Response
        # If course is detected, append enrichment fields to counselor answer
        # ═════════════════════════════════════════════════════════════════════════════
        detected_course = entities.get("course") if entities else None
        if detected_course and answer:
            course_enrichment = _get_course_enrichment(detected_course)
            if course_enrichment:
                enrichment_block = _build_enrichment_block(course_enrichment)
                answer = answer + enrichment_block
                logger.info(f"[ENRICHMENT] Added decision-support fields to counselor response for {detected_course}")
        
        return OrchestrationResult(
            answer=answer,
            intent=counselor_response.get("intents", ["counselor"])[0] if counselor_response.get("intents") else "counselor",
            confidence=counselor_response["confidence"],
            mode=response_mode,
            fallback=is_fallback,
            suggestions=[],
            stage_control=counselor_response.get("stage_control", {})
        )
    
    # Proceed with RAG pipeline
    rag_query = _inject_course_context(working_query, entities)
    if not retrieved_chunks:
        try:
            index = get_index()
            if index and index.validate_integrity():
                rag_chunks = index.keyword_search(rag_query, k=25)
                logger.info(f"[RAG_RETRIEVAL] Retrieved {len(rag_chunks)} chunks for '{rag_query}'")
                rag_chunks = _rerank_chunks_by_topic(rag_chunks, query=rag_query, max_chunks=5)
                logger.info(f"[RERANK] After topic reranking: {len(rag_chunks)} chunks")
                rag_chunks = _filter_chunks_by_relevance(rag_chunks, query=rag_query, course=entities.get('course'), max_chunks=5)
                logger.info(f"[CHUNK_FILTER] After filtering: {len(rag_chunks)} relevant chunks")
                rag_chunks = filter_junk_chunks(rag_chunks, working_query)
                logger.info(f"[JUNK_FILTER] After junk filtering: {len(rag_chunks)} chunks")
                
                # FIX #1: Strict course filtering to prevent wrong data leakage
                if entities.get('course'):
                    course_lower = entities['course'].lower()
                    filtered_chunks = []
                    for chunk in rag_chunks:
                        chunk_text = ""
                        if isinstance(chunk, dict):
                            chunk_text = chunk.get('text', '').lower()
                        elif isinstance(chunk, tuple) and len(chunk) > 0:
                            chunk_text = str(chunk[0]).lower()
                        elif isinstance(chunk, str):
                            chunk_text = chunk.lower()
                        
                        if course_lower in chunk_text:
                            filtered_chunks.append(chunk)
                    
                    logger.info(f"[COURSE_FILTER] Filtered from {len(rag_chunks)} to {len(filtered_chunks)} chunks for course {entities['course']}")
                    rag_chunks = filtered_chunks
                
        except Exception as e:
            logger.warning(f"[RAG_RETRIEVAL] Failed: {e}")
            rag_chunks = []
    else:
        rag_chunks = retrieved_chunks
        # FIX #1: Also apply strict course filtering to provided chunks
        if retrieved_chunks and entities.get('course'):
            course_lower = entities['course'].lower()
            filtered_chunks = []
            for chunk in retrieved_chunks:
                chunk_text = ""
                if isinstance(chunk, dict):
                    chunk_text = chunk.get('text', '').lower()
                elif isinstance(chunk, tuple) and len(chunk) > 0:
                    chunk_text = str(chunk[0]).lower()
                elif isinstance(chunk, str):
                    chunk_text = chunk.lower()
                
                if course_lower in chunk_text:
                    filtered_chunks.append(chunk)
            
            logger.info(f"[COURSE_FILTER] Filtered from {len(retrieved_chunks)} to {len(filtered_chunks)} chunks for course {entities['course']}")
            rag_chunks = filtered_chunks
    
    confidence = _compute_rag_confidence(rag_chunks, intents, working_query)
    logger.info(f"[CONFIDENCE] score={confidence:.2f} | chunks={len(rag_chunks)} | intents={intents}")
    
    if confidence < CLARIFICATION_THRESHOLD:
        logger.info("[DECISION] Low confidence → clarification")
        return generate_clarification_response(working_query, intents)
    
    if has_meaningful_chunks(rag_chunks) and confidence >= CLARIFICATION_THRESHOLD:
        answer = format_rag_response(rag_chunks)
        if any(word in working_query.lower() for word in ['placement', 'salary', 'package', 'worth', 'better']):
            answer = _clean_rag_answer(answer, max_lines=7, max_chars=500)
        else:
            answer = _clean_rag_answer(answer, max_lines=5, max_chars=450)
        mode = "rag"
        logger.info(f"[DECISION] RAG mode: {len(rag_chunks)} chunks → answer (len={len(answer or '')})")
        
        # ═══════════════════════════════════════════════════════════════════════════
        # ENRICHED DATA INJECTION (MICRO FIX - STEP 3a) - RAG Mode
        # If course is detected, append enrichment fields
        # ═══════════════════════════════════════════════════════════════════════════
        detected_course = entities.get("course") if entities else None
        if detected_course and answer:
            course_enrichment = _get_course_enrichment(detected_course)
            if course_enrichment:
                enrichment_block = _build_enrichment_block(course_enrichment)
                answer = answer + enrichment_block
                logger.info(f"[ENRICHMENT] Added decision-support fields for {detected_course}")
        
        return OrchestrationResult(
            answer=answer,
            intent=intents[0] if intents else "general",
            confidence=confidence,
            mode=mode,
            fallback=False,
            suggestions=[],
        )
    
    if len(working_query.strip().split()) == 1 and entities.get("course"):
        course = entities.get("course").upper()
        answer = f"What would you like to know about {course}? I can help with:\n• Fees\n• Admission process\n• Course details\n• Placement record"
        
        # ═══════════════════════════════════════════════════════════════════════════
        # ENRICHED DATA INJECTION (MICRO FIX - STEP 3b) - Single Course Query
        # ═════════════════════════════════════════════════════════════════════════════
        course_enrichment = _get_course_enrichment(course)
        if course_enrichment:
            enrichment_block = _build_enrichment_block(course_enrichment)
            answer = answer + enrichment_block
            logger.info(f"[ENRICHMENT] Added decision-support fields for {course}")
        
        return OrchestrationResult(
            answer=answer,
            intent="courses",
            confidence=0.7,
            mode="structured",
            fallback=False,
            suggestions=[f"{course} fees", f"{course} admission", f"{course} placements"]
        )
    
    # Final fallback
    # CHECK: If query mentions user's course and we would fallback, provide course-specific response
    logger.info(f"[FALLBACK_CHECK] query_mentions_user_course={query_mentions_user_course}, user_course={user_course}")
    
    if query_mentions_user_course and user_course:
        course_specific = generate_course_specific_fallback(user_course, working_query)
        logger.info(f"[FALLBACK_CHECK] course_specific result: {course_specific[:100] if course_specific else 'None'}")
        
        if course_specific:
            logger.info(f"[COURSE_AWARE] User queried their course ({user_course}) - using course-specific fallback instead of generic")
            
            # ═════════════════════════════════════════════════════════════════════════════
            # ENRICHED DATA INJECTION (MICRO FIX - STEP 3c) - Course-Specific Fallback
            # ═════════════════════════════════════════════════════════════════════════════
            course_enrichment = _get_course_enrichment(user_course)
            if course_enrichment:
                enrichment_block = _build_enrichment_block(course_enrichment)
                course_specific = course_specific + enrichment_block
                logger.info(f"[ENRICHMENT] Added decision-support fields for {user_course}")
            
            result = OrchestrationResult(
                answer=course_specific,
                intent="courses",
                confidence=0.6,
                mode="counselor",
                fallback=False,
                suggestions=[f"{user_course} fees", f"{user_course} admission", f"{user_course} placements"]
            )
            return result
    
    course_info = f" about {entities.get('course', '').upper()}" if entities.get("course") else ""
    fallback_answer = (
        f"I can help you find information about our programs, fees, admission process, "
        f"placements, and campus facilities. What would you like to know{course_info}?"
    )
    logger.info("[DECISION] No RAG or structured match → fallback")
    
    # ═════════════════════════════════════════════════════════════════════════════
    # ENRICHED DATA INJECTION (MICRO FIX - STEP 3d) - Generic Fallback
    # If course is detected, append enrichment fields
    # ═════════════════════════════════════════════════════════════════════════════
    detected_course = entities.get("course") if entities else None
    if detected_course:
        course_enrichment = _get_course_enrichment(detected_course)
        if course_enrichment:
            enrichment_block = _build_enrichment_block(course_enrichment)
            fallback_answer = fallback_answer + enrichment_block
            logger.info(f"[ENRICHMENT] Added decision-support fields to fallback for {detected_course}")
    
    result = OrchestrationResult(
        answer=fallback_answer,
        intent=intents[0] if intents else "general",
        confidence=0.3,
        mode="fallback",
        fallback=True
    )
    result.suggestions = generate_smart_suggestions(
        working_query,
        result.intent,
        entities,
        history=None
    )
    result.suggestions = enforce_suggestion_guard(result.suggestions)
    logger.info(
        f"[ORCHESTRATION_COMPLETE] mode={result.mode} | confidence={result.confidence:.2f} | "
        f"intent={result.intent} | fallback={result.fallback}"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DEPLOYMENT LOGGING (CRITICAL FOR OBSERVATION PHASE)
    # Log the 4 critical fields for controlled deployment analysis
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        fallback_reason = None
        response_type = result.mode  # Use mode as response_type (structured, rag, fallback, etc.)
        
        if result.fallback:
            # Determine why fallback occurred
            if result.confidence < 0.6:
                fallback_reason = "low_confidence"
            elif result.mode == "fallback" and result.intent == "unknown":
                fallback_reason = "no_intent"
            elif result.mode == "fallback":
                fallback_reason = "routing_gap"
            else:
                fallback_reason = "unknown"
        
        # Build intent scores from parsed intents (if available)
        intent_scores = {}
        if intents:
            # intents is a list of tuples: [(intent_name, score), ...]
            for i, (intent_name, score) in enumerate(intents[:3]):  # Top 3
                intent_scores[intent_name] = float(score)
        
        # Extract matched keywords from entities
        matched_keywords = []
        if entities:
            # Collect all entity values that were found
            if entities.get("course"):
                matched_keywords.append(entities.get("course").lower())
            if entities.get("courses"):
                matched_keywords.extend([c.lower() for c in entities.get("courses", [])])
            # Add detected intents as matched keywords
            if result.intent and result.intent != "unknown":
                matched_keywords.append(result.intent)
        
        log_deployment_event(
            raw_query=query,  # Original query from user
            query=working_query,  # Query after typo correction
            intents=[result.intent] if result.intent else [],
            intent_scores=intent_scores,
            matched_keywords=list(set(matched_keywords)),  # Remove duplicates
            response=result.answer,
            response_type=response_type,  # How response was generated
            fallback=result.fallback,
            fallback_reason=fallback_reason,
            session_id=session_id,
            metadata={
                "confidence": result.confidence,
                "mode": result.mode,
                "course": entities.get("course") if entities else None
            }
        )
    except Exception as e:
        logger.error(f"[DEPLOYMENT_LOG_ERROR] Failed to log deployment event: {e}")
    
    return result

# ===== HELPER FUNCTIONS =====
def _is_out_of_domain(query: str) -> bool:
    out_of_domain = ["iit", "harvard", "mit", "stanford", "iim", "iisc", "google", "facebook"]
    query_lower = query.lower()
    return any(x in query_lower for x in out_of_domain)

def generate_smart_suggestions(query: str, intent: str, entities: Dict, history=None) -> List[str]:
    suggestions = []
    suggestion_map = {
        "fees": ["Fees", "Scholarships", "Payment Plans"],
        "admission": ["Admission Process", "Eligibility", "Documents Required"],
        "placement": ["Placement Stats", "Top Recruiters", "Salary Packages"],
        "course": ["Course Details", "Specializations", "Duration"],
        "reasoning": ["Compare Options", "Pros/Cons", "ROI Analysis"],
        "location": ["Campus Map", "Directions", "Virtual Tour"],
        "contact": ["Phone", "Email", "Office Hours"]
    }
    if intent in suggestion_map:
        suggestions.extend(suggestion_map[intent])
    if not suggestions:
        suggestions = ["Fees", "Admission Process", "Placement Stats", "Course Details"]
    return suggestions[:4]

def enforce_suggestion_guard(suggestions: List[str]) -> List[str]:
    if not suggestions or len(suggestions) < 2:
        return ["Fees", "Admission Process", "Placement Stats", "Course Details"]
    return suggestions[:4]

def _clean_rag_answer(answer: str, max_lines: int = 5, max_chars: int = 450) -> str:
    lines = answer.split('\n')
    limited_lines = lines[:max_lines]
    limited_text = '\n'.join(limited_lines)
    if len(limited_text) > max_chars:
        limited_text = limited_text[:max_chars-3] + "..."
    return limited_text

# ===== EXISTING FUNCTIONS (placeholder for rest of the original functions) =====
# These functions need to be imported or defined elsewhere:
# - get_index()
# - _rerank_chunks_by_topic()
# - _filter_chunks_by_relevance()
# - filter_junk_chunks()