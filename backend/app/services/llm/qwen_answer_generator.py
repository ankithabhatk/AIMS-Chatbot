"""
Integration Bridge: Replace AnswerGenerator with Ollama Qwen

Drop-in replacement for the existing answer_generator.py
Swaps template-based answers for Qwen-powered synthesis
"""

import logging
from typing import List, Tuple, Optional
import sys
import os

sys.path.insert(0, '/Users/maneeth/Desktop/Chat-Bot')

logger = logging.getLogger(__name__)

# Try to import Qwen service
try:
    from run_ollama_qwen import OllamaQwenRunner
    OLLAMA_AVAILABLE = True
except Exception as e:
    logger.warning(f"Ollama not available: {e}")
    OLLAMA_AVAILABLE = False


class QwenAnswerGenerator:
    """Replace AnswerGenerator with Qwen 2.5 Coder"""
    
    def __init__(self, 
                 max_answer_length: int = 1400,
                 use_qwen: bool = True):
        """
        Initialize Qwen-based answer generator
        
        Args:
            max_answer_length: Max response length in chars
            use_qwen: Use Qwen (else fallback to templates)
        """
        self.max_answer_length = max_answer_length
        self.use_qwen = use_qwen and OLLAMA_AVAILABLE
        
        if self.use_qwen:
            try:
                self.runner = OllamaQwenRunner()
                if self.runner.check_ollama_running():
                    logger.info("✅ Qwen Answer Generator initialized")
                else:
                    logger.warning("Ollama not running, using templates")
                    self.use_qwen = False
            except Exception as e:
                logger.warning(f"Qwen init failed: {e}, using templates")
                self.use_qwen = False
    
    def synthesize(self, query: str, chunks: List[Tuple[str, float, str, str]]) -> str:
        """
        Synthesize answer using Qwen
        
        Args:
            query: User question
            chunks: List of (text, similarity, url, heading)
            
        Returns:
            Synthesized answer
        """
        if not chunks:
            return ""
        
        # Extract chunk content
        chunk_texts = [chunk[0] for chunk in chunks[:5]]  # Top 5 chunks
        context = "\n\n".join(chunk_texts)
        
        # Use Qwen if available
        if self.use_qwen:
            return self._synthesize_qwen(query, context)
        else:
            return self._synthesize_template(query, chunks)
    
    def _synthesize_qwen(self, query: str, context: str) -> str:
        """Generate answer using Qwen"""
        prompt = f"""You are a helpful college information assistant. 
Answer the user's question based on the provided context.
Keep the answer concise (1-2 sentences).
If the context doesn't contain the answer, say "I don't have specific information about that."

Context:
{context}

User Question: {query}

Answer:"""
        
        try:
            response = self.runner.generate(prompt)
            # Truncate if too long
            if len(response) > self.max_answer_length:
                response = response[:self.max_answer_length].rsplit(' ', 1)[0] + "..."
            return response
        except Exception as e:
            logger.error(f"Qwen synthesis failed: {e}")
            return ""
    
    def _synthesize_template(self, query: str, chunks: List[Tuple[str, float, str, str]]) -> str:
        """Fallback template-based synthesis"""
        if not chunks:
            return ""
        
        # Just return first chunk
        answer = chunks[0][0]
        if len(answer) > self.max_answer_length:
            answer = answer[:self.max_answer_length].rsplit(' ', 1)[0] + "..."
        return answer


def get_answer_generator(use_qwen: bool = True) -> QwenAnswerGenerator:
    """Factory function - returns Qwen-based generator"""
    return QwenAnswerGenerator(use_qwen=use_qwen)
