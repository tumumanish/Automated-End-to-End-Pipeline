"""
Module: freshness
Purpose:
    Monitor data freshness — how recent is the data relative to expectations.
"""

from datetime import datetime

from src.utils.logger import get_logger
from src.utils.timestamps import utc_now

logger = get_logger("monitoring.freshness")


class FreshnessMonitor:
    """
    Evaluates data freshness based on the time elapsed since last ingestion.

    Score calculation:
      - 100 = data just ingested (0 hours old)
      - 0   = data is at or beyond the max_age_hours threshold
      - Linear interpolation between 0 and 100
    """

    def __init__(self, max_age_hours: float = 24.0):
        """
        Args:
            max_age_hours: Maximum acceptable age in hours before freshness = 0.
        """
        self._max_age_hours = max_age_hours

    def calculate_score(self, last_ingestion_time: datetime) -> float:
        """
        Calculate a freshness score between 0 and 100.

        Args:
            last_ingestion_time: Timestamp of the most recent ingestion.

        Returns:
            Freshness score (0-100).
        """
        now = utc_now()
        # Ensure timezone awareness
        if last_ingestion_time.tzinfo is None:
            from datetime import timezone
            last_ingestion_time = last_ingestion_time.replace(tzinfo=timezone.utc)

        age_hours = (now - last_ingestion_time).total_seconds() / 3600.0

        if age_hours <= 0:
            score = 100.0
        elif age_hours >= self._max_age_hours:
            score = 0.0
        else:
            score = round(100.0 * (1.0 - age_hours / self._max_age_hours), 2)

        logger.info(
            "Freshness | age=%.1fh max=%.1fh score=%.1f",
            age_hours, self._max_age_hours, score,
        )
        return score

    def is_fresh(self, last_ingestion_time: datetime) -> bool:
        """Check whether data is considered fresh (score > 0)."""
        return self.calculate_score(last_ingestion_time) > 0.0
