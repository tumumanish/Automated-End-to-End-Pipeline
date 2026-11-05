"""
Package: storage.snowflake
Snowflake connection management and bulk data loading utilities.
(Optional — enable via config/settings.yaml when Snowflake credentials are configured.)
"""

from src.storage.snowflake.connection import (
    SnowflakeConfig,
    get_snowflake_connection,
    is_connector_available,
    test_connection,
)
from src.storage.snowflake.sf_loader import SnowflakeLoader

__all__ = [
    "SnowflakeConfig",
    "SnowflakeLoader",
    "get_snowflake_connection",
    "is_connector_available",
    "test_connection",
]
