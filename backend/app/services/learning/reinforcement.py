import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

SUCCESS_RESPONSES = []

def build_reinforcement_prompt(data: Dict, tuning: Dict, text_to_rewrite: str) -> str:
    signals = []
    if tuning.get("cta_style") == "soft":
        signals.append("- Avoid asking direct yes/no questions. Use guidance tone.")
    if tuning.get("force_simplification"):
        signals.append("- Simplify explanation into 2 options only.")
    if tuning.get("guidance_style") == "more_direct":
        signals.append("- Be slightly more confident in recommendation.")
    if tuning.get("focus_stage") == "ready_to_close":
        signals.append("- Do not push application directly. Offer help instead.")

    signals_text = "\n".join(signals) if signals else "- Be supportive, not pushy"
    
    stage = data.get("conversion_stage", "unknown")
    course = data.get("course", "unknown")
    marks = data.get("user_marks", "unknown")

    prompt = f"""You are a professional admission counselor.
Your job:
- Make the response sound natural and human
- Keep it short and clear
- Do NOT change facts
- Do NOT add new information

Context:
Stage: {stage}
Course: {course}
Student Marks: {marks}

System Tuning:
Tone: {tuning.get('cta_style', 'normal')}
Directness: {tuning.get('guidance_style', 'balanced')}

Rules:
{signals_text}
- Max 80 words

Rewrite this into a natural response:
"{text_to_rewrite}"
"""
    return prompt

def call_llm(prompt: str) -> str:
    try:
        from app.services.llm.response_generator import get_generator
        gen = get_generator(use_openai=True)
        if gen.use_openai:
            response = gen.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM rewrite failed: {e}")
    raise Exception("LLM call failed or not available")

def sanitize(text: str) -> str:
    banned = ["guaranteed job", "100% placement"]
    lower_text = text.lower()
    for b in banned:
        if b in lower_text:
            text = text.replace("guaranteed job", "strong career opportunities")
            text = text.replace("100% placement", "excellent placement support")
            text = text.replace("Guaranteed job", "Strong career opportunities")
            text = text.replace("100% Placement", "Excellent placement support")
    return text

def reinforce_response(text: str, data: Dict, tuning: Dict) -> str:
    stage = data.get("conversion_stage", "none")
    if stage not in ["decision_confirmed", "ready_to_close"]:
        return text
        
    try:
        prompt = build_reinforcement_prompt(data, tuning, text)
        llm_text = call_llm(prompt)
        return sanitize(llm_text)
    except:
        return text

def store_success(session: Dict, user_query: str, final_response: str):
    SUCCESS_RESPONSES.append({
        "input": user_query,
        "output": final_response
    })

def find_similar_success(query: str):
    for p in SUCCESS_RESPONSES:
        if query.lower() in p["input"].lower():
            return p
    return None

def get_style_hint(query: str) -> str:
    match = find_similar_success(query)
    if match:
        return f"Use tone similar to: {match['output']}"
    return ""
