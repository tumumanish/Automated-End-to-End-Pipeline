"""
Module: raw_storage
Purpose:
    Save raw ingested data to the local filesystem for preservation,
    replayability, versioning, and lineage.
"""

from pathlib import Path

import pandas as pd

from src.utils.file_utils import build_raw_path
from src.utils.logger import get_logger

logger = get_logger("pipeline")


def save_raw_data(
    df: pd.DataFrame,
    source_type: str,
    dataset_name: str,
    batch_id: str,
) -> Path:
    """
    Persist raw ingested data as a CSV file.

    Files are organized by source type, dataset name, and batch ID
    so that previous batches are never overwritten.

    Pattern:
        data/raw/<source_type>/<dataset_name>/<batch_id>.csv

    Args:
        df: The ingested DataFrame.
        source_type: Source category (api, csv, excel, database).
        dataset_name: Logical dataset name (e.g., 'transactions').
        batch_id: Unique batch identifier.

    Returns:
        The absolute path to the saved raw file.
    """
    raw_path = build_raw_path(source_type, dataset_name, batch_id, extension=".csv")
    df.to_csv(raw_path, index=False, encoding="utf-8")

    logger.info(
        "Raw data saved: %d records -> %s",
        len(df),
        raw_path,
    )
    return raw_path
