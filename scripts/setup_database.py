#!/usr/bin/env python
"""
Script: setup_database
Purpose:
    Connect to PostgreSQL and create required schemas and Phase 2 tables.
    Safe to execute multiple times (idempotent SQL).

Usage:
    python scripts/setup_database.py
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so ``src`` imports work.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_connection_string
from src.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("pipeline")

SQL_DIR = PROJECT_ROOT / "sql" / "postgres"

# SQL files to execute in order (Phase 2 only)
SQL_FILES = [
    "01_create_schemas.sql",
    "02_create_raw_tables.sql",
]


def run_sql_file(conn, filepath: Path) -> None:
    """Execute a SQL file against the given connection."""
    sql = filepath.read_text(encoding="utf-8")
    # Execute each statement separately (split on semicolons)
    from sqlalchemy import text
    statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
    for stmt in statements:
        conn.execute(text(stmt))
    conn.commit()


def main() -> None:
    from sqlalchemy import create_engine

    conn_str = get_connection_string()
    print(f"Connecting to PostgreSQL...")
    logger.info("Database setup started.")

    try:
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            for sql_file in SQL_FILES:
                filepath = SQL_DIR / sql_file
                if not filepath.exists():
                    print(f"  SKIP  {sql_file} (file not found)")
                    logger.warning("SQL file not found: %s", filepath)
                    continue

                print(f"  RUN   {sql_file} ... ", end="")
                run_sql_file(conn, filepath)
                print("OK")
                logger.info("Executed: %s", sql_file)

        engine.dispose()
        print("\nDatabase setup completed successfully.")
        logger.info("Database setup completed.")

    except Exception as exc:
        print(f"\nDatabase setup FAILED: {exc}")
        logger.error("Database setup failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
