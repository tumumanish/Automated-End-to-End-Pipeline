"""
Module: dim_date
Purpose:
    Generate and populate the date dimension table from a date range.
    The date dimension is pre-populated once and serves as a static
    lookup for temporal analysis.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import pandas as pd

from src.storage.postgres.pg_loader import PostgresLoader
from src.utils.logger import get_logger

logger = get_logger("warehouse.dim_date")

# Indian national holidays (simplified — extend as needed)
_HOLIDAYS = {
    (1, 26),   # Republic Day
    (8, 15),   # Independence Day
    (10, 2),   # Gandhi Jayanti
}


class DateDimensionLoader:
    """
    Generate and load the date dimension into ``warehouse.dim_date``.

    The date key format is ``YYYYMMDD`` (integer), which allows direct
    integer comparison and efficient range scans.
    """

    def __init__(self, loader: Optional[PostgresLoader] = None):
        self._loader = loader or PostgresLoader()

    def generate(
        self,
        start_date: date = date(2023, 1, 1),
        end_date: date = date(2027, 12, 31),
    ) -> pd.DataFrame:
        """
        Generate a DataFrame containing one row per calendar day.

        Args:
            start_date: First date in the dimension.
            end_date: Last date in the dimension.

        Returns:
            DataFrame with all date dimension columns.
        """
        rows = []
        current = start_date
        while current <= end_date:
            rows.append({
                "date_key": int(current.strftime("%Y%m%d")),
                "full_date": current,
                "day_of_week": current.isoweekday(),           # 1=Mon … 7=Sun
                "day_name": current.strftime("%A"),
                "day_of_month": current.day,
                "day_of_year": current.timetuple().tm_yday,
                "week_of_year": current.isocalendar()[1],
                "month": current.month,
                "month_name": current.strftime("%B"),
                "quarter": (current.month - 1) // 3 + 1,
                "year": current.year,
                "is_weekend": current.isoweekday() >= 6,
                "is_holiday": (current.month, current.day) in _HOLIDAYS,
                "fiscal_quarter": (current.month - 1) // 3 + 1,
                "fiscal_year": current.year,
            })
            current += timedelta(days=1)

        logger.info("Generated date dimension: %d rows (%s to %s)", len(rows), start_date, end_date)
        return pd.DataFrame(rows)

    def load(
        self,
        start_date: date = date(2023, 1, 1),
        end_date: date = date(2027, 12, 31),
    ) -> int:
        """
        Generate and load the date dimension into PostgreSQL.
        Replaces existing data (idempotent).

        Returns:
            Number of rows loaded.
        """
        df = self.generate(start_date, end_date)
        count = self._loader.load_dataframe(
            df, table_name="dim_date", schema="warehouse", if_exists="replace",
        )
        logger.info("Date dimension loaded: %d rows", count)
        return count
