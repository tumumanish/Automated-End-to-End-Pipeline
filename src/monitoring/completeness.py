"""
Module: completeness
Purpose:
    Monitor data completeness — are all expected fields and records present?
"""

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("monitoring.completeness")


class CompletenessMonitor:
    """
    Evaluates data completeness by measuring the percentage of non-null
    values across all fields in a DataFrame.
    """

    def __init__(self, min_percent: float = 95.0):
        """
        Args:
            min_percent: Minimum acceptable completeness percentage.
        """
        self._min_percent = min_percent

    def calculate_score(self, df: pd.DataFrame) -> float:
        """
        Calculate an aggregate completeness score (0-100).

        Score = average non-null percentage across all columns.

        Args:
            df: The DataFrame to evaluate.

        Returns:
            Completeness score (0-100).
        """
        if df.empty:
            return 0.0

        total_cells = df.shape[0] * df.shape[1]
        if total_cells == 0:
            return 0.0

        non_null_cells = df.notna().sum().sum()
        score = round(100.0 * non_null_cells / total_cells, 2)

        logger.info(
            "Completeness | cells=%d non_null=%d score=%.1f",
            total_cells, non_null_cells, score,
        )
        return score

    def per_field_scores(self, df: pd.DataFrame) -> dict[str, float]:
        """
        Calculate completeness score for each field individually.

        Args:
            df: The DataFrame to evaluate.

        Returns:
            Dict mapping column name to its completeness percentage.
        """
        if df.empty:
            return {}

        scores = {}
        for col in df.columns:
            non_null = int(df[col].notna().sum())
            scores[col] = round(100.0 * non_null / len(df), 2)

        return scores

    def is_complete(self, df: pd.DataFrame) -> bool:
        """Check whether data meets the minimum completeness threshold."""
        return self.calculate_score(df) >= self._min_percent

    def get_incomplete_fields(self, df: pd.DataFrame) -> dict[str, float]:
        """Return fields that fall below the minimum completeness threshold."""
        scores = self.per_field_scores(df)
        return {
            col: score for col, score in scores.items()
            if score < self._min_percent
        }
