"""
Unit tests for the date dimension loader.
Tests the date generation logic without requiring a database connection.
"""

from datetime import date

import pytest

from src.warehouse.dimensions.dim_date import DateDimensionLoader


class TestDateDimensionLoader:
    """Test the DateDimensionLoader.generate() method."""

    def setup_method(self):
        self.loader = DateDimensionLoader(loader=None)

    def test_generate_returns_dataframe(self):
        """generate() should return a non-empty DataFrame."""
        df = self.loader.generate(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )
        assert not df.empty
        assert len(df) == 31  # January has 31 days

    def test_date_key_format(self):
        """date_key should be in YYYYMMDD integer format."""
        df = self.loader.generate(
            start_date=date(2024, 3, 15),
            end_date=date(2024, 3, 15),
        )
        assert df.iloc[0]["date_key"] == 20240315

    def test_columns_present(self):
        """All expected columns should be present."""
        df = self.loader.generate(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )
        expected = {
            "date_key", "full_date", "day_of_week", "day_name",
            "day_of_month", "day_of_year", "week_of_year", "month",
            "month_name", "quarter", "year", "is_weekend", "is_holiday",
            "fiscal_quarter", "fiscal_year",
        }
        assert expected.issubset(set(df.columns))

    def test_weekend_detection(self):
        """Saturday and Sunday should be flagged as weekend."""
        # 2024-01-06 is Saturday, 2024-01-07 is Sunday
        df = self.loader.generate(
            start_date=date(2024, 1, 5),
            end_date=date(2024, 1, 8),
        )
        friday = df[df["date_key"] == 20240105].iloc[0]
        saturday = df[df["date_key"] == 20240106].iloc[0]
        sunday = df[df["date_key"] == 20240107].iloc[0]
        monday = df[df["date_key"] == 20240108].iloc[0]

        assert friday["is_weekend"] == False
        assert saturday["is_weekend"] == True
        assert sunday["is_weekend"] == True
        assert monday["is_weekend"] == False

    def test_quarter_assignment(self):
        """Quarter should be correctly derived from month."""
        df = self.loader.generate(
            start_date=date(2024, 1, 15),
            end_date=date(2024, 12, 15),
        )
        jan = df[df["month"] == 1].iloc[0]
        apr = df[df["month"] == 4].iloc[0]
        jul = df[df["month"] == 7].iloc[0]
        oct = df[df["month"] == 10].iloc[0]

        assert jan["quarter"] == 1
        assert apr["quarter"] == 2
        assert jul["quarter"] == 3
        assert oct["quarter"] == 4

    def test_holiday_detection(self):
        """Republic Day (Jan 26) should be flagged as holiday."""
        df = self.loader.generate(
            start_date=date(2024, 1, 25),
            end_date=date(2024, 1, 27),
        )
        jan26 = df[df["date_key"] == 20240126].iloc[0]
        jan25 = df[df["date_key"] == 20240125].iloc[0]

        assert jan26["is_holiday"] == True
        assert jan25["is_holiday"] == False

    def test_full_year_count(self):
        """A full leap year should have 366 rows."""
        df = self.loader.generate(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert len(df) == 366  # 2024 is a leap year
