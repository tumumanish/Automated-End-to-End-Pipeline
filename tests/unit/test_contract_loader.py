import json
import pytest
from pathlib import Path
from src.contracts.contract_loader import ContractLoader
from src.errors.exceptions import ContractNotFoundError, ContractValidationError

@pytest.fixture
def valid_contract_file(tmp_path):
    contract = {
        "dataset": "test_ds",
        "version": "1.0",
        "fields": {}
    }
    p = tmp_path / "valid.json"
    p.write_text(json.dumps(contract))
    return p

@pytest.fixture
def invalid_json_file(tmp_path):
    p = tmp_path / "invalid.json"
    p.write_text("{not_json}")
    return p

@pytest.fixture
def missing_meta_file(tmp_path):
    contract = {"dataset": "test"} # missing version, fields
    p = tmp_path / "missing_meta.json"
    p.write_text(json.dumps(contract))
    return p

def test_load_valid_contract(valid_contract_file):
    contract = ContractLoader.load(valid_contract_file)
    assert contract["dataset"] == "test_ds"

def test_load_missing_file():
    with pytest.raises(ContractNotFoundError):
        ContractLoader.load(Path("/does/not/exist.json"))

def test_load_invalid_json(invalid_json_file):
    with pytest.raises(ContractValidationError):
        ContractLoader.load(invalid_json_file)

def test_load_missing_meta(missing_meta_file):
    with pytest.raises(ContractValidationError):
        ContractLoader.load(missing_meta_file)
