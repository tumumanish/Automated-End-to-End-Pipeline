"""
Module: error_handler
Purpose:
    Centralized error handling — catch, log, and route errors appropriately.
"""

from src.utils.logger import get_logger

logger = get_logger("errors")


def handle_ingestion_error(
    error: Exception,
    batch_id: str | None = None,
    source_type: str | None = None,
    source_name: str | None = None,
) -> None:
    """
    Log and handle an ingestion error.

    Args:
        error: The exception that occurred.
        batch_id: The batch ID if available.
        source_type: Source type (csv, api, excel, database).
        source_name: Source identifier (file path or URL).
    """
    context = {
        "batch_id": batch_id,
        "source_type": source_type,
        "source_name": source_name,
        "error_type": type(error).__name__,
    }
    logger.error(
        "Ingestion error: %s | Context: %s",
        str(error),
        context,
        exc_info=True,
    )


def handle_storage_error(
    error: Exception,
    batch_id: str | None = None,
    operation: str | None = None,
) -> None:
    """
    Log and handle a storage error.

    Args:
        error: The exception that occurred.
        batch_id: The batch ID if available.
        operation: Description of the operation that failed.
    """
    context = {
        "batch_id": batch_id,
        "operation": operation,
        "error_type": type(error).__name__,
    }
    logger.error(
        "Storage error: %s | Context: %s",
        str(error),
        context,
        exc_info=True,
    )
