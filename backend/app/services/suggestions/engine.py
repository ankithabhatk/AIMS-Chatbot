"""Suggestion Engine - Generate follow-up questions"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """Generate contextual follow-up suggestions based on query"""
    
    # Heuristic mappings (query keyword → suggestions)
    # Later: Replace with ML-based suggestions from analytics
    SUGGESTIONS_MAP = {
        "admission": [
            "What documents are required?",
            "What is the eligibility criteria?",
            "When is the application deadline?"
        ],
        "fees": [
            "Is there a payment plan available?",
            "Are scholarships offered?",
            "What is the scholarship eligibility?"
        ],
        "placement": [
            "What is the average salary?",
            "Which companies recruit from AIMS?",
            "What is the placement rate?"
        ],
        "course": [
            "What is the course duration?",
            "What is the course fee?",
            "What are the career prospects?"
        ],
        "hostel": [
            "What is the hostel fee?",
            "Is hostel compulsory?",
            "What amenities are available?"
        ],
        "program": [
            "What programs are offered?",
            "What is the eligibility for this program?",
            "What is the duration and fee?"
        ],
        "campus": [
            "What facilities are available on campus?",
            "How far is the campus from the city?",
            "What is the transportation facility?"
        ],
        "faculty": [
            "What is the faculty qualification?",
            "What is the student-faculty ratio?",
            "Are visiting experts invited?"
        ]
    }
    
    # Default suggestions (if no match)
    DEFAULT_SUGGESTIONS = [
        "Tell me about AIMS programs",
        "What is the admission process?",
        "Are scholarships available?"
    ]
    
    @staticmethod
    def generate(query: str, fallback: bool = False) -> List[str]:
        """
        Generate suggestions for follow-up questions
        
        Args:
            query: User's original query
            fallback: Whether fallback was used (affects suggestion strategy)
        
        Returns:
            List of 2-3 suggestions (empty if fallback)
        """
        try:
            # Don't suggest follow-ups for fallback cases (encourage contacting support)
            if fallback:
                return []
            
            query_lower = query.lower()
            
            # Find matching keywords
            for keyword, suggestions in SuggestionEngine.SUGGESTIONS_MAP.items():
                if keyword in query_lower:
                    logger.debug(f"Generated {len(suggestions)} suggestions for keyword: {keyword}")
                    return suggestions
            
            # No specific match, return defaults
            logger.debug("Using default suggestions (no keyword match)")
            return SuggestionEngine.DEFAULT_SUGGESTIONS
        
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return []
    
    @staticmethod
    def get_top_queries_suggestions(top_queries: List[str]) -> List[str]:
        """
        Get most helpful suggestions based on top user queries
        
        Args:
            top_queries: Most frequently asked queries from stats
        
        Returns:
            List of contextual suggestions
        """
        try:
            if not top_queries:
                return SuggestionEngine.DEFAULT_SUGGESTIONS
            
            # Generate suggestions based on most common queries
            all_suggestions = set()
            for query in top_queries[:3]:  # Top 3
                suggestions = SuggestionEngine.generate(query, fallback=False)
                all_suggestions.update(suggestions)
            
            return list(all_suggestions)[:5]  # Return up to 5
        
        except Exception as e:
            logger.error(f"Failed to get suggestions from queries: {e}")
            return SuggestionEngine.DEFAULT_SUGGESTIONS


# Global singleton
_engine: Optional[SuggestionEngine] = None


def get_suggestion_engine() -> SuggestionEngine:
    """Get suggestion engine instance"""
    global _engine
    if _engine is None:
        _engine = SuggestionEngine()
    return _engine
