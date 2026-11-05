"""
Module: connection (PostgreSQL)
Purpose:
    Manage PostgreSQL database connections using SQLAlchemy.
    Credentials are loaded from environment variables — never hardcoded.
"""

import os
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
_is_sqlite: bool = False


def is_sqlite_mode() -> bool:
    """Return True if currently operating in SQLite fallback mode."""
    global _is_sqlite
    return _is_sqlite


def get_engine() -> Engine:
    """
    Return a SQLAlchemy engine (singleton per process).

    Tries to connect to PostgreSQL using configuration from environment variables.
    If PostgreSQL is unreachable (e.g. offline, local dev showcase) or if
    WAREHOUSE_BACKEND is set to 'sqlite', seamlessly falls back to a local SQLite
    database at data/warehouse/warehouse.db with attached schemas.
    """
    global _engine, _is_sqlite
    if _engine is not None:
        return _engine

    from pathlib import Path
    from sqlalchemy import event
    import sqlite3

    backend = os.getenv("WAREHOUSE_BACKEND", "postgres").lower()

    if backend != "sqlite":
        try:
            conn_str = get_connection_string()
            temp_engine = create_engine(
                conn_str,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3},
            )
            # Test immediate connectivity
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _engine = temp_engine
            _is_sqlite = False
            logger.info("Connected to PostgreSQL warehouse database.")
            return _engine
        except Exception as exc:
            logger.warning(
                "PostgreSQL unreachable (%s). Falling back to local SQLite warehouse.",
                exc,
            )

    # SQLite fallback
    from src.utils.file_utils import get_project_root
    db_dir = get_project_root() / "data" / "warehouse"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = (db_dir / "warehouse.db").resolve()

    _engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    _is_sqlite = True

    @event.listens_for(_engine, "connect")
    def _attach_sqlite_schemas(dbapi_conn, _):
        if isinstance(dbapi_conn, sqlite3.Connection):
            cur = dbapi_conn.cursor()
            for schema in ["raw", "staging", "warehouse", "analytics", "monitoring", "metadata"]:
                try:
                    cur.execute(f"ATTACH DATABASE '{db_path.as_posix()}' AS {schema};")
                except Exception:
                    pass
            cur.close()

    logger.info("SQLite warehouse engine initialized at: %s", db_path)
    return _engine


def dispose_engine() -> None:
    """Dispose the current engine and release all connections."""
    global _engine, _is_sqlite
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _is_sqlite = False
        logger.info("Database engine disposed.")



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
