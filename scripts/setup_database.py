#!/usr/bin/env python
"""
Script: setup_database
Purpose:
    Connect to the warehouse (PostgreSQL, or the SQLite fallback) and create
    all required schemas and tables. Safe to execute multiple times
    (idempotent SQL).

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

from sqlalchemy import text
from src.storage.postgres.connection import get_engine, is_sqlite_mode
from src.storage.sql_utils import adapt_sql_for_sqlite, split_sql_statements
from src.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("pipeline")

SQL_DIR = PROJECT_ROOT / "sql" / "postgres"

# SQL files to execute in order
SQL_FILES = [
    "01_create_schemas.sql",
    "02_create_raw_tables.sql",
    "03_create_validation_tables.sql",
    "03_create_staging_tables.sql",
    "04_create_dimensions.sql",
    "05_create_facts.sql",
    "06_create_views.sql",
    "07_create_monitoring_tables.sql",
    "08_create_lineage_tables.sql",
]


def run_sql_file(conn, filepath: Path, is_sqlite: bool = False) -> None:
    """Execute a SQL file against the given connection."""
    sql = filepath.read_text(encoding="utf-8")
    statements = split_sql_statements(sql)
    for stmt in statements:
        if is_sqlite:
            stmt = adapt_sql_for_sqlite(stmt)
            if not stmt:
                continue
        try:
            conn.execute(text(stmt))
        except Exception as exc:
            message = str(exc).lower()
            # SQLite does not support CREATE OR REPLACE or repeated indexes.
            if is_sqlite and ("already exists" in message or "syntax error" in message):
                logger.debug("Skipping SQLite statement (%s): %s", exc, stmt[:120])
                continue
            raise
    conn.commit()


def main() -> None:
    print("Connecting to Data Warehouse Engine...")
    logger.info("Database setup started.")

    try:
        engine = get_engine()
        is_sqlite = engine.dialect.name == "sqlite" or is_sqlite_mode()
        db_type = "SQLite (Local Offline Mode)" if is_sqlite else "PostgreSQL Server"
        print(f"  Target Warehouse Engine: {db_type}")

        with engine.connect() as conn:
            for sql_file in SQL_FILES:
                filepath = SQL_DIR / sql_file
                if not filepath.exists():
                    print(f"  SKIP  {sql_file} (file not found)")
                    logger.warning("SQL file not found: %s", filepath)
                    continue

                print(f"  RUN   {sql_file} ... ", end="")
                run_sql_file(conn, filepath, is_sqlite=is_sqlite)
                print("OK")
                logger.info("Executed: %s", sql_file)

        print("\nDatabase setup completed successfully.")
        logger.info("Database setup completed.")

    except Exception as exc:
        print(f"\nDatabase setup FAILED: {exc}")
        logger.error("Database setup failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
