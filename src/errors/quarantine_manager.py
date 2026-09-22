"""
Module: quarantine_manager
Purpose:
    Handle data that fails validation or ingestion, isolating it for review.
"""

import json
from pathlib import Path
from typing import Any
import pandas as pd

from src.utils.logger import get_logger
from src.utils.file_utils import get_project_root

logger = get_logger("errors")


class QuarantineManager:
    """Manages isolation of invalid or errored data."""

    def __init__(self, quarantine_dir: Path | None = None):
        self._root = quarantine_dir or (get_project_root() / "data" / "quarantine")
        self._root.mkdir(parents=True, exist_ok=True)

    def quarantine_invalid_records(
        self,
        df_invalid: pd.DataFrame,
        dataset_name: str,
        batch_id: str,
        validation_result: Any
    ) -> Path:
        """
        Save invalid records and their validation metadata to the quarantine zone.

        Args:
            df_invalid: DataFrame containing only the invalid rows.
            dataset_name: Name of the dataset (e.g., transactions).
            batch_id: The ingestion batch ID.
            validation_result: The ValidationResult containing error details.

        Returns:
            Path to the saved quarantined CSV.
        """
        if df_invalid.empty:
            logger.debug("No invalid records to quarantine for batch %s", batch_id)
            return self._root

        target_dir = self._root / "validation_errors" / dataset_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original data
        csv_path = target_dir / f"{batch_id}.csv"
        # Ensure we don't overwrite existing files
        if csv_path.exists():
            csv_path = target_dir / f"{batch_id}_v2.csv"
            
        df_invalid.to_csv(csv_path, index=False, encoding="utf-8")
        
        # Save rich metadata
        meta_path = csv_path.with_suffix(".json")
        metadata = {
            "batch_id": batch_id,
            "dataset": dataset_name,
            "contract_version": validation_result.contract_version,
            "invalid_record_count": len(df_invalid),
            "errors": [err.to_dict() for err in validation_result.data_errors] + 
                      [err.to_dict() for err in validation_result.schema_errors]
        }
        
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
            
        logger.info(
            "Quarantined %d records -> %s (Metadata: %s)", 
            len(df_invalid), csv_path, meta_path
        )
        return csv_path
