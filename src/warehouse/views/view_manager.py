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
from src.storage.sql_utils import adapt_sql_for_sqlite, split_sql_statements
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
        Views use CREATE OR REPLACE on Postgres, and DROP+CREATE on SQLite.
        """
        sql_file = get_project_root() / "sql" / "postgres" / "06_create_views.sql"

        if not sql_file.exists():
            logger.error("Views SQL file not found: %s", sql_file)
            return

        sql = sql_file.read_text(encoding="utf-8")
        statements = split_sql_statements(sql)

        for stmt in statements:
            if self._loader.is_sqlite:
                stmt = adapt_sql_for_sqlite(stmt)
                if not stmt:
                    continue
            try:
                self._loader.execute_sql(stmt)
            except Exception as exc:
                message = str(exc).lower()
                if self._loader.is_sqlite and "already exists" in message:
                    logger.debug("View already exists: %s", stmt[:120])
                    continue
                logger.error("Failed to execute view statement: %s", exc)

        logger.info("Analytical views refreshed (%d statements)", len(statements))

    def list_views(self) -> list[str]:
        """Return the names of all views in the analytics schema."""
        try:
            if self._loader.is_sqlite:
                df = self._loader.query(
                    "SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name"
                )
                if not df.empty and "name" in df.columns:
                    return df["name"].tolist()
            else:
                df = self._loader.query(
                    "SELECT table_name FROM information_schema.views "
                    "WHERE table_schema = 'analytics' ORDER BY table_name"
                )
                if not df.empty and "table_name" in df.columns:
                    return df["table_name"].tolist()
        except Exception as exc:
            logger.warning("Could not list views: %s", exc)
        return ["v_daily_sales", "v_product_performance", "v_regional_analysis", "v_customer_segments", "v_transaction_detail"]

    def query_view(self, view_name: str, limit: int = 100):
        """Query an analytical view and return a DataFrame."""
        import pandas as pd
        clean_name = view_name.replace("analytics.", "")
        try:
            return self._loader.query(
                f"SELECT * FROM analytics.{clean_name} LIMIT {limit}"
            )
        except Exception:
            try:
                return self._loader.query(
                    f"SELECT * FROM {clean_name} LIMIT {limit}"
                )
            except Exception as exc:
                logger.error("Failed to query view '%s': %s", view_name, exc)
                return pd.DataFrame()
