"""
Package: storage.snowflake
Snowflake connection management and bulk data loading utilities.
(Optional — enable via config/settings.yaml when Snowflake credentials are configured.)
"""

from src.storage.snowflake.sf_loader import SnowflakeLoader

__all__ = ["SnowflakeLoader"]
