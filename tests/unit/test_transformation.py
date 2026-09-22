import pandas as pd
from src.transformation.cleaning import DataCleaner
from src.transformation.normalization import DataNormalizer
from src.transformation.deduplication import Deduplicator
from src.transformation.business_rules import BusinessRuleEngine

def test_data_cleaner():
    df = pd.DataFrame([{"name": " Alice ", "city": "nan", "code": ""}])
    cleaned = DataCleaner.clean(df)
    assert cleaned.iloc[0]["name"] == "Alice"
    assert pd.isna(cleaned.iloc[0]["city"])
    assert pd.isna(cleaned.iloc[0]["code"])

def test_data_normalizer():
    df = pd.DataFrame([{"location": "hyderabad", "transaction_id": "trx-123", "transaction_date": "2026-09-22"}])
    norm = DataNormalizer.normalize(df, "transactions")
    assert norm.iloc[0]["location"] == "Hyderabad"
    assert norm.iloc[0]["transaction_id"] == "TRX-123"
    assert isinstance(norm.iloc[0]["transaction_date"], pd.Timestamp)

def test_deduplicator():
    df = pd.DataFrame([
        {"transaction_id": "T1", "transaction_date": "2026-09-21", "val": 10},
        {"transaction_id": "T1", "transaction_date": "2026-09-22", "val": 20}
    ])
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    dedup = Deduplicator.deduplicate(df, "transactions")
    assert len(dedup) == 1
    assert dedup.iloc[0]["val"] == 20 # Kept the latest

def test_business_rules():
    df = pd.DataFrame([{"quantity": 2, "unit_price": 50.0, "total_amount": 1500.0, "location": None}])
    biz = BusinessRuleEngine.apply_rules(df, "transactions")
    assert biz.iloc[0]["calculated_total"] == 100.0
    assert biz.iloc[0]["is_high_value"] == True
    assert biz.iloc[0]["needs_location_review"] == True
