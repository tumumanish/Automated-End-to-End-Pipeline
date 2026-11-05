"""
Unit Tests: Validation Utilities

Covers scalar null/type/range/format helpers shared by contracts and
quality monitors.
"""

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.validation_utils import (
    check_rules,
    in_range,
    is_allowed,
    is_blank,
    is_finite_number,
    is_null,
    is_type,
    matches_date_format,
    matches_format,
    validate_record,
)


class TestNullChecks:
    def test_null_values(self):
        assert is_null(None)
        assert is_null(np.nan)
        assert is_null(pd.NaT)

    def test_non_null_values(self):
        assert not is_null(0)
        assert not is_null("")
        assert not is_null([])
        assert not is_null("NaN")

    def test_blank(self):
        assert is_blank(None)
        assert is_blank("   ")
        assert not is_blank("x")


class TestTypeChecks:
    @pytest.mark.parametrize(
        "value,expected_type",
        [
            ("abc", "string"),
            (42, "integer"),
            (np.int64(7), "integer"),
            (3.14, "number"),
            (True, "boolean"),
            (pd.Timestamp("2024-01-01"), "date"),
            (datetime(2024, 1, 1), "datetime"),
        ],
    )
    def test_valid_types(self, value, expected_type):
        assert is_type(value, expected_type)

    def test_invalid_types(self):
        assert not is_type(42, "string")
        assert not is_type("42", "integer")
        assert not is_type(True, "integer")
        assert not is_type(3.14, "boolean")
        assert not is_type("not-a-date", "date")

    def test_unknown_type_is_permissive(self):
        assert is_type(object(), "custom_type")


class TestRangeAndFormat:
    def test_in_range(self):
        assert in_range(5, 1, 10)
        assert not in_range(0, 1, 10)
        assert not in_range(11, 1, 10)
        assert in_range(10, 1, 10)
        assert in_range(10, 1, 10, inclusive=True)

    def test_in_range_invalid_value(self):
        assert not in_range("5", 1, 10)
        assert not in_range(None, 1, 10)

    def test_is_finite_number(self):
        assert is_finite_number(1.5)
        assert not is_finite_number(float("inf"))
        assert not is_finite_number(float("nan"))
        assert not is_finite_number("1.5")

    def test_date_format_token(self):
        assert matches_date_format("2024-06-01", "YYYY-MM-DD")
        assert not matches_date_format("01-06-2024", "YYYY-MM-DD")

    def test_custom_regex_format(self):
        assert matches_format("AB-123", r"[A-Z]{2}-\d{3}")
        assert not matches_format("ab-123", r"[A-Z]{2}-\d{3}")

    def test_allowed_values(self):
        assert is_allowed("NYC", ["NYC", "LA"])
        assert not is_allowed("SF", ["NYC", "LA"])


class TestRuleEngine:
    def test_nullable_failure(self):
        failures = check_rules(None, {"type": "string", "nullable": False})
        assert failures == ["nullable"]

    def test_nullable_success(self):
        assert check_rules(None, {"type": "string", "nullable": True}) == []

    def test_type_failure_short_circuits(self):
        failures = check_rules("5", {"type": "integer", "minimum": 1})
        assert failures == ["type"]

    def test_minimum_and_maximum(self):
        assert check_rules(0, {"type": "integer", "minimum": 1}) == ["minimum"]
        assert check_rules(100, {"type": "integer", "maximum": 10}) == ["maximum"]
        assert check_rules(5, {"type": "integer", "minimum": 1, "maximum": 10}) == []

    def test_allowed_values_and_format(self):
        assert check_rules("NYC", {"type": "string", "allowed_values": ["NYC", "LA"]}) == []
        assert check_rules("SF", {"type": "string", "allowed_values": ["NYC", "LA"]}) == [
            "allowed_values"
        ]
        assert "format" in check_rules("123", {"type": "string", "format": r"[A-Z]+"})

    def test_validate_record(self):
        fields = {
            "id": {"type": "string", "nullable": False},
            "quantity": {"type": "integer", "minimum": 1},
        }
        errors = validate_record({"id": None, "quantity": 0}, fields)
        assert errors["id"] == ["nullable"]
        assert errors["quantity"] == ["minimum"]

    def test_validate_record_missing_field_is_ignored(self):
        fields = {"id": {"type": "string", "nullable": False}}
        assert validate_record({}, fields) == {}
