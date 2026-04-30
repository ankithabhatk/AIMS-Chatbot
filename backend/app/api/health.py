"""
Health check endpoint for monitoring and testing.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "service": "aims-chatbot",
        "version": "1.0.0"
    }


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AIMS Chatbot API",
        "status": "running",
        "docs": "/docs"
    }
