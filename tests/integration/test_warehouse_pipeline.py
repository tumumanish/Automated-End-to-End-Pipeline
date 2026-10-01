"""
Integration test: Warehouse Pipeline
Purpose:
    Tests the full warehouse loading pipeline end-to-end
    (requires PostgreSQL — skip if not available).
"""

import sys
from pathlib import Path

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.warehouse.staging.staging_loader import StagingLoader


@pytest.fixture
def sample_transactions():
    """Create a sample curated transactions DataFrame."""
    return pd.DataFrame({
        "transaction_id": [f"TXN-2024-{i:05d}" for i in range(10)],
        "customer_id": [f"CUST-{1000 + i}" for i in range(10)],
        "product_id": [f"PROD-{(i % 5) + 1:03d}" for i in range(10)],
        "transaction_date": [f"2024-{(i % 12) + 1:02d}-15" for i in range(10)],
        "quantity": [i + 1 for i in range(10)],
        "unit_price": [1000.0 * (i + 1) for i in range(10)],
        "total_amount": [1000.0 * (i + 1) * (i + 1) for i in range(10)],
        "location": ["Hyderabad", "Mumbai", "Delhi", "Bangalore", "Chennai",
                      "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"],
    })


class TestWarehousePipeline:
    """Integration test for the warehouse pipeline orchestration."""

    def test_staging_loader_reads_csv(self, tmp_path, sample_transactions):
        """StagingLoader should read CSV files from the curated directory."""
        curated_dir = tmp_path / "data" / "curated" / "transactions"
        curated_dir.mkdir(parents=True)
        sample_transactions.to_csv(curated_dir / "batch_test.csv", index=False)

        mock_loader = MagicMock()
        staging = StagingLoader(loader=mock_loader)

        with patch(
            "src.warehouse.staging.staging_loader.get_project_root",
            return_value=tmp_path,
        ):
            df = staging.read_curated_data("transactions")
            assert len(df) == 10
            assert "transaction_id" in df.columns

    def test_dimension_extraction_from_transactions(self, sample_transactions):
        """Dimension loaders should extract correct entities from transactions."""
        from src.warehouse.dimensions.dim_customer import CustomerDimensionLoader
        from src.warehouse.dimensions.dim_product import ProductDimensionLoader
        from src.warehouse.dimensions.dim_location import LocationDimensionLoader

        mock_loader = MagicMock()

        cust = CustomerDimensionLoader(loader=mock_loader)
        customers = cust.extract_customers(sample_transactions)
        assert len(customers) == 10  # 10 unique customers

        prod = ProductDimensionLoader(loader=mock_loader)
        products = prod.extract_products(sample_transactions)
        assert len(products) == 5  # 5 unique products (PROD-001 to PROD-005)

        loc = LocationDimensionLoader(loader=mock_loader)
        locations = loc.extract_locations(sample_transactions)
        assert len(locations) == 10  # 10 unique locations

    def test_full_pipeline_mock(self, tmp_path, sample_transactions):
        """Full pipeline should complete with mock database."""
        curated_dir = tmp_path / "data" / "curated" / "transactions"
        curated_dir.mkdir(parents=True)
        sample_transactions.to_csv(curated_dir / "batch_test.csv", index=False)

        mock_loader = MagicMock()
        mock_loader.load_dataframe.return_value = 10
        mock_loader.query.return_value = pd.DataFrame()

        staging = StagingLoader(loader=mock_loader)

        with patch(
            "src.warehouse.staging.staging_loader.get_project_root",
            return_value=tmp_path,
        ):
            result = staging.run("transactions")

        assert result["status"] == "SUCCESS"
        assert result["records_staged"] == 10
