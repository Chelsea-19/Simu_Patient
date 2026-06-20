"""
Database engine and session management.

SQLModel tables are created automatically on first startup via init_db().
"""

from __future__ import annotations

from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("db")

_engine = None


def _get_engine():
    """Create or return the cached database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            connect_args=connect_args,
        )
        logger.info("Database engine created: %s", settings.DATABASE_URL)
    return _engine


def init_db() -> None:
    """
    Create all tables that do not exist yet.

    Model imports register tables with SQLModel metadata.
    """
    import app.models  # noqa: F401

    engine = _get_engine()
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables initialized")


def get_session() -> Generator[Session, None, None]:
    """Yield a database session and ensure proper cleanup."""
    engine = _get_engine()
    with Session(engine) as session:
        yield session
