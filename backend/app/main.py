"""FastAPI Application Entry Point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.api import chat_v2, leads, analytics, health
from app.core.brain import BRAIN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting College Chatbot Backend")
    logger.info(f"Environment: {get_settings().app_name}")
    
    # Load project brain (reads memory.json)
    logger.info("\n📖 Loading Project Brain...")
    brain_dict = BRAIN.load()
    logger.info(f"   Project: {brain_dict.get('project_name')}")
    logger.info(f"   Phase: {brain_dict.get('current_phase')} - {brain_dict.get('phase_status')}")
    logger.info(f"   Completed: {len(brain_dict.get('completed_modules', []))} modules")
    logger.info(f"   Pending: {len(brain_dict.get('pending_modules', []))} modules")
    logger.info(f"   Identified Risks: {len(brain_dict.get('risks', []))}")
    
    try:
        # Initialize retrieval engine (FAISS + embeddings)
        logger.info("\n⚡ Initializing Retrieval Engine...")
        chat_v2.initialize_retrieval()
        logger.info("✅ Retrieval engine ready")
        
        health_result = await chat_v2.health_check()
        logger.info(f"   FAISS vectors: {health_result.get('faiss_vectors')}")
        logger.info(f"   Chunks loaded: {health_result.get('chunks_loaded')}")
        
        logger.info("✅ Chatbot fully initialized and ready\n")
    
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        # Continue anyway, but log the error

    yield
    
    # Shutdown
    logger.info("🛑 Shutting down College Chatbot Backend")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://www.theaims.ac.in"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chat_v2.router)
app.include_router(leads.router)
app.include_router(analytics.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "College Chatbot API",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "ready"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
