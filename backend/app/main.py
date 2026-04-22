"""FastAPI Application Entry Point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.api import health, stats, leads, analytics
from app.api import chat_phase4
from app.api import admin as admin_api
from app.core.brain import BRAIN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting College Chatbot Backend - Phase 4")
    logger.info(f"Environment: {get_settings().app_name}")
    
    try:
        # Initialize FAISS index and embeddings
        logger.info("\n⚡ Initializing Retrieval Engine...")
        from app.services.retrieval.faiss_index import get_index, INDEX_DIR
        from app.services.embeddings.embedding_service import load_embedding_model
        import os
        
        # Auto-rebuild FAISS on deployment (for ephemeral environments like Railway)
        index_file = os.path.join(INDEX_DIR, "index.faiss")
        if os.path.exists(index_file):
            logger.info("✅ Loading existing FAISS index...")
        else:
            logger.warning("⚠️ FAISS not found. Rebuilding from knowledge base...")
            from scripts.ingest import main as run_ingestion
            exit_code = run_ingestion()
            if exit_code != 0:
                logger.error("❌ FAISS auto-rebuild failed!")
            else:
                logger.info("✅ FAISS auto-rebuild complete.")
        
        # Load FAISS index
        index = get_index()
        stats = index.get_stats()
        logger.info(f"   FAISS Index: {stats['document_count']} documents")
        logger.info(f"   Synced: {stats['synced']}")
        
        # Load embedding model
        model = load_embedding_model()
        logger.info(f"   Embedding Model: Loaded")
        
        logger.info("\n✅ API Ready - POST /api/v1/chat")
        logger.info("   GET /api/v1/health")
        logger.info("   GET /api/v1/stats")
    
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        # Continue anyway, endpoints will handle gracefully

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
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5001",   # Primary frontend server
        "http://localhost:8001",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5001",   # Primary frontend server (127.0.0.1)
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8080",
        "https://www.theaims.ac.in",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (Phase 4 endpoints)
app.include_router(health.router)
app.include_router(stats.router)
app.include_router(chat_phase4.router)
app.include_router(leads.router)
app.include_router(analytics.router)
app.include_router(admin_api.router)  # Admin intelligence (protected by X-Admin-Key)


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
