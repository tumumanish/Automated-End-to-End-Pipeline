import pandas as pd
import json
from src.errors.quarantine_manager import QuarantineManager
from src.contracts.validation_result import ValidationResult, ValidationErrorMetadata

def test_quarantine_creates_files(tmp_path):
    qm = QuarantineManager(quarantine_dir=tmp_path)
    df = pd.DataFrame([{"id": 1, "bad": "yes"}])
    
    result = ValidationResult("test", "1.0")
    result.data_errors.append(
        ValidationErrorMetadata(row_index=0, field="bad", rule="type", message="err")
    )
    
    csv_path = qm.quarantine_invalid_records(df, "test", "batch_123", result)
    
    assert csv_path.exists()
    assert csv_path.name == "batch_123.csv"
    
    meta_path = csv_path.with_suffix(".json")
    assert meta_path.exists()
    
    with open(meta_path) as f:
        meta = json.load(f)
    assert meta["batch_id"] == "batch_123"
    assert meta["invalid_record_count"] == 1
    assert len(meta["errors"]) == 1

def test_quarantine_empty_df(tmp_path):
    qm = QuarantineManager(quarantine_dir=tmp_path)
    df = pd.DataFrame()
    result = ValidationResult("test", "1.0")
    
    path = qm.quarantine_invalid_records(df, "test", "batch_123", result)
    assert path == tmp_path # returns root if empty
