"""
Module: contract_validator
Purpose:
    High-level validation engine orchestrating schema and row-level checks
    against pandas DataFrames based on JSON contract rules.
"""

from typing import Any
import pandas as pd
import numpy as np

from src.contracts.schema_validator import SchemaValidator
from src.contracts.validation_result import ValidationResult, ValidationErrorMetadata


class ContractValidator:
    """Generic, rule-based data contract validation engine."""

    def __init__(self):
        self.schema_validator = SchemaValidator()

    def validate(self, df: pd.DataFrame, contract: dict[str, Any]) -> ValidationResult:
        """
        Validate a dataframe against a contract.

        Args:
            df: The dataframe to validate.
            contract: The loaded contract dictionary.

        Returns:
            ValidationResult with separated valid/invalid record counts and errors.
        """
        dataset = contract.get("dataset", "unknown")
        version = contract.get("version", "unknown")
        
        result = ValidationResult(
            dataset=dataset,
            contract_version=version,
            total_records=len(df),
            status="FAILED"
        )
        
        if df.empty:
            result.status = "PASS"
            return result

        # 1. Structural Schema Validation (Missing columns, etc.)
        schema_errors = self.schema_validator.validate(df, contract)
        result.schema_errors.extend(schema_errors)
        
        if any(e.rule == "schema_required_column" for e in schema_errors):
            # If critical schema errors exist, mark all records as invalid and abort row checks
            result.invalid_records = len(df)
            return result

        # 2. Row-level Field Validation
        contract_fields = contract.get("fields", {})
        data_errors = []
        invalid_indices = set()
        
        # Iterate over records as dicts for generic validation
        # Using iterrows is slower but allows precise error reporting per the requirements.
        for index, row in df.iterrows():
            row_invalid = False
            for field_name, rules in contract_fields.items():
                # Skip validation if field doesn't exist (handled by schema validator)
                if field_name not in row:
                    continue
                    
                val = row[field_name]
                
                # Check Nullability
                is_null = pd.isna(val)
                if is_null:
                    if rules.get("nullable", True) is False:
                        data_errors.append(
                            self._build_error(index, field_name, "nullable", "Null value in non-nullable field", val, "Not null")
                        )
                        row_invalid = True
                    continue # Skip other rules if null
                
                # Check Type
                expected_type = rules.get("type")
                if expected_type and not self._validate_type(val, expected_type):
                    data_errors.append(
                        self._build_error(index, field_name, "type", f"Expected type {expected_type}", val, expected_type)
                    )
                    row_invalid = True
                    continue # Skip range/format checks if type is fundamentally wrong
                
                # Numeric checks (minimum, maximum)
                if expected_type in ("integer", "number"):
                    if "minimum" in rules and val < rules["minimum"]:
                        data_errors.append(
                            self._build_error(index, field_name, "minimum", f"Value below minimum {rules['minimum']}", val, f">= {rules['minimum']}")
                        )
                        row_invalid = True
                    if "maximum" in rules and val > rules["maximum"]:
                        data_errors.append(
                            self._build_error(index, field_name, "maximum", f"Value above maximum {rules['maximum']}", val, f"<= {rules['maximum']}")
                        )
                        row_invalid = True
                        
                # Allowed Values
                if "allowed_values" in rules:
                    if val not in rules["allowed_values"]:
                        data_errors.append(
                            self._build_error(index, field_name, "allowed_values", "Value not in allowed list", val, rules["allowed_values"])
                        )
                        row_invalid = True

                # Format checks (e.g. date formatting)
                if expected_type == "date" and "format" in rules:
                    # In pandas, if it's already a datetime object, format is implicit.
                    # If it's a string, we attempt to parse it. 
                    # The prompt emphasizes: "The validator must not blindly enforce a format unless it is present."
                    if isinstance(val, str):
                        try:
                            # A simple check: can pandas parse it according to a strict format?
                            # For complex format strings like YYYY-MM-DD, a generic implementation is complex, 
                            # but we can enforce basic ISO formats as a proxy.
                            pd.to_datetime(val, format="%Y-%m-%d" if rules["format"] == "YYYY-MM-DD" else None, errors='raise')
                        except ValueError:
                            data_errors.append(
                                self._build_error(index, field_name, "format", f"Value does not match format {rules['format']}", val, rules["format"])
                            )
                            row_invalid = True

            if row_invalid:
                invalid_indices.add(index)

        result.data_errors.extend(data_errors)
        result.invalid_records = len(invalid_indices)
        result.valid_records = len(df) - result.invalid_records
        
        if result.invalid_records == 0 and not result.schema_errors:
            result.status = "PASS"
            
        return result

    def _validate_type(self, val: Any, expected_type: str) -> bool:
        """Helper to loosely validate python/pandas types against contract definitions."""
        if expected_type == "string":
            return isinstance(val, str)
        if expected_type == "integer":
            # numpy types can be tricky
            return isinstance(val, (int, np.integer))
        if expected_type == "number":
            return isinstance(val, (int, float, np.number))
        if expected_type == "boolean":
            return isinstance(val, (bool, np.bool_))
        if expected_type in ("date", "datetime"):
            # If it's a pandas timestamp, it's valid. If it's a string, it must be parseable.
            if isinstance(val, (pd.Timestamp, np.datetime64)):
                return True
            if isinstance(val, str):
                try:
                    pd.to_datetime(val)
                    return True
                except ValueError:
                    return False
            return False
        return True

    def _build_error(self, row, field, rule, msg, actual, expected) -> ValidationErrorMetadata:
        return ValidationErrorMetadata(
            row_index=row,
            field=field,
            rule=rule,
            message=msg,
            actual_value=actual,
            expected_value=expected
        )
