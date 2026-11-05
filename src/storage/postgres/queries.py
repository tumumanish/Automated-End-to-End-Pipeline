"""
Module: queries (PostgreSQL)
Purpose:
    Centralized SQL query definitions and small builders for PostgreSQL
    operations.

All builders validate identifiers to prevent SQL injection when schema or
table names come from configuration rather than literals. Values are always
passed as bound parameters.
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# ─── Metadata / batch audit queries ─────────────────────────────────────

CREATE_BATCH = """
    INSERT INTO metadata.ingestion_batches
        (batch_id, source_type, source_name, dataset_name, status)
    VALUES
        (:batch_id, :source_type, :source_name, :dataset_name, 'RUNNING')
    ON CONFLICT (batch_id) DO NOTHING
"""

COMPLETE_BATCH = """
    UPDATE metadata.ingestion_batches
    SET status       = 'SUCCESS',
        completed_at = :completed_at,
        record_count = :record_count,
        file_path    = :file_path
    WHERE batch_id = :batch_id
"""

FAIL_BATCH = """
    UPDATE metadata.ingestion_batches
    SET status        = 'FAILED',
        completed_at  = :completed_at,
        error_message = :error_message
    WHERE batch_id = :batch_id
"""

INSERT_AUDIT_EVENT = """
    INSERT INTO metadata.ingestion_audit
        (batch_id, stage, event_type, message, record_count)
    VALUES
        (:batch_id, :stage, :event_type, :message, :record_count)
"""


# ─── Generic query builders ─────────────────────────────────────────────

def validate_identifier(identifier: str) -> str:
    """Validate a SQL identifier (schema, table, or column name)."""
    if not identifier or not _IDENTIFIER_RE.match(identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier!r}")
    return identifier


def qualified_name(schema: str, table: str) -> str:
    """Return a validated ``schema.table`` name."""
    return f"{validate_identifier(schema)}.{validate_identifier(table)}"


def _column_list(columns: str | Sequence[str]) -> str:
    if columns == "*":
        return "*"
    if isinstance(columns, str):
        columns = [c.strip() for c in columns.split(",") if c.strip()]
    if not columns:
        raise ValueError("At least one column is required")
    return ", ".join(validate_identifier(c) for c in columns)


def insert_statement(
    schema: str,
    table: str,
    columns: Sequence[str],
    *,
    on_conflict_do_nothing: bool = False,
) -> str:
    """
    Build an INSERT statement using named bind parameters.

    Example:
        >>> insert_statement("raw", "transactions", ["transaction_id", "amount"])
        'INSERT INTO raw.transactions (transaction_id, amount) '
        'VALUES (:transaction_id, :amount)'
    """
    cols = list(columns)
    if not cols:
        raise ValueError("At least one column is required")
    column_sql = ", ".join(validate_identifier(c) for c in cols)
    value_sql = ", ".join(f":{validate_identifier(c)}" for c in cols)
    sql = f"INSERT INTO {qualified_name(schema, table)} ({column_sql}) VALUES ({value_sql})"
    if on_conflict_do_nothing:
        sql += " ON CONFLICT DO NOTHING"
    return sql


def select_statement(
    schema: str,
    table: str,
    columns: str | Sequence[str] = "*",
    *,
    where: str | None = None,
    order_by: str | None = None,
    limit: int | None = None,
) -> str:
    """
    Build a SELECT statement.

    ``where``, ``order_by``, and ``limit`` must be static SQL fragments;
    never interpolate untrusted user input into them.
    """
    sql = f"SELECT {_column_list(columns)} FROM {qualified_name(schema, table)}"
    if where:
        sql += f" WHERE {where}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit is not None:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        sql += f" LIMIT {int(limit)}"
    return sql


def truncate_statement(schema: str, table: str, *, restart_identity: bool = True) -> str:
    """Build a TRUNCATE statement for a table."""
    sql = f"TRUNCATE TABLE {qualified_name(schema, table)}"
    if restart_identity:
        sql += " RESTART IDENTITY"
    return sql + " CASCADE"


def count_statement(schema: str, table: str) -> str:
    """Build a row-count query for a table."""
    return f"SELECT COUNT(*) FROM {qualified_name(schema, table)}"


def table_exists_statement() -> str:
    """Query for checking table existence in PostgreSQL."""
    return """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
        )
    """


def placeholders(columns: Iterable[str]) -> str:
    """Return a comma-separated list of named bind placeholders."""
    return ", ".join(f":{validate_identifier(c)}" for c in columns)
