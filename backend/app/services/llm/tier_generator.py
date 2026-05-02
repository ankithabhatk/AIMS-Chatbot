"""
Tiered LLM Generator - Executes generation based on model tier.
Supports Small (Fast/Cheap) and Medium (Complex/Smart) models.
"""

import logging
import os
from typing import List, Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TierGenerator:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ TierGenerator: OpenAI client initialized")
            except Exception as e:
                logger.warning(f"TierGenerator: Failed to initialize OpenAI: {e}")

    def generate(self, tier: str, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generates a response using the specified model tier.
        """
        if not self.client:
            logger.error("TierGenerator: No OpenAI client. Cannot generate.")
            return ""

        # Map tiers to specific models - prefer cost-effective options
        model_map = {
            "small": "gpt-3.5-turbo",      # Fast and cheap
            "medium": "gpt-3.5-turbo"      # Still good quality for most queries
        }
        
        model = model_map.get(tier, "gpt-3.5-turbo")

        try:
            from app.services.llm.prompt_builder import (
                build_messages, validate_answer, apply_grounding_prefix, FALLBACK_ANSWER
            )
            messages = build_messages(query, context_chunks)

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=250,
                top_p=1.0,
            )

            raw = response.choices[0].message.content.strip()
            answer = apply_grounding_prefix(validate_answer(raw))
            logger.info("TierGenerator: answer=%d chars model=%s", len(answer), model)
            return answer

        except Exception as e:
            logger.error("TierGenerator: generation failed tier=%s: %s", tier, e)
            return ""

    def judge_answer(
        self,
        tier: str,
        query: str,
        answer: str,
        context_chunks: List[Dict[str, Any]],
    ) -> Optional[Tuple[bool, str]]:
        """Evaluate whether an answer is correct, relevant, and AIMS-specific."""
        if not self.client:
            logger.warning("TierGenerator: No OpenAI client. Skipping judge.")
            return None

        prompt = f"""You are a strict answer evaluator for AIMS Institutes.
Use ONLY the provided context to judge the answer.

QUESTION:
{query}

CONTEXT:
{self._format_context(context_chunks)}

ANSWER:
{answer}

EVALUATION RULES:
- Mark GOOD only if the answer is correct, relevant, specific to AIMS, and grounded in context.
- Mark BAD if it is vague, unsupported, contradictory, off-domain, or misses the question.
- Do not reward length or confident tone.

Reply in exactly this format:
VERDICT: GOOD or BAD
REASON: one short sentence
"""

        try:
            response = self.client.chat.completions.create(
                model=self._model_for_tier(tier),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=80,
                top_p=1.0,
            )
            content = response.choices[0].message.content.strip()
            verdict_line = content.splitlines()[0].upper() if content else ""
            approved = "GOOD" in verdict_line and "BAD" not in verdict_line
            reason = content.replace("\n", " ")[:200] or "empty_judge_response"
            logger.info("TierGenerator: Judge verdict=%s reason=%s", approved, reason)
            return approved, reason
        except Exception as e:
            # Gracefully handle API errors (quota, rate limit, etc.)
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "rate_limit" in error_str:
                logger.warning(f"TierGenerator: API quota/rate limit hit. Judge disabled.")
            else:
                logger.error(f"TierGenerator: Judge failed for tier {tier}: {e}")
            return None

    def repair_answer(
        self,
        tier: str,
        query: str,
        answer: str,
        context_chunks: List[Dict[str, Any]],
        feedback: str,
    ) -> str:
        """Regenerate one corrected answer using judge feedback."""
        if not self.client:
            logger.warning("TierGenerator: No OpenAI client. Cannot repair answer.")
            return ""

        prompt = f"""You are an academic assistant for AIMS Institutes.
The previous answer failed validation. Rewrite it using ONLY the context.

QUESTION:
{query}

CONTEXT:
{self._format_context(context_chunks)}

PREVIOUS ANSWER:
{answer}

VALIDATION FEEDBACK:
{feedback}

INSTRUCTIONS:
- Correct the answer instead of explaining the mistake.
- Stay specific to AIMS Institutes.
- If the context lacks the requested detail, say that clearly.
- Keep the answer concise and professional.

CORRECTED ANSWER:"""

        try:
            response = self.client.chat.completions.create(
                model=self._model_for_tier(tier),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=220,
                top_p=0.95,
            )
            repaired = response.choices[0].message.content.strip()
            logger.info("TierGenerator: Repaired answer (%d chars)", len(repaired))
            return repaired
        except Exception as e:
            logger.error(f"TierGenerator: Repair failed for tier {tier}: {e}")
            return ""

    def _model_for_tier(self, tier: str) -> str:
        model_map = {
            "small": "gpt-3.5-turbo",
            "medium": "gpt-3.5-turbo",
        }
        return model_map.get(tier, "gpt-3.5-turbo")

    def _format_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        context_lines = []
        for chunk in context_chunks[:5]:
            heading = chunk.get("heading", "Info")
            content = chunk.get("content", "")[:500]
            if content.strip():
                context_lines.append(f"[{heading}]\n{content}")
        return "\n\n".join(context_lines) if context_lines else "No relevant data found."

_tier_generator: Optional[TierGenerator] = None

def get_tier_generator() -> TierGenerator:
    global _tier_generator
    if _tier_generator is None:
        _tier_generator = TierGenerator()
    return _tier_generator
