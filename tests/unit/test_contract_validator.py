import pandas as pd
from src.contracts.contract_validator import ContractValidator

def test_valid_row():
    contract = {
        "dataset": "test",
        "version": "1.0",
        "fields": {
            "age": {"type": "integer", "nullable": False, "minimum": 18}
        }
    }
    df = pd.DataFrame([{"age": 25}])
    validator = ContractValidator()
    res = validator.validate(df, contract)
    assert res.is_valid
    assert res.valid_records == 1
    assert res.invalid_records == 0

def test_nullability():
    contract = {
        "dataset": "test",
        "fields": {
            "name": {"type": "string", "nullable": False}
        }
    }
    df = pd.DataFrame([{"name": None}])
    validator = ContractValidator()
    res = validator.validate(df, contract)
    assert not res.is_valid
    assert res.invalid_records == 1
    assert res.data_errors[0].rule == "nullable"

def test_type_integer():
    contract = {
        "fields": {
            "age": {"type": "integer"}
        }
    }
    df = pd.DataFrame([{"age": "twenty"}])
    validator = ContractValidator()
    res = validator.validate(df, contract)
    assert not res.is_valid
    assert res.data_errors[0].rule == "type"

def test_minimum_range():
    contract = {
        "fields": {
            "qty": {"type": "integer", "minimum": 1}
        }
    }
    df = pd.DataFrame([{"qty": 0}])
    validator = ContractValidator()
    res = validator.validate(df, contract)
    assert res.invalid_records == 1
    assert res.data_errors[0].rule == "minimum"

def test_allowed_values():
    contract = {
        "fields": {
            "loc": {"type": "string", "allowed_values": ["A", "B"]}
        }
    }
    df = pd.DataFrame([{"loc": "C"}])
    res = ContractValidator().validate(df, contract)
    assert res.invalid_records == 1
    assert res.data_errors[0].rule == "allowed_values"

def test_format_date():
    contract = {
        "fields": {
            "dt": {"type": "date", "format": "YYYY-MM-DD"}
        }
    }
    df = pd.DataFrame([{"dt": "2026/09/22"}])
    res = ContractValidator().validate(df, contract)
    assert res.invalid_records == 1
    assert res.data_errors[0].rule == "format"
