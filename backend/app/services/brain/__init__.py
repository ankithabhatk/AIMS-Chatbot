"""
Brain Layer - Production-grade refinement layer for answer quality.

This module contains 5 critical components:
1. rag_cleaner - Removes noise and duplicates from chunks
2. context_resolver - Injects context for follow-ups
3. answer_scorer - Validates quality (CRITICAL gating)
4. domain_guard - Rejects out-of-domain queries
5. answer_merger - Intelligently combines answers
6. answer_judge - LLM-backed validation and repair
"""

from .rag_cleaner import clean_chunks
from .context_resolver import inject_context
from .answer_scorer import score_answer
from .answer_judge import JudgeResult, judge_and_repair_answer
from .domain_guard import is_out_of_domain
from .answer_merger import merge_answers

__all__ = [
    "clean_chunks",
    "inject_context", 
    "score_answer",
    "JudgeResult",
    "judge_and_repair_answer",
    "is_out_of_domain",
    "merge_answers"
]
