
import logging
import re
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class AnswerShaper:
    """
    Answer Shaping Layer - Transforms raw retrieved chunks into conversational responses.
    Implements question detection, course filtering, and formatting rules.
    """

    GREETINGS = ["hi", "hello", "hey", "good morning", "good afternoon", "greetings"]
    GOODBYES = ["bye", "goodbye", "see you", "thanks", "thank you"]
    FOLLOW_UPS = ["tell me more", "more details", "explain", "details", "expand"]
    
    YES_NO_KEYWORDS = ["is", "does", "do", "can", "are", "will", "has"]
    COURSES = ["mba", "mca", "bba", "bca", "phd"]

    def __init__(self):
        pass

    def detect_type(self, query: str) -> str:
        """Phase 1: Question Type Detection"""
        q = query.lower().strip()
        
        # Check for greetings
        if any(word == q or q.startswith(word + " ") for word in self.GREETINGS):
            return "greeting"
        
        # Check for goodbyes
        if any(word in q for word in self.GOODBYES):
            return "greeting"
            
        # Check for follow-up
        if any(keyword in q for keyword in self.FOLLOW_UPS):
            return "follow_up"
            
        # Check for Yes/No (heuristic: starts with auxiliary verb)
        first_word = q.split()[0] if q.split() else ""
        if first_word in self.YES_NO_KEYWORDS or q.endswith("?"):
            # Simple check if it's a binary question
            if any(word in q for word in ["what", "how", "why", "where", "when", "who"]):
                return "factual"
            return "yes_no"
            
        return "factual"

    def filter_chunks_by_course(self, query: str, chunks: List[Tuple]) -> List[Tuple]:
        """Phase 4: Course-Specific Control"""
        q = query.lower()
        mentioned_courses = [c for c in self.COURSES if c in q]
        
        if not mentioned_courses:
            return chunks
            
        filtered = []
        for chunk in chunks:
            text = chunk[0].lower()
            # If any mentioned course is in the text, or if text mentions no specific course
            if any(course in text for course in mentioned_courses):
                filtered.append(chunk)
                
        return filtered if filtered else chunks

    def shape_answer(self, query: str, chunks: List[Tuple], query_type: str) -> Dict:
        """Main method to shape the answer"""
        
        # Phase 2: Greeting Handler
        if query_type == "greeting":
            q = query.lower()
            if any(word in q for word in self.GOODBYES):
                return {
                    "answer": "Goodbye! Feel free to reach out anytime if you have more questions about AIMS Institutes.",
                    "type": "greeting",
                    "follow_up": ""
                }
            return {
                "answer": "Hi! I'm the AIMS Academic Assistant. What would you like to know about AIMS Institutes today?",
                "type": "greeting",
                "follow_up": "I can help with MBA, MCA, BBA, placements, and more."
            }

        # Filter chunks if needed
        relevant_chunks = self.filter_chunks_by_course(query, chunks)
        
        if not relevant_chunks:
            return {
                "answer": "I'm sorry, I don't have specific details on that in AIMS Institutes' records. Would you like to ask about our programs or placements?",
                "type": "factual",
                "follow_up": ""
            }

        # Phase 8: Remove Noise and Phase 5: Short Answer Rule
        raw_text = " ".join([c[0] for c in relevant_chunks[:2]])
        # Clean text
        clean_text = self._clean_content(raw_text)
        
        # Extract key sentences (limit to 3-4)
        sentences = re.split(r'(?<=[.!?]) +', clean_text)
        short_answer = " ".join(sentences[:3])

        # Phase 7: Always include context
        if "AIMS Institutes" not in short_answer:
            short_answer = f"At AIMS Institutes, {short_answer}"

        # Phase 3: Yes/No Answer Format
        if query_type == "yes_no":
            # Simple heuristic: if we have relevant chunks, answer is likely Yes
            short_answer = f"Yes, AIMS Institutes {short_answer}"
            if not short_answer.endswith("?"):
                follow_up = "Would you like more details about this?"
            else:
                follow_up = ""
        else:
            follow_up = "Would you like more details on this topic?"

        # Phase 6: Follow-up Expansion
        if query_type == "follow_up":
            # Use more sentences for follow-up
            short_answer = " ".join(sentences[:6])
            follow_up = "Is there anything else specific you'd like to know?"

        # Phase 9: Optional Suggestions
        suggestions = ""
        if "mca" in query.lower():
            suggestions = "\n\nRelated programs you may consider: BCA, B.Sc (IT)."
        elif "mba" in query.lower():
            suggestions = "\n\nRelated programs you may consider: PGDM, BBA."

        return {
            "answer": short_answer + suggestions,
            "type": query_type,
            "follow_up": follow_up
        }

    def _clean_content(self, text: str) -> str:
        """Phase 8: Remove Noise"""
        # Remove repeated sentences
        sentences = re.split(r'(?<=[.!?]) +', text)
        seen = set()
        unique_sentences = []
        for s in sentences:
            s_clean = s.strip().lower()
            if s_clean not in seen and len(s_clean) > 10:
                seen.add(s_clean)
                unique_sentences.append(s.strip())
        
        text = " ".join(unique_sentences)
        # Remove navigation artifacts
        text = re.sub(r'Home\s*>\s*[^>]+', '', text)
        # Remove marketing fluff like "Click here"
        text = re.sub(r'Click here to [^.]+.', '', text)
        return text

# Global instance
_shaper = AnswerShaper()

def get_answer_shaper() -> AnswerShaper:
    return _shaper
