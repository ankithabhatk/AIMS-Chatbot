"""
Model Router - Decisions on optimal model allocation for production.
Routes between No LLM (Deterministic), Small Model (Fast RAG), and Medium Model (Complex).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

def select_model(mode: str, confidence: float, has_chunks: bool) -> str:
    """
    Decides which model tier to use for the response generation.
    
    Tiers:
    - no_llm: Deterministic/Structured (Zero Cost, Zero Latency)
    - small: Lightweight LLM (e.g., GPT-4o-mini / Haiku) (Low Cost, Fast)
    - medium: Capable LLM (e.g., GPT-4o / Claude Sonnet) (Mid Cost, Smart)
    """
    # 🚨 RULE: Never override structured answers with LLM
    if mode == "structured":
        return "no_llm"
    
    # RAG Logic
    if mode == "rag":
        # High confidence + good data = Small model is enough
        if has_chunks and confidence > 0.6:
            return "small"
        
        # Low confidence or missing chunks = Medium model for better reasoning/fallback
        return "medium"
    
    # Fallback/Unknown
    return "no_llm"
