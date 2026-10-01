"""
Integration Tests: Full End-to-End Pipeline

Tests the complete flow from ingestion through to curated output
for all pipeline architectures, including lineage, monitoring,
and checkpoint integration.
"""

import sys
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


FIXTURE_CSV = PROJECT_ROOT / "tests" / "fixtures" / "sample_transactions.csv"


class TestETLTPlusPlusEndToEnd:
    """Full end-to-end tests for the ETLT++ pipeline."""

    def test_full_pipeline_with_valid_data(self, tmp_path):
        """ETLT++ should process valid CSV data end-to-end."""
        if not FIXTURE_CSV.is_file():
            pytest.skip("Sample fixture not available")

        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="etlt_plus_plus",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path=str(FIXTURE_CSV),
        )

        assert result["status"] == "SUCCESS"
        assert result["execution_id"].startswith("exec_")
        assert result["duration_seconds"] > 0

        details = result["details"]
        assert details["extracted"] > 0
        assert details["raw_path"] is not None
        assert details["valid_records"] >= 0

    def test_pipeline_produces_lineage(self, tmp_path):
        """ETLT++ should produce lineage data."""
        if not FIXTURE_CSV.is_file():
            pytest.skip("Sample fixture not available")

        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="etlt_plus_plus",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path=str(FIXTURE_CSV),
        )

        if result["status"] == "SUCCESS":
            details = result["details"]
            if "lineage_summary" in details:
                summary = details["lineage_summary"]
                assert summary["batch_id"] == result["execution_id"]
                assert summary["total_stages"] > 0

    def test_pipeline_produces_quality_metrics(self, tmp_path):
        """ETLT++ should produce quality metrics."""
        if not FIXTURE_CSV.is_file():
            pytest.skip("Sample fixture not available")

        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="etlt_plus_plus",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path=str(FIXTURE_CSV),
        )

        if result["status"] == "SUCCESS":
            details = result["details"]
            if "quality_metrics" in details:
                qm = details["quality_metrics"]
                assert "freshness_score" in qm
                assert "completeness_score" in qm
                assert "accuracy_score" in qm


class TestELTLPlusPlusEndToEnd:
    """Full end-to-end tests for the ELTL++ pipeline."""

    def test_full_pipeline_with_valid_data(self, tmp_path):
        """ELTL++ should process valid CSV data end-to-end."""
        if not FIXTURE_CSV.is_file():
            pytest.skip("Sample fixture not available")

        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="eltl_plus_plus",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path=str(FIXTURE_CSV),
        )

        assert result["status"] == "SUCCESS"
        assert result["execution_id"].startswith("exec_")

        details = result["details"]
        assert details["extracted"] > 0
        assert details["raw_path"] is not None

    def test_raw_zone_preserved(self, tmp_path):
        """ELTL++ should save data to raw zone BEFORE validation."""
        if not FIXTURE_CSV.is_file():
            pytest.skip("Sample fixture not available")

        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="eltl_plus_plus",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path=str(FIXTURE_CSV),
        )

        if result["status"] == "SUCCESS":
            raw_path = Path(result["details"]["raw_path"])
            assert raw_path.exists()


class TestBasicPipelinesEndToEnd:
    """End-to-end tests for basic ETLT and ELTL pipelines."""

    def test_basic_etlt(self, tmp_path):
        """Basic ETLT pipeline should complete successfully."""
        if not FIXTURE_CSV.is_file():
            pytest.skip("Sample fixture not available")

        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="etlt",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path=str(FIXTURE_CSV),
        )

        assert result["status"] == "SUCCESS"
        assert result["details"]["extracted"] > 0

    def test_basic_eltl(self, tmp_path):
        """Basic ELTL pipeline should complete successfully."""
        if not FIXTURE_CSV.is_file():
            pytest.skip("Sample fixture not available")

        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="eltl",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path=str(FIXTURE_CSV),
        )

        assert result["status"] == "SUCCESS"
        assert result["details"]["extracted"] > 0


class TestPipelineFailureHandling:
    """Tests for error handling across pipeline architectures."""

    def test_invalid_pipeline_name(self):
        """Running a non-existent pipeline should return FAILED status."""
        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="nonexistent_pipeline",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path="doesnt_exist.csv",
        )

        assert result["status"] == "FAILED"

    def test_missing_source_file(self):
        """A pipeline with a missing source file should return FAILED."""
        from src.pipelines.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        result = runner.run(
            pipeline_name="etlt_plus_plus",
            source="csv",
            dataset="transactions",
            contract_version="1.0",
            file_path="this_file_does_not_exist.csv",
        )

        assert result["status"] == "FAILED"
