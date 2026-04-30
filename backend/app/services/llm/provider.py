import os
import json
import logging
import time
import requests
from typing import Tuple, List, Optional
from app.services.llm.ollama_service import get_llm_service

logger = logging.getLogger(__name__)

class AILlmProvider:
    """
    Thin provider abstraction for cloud LLMs with graceful fallbacks.
    Fallback order: Groq -> OpenRouter -> Local Ollama -> None (templates)
    """
    def __init__(self):
        self.primary_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_name = os.getenv("MODEL_NAME", "tinyllama")
        self.ollama_service = get_llm_service(use_ollama=True)

    def generate_response(self, query: str, context: List[str], system_prompt: str) -> Tuple[Optional[str], str]:
        """
        Generate response with fallbacks.
        Returns: (response_text, provider_used)
        """
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Inject context into user message if any
        if context:
            context_str = "\n".join(context)
            messages.append({"role": "user", "content": f"Context:\n{context_str}\n\nUser Question: {query}"})
        else:
            messages.append({"role": "user", "content": query})

        # 1. Try Primary Provider (Ollama by default now)
        if self.primary_provider == "ollama":
            try:
                logger.info("Using local Ollama as primary...")
                response, _ = self.ollama_service.generate_response(query, context, system_prompt)
                if response and len(response) > 5:
                    return response, "Ollama"
            except Exception as e:
                logger.warning(f"Ollama local inference failed: {e}")

        # 2. Try Groq (if not primary or primary failed)
        if self.groq_api_key and self.primary_provider != "groq":
            try:
                response = self._call_groq(messages)
                if response:
                    return response, "Groq"
            except Exception as e:
                logger.warning(f"Groq API failed: {e}")

        # 3. Try OpenRouter
        if self.openrouter_api_key:
            try:
                response = self._call_openrouter(messages)
                if response:
                    return response, "OpenRouter"
            except Exception as e:
                logger.warning(f"OpenRouter API failed: {e}")

        # 4. Try Ollama (if it wasn't primary but others failed)
        if self.primary_provider != "ollama":
            try:
                logger.info("Falling back to local Ollama...")
                response, _ = self.ollama_service.generate_response(query, context, system_prompt)
                if response and len(response) > 5:
                    return response, "Ollama"
            except Exception as e:
                logger.warning(f"Ollama local inference failed: {e}")

        # 4. Total Failure -> return None to trigger deterministic templates
        return None, "None (Template Fallback)"

    def _call_groq(self, messages: List[dict]) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 512
        }
        
        for attempt in range(2):
            try:
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=4.0)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Groq API attempt {attempt+1} failed: {e}")
                time.sleep(1.0)
        return None

    def _call_openrouter(self, messages: List[dict]) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name if "/" in self.model_name else f"meta-llama/{self.model_name}",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 512
        }
        
        for attempt in range(2):
            try:
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=4.0)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()
            except requests.exceptions.RequestException as e:
                logger.warning(f"OpenRouter API attempt {attempt+1} failed: {e}")
                time.sleep(1.0)
        return None

# Singleton instance
_provider_instance = None

def get_llm_provider() -> AILlmProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = AILlmProvider()
    return _provider_instance
