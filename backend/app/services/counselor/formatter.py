import json
from typing import Dict, Any

def build_counselor_prompt(data: Dict[str, Any]) -> str:
    """
    Converts structured engine output into a human-like counselor response prompt.
    """
    return f"""
You are a calm, helpful admission counselor.
Your job is to guide a confused student, not just give information.

RULES:
- Be conversational, not robotic
- Show understanding ("Based on what you said...")
- Explain recommendations clearly
- Do NOT sound like AI or JSON
- Keep it concise but helpful
- End with a helpful question

INPUT DATA:
{json.dumps(data, indent=2)}

Now respond naturally as a counselor.
"""

def format_with_gemini(data: Dict[str, Any], gemini_client: Any) -> str:
    """
    Calls Gemini (or the provided LLM client) to format the deterministic JSON into natural language.
    """
    prompt = build_counselor_prompt(data)
    try:
        # Assuming the client is a google.generativeai GenerativeModel instance
        response = gemini_client.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        # fallback (CRITICAL)
        print(f"[FORMATTER ERROR] LLM generation failed: {e}. Using fallback.")
        return fallback_format(data)

def format_composed_response(raw_text: str, user_query: str, context: Dict[str, Any], gemini_client: Any = None) -> str:
    """
    Rewrites a raw, assembled multi-intent string into a smooth counselor response.
    """
    prompt = f"""
You are a calm, helpful admission counselor.
Your job is to guide a confused student, not just give information.

RULES:
- Be conversational, not robotic
- Show understanding ("Based on what you said...")
- Connect the points smoothly so it feels like one person speaking
- Do NOT sound like AI
- Keep it concise but helpful
- Ensure the final follow-up question is clear

STUDENT QUERY: "{user_query}"
STUDENT CONTEXT: {json.dumps(context)}

RAW SYSTEM OUTPUT:
{raw_text}

Now rewrite the raw output naturally as a counselor. Do not invent new facts.
"""
    try:
        if gemini_client:
            response = gemini_client.generate_content(prompt)
            return response.text.strip()
        else:
            return raw_text # Fallback to raw text if no client
    except Exception as e:
        print(f"[FORMATTER ERROR] LLM generation failed: {e}. Using fallback.")
        return raw_text


def fallback_format(data: Dict[str, Any]) -> str:
    """
    Fallback deterministic formatter if the LLM fails.
    """
    courses = ", ".join(data.get("recommended_courses", []))
    reasoning = data.get("reasoning", "general student preferences")
    next_q = data.get("next_question", "How can I help you further?")
    
    return (
        f"Based on what you shared, {courses} could be a good option for you.\n\n"
        f"This is because {reasoning}.\n\n"
        f"{next_q}"
    )
