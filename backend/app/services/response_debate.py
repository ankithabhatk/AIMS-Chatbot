"""
Response Debate System - Multi-candidate generation and intelligent selection

Generates multiple answer styles for complex queries, then selects the most defensible one.
Not for every query (expensive) - only for reasoning/comparison queries.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DebateCandidate:
    """Single answer candidate in debate"""
    answer: str
    style: str  # "balanced", "critical", "optimistic"
    issues: List[str]
    score: float


def is_reasoning_query(query: str) -> bool:
    """Detect if query needs debate (decision-making, comparison, reasoning)"""
    reasoning_triggers = [
        "worth", "value", "better", "compare", "versus", "vs",
        "should i", "which is", "pros and cons", "difference",
        "why", "recommend", "which course", "best"
    ]
    query_lower = query.lower()
    return any(trigger in query_lower for trigger in reasoning_triggers)


def should_use_debate(query: str, confidence: float, query_length: int) -> bool:
    """Decide if debate is worth the computational cost
    
    Args:
        query: User query
        confidence: Current confidence score (0-1)
        query_length: Number of words in query
    
    Returns:
        True if debate should run, False for fast path
    """
    # Don't run debate if already high confidence
    if confidence > 0.75:
        return False
    
    # Don't run debate for short simple queries
    if query_length < 3:
        return False
    
    # Do run debate for reasoning queries
    if is_reasoning_query(query):
        return True
    
    return False


def extract_claims(answer: str) -> List[str]:
    """Break answer into verifiable claims
    
    Example:
        Input: "MBA has 84% placements and ₹8L avg salary"
        Output: ["84% placements", "₹8L average salary"]
    """
    claims = []
    
    # Extract numeric claims (salary, percentage, etc.)
    import re
    patterns = [
        r'₹[\d,]+\s*(?:L|lakh|LPA)',  # salary
        r'\d+%',  # percentages
        r'\d+\s+(?:years?|months?)',  # durations
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, answer)
        claims.extend(matches)
    
    # Extract key phrases
    key_phrases = [
        "placement",
        "salary",
        "fees",
        "ROI",
        "recruiter",
        "package"
    ]
    
    for phrase in key_phrases:
        if phrase.lower() in answer.lower():
            # Extract sentence containing this phrase
            sentences = answer.split('.')
            for sent in sentences:
                if phrase.lower() in sent.lower():
                    claims.append(sent.strip())
                    break
    
    return list(set(claims))  # Remove duplicates


def critique_answer(answer: str, chunks: List[Any]) -> List[str]:
    """Generate list of issues/weaknesses with answer
    
    Returns list of critique points like:
    - "missing salary evidence"
    - "too generic"
    - "not grounded in data"
    """
    issues = []
    
    # Check 1: Evidence grounding
    chunk_text = " ".join([
        (c[0] if isinstance(c, tuple) else c.get("content", "")) 
        for c in chunks
    ]).lower()
    
    claims = extract_claims(answer)
    grounded = 0
    for claim in claims:
        if claim.lower() in chunk_text:
            grounded += 1
    
    if len(claims) > 0 and grounded / len(claims) < 0.5:
        issues.append("not_fully_grounded")
    
    # Check 2: Specificity
    if len(answer.split()) < 20:
        issues.append("too_short")
    
    if any(w in answer.lower() for w in ["vague", "unclear", "something like", "maybe"]):
        issues.append("too_vague")
    
    # Check 3: Structure
    if "\n" not in answer and len(answer) > 200:
        issues.append("poor_structure")
    
    # Check 4: Data richness
    salary_keywords = ["salary", "lpa", "package", "₹"]
    if "placement" in answer.lower() and not any(k in answer.lower() for k in salary_keywords):
        issues.append("missing_salary_data")
    
    return issues


def score_answer(answer: str, issues: List[str], base_score: float = 0.7) -> float:
    """Score answer quality
    
    Base score reduced by penalties for each issue
    """
    penalty_per_issue = 0.15
    final_score = base_score - (len(issues) * penalty_per_issue)
    return max(0.0, min(1.0, final_score))  # Clamp 0-1


def run_debate(
    query: str,
    chunks: List[Any],
    generate_answer_fn,
    base_confidence: float = 0.7
) -> Tuple[str, float, str]:
    """Run multi-candidate debate and return best answer
    
    Args:
        query: User query
        chunks: Retrieved chunks
        generate_answer_fn: Function to generate answer from chunks
        base_confidence: Base confidence before debate
    
    Returns:
        (best_answer, final_confidence, winning_style)
    """
    logger.info("[DEBATE] Starting debate for query")
    
    # STEP 1: Generate multiple candidates
    styles = ["balanced", "critical"]
    candidates: List[DebateCandidate] = []
    
    for style in styles:
        try:
            # Generate answer with specific style
            answer = generate_answer_fn(
                query=query,
                chunks=chunks,
                style=style
            )
            
            if not answer:
                continue
            
            # Critique this answer
            issues = critique_answer(answer, chunks)
            
            # Score it
            score = score_answer(answer, issues, base_confidence)
            
            candidate = DebateCandidate(
                answer=answer,
                style=style,
                issues=issues,
                score=score
            )
            candidates.append(candidate)
            logger.debug(f"  [{style}] score={score:.2f} issues={len(issues)}")
            
        except Exception as e:
            logger.warning(f"  [{style}] failed: {e}")
            continue
    
    # STEP 2: Select winner
    if not candidates:
        logger.warning("[DEBATE] No candidates generated, returning base answer")
        return generate_answer_fn(query, chunks), base_confidence, "fallback"
    
    winner = max(candidates, key=lambda c: c.score)
    logger.info(f"[DEBATE] Winner: {winner.style} (score={winner.score:.2f})")
    
    # Slightly boost confidence for debated answers (they're more considered)
    final_confidence = min(winner.score + 0.05, 0.95)
    
    return winner.answer, final_confidence, winner.style


def debate_gate(
    query: str,
    current_answer: str,
    current_confidence: float,
    chunks: List[Any],
    generate_answer_fn
) -> Tuple[str, float]:
    """Wrapper that decides whether to run debate
    
    Returns: (potentially_debated_answer, final_confidence)
    """
    query_length = len(query.split())
    
    if should_use_debate(query, current_confidence, query_length):
        logger.info("[DEBATE_GATE] Running debate")
        debated_answer, new_confidence, _ = run_debate(
            query=query,
            chunks=chunks,
            generate_answer_fn=generate_answer_fn,
            base_confidence=current_confidence
        )
        return debated_answer, new_confidence
    else:
        logger.debug("[DEBATE_GATE] Skipping debate (confidence sufficient or query too simple)")
        return current_answer, current_confidence
