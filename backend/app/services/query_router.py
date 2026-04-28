"""
Query Router & Latency Optimizer - Control which pipeline to use based on query type

Decides:
- Use fast path (structured) vs expensive path (debate)
- Skip verification layer if confidence already high
- Reduce chunk count for simple queries
- Skip LLM reranking if FAISS score is excellent
"""

import logging
from typing import Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionPath(str, Enum):
    """Execution paths with different latency/quality tradeoffs"""
    FAST = "fast"          # ~200ms - direct structured lookup
    NORMAL = "normal"      # ~800ms - RAG with standard processing
    DEEP = "deep"          # ~1500ms+ - RAG + debate + verification
    SEARCH = "search"      # ~500ms - keyword search only, no LLM


class QueryProfile:
    """Analyze query to determine optimal execution path"""
    
    def __init__(self, query: str):
        self.query = query.lower()
        self.words = query.split()
        self.length = len(self.words)
        self.has_numbers = any(c.isdigit() for c in query)
        self.is_simple = self.length <= 3
        self.is_complex = self.length > 10
        self.is_reasoning = self._detect_reasoning()
        self.is_comparison = self._detect_comparison()
        self.is_structured_intent = self._detect_structured_intent()
    
    def _detect_reasoning(self) -> bool:
        """Check if query needs reasoning/debate"""
        triggers = [
            "worth", "value", "better", "why", "how",
            "should i", "which is best", "compare", "vs"
        ]
        return any(t in self.query for t in triggers)
    
    def _detect_comparison(self) -> bool:
        """Check if query is comparing two things"""
        return any(w in self.query for w in ["vs", "versus", "compare", "difference between"])
    
    def _detect_structured_intent(self) -> bool:
        """Check if query matches structured KB intents"""
        structured_keywords = ["fee", "admission", "course", "contact", "scholarship"]
        return any(k in self.query for k in structured_keywords)


def select_execution_path(
    query: str,
    base_confidence: float = 0.7,
    mode: str = "rag"
) -> Dict[str, Any]:
    """Select execution path based on query and current confidence
    
    Args:
        query: User query
        base_confidence: Initial confidence from structured/RAG
        mode: Current mode (structured/rag/fallback)
    
    Returns:
        Configuration dict with:
        - path: which execution path to use
        - retrieve_top_k: how many chunks to retrieve
        - use_debate: whether to run debate
        - use_verification: whether to verify
        - use_reranking: whether to use LLM reranking
    """
    
    profile = QueryProfile(query)
    
    logger.debug(f"[ROUTER] Query profile: simple={profile.is_simple} "
                f"complex={profile.is_complex} reasoning={profile.is_reasoning}")
    
    # RULE 1: Already high confidence → fast path (skip expensive layers)
    if base_confidence > 0.8 and not profile.is_reasoning:
        logger.info("[ROUTER] High confidence, using FAST path")
        return {
            "path": ExecutionPath.FAST,
            "retrieve_top_k": 3,
            "use_debate": False,
            "use_verification": False,
            "use_reranking": False,
            "latency_target_ms": 200
        }
    
    # RULE 2: Simple queries (1-3 words) → normal, not debate
    if profile.is_simple and mode == "rag":
        logger.info("[ROUTER] Simple query, using SEARCH path")
        return {
            "path": ExecutionPath.SEARCH,
            "retrieve_top_k": 5,
            "use_debate": False,
            "use_verification": False,
            "use_reranking": False,
            "latency_target_ms": 500
        }
    
    # RULE 3: Structured intent → use fast path through structured KB
    if profile.is_structured_intent and mode == "structured":
        logger.info("[ROUTER] Structured intent, using FAST path")
        return {
            "path": ExecutionPath.FAST,
            "retrieve_top_k": 0,  # No RAG needed
            "use_debate": False,
            "use_verification": False,
            "use_reranking": False,
            "latency_target_ms": 100
        }
    
    # RULE 4: Complex reasoning queries → use DEEP path with debate
    if profile.is_reasoning or profile.is_comparison:
        logger.info("[ROUTER] Reasoning query, using DEEP path with debate")
        return {
            "path": ExecutionPath.DEEP,
            "retrieve_top_k": 10,
            "use_debate": True,
            "use_verification": True,
            "use_reranking": True,
            "latency_target_ms": 1500
        }
    
    # DEFAULT: Normal RAG processing
    logger.info("[ROUTER] Standard query, using NORMAL path")
    return {
        "path": ExecutionPath.NORMAL,
        "retrieve_top_k": 5,
        "use_debate": False,
        "use_verification": True,
        "use_reranking": False,
        "latency_target_ms": 800
    }


def optimize_retrieval_config(
    query: str,
    base_confidence: float = 0.7
) -> Dict[str, Any]:
    """Get optimized retrieval configuration
    
    Returns:
        Config dict with:
        - top_k: number of chunks to retrieve
        - min_score: minimum relevance score
        - use_reranking: whether to rerank
    """
    
    profile = QueryProfile(query)
    
    # Simple queries need fewer chunks
    if profile.is_simple:
        return {
            "top_k": 3,
            "min_score": 0.4,
            "use_reranking": False
        }
    
    # Complex queries need more context
    if profile.is_complex:
        return {
            "top_k": 10,
            "min_score": 0.3,
            "use_reranking": True
        }
    
    # Default
    return {
        "top_k": 5,
        "min_score": 0.35,
        "use_reranking": False
    }


def should_skip_layer(
    layer: str,
    base_confidence: float,
    base_score: float = 0.7
) -> bool:
    """Decide if we can skip expensive processing layer
    
    Args:
        layer: Layer name ("verification", "reranking", "debate")
        base_confidence: Current confidence score
        base_score: Baseline quality score
    
    Returns:
        True if layer can be skipped
    """
    
    # Skip expensive layers if already confident
    if layer == "verification" and base_confidence > 0.75:
        logger.debug("[ROUTER] Skipping verification (high confidence)")
        return True
    
    if layer == "reranking" and base_score > 0.8:
        logger.debug("[ROUTER] Skipping reranking (high base score)")
        return True
    
    if layer == "debate" and base_confidence > 0.80:
        logger.debug("[ROUTER] Skipping debate (already confident)")
        return True
    
    return False


def estimate_latency(execution_config: Dict[str, Any]) -> int:
    """Estimate query latency in milliseconds based on configuration"""
    return execution_config.get("latency_target_ms", 800)


def log_execution_metrics(
    query: str,
    execution_config: Dict[str, Any],
    actual_latency_ms: int
) -> None:
    """Log execution metrics for monitoring"""
    logger.info(
        f"[METRICS] query_len={len(query)} "
        f"path={execution_config['path']} "
        f"latency={actual_latency_ms}ms "
        f"target={execution_config.get('latency_target_ms')}ms"
    )


def get_retrieval_strategy(query: str) -> str:
    """Get retrieval strategy for this query
    
    Returns: "keyword", "semantic", or "hybrid"
    """
    profile = QueryProfile(query)
    
    # Structured queries prefer keyword search
    if profile.is_structured_intent:
        return "keyword"
    
    # Complex reasoning needs semantic understanding
    if profile.is_reasoning:
        return "semantic"
    
    # Default: hybrid
    return "hybrid"
