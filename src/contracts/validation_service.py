"""
Module: validation_service
Purpose:
    Orchestrates the entire validation flow: loading contracts, validating 
    dataframes, splitting data, and quarantining invalid records.
"""

from typing import Tuple
import pandas as pd

from src.contracts.contract_registry import ContractRegistry
from src.contracts.contract_validator import ContractValidator
from src.contracts.validation_result import ValidationResult
from src.errors.quarantine_manager import QuarantineManager
from src.utils.logger import get_logger

logger = get_logger("validation")


class ValidationService:
    """High-level service connecting raw data to contracts and quarantine."""

    def __init__(self):
        self.registry = ContractRegistry()
        self.validator = ContractValidator()
        self.quarantine = QuarantineManager()

    def run_validation(
        self, 
        df: pd.DataFrame, 
        dataset_name: str, 
        contract_version: str, 
        batch_id: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame, ValidationResult]:
        """
        Run the complete validation pipeline for a batch.

        Args:
            df: The raw dataframe extracted from ingestion.
            dataset_name: Logical dataset name.
            contract_version: The version to validate against.
            batch_id: The ingestion batch ID.

        Returns:
            A tuple of (valid_dataframe, invalid_dataframe, validation_result).
        """
        logger.info(
            "Starting validation | batch_id=%s dataset=%s version=%s",
            batch_id, dataset_name, contract_version
        )
        
        # 1. Load Contract
        contract = self.registry.get_contract(dataset_name, contract_version)
        
        # 2. Validate
        result = self.validator.validate(df, contract)
        
        # 3. Split valid and invalid rows
        if result.invalid_records > 0 and not result.schema_errors:
            invalid_indices = {err.row_index for err in result.data_errors if err.row_index is not None}
            df_invalid = df[df.index.isin(invalid_indices)].copy()
            df_valid = df[~df.index.isin(invalid_indices)].copy()
        elif result.schema_errors:
            # If structural schema fails, all records are considered invalid
            df_invalid = df.copy()
            df_valid = pd.DataFrame(columns=df.columns)
        else:
            df_invalid = pd.DataFrame(columns=df.columns)
            df_valid = df.copy()

        # 4. Quarantine
        if not df_invalid.empty:
            self.quarantine.quarantine_invalid_records(
                df_invalid, dataset_name, batch_id, result
            )
            
        logger.info(
            "Validation completed | batch_id=%s status=%s valid=%d invalid=%d",
            batch_id, result.status, len(df_valid), len(df_invalid)
        )
        
        return df_valid, df_invalid, result
