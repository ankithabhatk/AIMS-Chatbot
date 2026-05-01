"""
Counselor Layer - Handles exploratory and guidance queries.

This module provides conversational guidance for students who are:
- Exploring career options ("I like coding, what should I choose?")
- Unsure about their path ("I'm not sure what to study")
- Seeking recommendations ("What's best for me?")
- Comparing programs ("BCA or BBA?")

Instead of info dumps, provides guided, conversational responses.
"""

import re
import logging
from typing import Optional, Dict, List, Any
from app.services.conversation_memory import (
    get_memory_store, 
    extract_user_profile, 
    UserProfile, 
    should_force_counselor, 
    build_memory_context,
    is_decision_query,
    build_final_recommendation,
)
from app.services.retrieval.hybrid_retriever import get_hybrid_retriever
from app.services.llm.provider import get_llm_provider

logger = logging.getLogger(__name__)


def adjust_tone(profile: UserProfile) -> str:
    """Adjust tone based on user's confidence level.
    
    Returns:
    - "supportive" for low confidence (slower, more questions, reassuring)
    - "normal" for medium/high confidence (balanced/direct)
    
    Args:
        profile: UserProfile with confidence_level
        
    Returns:
        str: "supportive" or "normal"
    """
    if profile.confidence_level == "low":
        return "supportive"
    else:
        return "normal"


def should_force_decision(query: str) -> bool:
    """
    Detect if user is explicitly requesting a decision.
    
    Decision signals: "what should i do", "what do you recommend", 
                     "suggest", "final advice", "what should i choose"
    
    This is CRITICAL for preventing the system from staying in exploratory mode
    indefinitely when the user is ready for guidance.
    
    Args:
        query: Current user query
        
    Returns:
        bool: True if explicit decision request detected
    """
    q = query.lower()
    
    decision_signals = [
        "what should i do",
        "what do you recommend",
        "what do you suggest",
        "suggest me",
        "recommend me",
        "what should i choose",
        "which one should i",
        "what's your recommendation",
        "what would you recommend",
        "help me decide",
        "final advice",
        "what's best",
        "which is best",
    ]
    
    return any(signal in q for signal in decision_signals)


def is_exploratory_query(query: str) -> bool:
    """Detect if query is exploratory/guidance-seeking.
    
    Returns True for:
    - Career exploration ("I like coding")
    - Uncertainty ("not sure what to study")
    - Recommendation requests ("what should I choose")
    - Program comparisons ("BCA or BBA")
    - Constraint-based queries ("weak in math but like coding")
    
    PRIORITY: Constraint signals override other intent detection.
    """
    q = query.lower()
    
    # Constraint signals (HIGHEST PRIORITY - P2 fix)
    # These indicate student needs counseling, not just facts
    constraint_signals = [
        "weak in", "not good at", "bad at", "struggle with",
        "poor at", "not great at", "difficulty with",
        "but i", "however i", "although i",
        "confused", "not sure", "don't know",
        "hate", "dislike", "don't like", "not interested in", "boring",
    ]
    
    # Check for constraint signals FIRST (highest priority)
    for signal in constraint_signals:
        if signal in q:
            return True
    
    # Exploratory signals
    exploratory_signals = [
        "i like", "i love", "i enjoy", "i'm interested in",
        "i want to", "i'm good at", "my passion",
        "help me choose",
        "what should i", "which is better for me", "recommend",
        "best for me", "suitable for me", "right for me",
        "career", "future", "job opportunities",
    ]
    
    # Program comparison signals (internal AIMS programs)
    program_comparison_signals = [
        "bca or bba", "bba or bca",
        "mba or mca", "mca or mba",
        "bca vs bba", "bba vs bca",
        "difference between bca and bba",
        "which course", "which program",
    ]
    
    # Check for exploratory signals
    for signal in exploratory_signals:
        if signal in q:
            return True
    
    # Check for program comparisons
    for signal in program_comparison_signals:
        if signal in q:
            return True
    
    # Pattern: "I [verb] [interest area]"
    interest_patterns = [
        r"\bi\s+(like|love|enjoy|want)\s+\w+",
        r"\bi'm\s+(interested|good)\s+",
        r"\bmy\s+(passion|interest)\s+",
    ]
    
    for pattern in interest_patterns:
        if re.search(pattern, q):
            return True
    
    return False
    return False


def get_counselor_response(query: str, session_id: Optional[str] = None, query_data: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
    """Generate guided counselor response for exploratory queries.

    Uses session memory to combine signals across multiple turns.
    
    NEW: Decision Synthesis Layer
    - If user has accumulated profile (interests + constraints + goals)
    - AND query is decision-type ("what should I do", "recommend", etc.)
    - THEN provide final recommendation with reasoning

    Returns None if not an exploratory query.
    Returns dict with answer, intent, confidence if exploratory.
    """
    # Get or create session profile
    memory = get_memory_store()
    profile = memory.get_profile(session_id) if session_id else UserProfile()

    # Extract new signals from this query and update profile
    new_signals = extract_user_profile(query, profile)
    if session_id:
        profile = memory.update_profile(session_id, new_signals)

    # DECISION SYNTHESIS: Check if this is a decision query with sufficient profile
    # CRITICAL: Check both is_decision_query AND should_force_decision
    # should_force_decision overrides uncertainty handling
    force_decision = should_force_decision(query)
    
    if (is_decision_query(query) or force_decision) and profile.interests:
        final_recommendation = build_final_recommendation(profile, query, force=force_decision)
        if final_recommendation:
            return {
                "answer": final_recommendation,
                "intent": "counselor_decision_synthesis",
                "confidence": profile.confidence_score,
                "mode": "counselor",
                "sources": [{"title": "Career Guidance", "url": "https://www.theaims.ac.in"}],
            }

    # Check if this should be counselor mode
    # CRITICAL: If profile has ANY signals, stay in counselor mode (don't return None)
    has_profile = bool(profile.interests or profile.constraints or profile.goals or profile.ambiguity_signals)
    
    if not is_exploratory_query(query) and not should_force_counselor(profile, query) and not has_profile:
        return None

    q = query.lower()

    # Detect interest area
    interest_area = _detect_interest_area(q)

    # Build memory context for adaptive responses
    memory_context = build_memory_context(profile) if session_id else ""

    # PRIMARY RESPONSE: Try Qwen RAG Synthesis
    llm_result = _synthesize_counselor_with_llm(query, profile, memory_context, query_data, interest_area)
    if llm_result:
        return llm_result

    # FALLBACK RESPONSE: Use rigid templates if Qwen fails or is unavailable
    logger.warning("LLM Synthesis failed or unavailable. Falling back to rigid templates.")
    if interest_area == "coding":
        return _handle_coding_interest(q, profile, memory_context)
    elif interest_area == "business":
        return _handle_business_interest(q, profile, memory_context)
    elif interest_area == "management":
        return _handle_management_interest(q, profile, memory_context)
    elif interest_area == "hospitality":
        return _handle_hospitality_interest(q, profile, memory_context)
    elif interest_area == "commerce":
        return _handle_commerce_interest(q, profile, memory_context)
    elif interest_area == "program_comparison":
        return _handle_program_comparison(q, profile, memory_context)
    else:
        return _handle_general_exploration(q, profile, memory_context)

def _synthesize_counselor_with_llm(
    query: str, 
    profile: UserProfile, 
    memory_context: str, 
    query_data: Optional[Dict[str, Any]],
    interest_area: str
) -> Optional[Dict]:
    """Primary synthesis layer using RAG + Qwen"""
    try:
        # Retrieve facts if query_data is provided
        retrieved_context = []
        sources = []
        if query_data:
            retriever = get_hybrid_retriever()
            # Fast synchronous retrieve for counselor context
            results = retriever.search(query_data, 5, 5, 5)
            chunks = retriever.to_chunk_tuples(results)
            seen_texts = set()
            for chunk in chunks[:4]:  # Top 4 chunks
                text = chunk[0].strip()
                distance = chunk[1]
                
                # Filter noise and exact duplicates
                if distance > 1.2 or text in seen_texts:
                    continue
                    
                seen_texts.add(text)
                retrieved_context.append(f"• {text}")
                if chunk[2]:  # URL
                    sources.append({"title": chunk[3] or "AIMS Info", "url": chunk[2]})
                    
        # Remove duplicates from sources
        unique_sources = {s["url"]: s for s in sources}.values()
        
        context_str = "\n".join(retrieved_context) if retrieved_context else "No specific program documentation retrieved."
        
        provider = get_llm_provider()

        # Generate lightweight reflection
        reflection_summary = _generate_reflection(profile, query)

        # Build dynamic prompt optimized for TinyLlama
        system_prompt = f"""You are a helpful AIMS College counselor.
Keep answers extremely short (1-3 sentences max).
End with exactly ONE simple question.
Do not over-explain. Do not sound like a robot.

STUDENT PROFILE:
Interests: {', '.join(profile.interests) if profile.interests else 'None'}
Confidence: {profile.confidence_level.upper()}
Note: {reflection_summary}

FACTS:
{context_str}

Respond directly to the user like a human."""

        response_text, provider_used = provider.generate_response(
            query=query,
            context=[], # Context already in system_prompt
            system_prompt=system_prompt
        )
        
        if not response_text or len(response_text) < 5:
            return None
            
        return {
            "answer": response_text,
            "intent": f"counselor_{interest_area}",
            "confidence": profile.confidence_score,
            "mode": "counselor",
            "provider": provider_used,
            "reflection": reflection_summary,
            "sources": list(unique_sources)
        }
    except Exception as e:
        logger.error(f"LLM Counselor synthesis failed: {e}")
        return None

def _generate_reflection(profile: UserProfile, query: str) -> str:
    """Generate a lightweight emotional interpretation based on profile state."""
    reflections = []
    
    # Emotional interpretations
    if "frustration" in profile.recent_emotions:
        reflections.append("Student is frustrated. Validate their struggle patiently.")
    if "fear" in profile.recent_emotions or "insecurity" in profile.recent_emotions:
        reflections.append("Student is exhibiting fear or insecurity. Be extra encouraging and remove pressure.")
    if "curiosity" in profile.recent_emotions:
        reflections.append("Student is curious. Reward exploration with interesting facts.")
    if "avoidance" in profile.recent_emotions:
        reflections.append("Student is avoiding certain paths. Don't force them; pivot smoothly.")
        
    # Contradiction reflection
    q_lower = query.lower()
    if any(kw in q_lower for kw in ["actually", "wait", "hate", "don't like", "instead"]):
        reflections.append("Student is pivoting or contradicting a previous interest. Support the pivot naturally.")
        
    # Interest ranking (top 2 by importance)
    if profile.interest_importance:
        sorted_interests = sorted(profile.interest_importance.items(), key=lambda x: x[1], reverse=True)
        top_interests = [k for k, v in sorted_interests[:2] if v >= 1.0]
        if top_interests:
            reflections.append(f"Strongest underlying interests seem to be: {', '.join(top_interests)}.")

    if not reflections:
        return "Student is in a standard exploratory state. Proceed naturally."
        
    return " ".join(reflections)


def _detect_interest_area(query: str) -> str:
    """Detect student's interest area from query."""
    q = query.lower()
    
    # Check for avoidance (if they hate it, don't route to that interest)
    avoidance_signals = ["hate", "dislike", "don't like", "not interested in", "boring"]
    if any(signal in q for signal in avoidance_signals):
        return "general"
    
    # Coding/tech signals
    coding_signals = ["coding", "programming", "software", "tech", "computer", "app", "website", "developer"]
    if any(signal in q for signal in coding_signals):
        return "coding"
    
    # Business signals
    business_signals = ["business", "entrepreneur", "startup", "company", "sales", "marketing"]
    if any(signal in q for signal in business_signals):
        return "business"
    
    # Management signals
    management_signals = ["management", "mba", "manager", "leadership", "corporate"]
    if any(signal in q for signal in management_signals):
        return "management"
    
    # Hospitality signals
    hospitality_signals = ["hotel", "hospitality", "tourism", "restaurant", "chef", "culinary"]
    if any(signal in q for signal in hospitality_signals):
        return "hospitality"
    
    # Commerce signals
    commerce_signals = ["commerce", "accounting", "finance", "banking", "taxation"]
    if any(signal in q for signal in commerce_signals):
        return "commerce"
    
    # Program comparison
    if any(word in q for word in ["or", "vs", "versus", "difference between", "which course", "which program"]):
        return "program_comparison"
    
    return "general"


def _handle_coding_interest(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    """Handle coding/tech interest queries with constraint awareness.

    Uses accumulated profile from multiple turns for adaptive responses.
    """
    # Check for constraints from profile (accumulated across turns)
    has_math_constraint = (
        any("math" in c for c in profile.constraints) or
        any(term in query for term in ["weak in math", "not good at math", "bad at math", "poor at math", "struggle with math"])
    )
    has_study_constraint = (
        any("stud" in c or "student" in c or "grade" in c for c in profile.constraints) or
        any(term in query for term in ["not great at studies", "not good at studies", "weak student", "poor grades"])
    )
    has_salary_concern = (
        any("salary" in g or "pay" in g or "money" in g for g in profile.goals) or
        any(term in query for term in ["salary", "package", "money", "pay", "earning"])
    )
    has_parental_pressure = "parental_pressure" in profile.constraints

    # P2 FIX: Salary + constraint = counselor mode (not placement facts)
    if has_salary_concern and (has_study_constraint or has_math_constraint):
        answer = (
            "Honest answer: BCA can lead to good salaries, but it requires consistent effort.\n\n"
            "**Reality check:**\n"
            "• BCA (3 years) → Entry packages: ₹3-8 LPA\n"
            "  - Good if: You're okay with steady effort\n"
            "  - Challenge: Need to build coding skills consistently\n\n"
            "• BCA → MCA (3+2 years) → Higher packages: ₹6-16 LPA\n"
            "  - Good if: You're willing to invest more time\n"
            "  - Challenge: More academic rigor\n\n"
            "**Key insight:**\n"
            "Interest matters more than grades. If you genuinely like coding, you'll find the motivation to push through.\n\n"
            "**Trade-off:**\n"
            "• Want quick job + decent salary → BCA (but need consistent effort)\n"
            "• Want higher salary + deeper skills → BCA+MCA (but longer path)\n\n"
            "**Let me ask you:**\n"
            "Are you more interested in getting a job quickly or building deep expertise?"
        )
    elif has_parental_pressure:
        # NEW: Handle conflict between parents' wishes and user's interest
        answer = (
            "This is a common situation — and it's totally normal to feel torn. 💭\n\n"
            "**Let me break this down honestly:**\n\n"
            "**Your parents' perspective:**\n"
            "• They likely see MBA as \"safe\" or \"prestigious\"\n"
            "• They want stability and good career prospects for you\n"
            "• They may not fully understand the tech industry\n\n"
            "**Your perspective:**\n"
            "• You're genuinely interested in tech/coding\n"
            "• You want to work in something you enjoy\n"
            "• Forcing MBA when you love tech → burnout risk\n\n"
            "**Reality check:**\n"
            "• BCA → MCA can lead to ₹6-16 LPA (same or better than many MBAs)\n"
            "• Tech industry values skills over degrees\n"
            "• You can always do MBA later if needed (executive MBA while working)\n\n"
            "**My suggestion:**\n"
            "Have an open conversation with your parents about:\n"
            "• Your genuine interest in coding\n"
            "• Real salary data from BCA/MCA grads\n"
            "• The option to do MBA later if you want\n\n"
            "**What's the main concern your parents have?** I can help you address it."
        )
    elif has_math_constraint:
        answer = (
            "BCA is manageable even if you're weak in math — but here's the honest picture:\n\n"
            "**What you WON'T face:**\n"
            "• Heavy calculus or engineering-level math\n"
            "• Complex mathematical proofs\n\n"
            "**What you WILL need:**\n"
            "• Basic logic and problem-solving (this improves with coding practice)\n"
            "• Discrete math (sets, logic, basic probability)\n"
            "• Statistics basics (for data handling)\n\n"
            "Most students improve these over time — especially through hands-on coding.\n\n"
            "**Real talk:**\n"
            "• If you enjoy building apps/websites → you're fine\n"
            "• If you struggle with logic puzzles → you'll need extra effort\n"
            "• Math-heavy areas like data science → avoid initially\n\n"
            "So yes — you can take BCA, just don't expect it to be \"zero math\".\n\n"
            "**Let me ask you:**\n"
            "Do you enjoy hands-on coding (apps/web) or more theoretical learning?"
        )
    elif has_study_constraint:
        answer = (
            "Honest answer: BCA requires consistent effort, but it's very doable if you're interested in coding.\n\n"
            "**Trade-offs:**\n"
            "• BCA (3 years) → Faster entry into jobs (₹3-8 LPA)\n"
            "  - Good if: You want practical skills and quick job\n"
            "  - Challenge: Need to stay consistent with coursework\n\n"
            "• BCA → MCA (3+2 years) → Higher packages (₹6-16 LPA)\n"
            "  - Good if: You're willing to go deeper\n"
            "  - Challenge: More academic rigor\n\n"
            "**Key insight:**\n"
            "Interest matters more than grades. If you genuinely like coding, you'll find the motivation.\n\n"
            "**Let me ask you:**\n"
            "Do you want a job quickly (BCA) or are you okay with longer study (BCA+MCA)?"
        )
    else:
        # Standard response
        answer = (
            "Nice — coding is a great direction! 👨‍💻\n\n"
            "**You have 2 main paths at AIMS:**\n\n"
            "**1. BCA (Bachelor of Computer Applications)** - 3 years\n"
            "• Faster entry into tech jobs\n"
            "• Learn: Programming, Web Development, Database, Software Engineering\n"
            "• Good for: Getting a job quickly as a developer\n"
            "• Placements: ₹3-8 LPA in companies like TCS, Infosys, Wipro\n\n"
            "**2. BCA → MCA** - 3+2 years\n"
            "• Deeper specialization in computer science\n"
            "• Learn: Advanced algorithms, AI/ML, Cloud Computing, System Design\n"
            "• Good for: Higher packages, senior roles, research\n"
            "• Placements: ₹6-16 LPA in product companies\n\n"
            "**Let me ask you:**\n"
            "Do you want to get a job quickly (BCA) or go deep into tech (BCA+MCA)?\n\n"
            "I can also tell you about:\n"
            "• BCA curriculum and projects\n"
            "• Placement companies and packages\n"
            "• Eligibility and admission process"
        )
    
    return {
        "answer": answer,
        "intent": "counselor_coding",
        "confidence": profile.confidence_score,
        "mode": "counselor",
        "sources": [{"title": "BCA Program", "url": "https://www.theaims.ac.in/bca"}],
    }


def _handle_business_interest(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    """Handle business/entrepreneurship interest queries."""

    has_salary_concern = any("salary" in g or "pay" in g for g in profile.goals) or any(term in query for term in ["salary", "package", "money"])
    has_study_constraint = any("study" in c or "grade" in c for c in profile.constraints)

    if has_salary_concern and has_study_constraint:
        answer = (
            "Honest answer: BBA can lead to good careers, but it depends on your approach.\n\n"
            "**Reality check:**\n"
            "• BBA (3 years) → Entry roles: ₹3-6 LPA\n"
            "  - Good if: You want to start working quickly\n"
            "  - Challenge: Need to build practical skills alongside degree\n\n"
            "• BBA → MBA (3+2 years) → Higher packages: ₹6-16 LPA\n"
            "  - Good if: You're willing to invest more time\n"
            "  - Challenge: More academic rigor\n\n"
            "**Key insight:**\n"
            "Business is about skills + network, not just grades.\n\n"
            "**Let me ask you:**\n"
            "Are you thinking of starting your own business or working in a company first?"
        )
    else:
        answer = (
        "Great — business is an exciting path! 🚀\n\n"
        "**You have 2 main paths at AIMS:**\n\n"
        "**1. BBA (Bachelor of Business Administration)** - 3 years\n"
        "• Foundation in business management\n"
        "• Learn: Marketing, Finance, HR, Operations, Entrepreneurship\n"
        "• Good for: Starting your career in business roles\n"
        "• Placements: ₹3-6 LPA in sales, marketing, HR roles\n\n"
        "**2. BBA → MBA** - 3+2 years\n"
        "• Advanced business leadership skills\n"
        "• Learn: Strategy, Leadership, Business Analytics, Corporate Management\n"
        "• Good for: Management positions, higher packages, entrepreneurship\n"
        "• Placements: ₹6-16 LPA in management roles\n\n"
        "**Let me ask you:**\n"
        "Are you thinking of starting your own business or working in a company first?\n\n"
        "I can also tell you about:\n"
        "• BBA specializations and curriculum\n"
        "• Entrepreneurship support at AIMS\n"
        "• Placement companies and roles"
    )
    
    return {
        "answer": answer,
        "intent": "counselor_business",
        "confidence": profile.confidence_score,
        "mode": "counselor",
        "sources": [{"title": "BBA Program", "url": "https://www.theaims.ac.in/bba"}],
    }


def _handle_management_interest(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    """Handle management/MBA interest queries."""

    answer = (
        "Management is a strong choice! 📊\n\n"
        "**MBA at AIMS** - 2 years\n"
        "• Eligibility: Graduation with 50%+ marks\n"
        "• Entrance: CAT, MAT, ATMA, CMAT accepted\n"
        "• Specializations: Finance, Marketing, HR, Business Analytics\n"
        "• Placements: ₹6-16 LPA (highest: ₹27 LPA)\n\n"
        "**What makes AIMS MBA different:**\n"
        "• Industry-integrated curriculum with live projects\n"
        "• 300+ corporate tie-ups for internships\n"
        "• Focus on practical skills, not just theory\n"
        "• Located in Bangalore - India's business hub\n\n"
        "**Let me ask you:**\n"
        "Which specialization interests you most — Finance, Marketing, HR, or Analytics?\n\n"
        "I can also tell you about:\n"
        "• MBA admission process and entrance exams\n"
        "• Specialization details and career paths\n"
        "• Fees and scholarship options"
    )
    
    return {
        "answer": answer,
        "intent": "counselor_management",
        "confidence": profile.confidence_score,
        "mode": "counselor",
        "sources": [{"title": "MBA Program", "url": "https://www.theaims.ac.in/mba"}],
    }


def _handle_hospitality_interest(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    """Handle hospitality/hotel management interest queries."""

    answer = (
        "Hospitality is a dynamic industry! 🏨\n\n"
        "**BHM (Bachelor of Hotel Management)** at AIMS - 3 years\n"
        "• Learn: Hotel Operations, Food & Beverage, Front Office, Housekeeping\n"
        "• Practical training in AIMS's own training facilities\n"
        "• Industry internships in 5-star hotels\n"
        "• Career paths: Hotel Manager, Restaurant Manager, Event Manager, Chef\n\n"
        "**What makes BHM special:**\n"
        "• Hands-on training, not just theory\n"
        "• Bangalore has a booming hospitality industry\n"
        "• Placements in hotels, resorts, airlines, cruise lines\n"
        "• Opportunity to work globally\n\n"
        "**Let me ask you:**\n"
        "Are you more interested in hotel operations, culinary arts, or event management?\n\n"
        "I can also tell you about:\n"
        "• BHM curriculum and training facilities\n"
        "• Placement companies and packages\n"
        "• Eligibility and admission process"
    )
    
    return {
        "answer": answer,
        "intent": "counselor_hospitality",
        "confidence": profile.confidence_score,
        "mode": "counselor",
        "sources": [{"title": "BHM Program", "url": "https://www.theaims.ac.in/bhm"}],
    }


def _handle_commerce_interest(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    """Handle commerce/accounting interest queries."""

    answer = (
        "Commerce is a solid foundation! 💼\n\n"
        "**You have 2 main paths at AIMS:**\n\n"
        "**1. B.Com (Bachelor of Commerce)** - 3 years\n"
        "• Learn: Accounting, Finance, Taxation, Business Law\n"
        "• Good for: CA/CMA preparation, banking, accounting jobs\n"
        "• Career paths: Accountant, Tax Consultant, Financial Analyst\n\n"
        "**2. B.Com → M.Com** - 3+2 years\n"
        "• Advanced specialization in commerce\n"
        "• Good for: Teaching, research, higher positions\n"
        "• Career paths: Professor, Financial Manager, Research Analyst\n\n"
        "**Let me ask you:**\n"
        "Are you planning to pursue CA/CMA alongside B.Com, or focus on placements?\n\n"
        "I can also tell you about:\n"
        "• B.Com curriculum and specializations\n"
        "• Support for CA/CMA preparation\n"
        "• Placement companies and packages"
    )
    
    return {
        "answer": answer,
        "intent": "counselor_commerce",
        "confidence": profile.confidence_score,
        "mode": "counselor",
        "sources": [{"title": "B.Com Program", "url": "https://www.theaims.ac.in/bcom"}],
    }


def _handle_program_comparison(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    """Handle internal program comparison queries (BCA vs BBA, etc.).

    Uses profile to give personalized comparison based on user's interests and constraints.
    """
    q = query.lower()
    
    # BCA vs BBA
    if ("bca" in q and "bba" in q) or ("computer" in q and "business" in q):
        answer = (
            "Great question — BCA and BBA are very different paths! 🎯\n\n"
            "**BCA (Computer Applications):**\n"
            "• For: Students who like coding and technology\n"
            "• Learn: Programming, Web Development, Database, Software\n"
            "• Career: Software Developer, Web Developer, System Analyst\n"
            "• Packages: ₹3-8 LPA (tech companies)\n\n"
            "**BBA (Business Administration):**\n"
            "• For: Students who like business, management, people skills\n"
            "• Learn: Marketing, Finance, HR, Operations, Entrepreneurship\n"
            "• Career: Sales Manager, Marketing Executive, HR Manager\n"
            "• Packages: ₹3-6 LPA (business roles)\n\n"
            "**Quick decision guide:**\n"
            "• Like coding/tech? → BCA\n"
            "• Like business/people? → BBA\n"
            "• Want to start a tech company? → BCA first, then MBA\n"
            "• Want to start a business? → BBA first, then MBA\n\n"
            "Which one sounds more like you?"
        )
        intent = "counselor_bca_vs_bba"
    
    # MBA vs MCA
    elif ("mba" in q and "mca" in q):
        answer = (
            "MBA and MCA serve different career goals! 🎯\n\n"
            "**MCA (Computer Applications):**\n"
            "• For: Students with tech background (BCA/B.Sc) who want to go deeper\n"
            "• Learn: Advanced programming, AI/ML, Cloud, System Design\n"
            "• Career: Senior Developer, Tech Lead, System Architect\n"
            "• Packages: ₹6-16 LPA (tech roles)\n\n"
            "**MBA (Business Administration):**\n"
            "• For: Anyone who wants to move into management\n"
            "• Learn: Strategy, Leadership, Business Analytics, Management\n"
            "• Career: Manager, Business Analyst, Product Manager\n"
            "• Packages: ₹6-16 LPA (management roles)\n\n"
            "**Quick decision guide:**\n"
            "• Want to stay in tech and code? → MCA\n"
            "• Want to manage teams and projects? → MBA\n"
            "• Want to become CTO? → MCA first\n"
            "• Want to become CEO? → MBA first\n\n"
            "What's your career goal — technical expert or business leader?"
        )
        intent = "counselor_mba_vs_mca"
    
    else:
        # Generic program comparison
        answer = (
            "I can help you compare AIMS programs! 🎯\n\n"
            "**At AIMS, we offer:**\n"
            "• **Tech path**: BCA, MCA (for coding/software)\n"
            "• **Business path**: BBA, MBA (for management/entrepreneurship)\n"
            "• **Commerce path**: B.Com, M.Com (for accounting/finance)\n"
            "• **Hospitality path**: BHM (for hotel/tourism industry)\n\n"
            "**To help you choose, tell me:**\n"
            "• What are you interested in? (tech, business, finance, hospitality)\n"
            "• What's your current education level? (12th, graduation)\n"
            "• What kind of career do you see yourself in?\n\n"
            "I can then give you a detailed comparison!"
        )
        intent = "counselor_program_comparison"
    
    return {
        "answer": answer,
        "intent": intent,
        "confidence": profile.confidence_score,
        "mode": "counselor",
        "sources": [{"title": "AIMS Programs", "url": "https://www.theaims.ac.in"}],
    }


def build_progressive_response(profile: UserProfile, query: str) -> str:
    """
    Build progressive response that always references accumulated profile.
    
    NEVER returns generic greetings when profile exists.
    ALWAYS summarizes known signals.
    ALWAYS adds one step forward.
    
    NEW (Task 4.3): Adjusts tone based on confidence level.
    - Low confidence: Adds reassuring language, asks more questions, avoids strong recommendations
    - Normal/High confidence: Provides balanced guidance
    
    Logic:
    - If profile has interests: Acknowledge them ("You've mentioned: {interests}")
    - If profile has constraints: Acknowledge them ("You're dealing with: {constraints}")
    - If profile has goals: Acknowledge them ("You want: {goals}")
    - Always add forward step: "So let's narrow this down..."
    
    Args:
        profile: UserProfile with accumulated signals
        query: Current user query
        
    Returns:
        str: Progressive response building on known context
    """
    parts = []
    
    # Check confidence level and adjust tone (Task 4.3)
    tone = adjust_tone(profile)
    
    # Add reassuring language for low confidence users (Task 4.3)
    if tone == "supportive":
        parts.append("It's okay to be unsure — we can figure this out step by step. 💭")
        parts.append("")
    
    # Start by acknowledging what we know (not generic greeting)
    if profile.interests:
        interests_list = ', '.join(profile.interests)
        parts.append(f"You've mentioned: {interests_list}.")
    
    if profile.constraints:
        constraint_list = []
        for c in profile.constraints:
            if "math" in c:
                constraint_list.append("weak in math")
            elif "stud" in c or "grade" in c:
                constraint_list.append("not strong in studies")
            elif "parental_pressure" in c:
                constraint_list.append("parental pressure")
            elif "budget" in c:
                constraint_list.append("budget constraints")
            elif "time" in c:
                constraint_list.append("time constraints")
            else:
                # Generic constraint display
                readable = c.replace("_", " ")
                constraint_list.append(readable)
        if constraint_list:
            parts.append(f"You're dealing with: {', '.join(constraint_list)}.")
    
    if profile.goals:
        goal_list = []
        for g in profile.goals:
            if "salary" in g:
                goal_list.append("good salary")
            elif "quick" in g:
                goal_list.append("quick job")
            elif "stable" in g:
                goal_list.append("stable career")
            elif "higher_studies" in g:
                goal_list.append("higher studies")
            elif "entrepreneurship" in g:
                goal_list.append("start your own business")
            else:
                # Generic goal display
                readable = g.replace("goal_", "").replace("_", " ")
                goal_list.append(readable)
        if goal_list:
            parts.append(f"You want: {', '.join(goal_list)}.")
    
    parts.append("")
    
    # Adjust language based on confidence level (Task 4.3)
    if tone == "supportive":
        parts.append("**Let's explore this together:**")
    else:
        parts.append("**So let's narrow this down:**")
    parts.append("")
    
    # Provide next steps based on what we know
    if profile.interests:
        primary_interest = list(profile.interests)[0]
        if primary_interest == "coding":
            parts.append("For coding, you have 2 main paths:")
            parts.append("• BCA (3 years) → Quick job entry")
            parts.append("• BCA + MCA (5 years) → Higher salary")
            parts.append("")
            if profile.constraints:
                if any("math" in c for c in profile.constraints):
                    parts.append("Since you're weak in math:")
                    parts.append("• Focus on web/app development (less math)")
                    parts.append("• Avoid data science initially")
                    parts.append("")
            if profile.goals:
                if any("quick" in g for g in profile.goals):
                    # Soften recommendation for low confidence (Task 4.3)
                    if tone == "supportive":
                        parts.append("Since you want a job quickly, BCA (3 years) could be a good option to consider.")
                    else:
                        parts.append("Since you want a job quickly → BCA (3 years) makes sense")
                elif any("salary" in g for g in profile.goals):
                    # Soften recommendation for low confidence (Task 4.3)
                    if tone == "supportive":
                        parts.append("Since you want good salary, BCA + MCA (5 years) might be worth exploring.")
                    else:
                        parts.append("Since you want good salary → BCA + MCA (5 years) is better")
            parts.append("")
            
            # Ask more clarifying questions for low confidence (Task 4.3)
            if tone == "supportive":
                parts.append("**To help you decide, let me ask:**")
                parts.append("• How do you feel about studying for 3 years vs 5 years?")
                parts.append("• What matters more to you right now — getting started quickly or building deeper skills?")
                parts.append("• Is there anything else that's making you uncertain?")
            else:
                parts.append("**What else would help me give you a clear recommendation?**")
        elif primary_interest == "business":
            parts.append("For business, you have 2 main paths:")
            parts.append("• BBA (3 years) → Quick entry into business roles")
            parts.append("• BBA + MBA (5 years) → Management positions")
            parts.append("")
            if profile.goals:
                if any("quick" in g for g in profile.goals):
                    # Soften recommendation for low confidence (Task 4.3)
                    if tone == "supportive":
                        parts.append("Since you want a job quickly, BBA (3 years) could be a good option to consider.")
                    else:
                        parts.append("Since you want a job quickly → BBA (3 years) makes sense")
                elif any("salary" in g for g in profile.goals):
                    # Soften recommendation for low confidence (Task 4.3)
                    if tone == "supportive":
                        parts.append("Since you want good salary, BBA + MBA (5 years) might be worth exploring.")
                    else:
                        parts.append("Since you want good salary → BBA + MBA (5 years) is better")
            parts.append("")
            
            # Ask more clarifying questions for low confidence (Task 4.3)
            if tone == "supportive":
                parts.append("**To help you decide, let me ask:**")
                parts.append("• How do you feel about studying for 3 years vs 5 years?")
                parts.append("• What matters more to you right now — getting started quickly or higher positions later?")
                parts.append("• Is there anything else that's making you uncertain?")
            else:
                parts.append("**What else would help me give you a clear recommendation?**")
        else:
            parts.append(f"For {primary_interest}, let me know:")
            parts.append("• Do you want a job quickly or willing to study longer?")
            parts.append("• Any other concerns I should know about?")
    else:
        # Shouldn't reach here if profile exists, but fallback
        if tone == "supportive":
            parts.append("No pressure — let's take this one step at a time.")
            parts.append("")
        parts.append("Tell me more about:")
        parts.append("• What interests you? (coding, business, etc.)")
        parts.append("• Any concerns or constraints?")
    
    return "\n".join(parts)


def _handle_general_exploration(query: str, profile: UserProfile, memory_context: str = "") -> Dict:
    """Handle general exploratory queries.

    Uses accumulated profile to give more targeted guidance.
    
    CRITICAL: If profile exists, ALWAYS build forward - never reset to generic.
    """
    # If we have memory context, use it to personalize the response
    if profile.interests or profile.constraints or profile.goals:
        # Use progressive response builder - ALWAYS reference what we know
        answer = build_progressive_response(profile, query)
    else:
        # Only use generic if NO profile exists
        answer = (
        "I'm here to help you find the right path! 🎓\n\n"
        "**Let's start with a few questions:**\n\n"
        "**1. What interests you most?**\n"
        "• Technology and coding?\n"
        "• Business and entrepreneurship?\n"
        "• Finance and accounting?\n"
        "• Hotel and hospitality?\n\n"
        "**2. What's your current education?**\n"
        "• Completed 12th? (UG programs: BCA, BBA, B.Com, BHM)\n"
        "• Completed graduation? (PG programs: MBA, MCA, M.Com)\n\n"
        "**3. What's your career goal?**\n"
        "• Get a job quickly?\n"
        "• Build deep expertise?\n"
        "• Start your own business?\n"
        "• Work in a specific industry?\n\n"
        "Tell me more about your interests, and I'll guide you to the right program!"
    )
    
    return {
        "answer": answer,
        "intent": "counselor_general",
        "confidence": profile.confidence_score,
        "mode": "counselor",
        "sources": [{"title": "AIMS Programs", "url": "https://www.theaims.ac.in"}],
    }
