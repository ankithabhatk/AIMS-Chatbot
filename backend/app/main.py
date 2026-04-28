"""FastAPI application entry point for the local AIMS assistant."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin as admin_api
from app.api import analytics, chat, health, leads, stats, deployment_logs
from app.config import get_settings
from app.core.brain import BRAIN

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting AIMS chatbot backend")
    logger.info("Environment: %s", get_settings().app_name)

    try:
        import faiss
        from app.services.conversation_store import get_conversation_store
        from app.services.embeddings.embedding_service import embed_text, load_embedding_model
        from app.services.intelligence_layer import get_intelligence_layer
        from app.services.query_cache import get_query_response_cache
        from app.services.query_processing import get_query_processor
        from app.services.retrieval.faiss_index import INDEX_DIR, get_index
        from app.services.retrieval.hybrid_retriever import get_hybrid_retriever
        from scripts.rebuild_local_index import main as rebuild_local_index

        logger.info("Initializing retrieval engine...")
        index_file = os.path.join(INDEX_DIR, "index.faiss")
        if not os.path.exists(index_file):
            logger.warning("FAISS index missing. Rebuilding from local knowledge cache...")
            if rebuild_local_index() != 0:
                logger.error("Local FAISS rebuild failed during startup")

        index = get_index()
        stats_data = index.get_stats()

        if stats_data.get("metric_type") != faiss.METRIC_INNER_PRODUCT:
            logger.warning("Legacy FAISS metric detected. Rebuilding cosine index locally...")
            if rebuild_local_index() == 0:
                index.load()
                stats_data = index.get_stats()
                logger.info("Local cosine index rebuild complete")
            else:
                logger.error("Local cosine index rebuild failed")

        logger.info("FAISS index: %s documents", stats_data["document_count"])
        logger.info("Index synced: %s", stats_data["synced"])

        load_embedding_model()
        embed_text("aims mba admission process")
        get_query_processor()
        get_intelligence_layer()
        get_query_response_cache()
        get_conversation_store()

        retriever = get_hybrid_retriever()
        warm_query = get_query_processor().process("mba fees")
        retriever.search(warm_query, k=1, vector_k=2, keyword_k=2)

        logger.info("Embedding model loaded")
        logger.info("Retrieval caches warmed")
        logger.info("API ready at /api/v1/chat")
    except Exception as exc:
        logger.error("Startup error: %s", exc, exc_info=True)

    yield

    logger.info("Shutting down AIMS chatbot backend")


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5001",
        "http://localhost:8001",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5001",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8080",
        "https://www.theaims.ac.in",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(stats.router)
app.include_router(chat.router)
app.include_router(leads.router)
app.include_router(analytics.router)
app.include_router(admin_api.router)
app.include_router(deployment_logs.router)


@app.get("/")
async def root():
    return {
        "message": "College Chatbot API",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "ready",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
