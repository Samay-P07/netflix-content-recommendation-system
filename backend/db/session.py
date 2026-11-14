"""
Database Session Management
Provides SQLAlchemy engine, session maker, and connection resilience.
"""

import os
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from backend.core.config import settings
from backend.db.models import Base

logger = logging.getLogger(__name__)

engine = None
SessionLocal = None
_db_available: bool = False

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"connect_timeout": 3}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    _db_available = True
    logger.info("Successfully connected to PostgreSQL at %s:%s", settings.DB_HOST, settings.DB_PORT)
except Exception as e:
    logger.warning("PostgreSQL unavailable (%s). Falling back to local SQLite engine.", e)
    _db_available = False
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        dev_db_path = "/tmp/cinematch_dev.db"
    else:
        dev_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "cinematch_dev.db"
        )
    engine = create_engine(
        f"sqlite:///{dev_db_path}",
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Initialized local SQLite fallback at %s", dev_db_path)


def is_db_available() -> bool:
    """Returns True if database connection is operational."""
    return engine is not None and SessionLocal is not None


def init_db() -> None:
    """Initializes tables in the active database engine."""
    if engine is not None:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created successfully.")
        except Exception as e:
            logger.warning("Could not initialize database tables: %s", e)


# Auto-ensure tables exist upon module import
init_db()


def get_db() -> Generator[Optional[Session], None, None]:
    """FastAPI dependency for yielding database session."""
    if SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
