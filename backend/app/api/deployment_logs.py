"""
Deployment Logs API

Simple endpoints to view and analyze deployment observation logs.
Used during controlled deployment phase to monitor system behavior.

Endpoints:
- GET /api/deployment/logs - Get recent logs
- GET /api/deployment/analysis - Get quick analysis
- GET /api/deployment/export - Export logs as CSV
"""

from fastapi import APIRouter, Query
from typing import List, Dict, Any
import logging

from app.services.orchestration.deployment_logger import (
    get_deployment_logs,
    analyze_deployment_logs,
    export_deployment_logs_csv
)

router = APIRouter(prefix="/api/deployment", tags=["deployment"])
logger = logging.getLogger(__name__)


@router.get("/logs")
async def get_logs(limit: int = Query(50, ge=1, le=1000)) -> Dict[str, Any]:
    """
    Get recent deployment observation logs.
    
    Args:
        limit: Number of recent logs to return (default: 50, max: 1000)
    
    Returns:
        List of log entries with query, intents, response, fallback info
    """
    try:
        logs = get_deployment_logs(limit=limit)
        return {
            "status": "success",
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        logger.error(f"[DEPLOYMENT_API] Error fetching logs: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/analysis")
async def get_analysis() -> Dict[str, Any]:
    """
    Get quick analysis of deployment logs.
    
    Returns:
        Analysis including:
        - total_queries: Total queries logged
        - fallback_rate: % of queries that triggered fallback
        - top_intents: Most common intents
        - fallback_reasons: Distribution of fallback reasons
    """
    try:
        analysis = analyze_deployment_logs()
        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"[DEPLOYMENT_API] Error analyzing logs: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/export")
async def export_logs() -> Dict[str, Any]:
    """
    Export deployment logs to CSV file.
    
    Returns:
        Path to exported CSV file
    """
    try:
        csv_path = export_deployment_logs_csv()
        if csv_path:
            return {
                "status": "success",
                "csv_file": csv_path,
                "message": "Logs exported successfully"
            }
        else:
            return {
                "status": "error",
                "message": "No logs to export"
            }
    except Exception as e:
        logger.error(f"[DEPLOYMENT_API] Error exporting logs: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get deployment logging status.
    
    Returns:
        Status of deployment logging system
    """
    try:
        analysis = analyze_deployment_logs()
        
        if analysis.get("status") == "no_logs_yet":
            return {
                "status": "ready",
                "message": "Deployment logging is active and ready. No logs collected yet.",
                "logs_collected": 0
            }
        
        return {
            "status": "active",
            "message": "Deployment logging is active and collecting data",
            "logs_collected": analysis.get("total_queries", 0),
            "fallback_rate": analysis.get("fallback_rate"),
            "log_file": analysis.get("log_file")
        }
    except Exception as e:
        logger.error(f"[DEPLOYMENT_API] Error getting status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
