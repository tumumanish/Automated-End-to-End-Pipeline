"""
Module: schema_validator
Purpose:
    Validate DataFrame schemas against a data contract structurally.
"""

from typing import Any
import pandas as pd

from src.contracts.validation_result import ValidationErrorMetadata
from src.errors.exceptions import SchemaValidationError


class SchemaValidator:
    """Validates dataframe schema (columns) against a contract."""

    @staticmethod
    def validate(df: pd.DataFrame, contract: dict[str, Any]) -> list[ValidationErrorMetadata]:
        """
        Validate that the DataFrame contains all required columns as per the contract.
        
        Args:
            df: The pandas DataFrame to validate.
            contract: The loaded data contract dictionary.
            
        Returns:
            A list of structural schema errors. Empty if schema is valid.
        """
        errors = []
        contract_fields = contract.get("fields", {})
        df_columns = set(df.columns)
        
        for field_name, rules in contract_fields.items():
            is_required = rules.get("required", False)
            if is_required and field_name not in df_columns:
                errors.append(
                    ValidationErrorMetadata(
                        row_index=None,
                        field=field_name,
                        rule="schema_required_column",
                        message=f"Required column '{field_name}' is missing from the dataset.",
                        expected_value="Column exists"
                    )
                )

        # Optional: check for unexpected columns (not strictly required by prompt but good practice)
        for col in df_columns:
            if col not in contract_fields:
                errors.append(
                    ValidationErrorMetadata(
                        row_index=None,
                        field=col,
                        rule="schema_unexpected_column",
                        message=f"Unexpected column '{col}' found in the dataset.",
                        expected_value="Column not in contract"
                    )
                )

        return errors
