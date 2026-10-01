"""
Module: view_manager
Purpose:
    Create and refresh analytical views in the analytics schema.
    Views are defined in SQL and can be re-created on demand.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.file_utils import get_project_root
from src.utils.logger import get_logger

logger = get_logger("warehouse.views")


class ViewManager:
    """
    Manage analytical views in the PostgreSQL ``analytics`` schema.

    Views are defined in ``sql/postgres/06_create_views.sql`` and
    can be refreshed by re-executing that file.
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()

    def refresh_views(self) -> None:
        """
        Re-create all analytical views by executing the views SQL file.
        Views use CREATE OR REPLACE so this is idempotent.
        """
        sql_file = get_project_root() / "sql" / "postgres" / "06_create_views.sql"

        if not sql_file.exists():
            logger.error("Views SQL file not found: %s", sql_file)
            return

        sql = sql_file.read_text(encoding="utf-8")

        # Split on semicolons and execute each statement
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
        for stmt in statements:
            try:
                self._loader.execute_sql(stmt)
            except Exception as exc:
                logger.error("Failed to execute view statement: %s", exc)

        logger.info("Analytical views refreshed (%d statements)", len(statements))

    def list_views(self) -> list[str]:
        """Return the names of all views in the analytics schema."""
        try:
            df = self._loader.query(
                "SELECT table_name FROM information_schema.views "
                "WHERE table_schema = 'analytics' ORDER BY table_name"
            )
            return df["table_name"].tolist()
        except Exception:
            return []

    def query_view(self, view_name: str, limit: int = 100):
        """Query an analytical view and return a DataFrame."""
        import pandas as pd
        try:
            return self._loader.query(
                f"SELECT * FROM analytics.{view_name} LIMIT {limit}"
            )
        except Exception as exc:
            logger.error("Failed to query view '%s': %s", view_name, exc)
            return pd.DataFrame()
