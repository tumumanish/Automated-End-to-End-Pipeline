"""
Module: loader (Snowflake)
Purpose:
    Load data into Snowflake tables — raw, staging, warehouse schemas.

Provides a small functional API mirroring ``src.storage.postgres.loader``
plus helpers for stage-based bulk loads. Snowflake support is optional: the
connector is imported lazily so the rest of the project runs without it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.storage.snowflake.connection import SnowflakeConfig, get_snowflake_cursor
from src.storage.snowflake.queries import (
    COPY_INTO_TABLE,
    CREATE_STAGE,
    count_statement,
    qualified_name,
    truncate_statement,
    validate_identifier,
)
from src.storage.snowflake.sf_loader import SnowflakeLoader
from src.utils.logger import get_logger

logger = get_logger("storage.snowflake")


def _loader_from_config(config: SnowflakeConfig | None = None) -> SnowflakeLoader:
    cfg = config or SnowflakeConfig.from_env()
    return SnowflakeLoader(
        account=cfg.account,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        schema=cfg.schema,
        warehouse=cfg.warehouse,
        role=cfg.role,
    )


def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    schema: Optional[str] = None,
    config: SnowflakeConfig | None = None,
    overwrite: bool = False,
) -> int:
    """
    Load a DataFrame into a Snowflake table via ``write_pandas``.

    Returns:
        Number of rows loaded (0 for an empty DataFrame).
    """
    loader = _loader_from_config(config)
    try:
        return loader.load_dataframe(
            df,
            table_name=table_name,
            schema=schema,
            overwrite=overwrite,
        )
    finally:
        loader.disconnect()


def truncate_table(
    table_name: str,
    schema: str = "PUBLIC",
    config: SnowflakeConfig | None = None,
) -> None:
    """Remove all rows from a Snowflake table."""
    with get_snowflake_cursor(config) as cursor:
        cursor.execute(truncate_statement(schema, table_name))
    logger.info("Truncated %s", qualified_name(schema, table_name))


def table_row_count(
    table_name: str,
    schema: str = "PUBLIC",
    config: SnowflakeConfig | None = None,
) -> int:
    """Return the row count for a Snowflake table."""
    with get_snowflake_cursor(config) as cursor:
        cursor.execute(count_statement(schema, table_name))
        row = cursor.fetchone()
    return int(row[0]) if row else 0


def ensure_stage(
    stage_name: str,
    config: SnowflakeConfig | None = None,
) -> None:
    """Create an internal CSV stage if it does not exist."""
    validate_identifier(stage_name)
    with get_snowflake_cursor(config) as cursor:
        cursor.execute(CREATE_STAGE.format(stage=stage_name))
    logger.info("Ensured Snowflake stage: %s", stage_name)


def copy_from_stage(
    table_name: str,
    stage_name: str,
    schema: str = "PUBLIC",
    config: SnowflakeConfig | None = None,
) -> None:
    """Run COPY INTO for a previously uploaded stage."""
    validate_identifier(stage_name)
    sql = COPY_INTO_TABLE.format(
        table=qualified_name(schema, table_name),
        stage=stage_name,
    )
    with get_snowflake_cursor(config) as cursor:
        cursor.execute(sql)
    logger.info("COPY INTO complete for %s", qualified_name(schema, table_name))


def upload_csv_to_stage(
    local_path: str | Path,
    stage_name: str,
    config: SnowflakeConfig | None = None,
) -> None:
    """
    Upload a local CSV to an internal stage using ``PUT``.

    Note: Snowflake does not support bind parameters for ``PUT`` paths, so the
    path is validated to exist before being embedded in the statement.
    """
    path = Path(local_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")
    validate_identifier(stage_name)
    uri = path.as_posix()
    with get_snowflake_cursor(config) as cursor:
        cursor.execute(f"PUT 'file://{uri}' @{stage_name} AUTO_COMPRESS=TRUE OVERWRITE=TRUE")
    logger.info("Uploaded %s to stage @%s", path.name, stage_name)


def execute_sql(
    sql: str,
    config: SnowflakeConfig | None = None,
    params: Optional[dict[str, Any]] = None,
) -> None:
    """Execute a raw SQL statement on Snowflake."""
    with get_snowflake_cursor(config) as cursor:
        cursor.execute(sql, params or None)
