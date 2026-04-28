"""
Answer Judge - LLM-backed validation and one-pass repair.

This layer sits after answer generation/merge and before final fallback.
It keeps the existing heuristic scorer as a safety net, then asks the LLM to
judge groundedness when a generator with judge/repair methods is available.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .answer_scorer import score_answer

logger = logging.getLogger(__name__)


@dataclass
class JudgeResult:
    answer: str
    approved: bool
    score: float
    reason: str
    repaired: bool = False


def judge_and_repair_answer(
    query: str,
    answer: str,
    context_chunks: List[Dict[str, Any]],
    generator: Any,
    tier: str,
    min_score: float = 0.5,
) -> JudgeResult:
    """
    Validate an answer and repair it once if the LLM judge rejects it.

    The function is deliberately defensive: if the LLM judge is unavailable,
    it falls back to the existing deterministic scorer instead of breaking the
    chat pipeline.
    """
    score, reason = score_answer(answer, query)
    if not answer:
        return JudgeResult(answer="", approved=False, score=score, reason=reason)

    if not context_chunks or not hasattr(generator, "judge_answer"):
        return JudgeResult(
            answer=answer,
            approved=score >= min_score,
            score=score,
            reason=f"heuristic_only:{reason}",
        )

    try:
        judge = generator.judge_answer(tier, query, answer, context_chunks)
    except Exception as e:
        logger.warning(f"Judge call failed with exception: {e}. Using heuristic scorer.")
        judge = None
    
    if judge is None:
        return JudgeResult(
            answer=answer,
            approved=score >= min_score,
            score=score,
            reason=f"judge_unavailable:{reason}",
        )

    judge_approved, judge_reason = judge
    if judge_approved and score >= min_score:
        return JudgeResult(
            answer=answer,
            approved=True,
            score=score,
            reason=f"judge_good:{judge_reason}; {reason}",
        )

    if not hasattr(generator, "repair_answer"):
        return JudgeResult(
            answer=answer,
            approved=False,
            score=score,
            reason=f"judge_bad_no_repair:{judge_reason}; {reason}",
        )

    repaired = generator.repair_answer(tier, query, answer, context_chunks, judge_reason)
    repaired_score, repaired_reason = score_answer(repaired, query)
    if not repaired:
        return JudgeResult(
            answer=answer,
            approved=False,
            score=score,
            reason=f"repair_empty:{judge_reason}; {reason}",
        )

    repaired_judge = generator.judge_answer(tier, query, repaired, context_chunks)
    repaired_approved = repaired_score >= min_score
    repaired_judge_reason: Optional[str] = None
    if repaired_judge is not None:
        repaired_approved, repaired_judge_reason = repaired_judge
        repaired_approved = repaired_approved and repaired_score >= min_score

    final_reason = f"repaired:{repaired_reason}"
    if repaired_judge_reason:
        final_reason = f"{final_reason}; {repaired_judge_reason}"

    logger.info(
        "[JUDGE] repaired=%s approved=%s score=%.2f reason=%s",
        True,
        repaired_approved,
        repaired_score,
        final_reason,
    )
    return JudgeResult(
        answer=repaired,
        approved=repaired_approved,
        score=repaired_score,
        reason=final_reason,
        repaired=True,
    )
