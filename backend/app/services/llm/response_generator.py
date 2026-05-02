"""
Response Generator for RAG

Generates natural responses from retrieved chunks.
Fallback to template-based if LLM unavailable.
"""

import logging
from typing import List, Tuple, Optional
import os

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generate responses from retrieved context"""
    
    def __init__(self, use_openai: bool = False):
        """
        Initialize response generator
        
        Args:
            use_openai: Whether to use OpenAI API for generation
        """
        self.use_openai = use_openai and os.getenv("OPENAI_API_KEY")
        
        if self.use_openai:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}, using templates")
                self.use_openai = False
    
    def generate(self, query: str, retrieved_chunks: List[Tuple[str, float, str, str]],
                 confidence_threshold: float = 0.7) -> Tuple[str, float, bool]:
        """
        Generate response from query and retrieved chunks
        
        Args:
            query: Original user query
            retrieved_chunks: List of (text, similarity, url, heading)
            confidence_threshold: Min similarity for confident response
            
        Returns:
            (response_text, confidence_score, is_fallback)
        """
        if not retrieved_chunks:
            return self._fallback_response(query)
        
        # Check if we have relevant results
        best_score = retrieved_chunks[0][1]
        
        if best_score < confidence_threshold:
            return self._fallback_response(query)
        
        # Generate response from context
        if self.use_openai:
            return self._generate_openai(query, retrieved_chunks)
        else:
            return self._generate_template(query, retrieved_chunks)
    
    def _generate_template(self, query: str, retrieved_chunks: List[Tuple[str, float, str, str]]) -> Tuple[str, float, bool]:
        """
        Simple template-based response generation
        
        Args:
            query: User query
            retrieved_chunks: Retrieved context
            
        Returns:
            (response, confidence, is_fallback)
        """
        # Extract best chunk
        text, score, url, heading = retrieved_chunks[0]
        
        # Clean and summarize text
        summary = self._summarize_text(text, max_length=200)
        
        # Build response
        response = f"Based on information about '{heading}': {summary}"
        
        # Confidence is the similarity score of best result
        confidence = float(score)
        
        return response, confidence, False
    
    def _generate_openai(self, query: str, retrieved_chunks: List[Tuple[str, float, str, str]]) -> Tuple[str, float, bool]:
        """
        Generate response using OpenAI
        
        Args:
            query: User query
            retrieved_chunks: Retrieved context chunks
            
        Returns:
            (response, confidence, is_fallback)
        """
        try:
            from app.services.llm.prompt_builder import (
                build_messages, validate_answer, apply_grounding_prefix, FALLBACK_ANSWER
            )
            messages = build_messages(query, retrieved_chunks)

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.1,
                max_tokens=250,
                top_p=1.0,
            )

            raw = response.choices[0].message.content.strip()
            answer = apply_grounding_prefix(validate_answer(raw))
            confidence = float(retrieved_chunks[0][1])
            is_fallback = answer == FALLBACK_ANSWER
            return answer, confidence, is_fallback

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}, using template")
            return self._generate_template(query, retrieved_chunks)
    
    def _summarize_text(self, text: str, max_length: int = 200) -> str:
        """Extract first sentences up to max_length"""
        if len(text) <= max_length:
            return text
        
        # Find sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind(".")
        
        if last_period > 0:
            return truncated[:last_period + 1]
        return truncated + "..."
    
    def _fallback_response(self, query: str) -> Tuple[str, float, bool]:
        """
        Fallback response when no relevant chunks found
        
        Returns:
            (response, confidence, is_fallback=True)
        """
        response = (
            f"I don't have specific information about '{query}' in my knowledge base. "
            "Please contact AIMS admissions at admissions@theaims.ac.in or call +91-XXX-XXXX-XXXX for more details."
        )
        return response, 0.0, True


# Global instance
_generator: Optional[ResponseGenerator] = None


def get_generator(use_openai: bool = False) -> ResponseGenerator:
    """Get or create response generator"""
    global _generator
    if _generator is None:
        _generator = ResponseGenerator(use_openai=use_openai)
    return _generator
