"""
Module: database_ingestion
Purpose:
    Extract data from relational databases via SQLAlchemy.
"""

import pandas as pd
from sqlalchemy import create_engine, text

from src.errors.exceptions import IngestionError
from src.ingestion.base import BaseIngestion
from src.utils.logger import get_logger

logger = get_logger("pipeline")


class DatabaseIngestion(BaseIngestion):
    """
    Extract data from a relational database using a SQL query.

    Args:
        connection_string: SQLAlchemy connection string.
        query: SQL SELECT statement to execute.
    """

    def __init__(self, connection_string: str, query: str):
        self._connection_string = connection_string
        self._query = query

    @property
    def source_type(self) -> str:
        return "database"

    @property
    def source_name(self) -> str:
        # Mask credentials in logs
        return "database_query"

    def extract(self) -> pd.DataFrame:
        """
        Execute the SQL query and return results as a DataFrame.

        Raises:
            IngestionError: On connection or query execution failure.

        Returns:
            DataFrame with query results.
        """
        logger.info("Extracting from database via SQL query")

        try:
            engine = create_engine(self._connection_string)
        except Exception as exc:
            raise IngestionError(
                f"Failed to create database engine: {exc}",
            ) from exc

        try:
            with engine.connect() as conn:
                df = pd.read_sql(text(self._query), conn)
        except Exception as exc:
            raise IngestionError(
                f"Database query execution failed: {exc}",
                details={"query": self._query[:200]},
            ) from exc
        finally:
            engine.dispose()

        logger.info("Database extracted: %d records, %d columns", len(df), len(df.columns))
        return df
