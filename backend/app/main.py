"""FastAPI Application Entry Point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.api import chat, leads, analytics, health
from app.services.data_ingestion import test_with_sample_data
from app.services.embeddings.embedding_service import load_embedding_model
from app.services.retrieval.faiss_index import get_index

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting College Chatbot Backend")
    logger.info(f"Environment: {get_settings().app_name}")
    
    try:
        # Load embedding model
        logger.info("Loading embedding model...")
        load_embedding_model("all-MiniLM-L6-v2")
        logger.info("✅ Embedding model loaded")
        
        # Initialize vector index
        logger.info("Initializing vector index...")
        index = get_index()
        logger.info(f"Index initialized. Stats: {index.get_stats()}")
        
        # Load sample data if index is empty
        if index.doc_count == 0:
            logger.info("Index empty, loading sample data...")
            result = test_with_sample_data()
            logger.info(f"Sample data loaded: {result}")
        
        logger.info("✅ RAG system initialized and ready")
    
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
app.include_router(chat.router)
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
