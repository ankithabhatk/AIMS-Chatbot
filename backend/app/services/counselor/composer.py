from typing import Dict, List, Optional
from app.services.counselor.formatter import format_composed_response

def compose_response(
    results: Dict[str, Dict],
    user_query: str,
    context: Optional[Dict] = None
) -> str:
    """
    Merge multiple engine outputs into a single counselor-style response.
    
    results example:
    {
        "guidance": {...},
        "compare": {...},
        "career": {...},
        "constraint": {...}
    }
    """
    parts = []
    
    # -------------------------
    # 1. Constraint FIRST (reality check)
    # -------------------------
    constraint = results.get("constraint")
    if constraint:
        parts.append(constraint.get("message", ""))
        
    # -------------------------
    # 2. Guidance (core direction)
    # -------------------------
    guidance = results.get("guidance")
    if guidance:
        rec = guidance.get("recommended_courses", [])
        reasoning = guidance.get("reasoning", "")
        
        if rec:
            parts.append(
                f"Based on your profile, these courses suit you best: {', '.join(rec)}."
            )
        if reasoning:
            parts.append(reasoning)
            
    # -------------------------
    # 3. Comparator (decision clarity)
    # -------------------------
    compare = results.get("compare")
    if compare:
        answer = compare.get("answer")
        if answer:
            parts.append(answer)
        else:
            # Legacy fallback
            c1 = compare.get("course_1")
            c2 = compare.get("course_2")
            comparison = compare.get("comparison", [])
            
            if c1 and c2:
                parts.append(f"Here’s a quick comparison between {c1} and {c2}:")
                for row in comparison[:3]:  # keep short
                    parts.append(
                        f"- {row['factor']}: {c1} → {row[c1]} | {c2} → {row[c2]}"
                    )
                    
            if compare.get("recommendation"):
                parts.append(compare["recommendation"])
            
    # -------------------------
    # 4. Career (future hook)
    # -------------------------
    career = results.get("career")
    if career:
        roles = career.get("roles", [])
        salary = career.get("average_salary")
        
        if roles:
            parts.append(
                f"This path can lead to roles like {', '.join(roles[:3])}."
            )
        if salary:
            parts.append(f"Average starting salary is around {salary}.")
            
    # -------------------------
    # 5. Life (emotional trust)
    # -------------------------
    life = results.get("life")
    if life:
        hostel = life.get("hostel")
        facilities = life.get("facilities", [])
        
        if hostel:
            parts.append(f"Hostel: {hostel}")
        if facilities:
            parts.append(f"Facilities include {', '.join(facilities[:3])}")
            
    # -------------------------
    # 6. Final Follow-up Question
    # -------------------------
    follow_up = (
        guidance.get("next_question")
        if guidance else None
    )
    
    if follow_up:
        parts.append(follow_up)
    else:
        parts.append("Would you like me to help you decide further?")
        
    # -------------------------
    # 7. Merge all parts
    # -------------------------
    raw_response = "\n\n".join([p for p in parts if p])
    
    # -------------------------
    # 8. Format with LLM (tone only)
    # -------------------------
    final_response = format_composed_response(
        raw_response,
        user_query=user_query,
        context=context or {}
    )
    
    return final_response
