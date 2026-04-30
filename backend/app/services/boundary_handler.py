"""
Knowledge Boundary Handler - Detects out-of-scope queries and provides safe responses.

This module handles queries about:
- External entrance exams (JEE, NEET, SAT, etc.)
- Comparative questions (vs other colleges)
- External cutoffs, ranks, percentiles
- Questions outside AIMS domain

Instead of hallucinating or failing, it provides truthful, helpful redirects.
"""

import re
from typing import Optional, Dict


def is_out_of_scope(query: str) -> bool:
    """Detect if query is outside AIMS knowledge boundary.
    
    Returns True for:
    - External entrance exam queries (JEE, NEET, SAT, etc.)
    - Comparative questions (vs other colleges)
    - External cutoff/rank queries
    - Questions about other institutions
    """
    q = query.lower()
    
    # External entrance exams
    external_exams = [
        "jee", "neet", "cet", "kcet", "comedk", "kcet",
        "sat", "act", "gre", "gmat", "toefl", "ielts",
        "cat", "mat", "xat", "snap", "nmat", "cmat", "atma",
        "gate", "ugc net", "csir net",
    ]
    
    # Comparative signals
    comparative_signals = [
        "vs", "versus", "compared to", "compare with",
        "better than", "which is better",
        "other colleges", "other universities",
        "top colleges", "best colleges",
        "top engineering", "best engineering",
        "top universities", "best universities",
        "iit", "nit", "iiit", "bits",
        "christ", "jain", "pes", "rv", "bms",
    ]
    
    # External data signals
    external_data_signals = [
        "cutoff", "cut off", "cut-off",
        "rank", "percentile",
        "national level", "state level",
        "all india", "state quota",
    ]
    
    # Check for external exams
    for exam in external_exams:
        # Word boundary check to avoid false positives
        if re.search(rf"\b{re.escape(exam)}\b", q):
            return True
    
    # Check for comparative queries
    for signal in comparative_signals:
        if signal in q:
            return True
    
    # Check for external data queries
    for signal in external_data_signals:
        if signal in q:
            # Exception: if query also mentions AIMS, it might be about AIMS cutoff
            if "aims" in q or "our" in q or "your" in q:
                continue
            return True
    
    return False


def get_out_of_scope_response(query: str) -> Dict:
    """Generate safe, helpful response for out-of-scope queries.
    
    Instead of hallucinating or failing, provides:
    - Clear boundary statement
    - What AIMS can help with
    - Helpful redirect
    """
    q = query.lower()
    
    # Detect specific out-of-scope category
    category = _detect_out_of_scope_category(q)
    
    if category == "external_exam":
        return _handle_external_exam_query(q)
    elif category == "comparative":
        return _handle_comparative_query(q)
    elif category == "external_cutoff":
        return _handle_external_cutoff_query(q)
    else:
        return _handle_generic_out_of_scope(q)


def _detect_out_of_scope_category(query: str) -> str:
    """Detect specific category of out-of-scope query."""
    q = query.lower()
    
    # Comparative (CHECK FIRST - highest priority for guidance)
    # Especially important for queries like "JEE score, should I join AIMS or NIT?"
    comparative_signals = ["vs", "versus", "compared to", "compare", "better than", "which is better", " or ", "should i join"]
    if any(signal in q for signal in comparative_signals):
        return "comparative"
    
    # External exams
    external_exams = ["jee", "neet", "cet", "sat", "act", "gre", "gmat", "cat", "mat"]
    if any(exam in q for exam in external_exams):
        return "external_exam"
    
    # External cutoff/rank
    if any(term in q for term in ["cutoff", "cut off", "rank", "percentile"]):
        return "external_cutoff"
    
    return "generic"


def _handle_external_exam_query(query: str) -> Dict:
    """Handle queries about external entrance exams (JEE, NEET, etc.)."""
    
    # Detect which exam and provide real-world context
    exam_mentioned = None
    exam_context = None
    
    exam_map = {
        "jee": {
            "name": "JEE (Joint Entrance Examination)",
            "context": "JEE Main and JEE Advanced are national-level engineering entrance exams used for admission to IITs, NITs, and other engineering colleges through JoSAA counseling."
        },
        "neet": {
            "name": "NEET (National Eligibility cum Entrance Test)",
            "context": "NEET is the national medical entrance exam required for admission to MBBS, BDS, and other medical programs across India."
        },
        "cet": {
            "name": "CET (Common Entrance Test)",
            "context": "CET (like KCET in Karnataka) is a state-level entrance exam used for admission to engineering, medical, and other professional courses in state colleges."
        },
        "kcet": {
            "name": "KCET (Karnataka CET)",
            "context": "KCET is Karnataka's state-level entrance exam for admission to engineering, medical, and other professional courses in Karnataka colleges."
        },
        "comedk": {
            "name": "COMEDK",
            "context": "COMEDK is an entrance exam conducted by private engineering colleges in Karnataka for admission to their programs."
        },
        "sat": {
            "name": "SAT",
            "context": "SAT is a standardized test used for undergraduate admissions in US universities and some international institutions."
        },
        "act": {
            "name": "ACT",
            "context": "ACT is a standardized test used for undergraduate admissions in US universities, similar to SAT."
        },
        "gre": {
            "name": "GRE",
            "context": "GRE is a standardized test required for graduate program admissions (Master's, PhD) in US and international universities."
        },
        "gmat": {
            "name": "GMAT",
            "context": "GMAT is a standardized test used for MBA and business school admissions globally."
        },
        "cat": {
            "name": "CAT (Common Admission Test)",
            "context": "CAT is India's premier MBA entrance exam conducted by IIMs, used for admission to IIMs and top B-schools across India."
        },
        "mat": {
            "name": "MAT (Management Aptitude Test)",
            "context": "MAT is a national-level MBA entrance exam accepted by many business schools across India."
        },
    }
    
    for exam_key, exam_info in exam_map.items():
        if exam_key in query.lower():
            exam_mentioned = exam_info["name"]
            exam_context = exam_info["context"]
            break
    
    if exam_mentioned and exam_context:
        answer = (
            f"**About {exam_mentioned}:**\n"
            f"{exam_context}\n\n"
            f"**For AIMS admissions:**\n"
            f"• Most of our programs (BCA, BBA, B.Com, BHM) do NOT require national entrance exams\n"
            f"• Admission is based on your 10+2 marks and personal interview\n"
            f"• For MBA: We accept CAT, MAT, ATMA, and CMAT scores\n"
            f"• For MCA: We accept NIMCET scores\n\n"
            f"**If you're asking about {exam_mentioned} for other colleges:**\n"
            f"Those requirements vary by institution. I can only provide information about AIMS admissions.\n\n"
            f"Would you like to know more about AIMS admission process?"
        )
    else:
        answer = (
            "I can help you with AIMS admission requirements!\n\n"
            "**For AIMS admissions:**\n"
            "• Most programs (BCA, BBA, B.Com, BHM) do NOT require national entrance exams\n"
            "• Admission is based on your 10+2 marks and personal interview\n"
            "• For MBA: We accept CAT, MAT, ATMA, and CMAT scores\n"
            "• For MCA: We accept NIMCET scores\n\n"
            "If you're asking about entrance exams for other colleges, those requirements vary by institution.\n\n"
            "Would you like to know more about AIMS admission process?"
        )
    
    return {
        "answer": answer,
        "intent": "out_of_scope_exam",
        "confidence": 1.0,
        "mode": "boundary",
        "sources": [{"title": "AIMS Admissions", "url": "https://www.theaims.ac.in"}],
    }


def _handle_comparative_query(query: str) -> Dict:
    """Handle comparative queries (AIMS vs other colleges).
    
    P2 FIX: Provide guidance instead of deflection.
    """
    q = query.lower()
    
    # Detect if JEE/NEET mentioned (high-stakes comparison)
    has_jee = "jee" in q or "joint entrance" in q
    has_neet = "neet" in q
    has_nit = "nit" in q or "national institute" in q
    has_iit = "iit" in q or "indian institute" in q
    
    # P2 FIX: Acknowledge their achievement, then provide guidance
    if has_jee and (has_nit or has_iit):
        # Extract percentile if mentioned
        percentile_match = re.search(r'(\d+)\s*percentile', q)
        percentile = percentile_match.group(1) if percentile_match else None
        
        if percentile and int(percentile) >= 90:
            answer = (
                f"**With {percentile} percentile in JEE, you likely have good chances at NITs** depending on your rank, branch preference, and category.\n\n"
                "**Honest comparison:**\n"
                "• If you're aiming for **engineering** (B.Tech) → NIT is the stronger path\n"
                "  - Better for: Core engineering, research, higher studies\n"
                "  - Placement range: ₹6-40 LPA (varies by branch)\n\n"
                "• If you're looking at **IT/software development** → AIMS BCA/MCA is a viable alternative\n"
                "  - Better for: Practical coding, app development, quick job entry\n"
                "  - Placement range: ₹3-16 LPA (BCA: ₹3-8 LPA, MCA: ₹6-16 LPA)\n\n"
                "**Key question:**\n"
                "What matters more to you — the **NIT brand** or the **specific career path**?\n\n"
                "• Engineering career (hardware, core branches) → NIT\n"
                "• Software/IT career (apps, web, coding) → Both work, NIT has edge\n"
                "• Business/management → AIMS MBA after graduation\n\n"
                "**My suggestion:**\n"
                "With your JEE score, explore NIT options first. AIMS is a solid backup if:\n"
                "• You don't get your preferred NIT branch\n"
                "• You prefer Bangalore's IT ecosystem\n"
                "• You want more affordable fees\n\n"
                "What are you more interested in — engineering or software development?"
            )
        else:
            answer = (
                "**About JEE and college choices:**\n"
                "JEE opens doors to NITs, IIITs, and other engineering colleges. Your final choice depends on your rank, branch preference, and career goals.\n\n"
                "**Honest comparison:**\n"
                "• If you're aiming for **engineering** (B.Tech) → NIT/IIIT is the stronger path\n"
                "  - Better for: Core engineering, research, higher studies\n\n"
                "• If you're looking at **IT/software development** → AIMS BCA/MCA is a viable alternative\n"
                "  - Better for: Practical coding, app development, quick job entry\n"
                "  - Placement range: ₹3-16 LPA\n\n"
                "**AIMS is more suitable if:**\n"
                "• You prefer BCA (software/app development) over B.Tech\n"
                "• You want Bangalore's IT ecosystem and internship opportunities\n"
                "• You're looking for more affordable fees\n\n"
                "**Key question:**\n"
                "What's your goal — engineering career or software development career?\n\n"
                "I can tell you more about AIMS programs if you're considering the IT/software path!"
            )
    else:
        # Generic comparison
        answer = (
            "**About college comparisons:**\n"
            "Choosing the right college depends on multiple factors like program quality, placements, fees, location, campus culture, and your career goals. Each institution has unique strengths.\n\n"
            "**What I can tell you about AIMS:**\n"
            "• Industry-integrated curriculum with 300+ corporate tie-ups\n"
            "• Around 80%+ placement rate with packages up to ₹27 LPA (top performers)\n"
            "• Modern campus with smart classrooms, labs, and Wi-Fi\n"
            "• Affordable fees with scholarship opportunities\n"
            "• Located in Bangalore - India's IT hub\n\n"
            "**For comparing colleges:**\n"
            "I'd recommend checking official websites, NIRF rankings, talking to current students, and visiting campuses to make an informed decision.\n\n"
            "Would you like to know more about specific AIMS programs or facilities?"
        )
    
    return {
        "answer": answer,
        "intent": "out_of_scope_comparative",
        "confidence": 1.0,
        "mode": "boundary",
        "sources": [{"title": "Why AIMS", "url": "https://www.theaims.ac.in"}],
    }


def _handle_external_cutoff_query(query: str) -> Dict:
    """Handle queries about external cutoffs, ranks, percentiles."""
    
    answer = (
        "**About cutoffs and ranks:**\n"
        "Cutoffs, ranks, and percentiles are used by many colleges for merit-based admissions. These vary by institution, program, category (General/OBC/SC/ST), and change every year based on competition and seat availability.\n\n"
        "**For AIMS admissions:**\n"
        "• We do NOT have cutoff ranks or percentiles\n"
        "• Admission is based on your academic performance (10+2 marks) and personal interview\n"
        "• Minimum eligibility varies by program:\n"
        "  - BCA/BBA: 10+2 with 50% marks\n"
        "  - MBA: Graduation with 50% marks\n"
        "  - MCA: BCA/B.Sc with Mathematics\n\n"
        "**If you're asking about cutoffs for other colleges:**\n"
        "Those vary by institution and change every year. I can only provide AIMS-specific information.\n\n"
        "Would you like to know more about AIMS eligibility criteria?"
    )
    
    return {
        "answer": answer,
        "intent": "out_of_scope_cutoff",
        "confidence": 1.0,
        "mode": "boundary",
        "sources": [{"title": "AIMS Admissions", "url": "https://www.theaims.ac.in"}],
    }


def _handle_generic_out_of_scope(query: str) -> Dict:
    """Handle generic out-of-scope queries."""
    
    answer = (
        "I'm here to help with information about AIMS Institutes! 🎓\n\n"
        "I can provide detailed information about:\n"
        "• Courses offered (MBA, MCA, BBA, BCA, B.Com, M.Com, BHM)\n"
        "• Fees and scholarships\n"
        "• Admission process and eligibility\n"
        "• Placements and career support\n"
        "• Campus facilities and hostel\n\n"
        "For questions outside AIMS, I'd recommend checking official sources or contacting the relevant institutions directly.\n\n"
        "What would you like to know about AIMS?"
    )
    
    return {
        "answer": answer,
        "intent": "out_of_scope_generic",
        "confidence": 1.0,
        "mode": "boundary",
        "sources": [{"title": "AIMS Information", "url": "https://www.theaims.ac.in"}],
    }
