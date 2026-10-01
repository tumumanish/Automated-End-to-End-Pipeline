"""
Unit tests for the warehouse staging loader.
Tests the data reading and staging DataFrame construction
without requiring a database connection.
"""

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from src.warehouse.staging.staging_loader import StagingLoader


class TestStagingLoader:
    """Test the StagingLoader data preparation methods."""

    def setup_method(self):
        self.mock_loader = MagicMock()
        self.staging = StagingLoader(loader=self.mock_loader)

    def _make_sample_df(self, n: int = 5) -> pd.DataFrame:
        """Create a sample curated transactions DataFrame."""
        return pd.DataFrame({
            "transaction_id": [f"TXN-{i:05d}" for i in range(n)],
            "customer_id": [f"CUST-{1000 + i}" for i in range(n)],
            "product_id": [f"PROD-{(i % 3) + 1:03d}" for i in range(n)],
            "transaction_date": ["2024-06-15"] * n,
            "quantity": [i + 1 for i in range(n)],
            "unit_price": [100.0] * n,
            "total_amount": [(i + 1) * 100.0 for i in range(n)],
            "location": ["Hyderabad", "Mumbai", "Delhi", "Bangalore", "Chennai"][:n],
        })

    def test_load_staging_constructs_correct_columns(self):
        """load_staging should produce a DataFrame with the right columns."""
        df = self._make_sample_df()
        self.mock_loader.load_dataframe.return_value = len(df)
        count = self.staging.load_staging(df, "batch_001")

        assert count == 5
        call_args = self.mock_loader.load_dataframe.call_args
        loaded_df = call_args[0][0]
        assert "transaction_id" in loaded_df.columns
        assert "batch_id" in loaded_df.columns
        assert loaded_df["batch_id"].iloc[0] == "batch_001"

    def test_load_staging_empty_df_returns_zero(self):
        """load_staging should return 0 for an empty DataFrame."""
        count = self.staging.load_staging(pd.DataFrame(), "batch_001")
        assert count == 0

    def test_read_curated_data_missing_dir(self, tmp_path):
        """read_curated_data should return empty DataFrame for missing dir."""
        with patch("src.warehouse.staging.staging_loader.get_project_root", return_value=tmp_path):
            df = self.staging.read_curated_data("nonexistent_dataset")
            assert df.empty

    def test_run_returns_no_data_when_empty(self, tmp_path):
        """run() should return NO_DATA status when no curated files exist."""
        with patch("src.warehouse.staging.staging_loader.get_project_root", return_value=tmp_path):
            result = self.staging.run("missing_dataset")
            assert result["status"] == "NO_DATA"

    def test_read_curated_csv_files(self, tmp_path):
        """read_curated_data should read CSV files from the curated directory."""
        curated_dir = tmp_path / "data" / "curated" / "test_dataset"
        curated_dir.mkdir(parents=True)

        df = self._make_sample_df(3)
        df.to_csv(curated_dir / "batch_001.csv", index=False)

        with patch("src.warehouse.staging.staging_loader.get_project_root", return_value=tmp_path):
            result = self.staging.read_curated_data("test_dataset")
            assert len(result) == 3
            assert "transaction_id" in result.columns
