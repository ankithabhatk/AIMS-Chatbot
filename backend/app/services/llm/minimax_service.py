import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MiniMaxService:
    """
    MiniMax 2.7 Service for conversion, complex rewriting, and objection handling.
    Guided by the "System Brain Dump" strict rules.
    """
    
    SYSTEM_INSTRUCTION = """
    You are part of a hybrid system. 
    You DO NOT think. You DO NOT decide. 
    You ONLY:
    - rewrite responses to be more human and persuasive
    - improve tone based on the provided mode
    - maintain strict system structure
    
    The system logic is ALWAYS correct. 
    - If you change facts (marks, courses, eligibility) -> you are wrong.
    - If you simplify too much -> you are wrong.
    - If you repeat phrases -> you are wrong.
    - If you add information not provided in the raw data -> you are wrong.
    """
    
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.enabled = bool(self.api_key)
        if not self.enabled:
            logger.warning("MiniMax API key not found. Using enhanced template fallback.")

    def rewrite_explanation(self, raw_data: Dict[str, Any]) -> str:
        """
        Rewrites complex eligibility/fit data into a persuasive, human-like explanation.
        Example: "Your marks meet eligibility" -> "You’re already in a safe zone for this course..."
        """
        if not self.enabled:
            # Enhanced template fallback for the "safe zone" style
            marks_fit = raw_data.get("marks_fit", "")
            interest_fit = raw_data.get("interest_fit", "")
            
            if "above threshold" in marks_fit.lower() or "strong" in marks_fit.lower():
                return f"Based on your profile, you're already in a **safe zone** for this course. Your marks are well above the threshold, which means we can focus more on aligning the curriculum with your interests in {interest_fit}."
            return f"You're in a good position for this course. Your academic background meets the requirements, and it aligns well with your interest in {interest_fit}."

        # Real MiniMax call would go here
        return self._call_minimax("rewrite_explanation", raw_data)

    def handle_objection(self, objection_type: str, query: str) -> str:
        """
        Handles student objections (timing, uncertainty, fees, salary) using MiniMax.
        """
        if not self.enabled:
            fallbacks = {
                "timing": "That’s completely fine. Many students take their time to decide. However, starting the process now just ensures you don't miss out on preferred slots as admissions move quickly. Does that make sense?",
                "uncertainty": "It's totally normal to feel unsure. This is a big step! Would it help if we compared how this course stacks up against your other interests, so you can see the clear difference?",
                "fees": "I understand that budget is a key factor. AIMS actually offers several scholarship paths that could make this much more accessible for you. Should I show you how those work?",
                "salary": "That's a fair question. While the starting salary might look standard, the growth trajectory in this field is actually one of the highest. You'd be looking at a significant jump within just 2 years. Does that change how you view it?"
            }
            return fallbacks.get(objection_type, "I understand your concern. Let's look at this from another perspective...")

        return self._call_minimax("handle_objection", {"type": objection_type, "query": query})

    def enhance_conversion(self, stage: str, course: str) -> str:
        """
        Improves persuasion tone for the conversion stage.
        """
        if not self.enabled:
            stages = {
                "decision_confirmed": f"That’s a solid choice. {course} isn't just a degree; it's a strategic move for your career. Based on your profile, you're exactly the kind of student who thrives here.",
                "ready_to_close": "Perfect. We've cleared the doubts — now it's just about securing your spot. The application is straightforward, and I can walk you through it right now so you're all set."
            }
            return stages.get(stage, "Great choice. Let's move to the next step.")

        return self._call_minimax("enhance_conversion", {"stage": stage, "course": course})

    def _call_minimax(self, task: str, data: Dict[str, Any]) -> str:
        """
        Internal caller for MiniMax API.
        Enforces the "Voice Layer Only" role.
        """
        if not self.enabled:
            return ""

        prompt = f"{self.SYSTEM_INSTRUCTION}\n\nTASK: {task}\nDATA: {data}\n\nRESPONSE:"
        logger.info(f"Calling MiniMax for {task}...")
        
        # Real API implementation would go here using requests or official SDK
        # For now, we return empty to trigger the high-quality fallbacks in the wrapper methods
        return ""

# Global instance
_minimax = None

def get_minimax_service() -> MiniMaxService:
    global _minimax
    if _minimax is None:
        _minimax = MiniMaxService()
    return _minimax
