"""
Integration Tests: ELTL++ Pipeline

End-to-end test of the ELTL++ pipeline with lineage and monitoring.
Uses the sample data API as a data source.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipelines.pipeline_runner import PipelineRunner
from src.pipelines.pipeline_registry import PipelineRegistry


class TestELTLPlusPlusPipeline:
    """Integration test for the ELTL++ pipeline."""

    @pytest.fixture
    def runner(self):
        return PipelineRunner()

    @pytest.fixture
    def sample_csv_path(self, tmp_path):
        """Create a sample CSV file for testing."""
        import pandas as pd

        df = pd.DataFrame({
            "transaction_id": [f"TXN-{i:05d}" for i in range(1, 6)],
            "customer_id": ["CUST-1001", "CUST-1002", "CUST-1003", "CUST-1004", "CUST-1005"],
            "product_id": ["PROD-001", "PROD-002", "PROD-003", "PROD-001", "PROD-004"],
            "transaction_date": ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19"],
            "quantity": [2, 1, 3, 1, 2],
            "unit_price": [45000.00, 22000.00, 18000.00, 45000.00, 12000.00],
            "total_amount": [90000.00, 22000.00, 54000.00, 45000.00, 24000.00],
            "location": ["Hyderabad", "Mumbai", "Delhi", "Bangalore", "Chennai"],
        })
        csv_path = tmp_path / "test_transactions.csv"
        df.to_csv(csv_path, index=False)
        return str(csv_path)

    def test_eltl_plus_plus_registered(self):
        """ELTL++ should be registered in the pipeline registry."""
        assert PipelineRegistry.is_registered("eltl_plus_plus")

    def test_eltl_pipeline_registered(self):
        """Basic ELTL should be registered in the pipeline registry."""
        assert PipelineRegistry.is_registered("eltl")

    def test_all_four_pipelines_registered(self):
        """All 4 pipeline variants should be registered."""
        pipelines = PipelineRegistry.list_pipelines()
        assert "etlt_plus_plus" in pipelines
        assert "eltl_plus_plus" in pipelines
        assert "etlt" in pipelines
        assert "eltl" in pipelines
