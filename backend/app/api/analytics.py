"""Analytics Endpoint"""

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from typing import Optional
import logging

router = APIRouter(prefix="/api/v1", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/logs/recent")
def recent_logs(n: int = 20):
    from app.services.logger import get_recent_logs
    return get_recent_logs(n)


@router.get("/logs/avg-confidence")
def avg_confidence():
    from app.services.logger import get_avg_confidence
    return {"avg_confidence": get_avg_confidence()}


@router.get("/logs/low-confidence")
def low_confidence_queries(threshold: float = 0.4):
    from app.services.logger import get_low_confidence_queries
    return get_low_confidence_queries(threshold)


@router.get("/leads/all")
def list_all_leads():
    from app.services.lead_service import get_all_leads
    leads = get_all_leads()
    return [
        {
            "session_id": l.session_id,
            "name": l.name,
            "phone": l.phone,
            "email": l.email,
            "course_interest": l.course_interest,
            "intent": l.intent,
            "timestamp": l.timestamp,
        }
        for l in leads
    ]


@router.get("/analytics/stats")
def get_analytics_stats():
    from app.services.analytics import get_stats
    return get_stats()


@router.get("/leads/export")
def export_leads():
    from app.utils.export import export_leads_to_csv
    path = export_leads_to_csv()
    return FileResponse(path, media_type="text/csv", filename="leads_export.csv")


@router.get("/analytics/dashboard")
async def get_analytics_dashboard(time_range: str = Query("7d", pattern="^(1d|7d|30d)$")):
    """
    Get analytics dashboard data
    
    Parameters:
    - time_range: "1d", "7d", or "30d"
    
    Returns:
    - Chat statistics
    - Lead statistics
    - Performance metrics
    """
    try:
        logger.info(f"Analytics request: {time_range}")
        
        # TODO: Implement analytics queries
        # - Query chat_events
        # - Query leads
        # - Calculate metrics
        
        return {
            "period": time_range,
            "chat_stats": {
                "total_queries": 0,
                "unique_sessions": 0,
                "avg_response_time": 0,
                "fallback_count": 0
            },
            "lead_stats": {
                "total_leads": 0,
                "unique_leads": 0,
                "avg_lead_score": 0
            },
            "fallback_rate": 0
        }
    
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return {"error": "Analytics retrieval failed"}
