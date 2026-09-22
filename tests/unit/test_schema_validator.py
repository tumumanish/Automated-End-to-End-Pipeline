import pandas as pd
from src.contracts.schema_validator import SchemaValidator

def test_valid_schema():
    contract = {
        "fields": {
            "id": {"required": True},
            "name": {"required": False}
        }
    }
    df = pd.DataFrame([{"id": 1, "name": "A"}])
    errors = SchemaValidator.validate(df, contract)
    assert len([e for e in errors if e.rule == "schema_required_column"]) == 0

def test_missing_required_column():
    contract = {
        "fields": {
            "id": {"required": True},
            "name": {"required": True}
        }
    }
    df = pd.DataFrame([{"id": 1}])
    errors = SchemaValidator.validate(df, contract)
    missing = [e for e in errors if e.rule == "schema_required_column"]
    assert len(missing) == 1
    assert missing[0].field == "name"

def test_unexpected_column():
    contract = {
        "fields": {
            "id": {"required": True}
        }
    }
    df = pd.DataFrame([{"id": 1, "extra": "A"}])
    errors = SchemaValidator.validate(df, contract)
    unexpected = [e for e in errors if e.rule == "schema_unexpected_column"]
    assert len(unexpected) == 1
    assert unexpected[0].field == "extra"
