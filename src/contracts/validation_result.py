"""
Module: validation_result
Purpose:
    Structured representations for validation errors and results.
"""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class ValidationErrorMetadata:
    """Represents a single rule violation in a dataset."""
    row_index: int | None
    field: str
    rule: str
    message: str
    actual_value: Any = None
    expected_value: Any = None

    def to_dict(self) -> dict:
        return {
            "row_index": self.row_index,
            "field": self.field,
            "rule": self.rule,
            "message": self.message,
            "actual_value": str(self.actual_value) if self.actual_value is not None else None,
            "expected_value": str(self.expected_value) if self.expected_value is not None else None,
        }


@dataclass
class ValidationResult:
    """Represents the complete result of a dataset validation run."""
    dataset: str
    contract_version: str
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    status: str = "FAILED"
    
    # Structural errors (e.g., missing columns)
    schema_errors: list[ValidationErrorMetadata] = field(default_factory=list)
    
    # Row-level data errors
    data_errors: list[ValidationErrorMetadata] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "contract_version": self.contract_version,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "status": self.status,
            "schema_errors": [e.to_dict() for e in self.schema_errors],
            "data_errors": [e.to_dict() for e in self.data_errors],
        }
