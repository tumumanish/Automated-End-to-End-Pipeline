"""
Module: connection (PostgreSQL)
Purpose:
    Manage PostgreSQL database connections using SQLAlchemy.
    Credentials are loaded from environment variables — never hardcoded.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.utils.config import get_connection_string
from src.utils.logger import get_logger

logger = get_logger("pipeline")

# Module-level engine cache
_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Return a SQLAlchemy engine (singleton per process).

    The connection string is built from environment variables
    (POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD).
    """
    global _engine
    if _engine is None:
        conn_str = get_connection_string()
        _engine = create_engine(
            conn_str,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        logger.info("PostgreSQL engine created.")
    return _engine


def dispose_engine() -> None:
    """Dispose the current engine and release all connections."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("PostgreSQL engine disposed.")


@contextmanager
def get_connection():
    """
    Context manager that yields a raw DBAPI connection.

    Usage::

        with get_connection() as conn:
            conn.execute(text("SELECT 1"))
    """
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager that yields a SQLAlchemy Session.

    Usage::

        with get_session() as session:
            session.execute(text("SELECT 1"))
    """
    engine = get_engine()
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """
    Test database connectivity.

    Returns:
        True if the database is reachable, False otherwise.
    """
    try:
        with get_connection() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection test: OK")
        return True
    except Exception as exc:
        logger.error("PostgreSQL connection test failed: %s", exc)
        return False
