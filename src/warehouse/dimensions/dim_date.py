"""
Module: dim_date
Purpose:
    Generate and load the date dimension table (warehouse.dim_date).
"""

import pandas as pd
from datetime import date, timedelta
from src.storage.postgres.pg_loader import bulk_insert, execute_query
from src.utils.logger import get_logger

logger = get_logger("warehouse.dim_date")

MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class DateDimensionLoader:
    """Generates and loads the date dimension from a date range."""

    SCHEMA = "warehouse"
    TABLE  = "dim_date"

    def generate(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Generate a date dimension DataFrame for the given range."""
        records = []
        current = start_date
        while current <= end_date:
            records.append({
                "date_key":   int(current.strftime("%Y%m%d")),
                "full_date":  current,
                "day_of_week": current.weekday() + 1,   # 1=Mon … 7=Sun
                "day_name":   DAY_NAMES[current.weekday()],
                "month":      current.month,
                "month_name": MONTH_NAMES[current.month - 1],
                "quarter":    (current.month - 1) // 3 + 1,
                "year":       current.year,
                "is_weekend": current.weekday() >= 5,
                "is_holiday": False,
            })
            current += timedelta(days=1)
        return pd.DataFrame(records)

    def load(self, start_date: date, end_date: date) -> int:
        """Generate and load date dimension, skipping already-loaded dates."""
        df = self.generate(start_date, end_date)

        existing = execute_query(f"SELECT date_key FROM {self.SCHEMA}.{self.TABLE}")
        existing_keys = {r["date_key"] for r in existing}
        new_rows = df[~df["date_key"].isin(existing_keys)]

        if new_rows.empty:
            logger.info("dim_date: all dates already loaded.")
            return 0

        count = bulk_insert(new_rows, self.SCHEMA, self.TABLE)
        logger.info(f"dim_date: loaded {count} new date records.")
        return count
