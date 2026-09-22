import pytest
import os
from pathlib import Path
from src.pipelines.pipeline_runner import PipelineRunner
from src.utils.file_utils import get_project_root

def test_etlt_plus_plus_pipeline_valid_data():
    runner = PipelineRunner()
    
    # Path to valid transactions
    csv_path = get_project_root() / "tests" / "fixtures" / "sample_transactions.csv"
    
    result = runner.run(
        pipeline_name="etlt_plus_plus",
        source="csv",
        dataset="transactions",
        contract_version="1.0",
        file_path=str(csv_path)
    )
    
    assert result["status"] == "SUCCESS"
    details = result["details"]
    assert details["extracted"] == 100
    assert details["valid_records"] == 100
    assert details["validation_status"] == "PASS"
    # Depending on duplicates in the sample, transformed_records might be <= 100
    assert details["transformed_records"] <= 100 
    assert details["curated_path"] is not None
    
    # Verify curated file exists
    assert Path(details["curated_path"]).exists()

def test_etlt_plus_plus_pipeline_invalid_data():
    runner = PipelineRunner()
    
    # Path to invalid transactions (which fail contract completely)
    csv_path = get_project_root() / "tests" / "fixtures" / "invalid_transactions.csv"
    
    result = runner.run(
        pipeline_name="etlt_plus_plus",
        source="csv",
        dataset="transactions",
        contract_version="1.0",
        file_path=str(csv_path)
    )
    
    # Pipeline shouldn't crash, but details should show 0 transformed
    assert result["status"] == "SUCCESS"
    details = result["details"]
    assert details["extracted"] == 10
    assert details["valid_records"] == 0
    assert details["invalid_records"] == 10
    assert details["transformed_records"] == 0
    assert details["curated_path"] is None
