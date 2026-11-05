"""
Module: connection (Snowflake)
Purpose:
    Manage Snowflake database connections.

Responsibilities:
    - Configuration from environment variables
    - Lazy connector import (Snowflake support is optional)
    - Session and cursor management
    - Health check

Requires ``snowflake-connector-python`` (optional dependency). Importing this
module never requires the connector; failure happens only on ``connect()``.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator, Optional

from src.utils.logger import get_logger

logger = get_logger("storage.snowflake")

_CONNECTOR_IMPORT_ERROR = (
    "Snowflake connector not installed. "
    "Install it with: pip install snowflake-connector-python"
)


@dataclass(frozen=True)
class SnowflakeConfig:
    """Snowflake connection settings loaded from environment variables."""

    account: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = "PIPELINE_WAREHOUSE"
    schema: str = "PUBLIC"
    warehouse: Optional[str] = None
    role: Optional[str] = None

    @classmethod
    def from_env(cls) -> "SnowflakeConfig":
        """Build configuration from ``SNOWFLAKE_*`` environment variables."""
        return cls(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            database=os.getenv("SNOWFLAKE_DATABASE", "PIPELINE_WAREHOUSE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            role=os.getenv("SNOWFLAKE_ROLE"),
        )

    @property
    def is_configured(self) -> bool:
        """Return True when the minimum credentials are present."""
        return bool(self.account and self.user and self.password)

    def to_connect_kwargs(self) -> dict[str, Any]:
        """Return kwargs accepted by ``snowflake.connector.connect``."""
        return {
            key: value
            for key, value in {
                "account": self.account,
                "user": self.user,
                "password": self.password,
                "database": self.database,
                "schema": self.schema,
                "warehouse": self.warehouse,
                "role": self.role,
            }.items()
            if value
        }


def get_snowflake_connection(
    config: SnowflakeConfig | None = None,
    **overrides: Any,
):
    """
    Open a Snowflake connection.

    Args:
        config: Optional explicit configuration. Defaults to environment.
        **overrides: Extra kwargs passed to the connector.

    Raises:
        ImportError: If ``snowflake-connector-python`` is not installed.
        ValueError: If required credentials are missing.
    """
    try:
        import snowflake.connector
    except ImportError as exc:  # pragma: no cover - dependency not installed
        raise ImportError(_CONNECTOR_IMPORT_ERROR) from exc

    cfg = config or SnowflakeConfig.from_env()
    if not cfg.is_configured:
        raise ValueError(
            "Snowflake credentials are not configured. Set SNOWFLAKE_ACCOUNT, "
            "SNOWFLAKE_USER, and SNOWFLAKE_PASSWORD."
        )

    kwargs = {**cfg.to_connect_kwargs(), **overrides}
    connection = snowflake.connector.connect(**kwargs)
    logger.info("Connected to Snowflake: %s.%s", cfg.database, cfg.schema)
    return connection


@contextmanager
def get_snowflake_cursor(
    config: SnowflakeConfig | None = None,
) -> Generator[Any, None, None]:
    """Context manager yielding a Snowflake cursor and closing resources."""
    connection = get_snowflake_connection(config)
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        connection.close()


def test_connection(config: SnowflakeConfig | None = None) -> bool:
    """Return True when Snowflake is reachable and usable."""
    try:
        with get_snowflake_cursor(config) as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        logger.info("Snowflake connection test: OK")
        return True
    except Exception as exc:
        logger.error("Snowflake connection test failed: %s", exc)
        return False


def is_connector_available() -> bool:
    """Return True when the optional Snowflake connector can be imported."""
    try:
        import snowflake.connector  # noqa: F401
        return True
    except ImportError:
        return False
