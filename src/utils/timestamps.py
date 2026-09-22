"""
Module: timestamps
Purpose:
    Generate and format timestamps for ingestion, versioning, and auditing.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime, fmt: str = "%Y-%m-%dT%H:%M:%S%z") -> str:
    """
    Format a datetime object to string.

    Args:
        dt: Datetime to format.
        fmt: strftime format string.

    Returns:
        Formatted timestamp string.
    """
    return dt.strftime(fmt)


def generate_batch_timestamp() -> str:
    """Return a compact timestamp string suitable for batch IDs and filenames."""
    return utc_now().strftime("%Y%m%d_%H%M%S")
