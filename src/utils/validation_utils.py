"""
Module: validation_utils
Purpose:
    Common validation helper functions used across contracts,
    schema validation, and data quality checks.

These helpers intentionally operate on scalar values so they can be reused
by row-level validators, quality monitors, and ad-hoc scripts without
pulling in the full contract validator.
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


# Supported contract date formats mapped to strptime patterns.
_DATE_FORMATS = {
    "YYYY-MM-DD": "%Y-%m-%d",
    "YYYY/MM/DD": "%Y/%m/%d",
    "DD-MM-YYYY": "%d-%m-%Y",
    "DD/MM/YYYY": "%d/%m/%Y",
    "MM/DD/YYYY": "%m/%d/%Y",
    "YYYY-MM-DDTHH:MM:SS": "%Y-%m-%dT%H:%M:%S",
    "ISO8601": "%Y-%m-%dT%H:%M:%S",
}

_NUMBER_TYPES = (int, float, np.integer, np.floating)
_INTEGER_TYPES = (int, np.integer)
_BOOLEAN_TYPES = (bool, np.bool_)


def is_null(value: Any) -> bool:
    """
    Return True when ``value`` represents a missing value.

    Handles ``None``, ``NaN``, ``NaT``, pandas ``NA``, and numpy masked
    values. Container values (lists/arrays) are never considered null.
    """
    if value is None:
        return True
    if isinstance(value, (list, tuple, dict, set)):
        return False
    try:
        result = pd.isna(value)
    except (TypeError, ValueError):
        return False
    if isinstance(result, (bool, np.bool_)):
        return bool(result)
    # pd.isna on arrays returns an array; not a scalar null.
    return False


def is_blank(value: Any) -> bool:
    """Return True for null values or whitespace-only strings."""
    if is_null(value):
        return True
    return isinstance(value, str) and value.strip() == ""


def is_type(value: Any, expected_type: str) -> bool:
    """
    Check whether a scalar matches a contract type.

    Supported types: string, integer, number, boolean, date, datetime.
    Unknown types are treated as valid (forward-compatible behaviour).
    """
    expected = (expected_type or "").lower()
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, _INTEGER_TYPES) and not isinstance(value, _BOOLEAN_TYPES)
    if expected in ("number", "float", "decimal"):
        return isinstance(value, _NUMBER_TYPES) and not isinstance(value, _BOOLEAN_TYPES)
    if expected == "boolean":
        return isinstance(value, _BOOLEAN_TYPES)
    if expected in ("date", "datetime"):
        if isinstance(value, (pd.Timestamp, np.datetime64, datetime, date)):
            return True
        if isinstance(value, str):
            return matches_date_format(value) or matches_format(value, "ISO8601")
        return False
    return True


def in_range(
    value: Any,
    minimum: Any = None,
    maximum: Any = None,
    inclusive: bool = True,
) -> bool:
    """Check that a numeric value lies within the optional bounds."""
    if is_null(value):
        return False
    if not isinstance(value, _NUMBER_TYPES):
        return False
    if minimum is not None:
        below_min = value < minimum if inclusive else value <= minimum
        if below_min:
            return False
    if maximum is not None:
        above_max = value > maximum if inclusive else value >= maximum
        if above_max:
            return False
    return True


def is_allowed(value: Any, allowed_values: Sequence[Any]) -> bool:
    """Check membership in an enumerated list of allowed values."""
    return value in allowed_values


def matches_date_format(value: Any, fmt: str | None = None) -> bool:
    """
    Check whether a string parses as a date.

    If ``fmt`` is a known contract token (e.g. ``YYYY-MM-DD``) it is mapped
    to a ``strptime`` pattern. If no format is given, common ISO formats are
    attempted.
    """
    if not isinstance(value, str):
        return isinstance(value, (date, datetime, pd.Timestamp, np.datetime64))

    if fmt:
        pattern = _DATE_FORMATS.get(fmt.upper(), fmt)
        try:
            datetime.strptime(value, pattern)
            return True
        except (ValueError, TypeError):
            return False

    for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            datetime.strptime(value, pattern)
            return True
        except (ValueError, TypeError):
            continue
    return False


def matches_format(value: Any, fmt: str) -> bool:
    """
    Check a value against a contract ``format`` rule.

    Date-style format tokens are handled as dates; anything else is treated
    as a regular expression matched against the string representation.
    """
    if fmt.upper() in _DATE_FORMATS:
        return matches_date_format(value, fmt)
    if not isinstance(value, str):
        return False
    try:
        return re.fullmatch(fmt, value) is not None
    except re.error:
        return False


def is_finite_number(value: Any) -> bool:
    """Return True for finite numeric values (excludes inf and NaN)."""
    if not isinstance(value, _NUMBER_TYPES):
        return False
    return math.isfinite(float(value))


def check_rules(value: Any, rules: Mapping[str, Any]) -> list[str]:
    """
    Apply a single contract field rule-set to a value.

    Args:
        value: Scalar field value.
        rules: Contract rules for the field (type, nullable, minimum, ...).

    Returns:
        List of violated rule names. Empty when the value is valid.
    """
    failures: list[str] = []

    if is_null(value):
        if rules.get("nullable", True) is False:
            failures.append("nullable")
        return failures

    expected_type = rules.get("type")
    if expected_type and not is_type(value, expected_type):
        failures.append("type")
        # Remaining checks assume a type-correct value.
        return failures

    if expected_type in ("integer", "number", "float", "decimal"):
        if not is_finite_number(value):
            failures.append("finite")
        if "minimum" in rules and value < rules["minimum"]:
            failures.append("minimum")
        if "maximum" in rules and value > rules["maximum"]:
            failures.append("maximum")

    if "allowed_values" in rules and not is_allowed(value, rules["allowed_values"]):
        failures.append("allowed_values")

    if "format" in rules and not matches_format(value, rules["format"]):
        failures.append("format")

    return failures


def validate_record(
    row: Mapping[str, Any],
    fields: Mapping[str, Mapping[str, Any]],
) -> dict[str, list[str]]:
    """
    Validate every contract field present on a record.

    Returns:
        Mapping of field name -> violated rule names. Empty when valid.
    """
    errors: dict[str, list[str]] = {}
    for field_name, rules in fields.items():
        if field_name not in row:
            continue
        failures = check_rules(row[field_name], rules)
        if failures:
            errors[field_name] = failures
    return errors
