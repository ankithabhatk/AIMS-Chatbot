import os
import logging
import re
from openai import OpenAI
from app.brain.context_builder import build_context

logger = logging.getLogger(__name__)

def clean_fallback_text(text: str) -> str:
    """Clean formatting noise from fallback text."""
    # Remove excessive newlines
    text = re.sub(r'\n+', ' ', text)
    # Remove basic bullet noise if it exists at the start of sentences
    text = re.sub(r'(?m)^[-•*]\s+', '', text)
    # Basic trim to keep it short and readable (~4-5 lines max)
    sentences = re.split(r'(?<=[.!?]) +', text)
    if len(sentences) > 5:
        text = " ".join(sentences[:5])
    
    # Enforce word limit (max 120 words roughly)
    words = text.split()
    if len(words) > 120:
        text = " ".join(words[:120]) + "..."
        
    return text.strip()

def generate_answer(query: str, results: list, mode="auto") -> str:
    """Generate answer using OpenAI synthesis or a structured extractive fallback."""
    
    # STEP 1: Handle empty input
    if not results:
        return "I don’t have enough information to answer that right now."
        
    context_text = build_context(results)
    
    # STEP 2: Try OpenAI synthesis
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        system_prompt = (
            "You are an AIMS college assistant. "
            "Answer clearly, concisely, and factually using ONLY the provided context. "
            "Never hallucinate beyond context. Never invent data. Keep answer under 120 words."
        )
        
        user_prompt = f"Context:\n{context_text}\n\nQuery:\n{query}"
        
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=150
        )
        
        logger.info("Answer generated successfully via OpenAI SDK")
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"OpenAI failed → fallback mode: {e}")
        
    # STEP 3: Fallback (CRITICAL)
    # If OpenAI fails or quota is exceeded
    fallback_text = clean_fallback_text(context_text)
    
    if not fallback_text:
        return "I don't have enough specific information on that right now."
        
    return fallback_text
