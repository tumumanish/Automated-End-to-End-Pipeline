"""
Module: loader (PostgreSQL)
Purpose:
    Load DataFrames into PostgreSQL tables and manage batch metadata.
"""

from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from src.storage.postgres.connection import get_engine, get_connection
from src.utils.logger import get_logger

logger = get_logger("pipeline")


def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    schema: str = "raw",
    if_exists: str = "append",
) -> int:
    """
    Load a DataFrame into a PostgreSQL table.

    Args:
        df: Data to load.
        table_name: Target table name.
        schema: Target schema (default: 'raw').
        if_exists: Behavior if table exists ('append', 'replace', 'fail').

    Returns:
        Number of records loaded.
    """
    engine = get_engine()
    row_count = len(df)

    df.to_sql(
        name=table_name,
        con=engine,
        schema=schema,
        if_exists=if_exists,
        index=False,
        method="multi",
        chunksize=500,
    )

    logger.info(
        "Loaded %d records into %s.%s",
        row_count,
        schema,
        table_name,
    )
    return row_count


# ------------------------------------------------------------------
# Batch metadata operations
# ------------------------------------------------------------------

def create_batch_record(
    batch_id: str,
    source_type: str,
    source_name: str,
    dataset_name: str,
) -> None:
    """
    Insert a new batch record with status RUNNING.

    Args:
        batch_id: Unique batch identifier.
        source_type: Source category (csv, api, excel, database).
        source_name: Source path or URL.
        dataset_name: Logical dataset name.
    """
    sql = text("""
        INSERT INTO metadata.ingestion_batches
            (batch_id, source_type, source_name, dataset_name, status)
        VALUES
            (:batch_id, :source_type, :source_name, :dataset_name, 'RUNNING')
        ON CONFLICT (batch_id) DO NOTHING
    """)
    with get_connection() as conn:
        conn.execute(sql, {
            "batch_id": batch_id,
            "source_type": source_type,
            "source_name": source_name,
            "dataset_name": dataset_name,
        })
    logger.info("Batch record created: %s (RUNNING)", batch_id)


def complete_batch(
    batch_id: str,
    record_count: int,
    file_path: str | None = None,
) -> None:
    """
    Mark a batch as SUCCESS.

    Args:
        batch_id: Batch identifier.
        record_count: Total records processed.
        file_path: Path to the raw file stored.
    """
    sql = text("""
        UPDATE metadata.ingestion_batches
        SET status       = 'SUCCESS',
            completed_at = :completed_at,
            record_count = :record_count,
            file_path    = :file_path
        WHERE batch_id = :batch_id
    """)
    with get_connection() as conn:
        conn.execute(sql, {
            "batch_id": batch_id,
            "completed_at": datetime.now(timezone.utc),
            "record_count": record_count,
            "file_path": file_path,
        })
    logger.info("Batch completed: %s (SUCCESS, %d records)", batch_id, record_count)


def fail_batch(batch_id: str, error_message: str) -> None:
    """
    Mark a batch as FAILED with an error message.

    Args:
        batch_id: Batch identifier.
        error_message: Description of the failure.
    """
    sql = text("""
        UPDATE metadata.ingestion_batches
        SET status        = 'FAILED',
            completed_at  = :completed_at,
            error_message = :error_message
        WHERE batch_id = :batch_id
    """)
    with get_connection() as conn:
        conn.execute(sql, {
            "batch_id": batch_id,
            "completed_at": datetime.now(timezone.utc),
            "error_message": str(error_message)[:2000],
        })
    logger.error("Batch failed: %s — %s", batch_id, error_message)


def insert_audit_event(
    batch_id: str,
    stage: str,
    event_type: str,
    message: str = "",
    record_count: int = 0,
) -> None:
    """
    Write an audit event for a batch.

    Args:
        batch_id: Batch identifier.
        stage: Pipeline stage (extract, raw_store, db_load, etc.).
        event_type: Event type (STARTED, COMPLETED, FAILED).
        message: Optional descriptive message.
        record_count: Record count at this stage.
    """
    sql = text("""
        INSERT INTO metadata.ingestion_audit
            (batch_id, stage, event_type, message, record_count)
        VALUES
            (:batch_id, :stage, :event_type, :message, :record_count)
    """)
    with get_connection() as conn:
        conn.execute(sql, {
            "batch_id": batch_id,
            "stage": stage,
            "event_type": event_type,
            "message": message,
            "record_count": record_count,
        })
