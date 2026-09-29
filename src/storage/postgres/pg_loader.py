"""
Module: pg_loader
Purpose:
    Generic PostgreSQL bulk loader for warehouse dimension and fact tables.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from typing import Optional
from src.utils.config import get_connection_string
from src.utils.logger import get_logger

logger = get_logger("storage.postgres")


def get_engine():
    return create_engine(get_connection_string())


def bulk_insert(df: pd.DataFrame, schema: str, table: str, if_exists: str = "append") -> int:
    """
    Bulk insert a DataFrame into a PostgreSQL table.

    Args:
        df: DataFrame to insert.
        schema: Target schema name.
        table: Target table name.
        if_exists: 'append' or 'replace'.

    Returns:
        Number of rows inserted.
    """
    if df.empty:
        logger.warning(f"No data to insert into {schema}.{table}")
        return 0

    engine = get_engine()
    df.to_sql(table, engine, schema=schema, if_exists=if_exists, index=False, method="multi", chunksize=500)
    logger.info(f"Inserted {len(df)} rows into {schema}.{table}")
    engine.dispose()
    return len(df)


def execute_query(sql: str, params: Optional[dict] = None) -> list:
    """Execute a SELECT query and return results as a list of dicts."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        rows = [dict(r._mapping) for r in result]
    engine.dispose()
    return rows


def upsert_dimension(df: pd.DataFrame, schema: str, table: str, natural_key: str) -> int:
    """
    Insert new dimension records, skipping existing ones by natural key.

    Args:
        df: DataFrame with dimension records.
        schema: Target schema.
        table: Target table.
        natural_key: Column name used to check for existing records.

    Returns:
        Number of new rows inserted.
    """
    if df.empty:
        return 0

    existing = execute_query(f'SELECT {natural_key} FROM {schema}."{table}"')
    existing_keys = {r[natural_key] for r in existing}

    new_rows = df[~df[natural_key].isin(existing_keys)].copy()
    if new_rows.empty:
        logger.info(f"No new records for {schema}.{table} (all {len(df)} already exist)")
        return 0

    return bulk_insert(new_rows, schema, table)
