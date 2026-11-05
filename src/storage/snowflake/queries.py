"""
Module: queries (Snowflake)
Purpose:
    Centralized SQL query definitions and builders for Snowflake.

Snowflake folds unquoted identifiers to uppercase, so builders preserve the
caller's case and let the warehouse handle folding.
"""

from __future__ import annotations

import re
from typing import Sequence

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def validate_identifier(identifier: str) -> str:
    """Validate a Snowflake identifier (schema, table, or column)."""
    if not identifier or not _IDENTIFIER_RE.match(identifier):
        raise ValueError(f"Invalid Snowflake identifier: {identifier!r}")
    return identifier


def qualified_name(schema: str, table: str) -> str:
    """Return a validated ``SCHEMA.TABLE`` name."""
    return f"{validate_identifier(schema)}.{validate_identifier(table)}"


def select_statement(
    schema: str,
    table: str,
    columns: str | Sequence[str] = "*",
    *,
    where: str | None = None,
    limit: int | None = None,
) -> str:
    """Build a Snowflake SELECT statement."""
    if columns == "*":
        column_sql = "*"
    elif isinstance(columns, str):
        column_sql = ", ".join(
            validate_identifier(c.strip()) for c in columns.split(",") if c.strip()
        )
    else:
        column_sql = ", ".join(validate_identifier(c) for c in columns)

    sql = f"SELECT {column_sql} FROM {qualified_name(schema, table)}"
    if where:
        sql += f" WHERE {where}"
    if limit is not None:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        sql += f" LIMIT {int(limit)}"
    return sql


def count_statement(schema: str, table: str) -> str:
    """Build a row-count query."""
    return f"SELECT COUNT(*) FROM {qualified_name(schema, table)}"


def truncate_statement(schema: str, table: str) -> str:
    """Build a Snowflake TRUNCATE statement."""
    return f"TRUNCATE TABLE IF EXISTS {qualified_name(schema, table)}"


TABLE_EXISTS = """
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
"""

CREATE_SCHEMA = "CREATE SCHEMA IF NOT EXISTS {schema}"

CREATE_STAGE = """
    CREATE STAGE IF NOT EXISTS {stage}
    FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
"""

COPY_INTO_TABLE = """
    COPY INTO {table}
    FROM @{stage}
    FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1)
    ON_ERROR = 'CONTINUE'
"""
