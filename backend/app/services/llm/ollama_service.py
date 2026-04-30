"""
Ollama Qwen Integration for Chat-Bot Backend
Provides drop-in replacement for LLM services using local Qwen models
"""

import logging
from typing import List, Tuple, Optional
import os
import sys
import requests

# Add run_ollama_qwen to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from run_ollama_qwen import OllamaQwenRunner
except ImportError:
    OllamaQwenRunner = None

logger = logging.getLogger(__name__)

class OllamaLLMService:
    """
    Drop-in replacement for OpenAI LLM service
    Uses local Ollama API directly via HTTP requests.
    """
    
    def __init__(self, 
                 model: str = "tinyllama",
                 temperature: float = 0.3,
                 max_tokens: int = 1024):
        self.model = os.getenv("MODEL_NAME", model)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        
        # Check connection
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            if res.status_code == 200:
                logger.info(f"✅ Ollama service connected to {self.base_url}")
            else:
                logger.warning(f"Ollama connected but returned {res.status_code}")
        except Exception as e:
            logger.warning(f"Ollama server not reachable: {e}")
    
    def generate_response(self, 
                         query: str, 
                         context: List[str],
                         system_prompt: Optional[str] = None) -> Tuple[str, float]:
        """Generate response via Ollama HTTP API."""
        prompt = system_prompt or "You are a helpful assistant."
        if context:
            prompt += "\n\nContext:\n" + "\n".join(context)
        prompt += f"\n\nUser: {query}\nAssistant:"
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=10.0)
            res.raise_for_status()
            response_text = res.json().get("response", "").strip()
            return response_text, 1.0
        except Exception as e:
            logger.error(f"Ollama API generation failed: {e}")
            raise
    
    def answer_rag_query(self,
                        query: str,
                        retrieved_chunks: List[Tuple[str, float, str, str]]) -> Tuple[str, float, bool]:
        """
        Answer query using RAG chunks (compatible with ResponseGenerator)
        
        Args:
            query: User query
            retrieved_chunks: List of (text, similarity, url, heading)
            
        Returns:
            (response, confidence, is_fallback)
        """
        if not retrieved_chunks:
            return "I don't have information about that.", 0.0, True
        
        # Extract chunks and check relevance
        best_score = retrieved_chunks[0][1]
        if best_score < 0.5:  # Low confidence threshold
            return "I don't have specific information about that topic.", 0.3, True
        
        # Build context from chunks
        context = [chunk[0][:300] for chunk in retrieved_chunks[:3]]
        
        system_prompt = """You are a helpful college information assistant for AIMS College. 
Answer questions based only on the provided context. 
If the context doesn't contain the answer, say 'I don't have specific information about that.'
Keep responses concise (1-2 sentences)."""
        
        response, conf = self.generate_response(query, context, system_prompt)
        
        return response, conf, False

    def generate_content(self, prompt: str):
        """Gemini-compatible interface for formatting"""
        class Response:
            def __init__(self, text):
                self.text = text
        
        response_text = self.runner.generate(prompt)
        return Response(response_text)


class HybridLLMService:
    """
    Hybrid service: Try Ollama first, fallback to template-based
    Safe for production use
    """
    
    def __init__(self):
        """Initialize hybrid service"""
        self.ollama_available = False
        self.ollama_service = None
        
        try:
            self.ollama_service = OllamaLLMService()
            self.ollama_available = True
            logger.info("✅ Using Ollama Qwen for generation")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}, falling back to templates")
    
    def answer_rag_query(self,
                        query: str,
                        retrieved_chunks: List[Tuple[str, float, str, str]]) -> Tuple[str, float, bool]:
        """
        Answer RAG query with Ollama or fallback to template
        """
        if self.ollama_available and self.ollama_service:
            try:
                return self.ollama_service.answer_rag_query(query, retrieved_chunks)
            except Exception as e:
                logger.warning(f"Ollama generation failed: {e}")
        
        return self._template_response(query, retrieved_chunks)

    def generate_response(self, 
                         query: str, 
                         context: List[str],
                         system_prompt: Optional[str] = None) -> Tuple[str, float]:
        """Fallback for generic generation"""
        if self.ollama_available and self.ollama_service:
            return self.ollama_service.generate_response(query, context, system_prompt)
        return "I'm currently unable to generate a dynamic response.", 0.0


    
    def _template_response(self,
                          query: str,
                          retrieved_chunks: List[Tuple[str, float, str, str]]) -> Tuple[str, float, bool]:
        """Template-based fallback response"""
        if not retrieved_chunks:
            return "I don't have information about that.", 0.0, True
        
        best_score = retrieved_chunks[0][1]
        if best_score < 0.5:
            return "I don't have specific information about that topic.", 0.3, True
        
        # Use first chunk as answer
        answer = retrieved_chunks[0][0][:200]
        confidence = min(best_score, 1.0)
        
        return answer, confidence, False


# Helper function for easy integration
def get_llm_service(use_ollama: bool = True):
    """Get appropriate LLM service"""
    if use_ollama:
        try:
            return OllamaLLMService()
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return HybridLLMService()
    else:
        return HybridLLMService()


if __name__ == "__main__":
    # Test
    try:
        service = OllamaLLMService()
        
        # Test with context
        response, conf = service.generate_response(
            "What is AI?",
            ["AI is artificial intelligence", "It involves machine learning"]
        )
        print(f"Response: {response}")
        print(f"Confidence: {conf}")
        
        # Test RAG-style
        chunks = [
            ("AIMS offers computer science programs", 0.8, "https://aims.edu", "Programs"),
            ("The college has excellent faculty", 0.7, "https://aims.edu", "About"),
        ]
        response, conf, is_fallback = service.answer_rag_query(
            "What programs does AIMS offer?",
            chunks
        )
        print(f"\nRAG Response: {response}")
        print(f"Confidence: {conf}, Fallback: {is_fallback}")
    except Exception as e:
        print(f"Test failed: {e}")

