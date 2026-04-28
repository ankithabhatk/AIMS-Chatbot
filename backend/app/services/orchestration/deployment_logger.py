"""
Minimal Deployment Logging Module

Captures 4 critical fields for controlled deployment observation:
1. user_query - The exact query from user
2. detected_intents - List of intents detected
3. response - The final answer returned
4. fallback - Whether fallback was triggered
5. fallback_reason - Why fallback occurred (optional but powerful)

This is NOT for production analytics.
This is for OBSERVATION during controlled deployment.

Usage:
    from app.services.orchestration.deployment_logger import log_deployment_event
    
    log_deployment_event(
        query="What are BCA fees?",
        intents=["fees"],
        response="BCA fees are ₹30,000 - ₹60,000",
        fallback=False,
        fallback_reason=None
    )
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Deployment logs directory
LOGS_DIR = Path(__file__).parent.parent.parent.parent / "logs" / "deployment"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Current deployment log file
DEPLOYMENT_LOG_FILE = LOGS_DIR / "deployment_observations.jsonl"


def log_deployment_event(
    query: str,
    intents: List[str],
    response: str,
    fallback: bool,
    fallback_reason: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    raw_query: Optional[str] = None,
    intent_scores: Optional[Dict[str, float]] = None,
    response_type: Optional[str] = None,
    matched_keywords: Optional[List[str]] = None
) -> None:
    """
    Log a single deployment observation event.
    
    Args:
        query: Processed query (after typo correction, normalization)
        intents: List of detected intents
        response: Final answer returned to user
        fallback: Whether fallback was triggered
        fallback_reason: Why fallback occurred (e.g., "no_intent", "low_confidence", "routing_gap")
        session_id: Optional session identifier
        metadata: Optional additional context
        raw_query: Original query before processing (CRITICAL for debugging)
        intent_scores: Top intent scores for debugging threshold issues
        response_type: How response was generated ("structured", "rag", "fallback", "form", "counselor")
        matched_keywords: Keywords that matched in the query (for language gap analysis)
    
    Returns:
        None
    
    Example:
        log_deployment_event(
            raw_query="feees for bca",
            query="fees for bca",
            intents=["fees"],
            intent_scores={"fees": 0.95, "courses": 0.12},
            matched_keywords=["fees", "bca"],
            response="BCA fees are ₹30,000 - ₹60,000",
            response_type="structured",
            fallback=False,
            fallback_reason=None,
            session_id="user_123",
            metadata={"course": "BCA", "confidence": 0.95}
        )
    """
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "raw_query": raw_query or query,  # Original query before processing
            "processed_query": query,  # Query after typo correction, normalization
            "matched_keywords": matched_keywords or [],  # Keywords that matched
            "detected_intents": intents,
            "final_intent": intents[0] if intents else None,
            "intent_scores": intent_scores or {},  # Top 3 scores for debugging
            "response_type": response_type or "unknown",  # How response was generated
            "response": response[:500],  # Truncate long responses
            "fallback": fallback,
            "fallback_reason": fallback_reason,
            "session_id": session_id,
            "metadata": metadata or {}
        }
        
        # Append to JSONL file (one JSON object per line)
        with open(DEPLOYMENT_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        logger.debug(f"[DEPLOYMENT_LOG] Logged event: intents={intents}, keywords={matched_keywords}, response_type={response_type}, fallback={fallback}")
        
    except Exception as e:
        logger.error(f"[DEPLOYMENT_LOG_ERROR] Failed to log event: {e}")


def get_deployment_logs(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Read deployment logs from file.
    
    Args:
        limit: Maximum number of recent logs to return (None = all)
    
    Returns:
        List of log entries
    """
    try:
        if not DEPLOYMENT_LOG_FILE.exists():
            return []
        
        logs = []
        with open(DEPLOYMENT_LOG_FILE, "r") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        # Return most recent logs first
        if limit:
            return logs[-limit:]
        return logs
    
    except Exception as e:
        logger.error(f"[DEPLOYMENT_LOG_ERROR] Failed to read logs: {e}")
        return []


def analyze_deployment_logs() -> Dict[str, Any]:
    """
    Quick analysis of deployment logs.
    
    Returns:
        Dictionary with key metrics:
        - total_queries: Total queries logged
        - fallback_rate: % of queries that triggered fallback
        - top_intents: Most common intents detected
        - fallback_reasons: Distribution of fallback reasons
        - language_mismatches: Potential keyword mismatches (raw vs processed)
        - low_confidence_intents: Intents with low scores (threshold issues)
        - routing_errors: Cases where intent was detected but wrong response_type used
        - language_gaps: Keywords that didn't match (for normalization rules)
    """
    logs = get_deployment_logs()
    
    if not logs:
        return {"status": "no_logs_yet"}
    
    total = len(logs)
    fallback_count = sum(1 for log in logs if log.get("fallback"))
    
    # Collect intents
    all_intents = []
    for log in logs:
        all_intents.extend(log.get("detected_intents", []))
    
    # Count intent frequencies
    intent_counts = {}
    for intent in all_intents:
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    # Collect fallback reasons
    fallback_reasons = {}
    for log in logs:
        if log.get("fallback"):
            reason = log.get("fallback_reason", "unknown")
            fallback_reasons[reason] = fallback_reasons.get(reason, 0) + 1
    
    # Detect language mismatches (raw vs processed query differences)
    language_mismatches = []
    for log in logs:
        raw = log.get("raw_query", "").lower()
        processed = log.get("processed_query", "").lower()
        if raw != processed:
            language_mismatches.append({
                "raw": raw,
                "processed": processed,
                "fallback": log.get("fallback"),
                "reason": log.get("fallback_reason")
            })
    
    # Detect low confidence intents (potential threshold issues)
    low_confidence_intents = []
    for log in logs:
        scores = log.get("intent_scores", {})
        for intent, score in scores.items():
            if score < 0.65:  # Below typical threshold
                low_confidence_intents.append({
                    "intent": intent,
                    "score": score,
                    "query": log.get("processed_query"),
                    "fallback": log.get("fallback")
                })
    
    # Detect routing errors (correct intent but wrong response_type)
    routing_errors = []
    for log in logs:
        intents = log.get("detected_intents", [])
        response_type = log.get("response_type", "unknown")
        fallback = log.get("fallback")
        
        # Heuristic: if intent detected but response is fallback/form, might be routing error
        if intents and response_type in ["fallback", "form"] and not fallback:
            routing_errors.append({
                "intents": intents,
                "response_type": response_type,
                "query": log.get("processed_query"),
                "confidence": log.get("metadata", {}).get("confidence")
            })
    
    # Detect language gaps (queries with no matched keywords)
    language_gaps = []
    for log in logs:
        matched = log.get("matched_keywords", [])
        if not matched and log.get("fallback"):
            language_gaps.append({
                "raw_query": log.get("raw_query"),
                "processed_query": log.get("processed_query"),
                "fallback_reason": log.get("fallback_reason"),
                "intent_scores": log.get("intent_scores", {})
            })
    
    # Count response types
    response_types = {}
    for log in logs:
        rt = log.get("response_type", "unknown")
        response_types[rt] = response_types.get(rt, 0) + 1
    
    return {
        "total_queries": total,
        "fallback_rate": f"{(fallback_count / total * 100):.1f}%",
        "fallback_count": fallback_count,
        "top_intents": sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        "fallback_reasons": fallback_reasons,
        "response_types": response_types,
        "language_mismatches_count": len(language_mismatches),
        "language_mismatches_sample": language_mismatches[:5],  # First 5 examples
        "low_confidence_intents_count": len(low_confidence_intents),
        "low_confidence_intents_sample": low_confidence_intents[:5],  # First 5 examples
        "routing_errors_count": len(routing_errors),
        "routing_errors_sample": routing_errors[:5],  # First 5 examples
        "language_gaps_count": len(language_gaps),
        "language_gaps_sample": language_gaps[:5],  # First 5 examples
        "log_file": str(DEPLOYMENT_LOG_FILE)
    }


def export_deployment_logs_csv() -> str:
    """
    Export deployment logs to CSV for analysis.
    
    Returns:
        Path to CSV file
    """
    import csv
    
    logs = get_deployment_logs()
    
    if not logs:
        logger.warning("[DEPLOYMENT_LOG] No logs to export")
        return None
    
    csv_file = LOGS_DIR / "deployment_observations.csv"
    
    try:
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "raw_query",
                    "processed_query",
                    "matched_keywords",
                    "detected_intents",
                    "final_intent",
                    "intent_scores",
                    "response_type",
                    "fallback",
                    "fallback_reason",
                    "session_id",
                    "confidence"
                ]
            )
            writer.writeheader()
            
            for log in logs:
                writer.writerow({
                    "timestamp": log.get("timestamp"),
                    "raw_query": log.get("raw_query"),
                    "processed_query": log.get("processed_query"),
                    "matched_keywords": ",".join(log.get("matched_keywords", [])),
                    "detected_intents": ",".join(log.get("detected_intents", [])),
                    "final_intent": log.get("final_intent"),
                    "intent_scores": json.dumps(log.get("intent_scores", {})),
                    "response_type": log.get("response_type"),
                    "fallback": log.get("fallback"),
                    "fallback_reason": log.get("fallback_reason"),
                    "session_id": log.get("session_id"),
                    "confidence": log.get("metadata", {}).get("confidence")
                })
        
        logger.info(f"[DEPLOYMENT_LOG] Exported {len(logs)} logs to {csv_file}")
        return str(csv_file)
    
    except Exception as e:
        logger.error(f"[DEPLOYMENT_LOG_ERROR] Failed to export CSV: {e}")
        return None
