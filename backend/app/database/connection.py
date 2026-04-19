"""
Database Connection and Session Management

This module handles PostgreSQL connection pooling and SQLAlchemy session management.
"""

from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

# Create database engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=pool.QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.debug,
    connect_args={"connect_timeout": 10}
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)


def get_db():
    """Dependency for FastAPI routes to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database tables"""
    try:
        from app.models.db_models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise


async def close_db():
    """Close database connections"""
    engine.dispose()
    logger.info("🔌 Database connections closed")
