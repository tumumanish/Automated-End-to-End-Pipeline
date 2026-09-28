"""
Module: accuracy
Purpose:
    Monitor data accuracy — do values conform to expected ranges and formats?
"""

from src.contracts.validation_result import ValidationResult
from src.utils.logger import get_logger

logger = get_logger("monitoring.accuracy")


class AccuracyMonitor:
    """
    Evaluates data accuracy based on the percentage of records that pass
    all contract validation rules.
    """

    def __init__(self, min_percent: float = 98.0):
        """
        Args:
            min_percent: Minimum acceptable accuracy percentage.
        """
        self._min_percent = min_percent

    def calculate_score(self, validation_result: ValidationResult) -> float:
        """
        Calculate accuracy score from a validation result.

        Score = (valid_records / total_records) * 100

        Args:
            validation_result: Result from contract validation.

        Returns:
            Accuracy score (0-100).
        """
        total = validation_result.total_records
        if total == 0:
            return 100.0

        valid = validation_result.valid_records
        score = round(100.0 * valid / total, 2)

        logger.info(
            "Accuracy | total=%d valid=%d invalid=%d score=%.1f",
            total, valid, validation_result.invalid_records, score,
        )
        return score

    def calculate_from_counts(self, total: int, valid: int) -> float:
        """
        Calculate accuracy from raw counts.

        Args:
            total: Total records.
            valid: Records passing all rules.

        Returns:
            Accuracy score (0-100).
        """
        if total == 0:
            return 100.0
        return round(100.0 * valid / total, 2)

    def is_accurate(self, validation_result: ValidationResult) -> bool:
        """Check whether data meets the minimum accuracy threshold."""
        return self.calculate_score(validation_result) >= self._min_percent

    def get_error_breakdown(self, validation_result: ValidationResult) -> dict[str, int]:
        """
        Break down validation errors by rule type.

        Returns:
            Dict mapping rule name to error count.
        """
        breakdown: dict[str, int] = {}
        for error in validation_result.data_errors:
            breakdown[error.rule] = breakdown.get(error.rule, 0) + 1
        for error in validation_result.schema_errors:
            breakdown[error.rule] = breakdown.get(error.rule, 0) + 1
        return breakdown
