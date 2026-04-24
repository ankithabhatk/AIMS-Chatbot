"""
Local intelligence layer for the production chat path.

Responsibilities:
- robust query understanding with typo handling
- safe session memory for follow-up queries
- conversational but extractive answer shaping
- internal control tokens for downstream routing
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from app.services.llm.answer_generator import get_answer_generator
from app.services.query_processing import get_query_processor

logger = logging.getLogger(__name__)


class IntelligenceLayer:
    """Coordinate query understanding, memory, and grounded response shaping."""

    CONTEXTUAL_TOPICS = {"fees", "placements", "hostel", "admission", "course"}

    def __init__(self) -> None:
        self.sessions: Dict[str, Dict[str, Optional[str]]] = {}
        self.processor = get_query_processor()

    def process_query(self, query: str, session_id: str) -> Dict:
        """Process a user query and safely enrich it with session context."""
        processed = self.processor.process(query)
        session = self._get_session(session_id)
        memory_notes: List[str] = []

        course = processed.get("course")
        topic = processed.get("topic")
        intent = processed.get("intent", "factual")
        corrected_query = processed.get("corrected_query", "")
        retrieval_query = processed.get("query", corrected_query)

        if self._should_use_memory(processed):
            if not course and session.get("active_course"):
                course = session["active_course"]
                memory_notes.append(f"course:{course}")
            if not topic and session.get("active_topic"):
                topic = session["active_topic"]
                memory_notes.append(f"topic:{topic}")

        retrieval_terms = [corrected_query]
        if course and course not in retrieval_query.split():
            retrieval_terms.append(course)
        if topic and topic not in retrieval_query.split():
            retrieval_terms.append(topic)
        retrieval_query = " ".join(part for part in retrieval_terms if part).strip()

        needs_clarification = bool(processed.get("needs_clarification"))
        clarification_message = processed.get("clarification_message")

        if not needs_clarification and topic in self.CONTEXTUAL_TOPICS and not course and not session.get("active_course"):
            clarification_message = f"Which course would you like {topic} information for?"
            needs_clarification = topic in {"fees", "hostel"}

        if not needs_clarification:
            session["last_query"] = query
            session["last_retrieval_query"] = retrieval_query
            session["last_intent"] = intent
            if course:
                session["active_course"] = course
            if topic:
                session["active_topic"] = topic

        control_tokens = list(processed.get("control_tokens", []))
        if course and not any(token.startswith("COURSE:") for token in control_tokens):
            control_tokens.append(f"COURSE:{str(course).upper()}")
        if topic and not any(token.startswith("TOPIC:") for token in control_tokens):
            control_tokens.append(f"TOPIC:{str(topic).upper()}")
        if needs_clarification and "<LOW_CONFIDENCE>" not in control_tokens:
            control_tokens.append("<LOW_CONFIDENCE>")

        return {
            **processed,
            "query": retrieval_query,
            "course": course,
            "topic": topic,
            "category": topic,
            "intent": intent,
            "is_follow_up": intent == "follow_up",
            "memory_notes": memory_notes,
            "needs_clarification": needs_clarification,
            "clarification_message": clarification_message,
            "control_tokens": control_tokens,
        }

    def synthesize_response(self, query_data: Dict, chunks: List[Tuple], confidence: float) -> Dict:
        """Generate a conversational but grounded answer from retrieved chunks."""
        intent = query_data.get("intent", "factual")
        course = query_data.get("course") or "General"
        topic = query_data.get("topic")

        if intent == "greeting":
            return {
                "answer": "Hi! I can help with AIMS courses, admissions, placements, hostel, and fees. What would you like to know?",
                "intent": intent,
                "course": course,
                "topic": topic,
                "confidence": 1.0,
            }

        if intent == "exit":
            return {
                "answer": "Happy to help. If you need anything else about AIMS, feel free to ask.",
                "intent": intent,
                "course": course,
                "topic": topic,
                "confidence": 1.0,
            }

        if not chunks:
            return {
                "answer": "I could not find a matching AIMS record for that. Please try mentioning the course or topic.",
                "intent": intent,
                "course": course,
                "topic": topic,
                "confidence": confidence,
            }

        preferred_chunks = self._prefer_contextual_chunks(chunks, course=course, topic=topic)
        topical_chunks = self._filter_topical_chunks(preferred_chunks, topic=topic)
        generator = get_answer_generator()
        synthesis_chunks = topical_chunks or preferred_chunks
        raw_answer = generator.synthesize(query_data.get("query", ""), synthesis_chunks)
        shaped_answer = self._shape_final_text(
            raw_answer,
            max_sentences=self._max_sentences(query_data),
        )

        if not shaped_answer:
            shaped_answer = self._fallback_to_snippet(synthesis_chunks)

        return {
            "answer": shaped_answer,
            "intent": intent,
            "course": course,
            "topic": topic,
            "confidence": confidence,
        }

    def _get_session(self, session_id: str) -> Dict[str, Optional[str]]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "active_course": None,
                "active_topic": None,
                "last_intent": None,
                "last_query": None,
                "last_retrieval_query": None,
            }
        return self.sessions[session_id]

    def _should_use_memory(self, processed: Dict) -> bool:
        query_tokens = processed.get("keyword_terms", [])
        intent = processed.get("intent")
        missing_context = not processed.get("course") or not processed.get("topic")
        if not missing_context:
            return False
        if intent == "follow_up":
            return True
        return len(query_tokens) <= 4

    def _prefer_contextual_chunks(
        self,
        chunks: List[Tuple],
        course: Optional[str],
        topic: Optional[str],
    ) -> List[Tuple]:
        if not chunks:
            return chunks

        boosted: List[Tuple[float, Tuple]] = []
        for chunk in chunks:
            text = chunk[0].lower() if chunk and chunk[0] else ""
            heading = chunk[3].lower() if len(chunk) > 3 and chunk[3] else ""
            score = float(chunk[1]) if len(chunk) > 1 else 0.0

            if course and course in text:
                score += 0.15
            if course and course in heading:
                score += 0.1
            if topic and topic in text:
                score += 0.12
            if topic and topic in heading:
                score += 0.08

            boosted.append((score, chunk))

        boosted.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in boosted]

    def _filter_topical_chunks(self, chunks: List[Tuple], topic: Optional[str]) -> List[Tuple]:
        if not topic:
            return []

        strict_topical: List[Tuple] = []
        for chunk in chunks:
            chunk_topic = chunk[8] if len(chunk) > 8 else None
            heading = chunk[3].lower() if len(chunk) > 3 and chunk[3] else ""

            if chunk_topic == topic:
                strict_topical.append(chunk)
            elif topic in heading:
                strict_topical.append(chunk)

        if strict_topical:
            return strict_topical[:5]

        topical: List[Tuple] = []
        for chunk in chunks:
            text = chunk[0].lower() if chunk and chunk[0] else ""
            if topic in text:
                topical.append(chunk)

        return topical[:3]

    def _shape_final_text(self, text: str, max_sentences: int) -> str:
        if not text:
            return ""

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        sentences: List[str] = []
        for line in lines:
            normalized = re.sub(r"^[\-\*\u2022]\s*", "", line)
            parts = re.split(r"(?<=[.!?])\s+", normalized)
            for part in parts:
                sentence = part.strip()
                if len(sentence) >= 18:
                    sentences.append(sentence)

        trimmed = sentences[:max_sentences]
        if not trimmed:
            return text.strip()

        return "\n".join(f"- {sentence}" for sentence in trimmed)

    def _max_sentences(self, query_data: Dict) -> int:
        detail_level = query_data.get("detail_level", "normal")
        if detail_level == "brief":
            return 2
        if detail_level == "detailed" or query_data.get("is_follow_up"):
            return 6
        return 4

    def _fallback_to_snippet(self, chunks: List[Tuple]) -> str:
        if not chunks:
            return ""
        text = chunks[0][0] if chunks[0] else ""
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        filtered = [sentence.strip() for sentence in sentences if len(sentence.strip()) >= 18]
        return "\n".join(f"- {sentence}" for sentence in filtered[:3])


_intelligence = IntelligenceLayer()


def get_intelligence_layer() -> IntelligenceLayer:
    """Return the shared intelligence layer."""
    return _intelligence
