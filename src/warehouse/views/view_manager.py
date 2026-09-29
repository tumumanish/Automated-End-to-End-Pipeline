"""
Module: view_manager
Purpose:
    Create and refresh analytical views in the analytics schema.
"""

from pathlib import Path
from src.storage.postgres.pg_loader import get_engine
from src.utils.logger import get_logger
from src.utils.file_utils import get_project_root
from sqlalchemy import text

logger = get_logger("warehouse.views")


class ViewManager:
    """Creates and refreshes analytical views from SQL scripts."""

    def __init__(self):
        self._sql_file = get_project_root() / "sql" / "postgres" / "06_create_views.sql"

    def create_views(self) -> None:
        """Execute the views SQL script to create/replace all analytical views."""
        if not self._sql_file.exists():
            logger.error(f"Views SQL file not found: {self._sql_file}")
            return

        sql = self._sql_file.read_text(encoding="utf-8")
        statements = [
            s.strip() for s in sql.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]

        engine = get_engine()
        with engine.connect() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
            conn.commit()
        engine.dispose()
        logger.info(f"Analytical views created/refreshed from {self._sql_file.name}")

    def list_views(self) -> list:
        """List all views in the analytics schema."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.views WHERE table_schema = 'analytics' ORDER BY table_name"
            ))
            views = [r[0] for r in result]
        engine.dispose()
        return views
