import os
import pytest
import pandas as pd
from src.contracts.validation_service import ValidationService
from src.utils.file_utils import get_project_root

@pytest.fixture
def service():
    # Use real root for registry to find contracts
    return ValidationService()

def test_integration_validation_valid_data(service):
    # The valid sample
    file_path = get_project_root() / "tests" / "fixtures" / "sample_transactions.csv"
    df = pd.read_csv(file_path)
    
    df_valid, df_invalid, result = service.run_validation(
        df=df,
        dataset_name="transactions",
        contract_version="1.0",
        batch_id="test_valid_batch"
    )
    
    assert result.is_valid
    assert result.invalid_records == 0
    assert len(df_valid) == len(df)
    assert len(df_invalid) == 0

def test_integration_validation_invalid_data(service):
    # The intentionally invalid sample
    file_path = get_project_root() / "tests" / "fixtures" / "invalid_transactions.csv"
    df = pd.read_csv(file_path)
    
    df_valid, df_invalid, result = service.run_validation(
        df=df,
        dataset_name="transactions",
        contract_version="1.0",
        batch_id="test_invalid_batch"
    )
    
    assert not result.is_valid
    # The invalid transactions file has 10 rows. 3 are valid, 7 are invalid.
    # We can just check that it separated them.
    assert result.invalid_records > 0
    assert len(df_invalid) == result.invalid_records
    assert len(df_valid) == result.valid_records
    assert len(result.data_errors) > 0
    
    # Check that quarantine metadata was written
    quarantine_path = get_project_root() / "data" / "quarantine" / "validation_errors" / "transactions" / "test_invalid_batch.json"
    assert quarantine_path.exists()
