"""
Module: sf_loader
Purpose:
    Snowflake bulk loader (optional — requires snowflake-connector-python).
    Mirrors the PostgresLoader interface for Snowflake target warehouses.

    Enable by installing ``pip install snowflake-connector-python`` and
    configuring Snowflake credentials in config/settings.yaml.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("storage.snowflake")


class SnowflakeLoader:
    """
    Snowflake data loader providing DataFrame-to-table loading.

    Uses snowflake-connector-python with the write_pandas()
    utility for optimized bulk loading.
    """

    def __init__(
        self,
        account: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        schema: str = "PUBLIC",
        warehouse: Optional[str] = None,
        role: Optional[str] = None,
    ):
        self._account = account
        self._user = user
        self._password = password
        self._database = database
        self._schema = schema
        self._warehouse = warehouse
        self._role = role
        self._connection = None

    def connect(self):
        """Establish a Snowflake connection."""
        try:
            import snowflake.connector
        except ImportError:
            raise ImportError(
                "Snowflake connector not installed. Run: pip install snowflake-connector-python"
            )

        self._connection = snowflake.connector.connect(
            account=self._account,
            user=self._user,
            password=self._password,
            database=self._database,
            schema=self._schema,
            warehouse=self._warehouse,
            role=self._role,
        )
        logger.info("Connected to Snowflake: %s.%s", self._database, self._schema)
        return self._connection

    def disconnect(self):
        """Close the Snowflake connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: Optional[str] = None,
        overwrite: bool = False,
    ) -> int:
        """
        Load a DataFrame into a Snowflake table using write_pandas.

        Args:
            df: Data to load.
            table_name: Target table name.
            schema: Schema override (default: configured schema).
            overwrite: Whether to overwrite existing data.

        Returns:
            Number of rows loaded.
        """
        if df.empty:
            return 0

        try:
            from snowflake.connector.pandas_tools import write_pandas
        except ImportError:
            raise ImportError("snowflake-connector-python not installed.")

        if not self._connection:
            self.connect()

        target_schema = schema or self._schema

        success, num_chunks, num_rows, output = write_pandas(
            conn=self._connection,
            df=df,
            table_name=table_name.upper(),
            schema=target_schema.upper(),
            overwrite=overwrite,
        )

        logger.info(
            "Snowflake load: %d rows into %s.%s (%d chunks)",
            num_rows, target_schema, table_name, num_chunks,
        )
        return num_rows

    def execute_sql(self, sql: str) -> None:
        """Execute raw SQL on Snowflake."""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        try:
            cursor.execute(sql)
        finally:
            cursor.close()

    def query(self, sql: str) -> pd.DataFrame:
        """Execute a SELECT query and return results as DataFrame."""
        if not self._connection:
            self.connect()

        cursor = self._connection.cursor()
        try:
            cursor.execute(sql)
            df = cursor.fetch_pandas_all()
            return df
        finally:
            cursor.close()
