"""
Module: pg_loader
Purpose:
    Generic PostgreSQL bulk loader used by the warehouse layer.
    Provides DataFrame-to-table insertion, upserts, truncation,
    and raw SQL execution via SQLAlchemy.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.storage.postgres.connection import get_engine, is_sqlite_mode
from src.storage.postgres.queries import (
    count_statement,
    qualified_name,
    table_exists_statement,
    truncate_statement,
)
from src.utils.logger import get_logger

logger = get_logger("storage.postgres")


class PostgresLoader:
    """
    Reusable bulk loader for warehouse ETL operations.
    Supports both PostgreSQL and SQLite (fallback / local mode) seamlessly.
    """

    def __init__(self, connection_string: Optional[str] = None):
        self._custom_conn_str = connection_string
        self._engine: Optional[Engine] = None

    # ── Engine lifecycle ────────────────────────────────────

    @property
    def engine(self) -> Engine:
        """Lazily obtain and return the SQLAlchemy engine."""
        if self._engine is None:
            if self._custom_conn_str:
                self._engine = create_engine(self._custom_conn_str)
            else:
                self._engine = get_engine()
        return self._engine

    @property
    def is_sqlite(self) -> bool:
        """Return True if using SQLite dialect."""
        try:
            return self.engine.dialect.name == "sqlite"
        except Exception:
            return is_sqlite_mode()

    def dispose(self) -> None:
        """Dispose of the engine connection pool."""
        if self._engine is not None and self._custom_conn_str:
            self._engine.dispose()
            self._engine = None

    # ── Core operations ─────────────────────────────────────

    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: str,
        if_exists: str = "append",
        index: bool = False,
    ) -> int:
        """
        Load a DataFrame into a PostgreSQL table.

        Args:
            df: The data to load.
            table_name: Target table name (without schema prefix).
            schema: PostgreSQL schema name.
            if_exists: How to behave if the table exists ('append', 'replace', 'fail').
            index: Whether to write the DataFrame index as a column.

        Returns:
            Number of rows loaded.
        """
        if df.empty:
            logger.warning("Empty DataFrame — skipping load to %s.%s", schema, table_name)
            return 0

        # Use chunksize to prevent SQLite "too many SQL variables" limit (max 999 or 32766)
        chunksize = 500 if self.is_sqlite else 1000
        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=schema,
            if_exists=if_exists,
            index=index,
            chunksize=chunksize,
            method="multi",
        )
        logger.info(
            "Loaded %d rows into %s.%s",
            len(df), schema, table_name,
        )
        return len(df)

    def truncate_table(self, table_name: str, schema: str) -> None:
        """Truncate a table (remove all rows, keep structure)."""
        fqn = qualified_name(schema, table_name)
        with self.engine.connect() as conn:
            if self.is_sqlite:
                conn.execute(text(f"DELETE FROM {fqn}"))
            else:
                conn.execute(text(truncate_statement(schema, table_name)))
            conn.commit()
        logger.info("Truncated %s", fqn)

    def execute_sql(self, sql: str, params: dict | None = None) -> None:
        """Execute a raw SQL statement."""
        with self.engine.connect() as conn:
            conn.execute(text(sql), params or {})
            conn.commit()

    def query(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        """Execute a SELECT query and return results as a DataFrame."""
        with self.engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})

    def table_row_count(self, table_name: str, schema: str) -> int:
        """Return the row count of a table."""
        with self.engine.connect() as conn:
            result = conn.execute(text(count_statement(schema, table_name)))
            return result.scalar() or 0

    def table_exists(self, table_name: str, schema: str) -> bool:
        """Check whether a table exists in the given schema."""
        with self.engine.connect() as conn:
            if self.is_sqlite:
                try:
                    conn.execute(text(f"SELECT 1 FROM {schema}.{table_name} LIMIT 0"))
                    return True
                except Exception:
                    return False
            else:
                result = conn.execute(
                    text(table_exists_statement()),
                    {"schema": schema, "table": table_name},
                )
                return bool(result.scalar())

    def get_max_key(self, table_name: str, schema: str, key_column: str) -> int:
        """Return the current maximum surrogate key value, or 0 if table is empty."""
        fqn = f"{schema}.{table_name}"
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT COALESCE(MAX({key_column}), 0) FROM {fqn}"))
            return result.scalar()
