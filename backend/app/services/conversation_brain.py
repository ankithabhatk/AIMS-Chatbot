"""
Conversation Brain - Session Memory & Context Intelligence
Safe wrapper layer for multi-turn conversation handling
Sits BEFORE RAG pipeline - input/output shaping only
"""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Global session store (in-memory for demo, can swap to Redis later)
SESSIONS: Dict[str, Dict] = {}

# Conversation patterns
FOLLOW_UP_KEYWORDS = ["tell more", "more", "more details", "explain", "details", "go on"]
CORRECTION_KEYWORDS = ["wrong", "not correct", "not what i asked", "incorrect", "doesn't answer", "not helpful"]
AFFIRMATION_KEYWORDS = ["yes", "right", "correct", "perfect", "thanks"]


def get_session(session_id: str) -> Dict:
    """Get or create session context"""
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "last_query": "",
            "last_answer": "",
            "last_intent": "",
            "turn_count": 0,
            "correction_count": 0
        }
    return SESSIONS[session_id]


def is_follow_up(query: str) -> bool:
    """Detect if query is asking for more details on previous topic"""
    q_lower = query.lower().strip()
    return any(keyword in q_lower for keyword in FOLLOW_UP_KEYWORDS)


def is_correction(query: str) -> bool:
    """Detect if user is correcting or rejecting the last answer"""
    q_lower = query.lower().strip()
    return any(keyword in q_lower for keyword in CORRECTION_KEYWORDS)


def is_affirmation(query: str) -> bool:
    """Detect if user is satisfied with answer"""
    q_lower = query.lower().strip()
    return any(keyword in q_lower for keyword in AFFIRMATION_KEYWORDS)


def preprocess_query(query: str, session_id: str) -> Tuple[str, Optional[Dict]]:
    """
    Pre-process query using conversation context
    
    Returns:
        (processed_query, brain_instruction)
        
    brain_instruction can be:
        - None: proceed normally
        - {"type": "retry"}: user rejected answer, retry with same query
        - {"type": "expand"}: expand short query with context
    """
    session = get_session(session_id)
    session["turn_count"] += 1
    
    q = query.lower().strip()
    
    # ================================================================
    # 1. CORRECTION HANDLING (User says "wrong", "not helpful", etc)
    # ================================================================
    if is_correction(q) and session["last_query"]:
        logger.info(f"[{session_id}] Turn {session['turn_count']}: CORRECTION DETECTED")
        session["correction_count"] += 1
        
        return session["last_query"], {
            "type": "correction",
            "message": "I'm sorry about that. Let me try to give you more accurate information."
        }
    
    # ================================================================
    # 2. FOLLOW-UP HANDLING (User says "tell more", "more details", etc)
    # ================================================================
    if is_follow_up(q) and session["last_query"]:
        logger.info(f"[{session_id}] Turn {session['turn_count']}: FOLLOW-UP DETECTED")
        
        # Expand follow-up with last query for context
        expanded_query = session["last_query"] + " more details"
        return expanded_query, {
            "type": "follow_up",
            "original": query,
            "expanded": expanded_query
        }
    
    # ================================================================
    # 3. AFFIRMATION HANDLING (User says "yes", "thanks", etc)
    # ================================================================
    if is_affirmation(q):
        logger.info(f"[{session_id}] Turn {session['turn_count']}: AFFIRMATION")
        
        return query, {
            "type": "affirmation",
            "message": "Great! Anything else you'd like to know about AIMS?"
        }
    
    # ================================================================
    # 4. SHORT QUERY EXPANSION (Single word or 2-3 words)
    # ================================================================
    # Only expand if not a completely new topic
    word_count = len(query.split())
    if word_count <= 3 and session["last_query"] and not is_new_topic(query, session["last_query"]):
        logger.info(f"[{session_id}] Turn {session['turn_count']}: SHORT QUERY EXPANSION")
        
        expanded_query = session["last_query"] + " " + query
        return expanded_query, {
            "type": "expand",
            "original": query,
            "expanded": expanded_query
        }
    
    # ================================================================
    # 5. DEFAULT: Normal query (no special handling)
    # ================================================================
    return query, None


def postprocess_response(
    original_query: str,
    processed_query: str,
    answer: str,
    confidence: float,
    session_id: str,
    brain_instruction: Optional[Dict] = None
) -> Tuple[str, str]:
    """
    Post-process response and update session
    
    Returns:
        (answer, confidence_label)
    """
    session = get_session(session_id)
    
    # Update session history
    session["last_query"] = original_query
    session["last_answer"] = answer
    
    # Modify answer based on brain instruction
    if brain_instruction:
        instruction_type = brain_instruction.get("type")
        
        if instruction_type == "correction":
            # Add apology before answer
            answer = f"I'm sorry about that confusion. Here's a more accurate answer:\n\n{answer}"
            logger.info(f"[{session_id}] Applied correction recovery")
        
        elif instruction_type == "follow_up":
            # No modification needed, just note it
            logger.info(f"[{session_id}] Applied follow-up context")
        
        elif instruction_type == "affirmation":
            # Keep answer as-is, user was satisfied
            logger.info(f"[{session_id}] Noted user affirmation")
        
        elif instruction_type == "expand":
            # No modification, just added context to retrieval
            logger.info(f"[{session_id}] Applied query expansion")
    
    return answer


def reset_session(session_id: str) -> None:
    """Clear session after user leaves or session expires"""
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        logger.info(f"[{session_id}] Session cleared")


def get_session_stats(session_id: str) -> Dict:
    """Get session conversation statistics"""
    session = get_session(session_id)
    return {
        "turn_count": session["turn_count"],
        "correction_count": session["correction_count"],
        "has_context": bool(session["last_query"])
    }


def is_new_topic(current_query: str, last_query: str) -> bool:
    """
    Heuristic: determine if current query is a new topic
    (not just follow-up to same topic)
    """
    # Simple check: if current_query shares no words with last_query, it's new
    current_words = set(current_query.lower().split())
    last_words = set(last_query.lower().split())
    
    # Remove common words
    common = ["the", "a", "at", "of", "is", "and", "or", "to", "for"]
    current_words = {w for w in current_words if w not in common}
    last_words = {w for w in last_words if w not in common}
    
    # If no word overlap, likely new topic
    overlap = current_words & last_words
    
    return len(overlap) == 0
