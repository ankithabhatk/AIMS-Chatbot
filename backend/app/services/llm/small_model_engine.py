"""
Small Model Engine - Controlled Chatbot Engine (Low-Compute Mode)
Strictly rule-based, deterministic assistant logic.
"""

import logging
from typing import Optional, Dict, Any, Iterable

from app.services.structured_knowledge import (
    detect_program,
    get_admission_structured,
    get_courses_structured,
    get_fees_structured,
    get_placements_structured,
)

logger = logging.getLogger(__name__)

class SmallModelEngine:
    """Deterministic, rule-based engine optimized for low-compute/small models"""

    FALLBACK_RESPONSE = (
        "I didn’t understand.\n\n"
        "Try:\n"
        "• MBA fees\n"
        "• Courses offered\n"
        "• Admission process"
    )

    def process(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process query using strict Small Model Spec rules.
        """
        trimmed_query = query.strip()
        q = " ".join(trimmed_query.lower().split())
        has_fees = "fee" in q or "fees" in q or "tuition" in q or "cost" in q or "price" in q
        has_courses = "course" in q or "courses" in q or "program" in q or "programs" in q
        has_admission = "admission" in q or "apply" in q or "eligibility" in q
        has_placements = "placement" in q or "placements" in q or "salary" in q or "package" in q

        if has_fees and has_placements:
            responses = [
                get_fees_structured(detect_program(q)),
                get_placements_structured(),
            ]
            return self._build_response(
                answer="\n".join(response["answer"] for response in responses if response.get("answer")),
                intent="fees_placements",
                mode="structured",
                sources=self._merge_sources(responses),
            )

        if has_fees:
            return self._from_structured(get_fees_structured(detect_program(q)), "fees")

        if has_courses:
            return self._from_structured(get_courses_structured(detect_program(q)), "courses")

        if has_admission:
            return self._from_structured(get_admission_structured(), "admission")

        if has_placements:
            return self._from_structured(get_placements_structured(), "placements")

        return self._build_response(
            answer=self.FALLBACK_RESPONSE,
            intent="unknown",
            mode="fallback",
            fallback=True,
            confidence=0.2,
        )

    def _from_structured(self, response: Dict[str, Any], intent: str) -> Dict[str, Any]:
        return self._build_response(
            answer=str(response.get("answer") or "").strip(),
            intent=intent,
            mode="structured",
            sources=response.get("sources") or [],
        )

    def _build_response(
        self,
        *,
        answer: str,
        intent: str,
        mode: str,
        fallback: bool = False,
        confidence: float = 1.0,
        sources: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Return a contract-compatible deterministic payload."""
        self_score = {
            "relevance": 0.95 if not fallback else 0.7,
            "clarity": 0.92 if not fallback else 0.95,
            "completeness": 0.9 if not fallback else 0.7,
        }
        return {
            "answer": answer,
            "intent": intent,
            "mode": mode,
            "confidence": confidence,
            "self_score": self_score,
            "fallback": fallback,
            "status": "unlock",
            "sources": list(sources or []),
            "suggestions": [],
        }

    @staticmethod
    def _merge_sources(responses: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
        merged = []
        seen = set()
        for response in responses:
            for source in response.get("sources") or []:
                url = source.get("url") or ""
                if url in seen:
                    continue
                merged.append(source)
                seen.add(url)
        return merged

# Global instance
_engine = None

def get_small_model_engine() -> SmallModelEngine:
    global _engine
    if _engine is None:
        _engine = SmallModelEngine()
    return _engine
