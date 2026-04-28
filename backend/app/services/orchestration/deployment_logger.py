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
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a single deployment observation event.
    
    Args:
        query: User's exact query
        intents: List of detected intents
        response: Final answer returned to user
        fallback: Whether fallback was triggered
        fallback_reason: Why fallback occurred (e.g., "no_intent", "low_confidence", "routing_gap")
        session_id: Optional session identifier
        metadata: Optional additional context
    
    Returns:
        None
    
    Example:
        log_deployment_event(
            query="What are BCA fees?",
            intents=["fees"],
            response="BCA fees are ₹30,000 - ₹60,000",
            fallback=False,
            fallback_reason=None,
            session_id="user_123",
            metadata={"course": "BCA", "confidence": 0.95}
        )
    """
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "intents": intents,
            "response": response[:500],  # Truncate long responses
            "fallback": fallback,
            "fallback_reason": fallback_reason,
            "session_id": session_id,
            "metadata": metadata or {}
        }
        
        # Append to JSONL file (one JSON object per line)
        with open(DEPLOYMENT_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        logger.debug(f"[DEPLOYMENT_LOG] Logged event: intents={intents}, fallback={fallback}")
        
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
        - language_mismatches: Potential keyword mismatches
    """
    logs = get_deployment_logs()
    
    if not logs:
        return {"status": "no_logs_yet"}
    
    total = len(logs)
    fallback_count = sum(1 for log in logs if log.get("fallback"))
    
    # Collect intents
    all_intents = []
    for log in logs:
        all_intents.extend(log.get("intents", []))
    
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
    
    return {
        "total_queries": total,
        "fallback_rate": f"{(fallback_count / total * 100):.1f}%",
        "fallback_count": fallback_count,
        "top_intents": sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        "fallback_reasons": fallback_reasons,
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
                fieldnames=["timestamp", "query", "intents", "fallback", "fallback_reason", "session_id"]
            )
            writer.writeheader()
            
            for log in logs:
                writer.writerow({
                    "timestamp": log.get("timestamp"),
                    "query": log.get("query"),
                    "intents": ",".join(log.get("intents", [])),
                    "fallback": log.get("fallback"),
                    "fallback_reason": log.get("fallback_reason"),
                    "session_id": log.get("session_id")
                })
        
        logger.info(f"[DEPLOYMENT_LOG] Exported {len(logs)} logs to {csv_file}")
        return str(csv_file)
    
    except Exception as e:
        logger.error(f"[DEPLOYMENT_LOG_ERROR] Failed to export CSV: {e}")
        return None
