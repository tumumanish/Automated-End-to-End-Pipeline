"""
Module: hashing
Purpose:
    Generate deterministic record hashes for deduplication and change detection.
    Used by the versioning system for SCD Type 2 comparisons.
"""

import hashlib
import json
from typing import Sequence

import pandas as pd


# Columns to exclude from hash computation by default
_META_COLUMNS = frozenset({
    "batch_id", "execution_id", "ingestion_timestamp",
    "valid_from", "valid_to", "is_current", "record_hash",
    "schema_version", "source_system", "loaded_timestamp",
})


def hash_record(row: dict, exclude_columns: Sequence[str] | None = None) -> str:
    """
    Compute a deterministic SHA-256 hash for a single record.

    Args:
        row: Dictionary representation of the record.
        exclude_columns: Columns to skip (defaults to metadata columns).

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    skip = set(exclude_columns) if exclude_columns else _META_COLUMNS
    filtered = {k: v for k, v in sorted(row.items()) if k not in skip}

    # Normalise values to strings for deterministic hashing
    canonical = json.dumps(filtered, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_dataframe(
    df: pd.DataFrame,
    exclude_columns: Sequence[str] | None = None,
    hash_column: str = "_record_hash",
) -> pd.DataFrame:
    """
    Add a hash column to every row of a DataFrame.

    Args:
        df: Input DataFrame.
        exclude_columns: Columns to skip in hash computation.
        hash_column: Name of the new hash column.

    Returns:
        DataFrame with the hash column appended.
    """
    df = df.copy()
    df[hash_column] = df.apply(
        lambda r: hash_record(r.to_dict(), exclude_columns), axis=1
    )
    return df


def hash_batch(df: pd.DataFrame) -> str:
    """
    Compute a single SHA-256 hash representing an entire batch.

    Useful for batch-level change detection.

    Args:
        df: The batch DataFrame.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    content = df.to_csv(index=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
