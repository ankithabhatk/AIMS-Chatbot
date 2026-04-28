from typing import Optional

def compress_response(text: str) -> str:
    words = text.split()
    if len(words) > 120:
        return " ".join(words[:100]) + "...\n\n👉 Want a quick summary or full details?"
    return text

def add_reflective_prompt(response: str) -> str:
    return response + "\n\nHow are you feeling about these options?"

def add_safe_visualization(role: str) -> str:
    return f"\n\nMany students who choose this path work towards roles like {role} over time, depending on their skills and experience."

def soften_recommendation(course: str) -> str:
    return f"Based on what you’ve shared, {course} could be a good fit for you."

def add_choice_reminder(response: str) -> str:
    return response + "\n\nTake your time—choosing a course is an important decision, and I’m here to help you explore it properly."

def normalize_uncertainty() -> str:
    return "It’s completely normal to feel unsure at this stage—most students explore a few options before deciding.\n\n"

def sanitize(text: str) -> str:
    FORBIDDEN = ["guaranteed job", "100% placement", "sure shot"]
    for word in FORBIDDEN:
        text = text.replace(word, "strong opportunities")
    return text

def detect_user_type(query: str) -> str:
    q = query.lower()
    if "parent" in q or "my son" in q or "my daughter" in q:
        return "parent"
    if "placement" in q or "salary" in q or "package" in q:
        return "career_focused"
    return "student"

def deep_personalization(context: dict) -> str:
    parts = []
    if context and context.get("marks"):
        parts.append(f"{context['marks']}% marks")
    if context and context.get("goal"):
        parts.append(f"aiming for {context['goal']}")
    if context and context.get("interest"):
        parts.append(f"interest in {context['interest']}")
    
    if not parts:
        return ""
        
    intros = [
        "Based on " + ", ".join(parts) + ", ",
        "Looking at " + " and ".join(parts) + ", ",
        "With " + " and ".join(parts) + " in mind, ",
        "Considering " + ", ".join(parts) + ", "
    ]
    import random
    return random.choice(intros)

def safe_mode(response: str, context: dict) -> str:
    response = normalize_uncertainty() + response
    response = add_choice_reminder(response)
    response += "\n\nWould you like me to help narrow this down step by step?"
    return response

def balanced_mode(response: str, context: dict) -> str:
    response = soften_recommendation(context.get("courses", ["this option"])[0]) + "\n\n" + response
    response += "\n\nIf you want, I can help you decide based on your strengths."
    return response

def conversion_mode(response: str, context: dict) -> str:
    # Notice: inject_informed_timing is handled in engine.py for high intent or imported if needed.
    response += "\n\nI can walk you through the process right now step by step."
    return response

def rotate_mode(context: dict) -> str:
    """Rotates through different persona modes to avoid repetitive tone."""
    MODES = ["supportive", "direct", "analytical"]
    turn = context.get("turn_count", 0)
    return MODES[turn % len(MODES)]

def apply_persona_layer(response: str, context: Optional[dict] = None) -> str:
    """
    Converts structured response into a real counselor tone.
    NO hallucination. Only rewriting tone.
    """
    if not response:
        return response
    
    context = context or {}
    
    # -------------------------
    # Style Rotation & Throttling
    # -------------------------
    mode = rotate_mode(context)
    last_comfort = context.get("comfort_phrase_used", False)
    skip_comfort = last_comfort  # Throttle: if used last time, skip this time
    
    # Compress if too long
    response = compress_response(response)
    
    # Sanitize forbidden words
    response = sanitize(response)
        
    # -------------------------
    # Base tone rules
    # -------------------------
    intro = ""
    if mode != "direct":
        intro = deep_personalization(context)
        
    closing = ""
    
    # Emotional validation (Comfort Phrases)
    comfort_used = False
    marks = context.get("marks") if context else None
    
    if marks and not skip_comfort and mode == "supportive":
        turn = context.get("turn_count", 1)
        if marks < 70:
            validations = [
                "Don’t worry — many students with similar marks do very well.\n\n",
                "That's a decent score, and it opens up several good paths.\n\n",
                "Many successful professionals started with similar marks.\n\n"
            ]
            intro += validations[turn % len(validations)]
            comfort_used = True
        else:
            validations = [
                "here’s how you can think about it.\n\n",
                "that's a strong score to build on.\n\n",
                "let's look at your options with those marks.\n\n"
            ]
            intro += validations[turn % len(validations)]
            comfort_used = True
    
    # Track comfort phrase usage for next turn throttling
    context["comfort_phrase_used"] = comfort_used
        
    if mode != "direct" and ("confused" in response.lower() or "difference" in response.lower()):
        if not skip_comfort:
            intro += normalize_uncertainty()
            comfort_used = True
        intro += "Let’s break it down simply.\n\n"
        
    # -------------------------
    # Mode-Specific Refinement
    # -------------------------
    if mode == "analytical":
        response = response.replace("I think", "Data suggests").replace("maybe", "typically")
    elif mode == "direct":
        # Strip conversational filler
        response = response.replace("It’s completely normal to feel unsure", "").strip()

    # -------------------------
    # Safe Recommendation (Compare Stage)
    # -------------------------
    courses = context.get("courses") if context else []
    if "compare" in response.lower() and courses:
        closing = "\n\n" + soften_recommendation(courses[0])
    elif "career" in response.lower() and courses:
        # Realistic Future Visualization
        closing = add_safe_visualization("a professional in this field")
    else:
        # Add guidance tone
        if mode == "supportive":
            closing = "\n\nIf you want, I can help you narrow this down based on your interests or career goals."
        elif mode == "analytical":
            closing = "\n\nWhich of these metrics (salary, growth, or fit) matters most to you right now?"
        else: # direct
            closing = "\n\nWhat's your next question on this?"
    
    # -------------------------
    # Clean formatting
    # -------------------------
    final = f"{intro}{response.strip()}{closing}"
    
    if "compare" in response.lower() and mode == "supportive":
        final = add_choice_reminder(final)
    
    # Optional: Reflective prompt if it's a long informational response
    if mode != "direct" and len(final.split()) > 50 and "👉" not in final:
        final = add_reflective_prompt(final)
        
    return final

def apply_hybrid_behavior(response: str, context: dict, level: str) -> str:
    """Central controller for adaptive intent-based tone."""
    base_response = apply_persona_layer(response, context)
    
    if level == "low":
        return safe_mode(base_response, context)
    elif level == "mid":
        return balanced_mode(base_response, context)
    elif level == "high":
        return conversion_mode(base_response, context)
        
    return base_response
