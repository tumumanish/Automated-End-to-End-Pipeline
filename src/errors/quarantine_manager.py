"""
Module: quarantine_manager
Purpose:
    Manage quarantined (invalid/rejected) records.

    Phase 2: Basic structure.  Full quarantine logic will be added in Phase 3
    when data-contract validation is implemented.
"""

from pathlib import Path

import pandas as pd

from src.utils.file_utils import ensure_directory, get_project_root
from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("errors")


def quarantine_records(
    records: pd.DataFrame,
    category: str,
    reason: str,
    batch_id: str,
    source_type: str = "unknown",
) -> Path:
    """
    Write rejected records to the quarantine zone.

    Args:
        records: DataFrame of rejected records.
        category: Quarantine category (validation_errors, schema_errors, rejected_records).
        reason: Human-readable rejection reason.
        batch_id: Batch identifier.
        source_type: Source that produced the records.

    Returns:
        Path to the quarantine file.
    """
    quarantine_dir = get_project_root() / "data" / "quarantine" / category
    ensure_directory(quarantine_dir)

    filename = f"{batch_id}_{source_type}.csv"
    filepath = quarantine_dir / filename

    records.to_csv(filepath, index=False)

    logger.warning(
        "Quarantined %d records | category=%s reason=%s batch_id=%s path=%s",
        len(records),
        category,
        reason,
        batch_id,
        filepath,
    )
    return filepath
