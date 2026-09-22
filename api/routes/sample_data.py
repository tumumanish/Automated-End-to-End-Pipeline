"""
Route: /api/v1/sample/transactions
Purpose:
    Return synthetic transaction records for development/testing.

    ⚠️  This is a DEVELOPMENT endpoint that serves sample data.
         It is NOT a production API.
"""

import random
from datetime import date, timedelta

from fastapi import APIRouter, Query

router = APIRouter()

# --- Synthetic reference data ---
_LOCATIONS = [
    "Hyderabad", "Mumbai", "Delhi", "Bangalore", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
]

_PRODUCTS = {
    "PROD-001": ("Laptop", 45000.00),
    "PROD-002": ("Smartphone", 22000.00),
    "PROD-003": ("Tablet", 18000.00),
    "PROD-004": ("Monitor", 12000.00),
    "PROD-005": ("Keyboard", 1500.00),
    "PROD-006": ("Mouse", 800.00),
    "PROD-007": ("Headphones", 3500.00),
    "PROD-008": ("Webcam", 4500.00),
    "PROD-009": ("Printer", 9000.00),
    "PROD-010": ("Speaker", 6000.00),
}

# Seed for reproducibility within a request
_RNG = random.Random(42)


def _generate_records(count: int) -> list[dict]:
    """Generate ``count`` synthetic transaction records."""
    rng = random.Random(42)
    base_date = date(2024, 1, 1)
    records = []

    for i in range(1, count + 1):
        product_id = rng.choice(list(_PRODUCTS.keys()))
        product_name, unit_price = _PRODUCTS[product_id]
        quantity = rng.randint(1, 10)
        txn_date = base_date + timedelta(days=rng.randint(0, 545))

        records.append({
            "transaction_id": f"TXN-{txn_date.strftime('%Y%m%d')}-{i:05d}",
            "customer_id": f"CUST-{rng.randint(1000, 5000):04d}",
            "product_id": product_id,
            "transaction_date": txn_date.isoformat(),
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": round(unit_price * quantity, 2),
            "location": rng.choice(_LOCATIONS),
        })

    return records


@router.get("/sample/transactions")
def get_sample_transactions(
    limit: int = Query(default=50, ge=1, le=1000, description="Number of records"),
):
    """
    Return synthetic transaction records.

    ⚠️  Development / sample data only — not a production API.
    """
    records = _generate_records(limit)
    return {
        "dataset": "transactions",
        "version": "1.0",
        "source": "sample_api",
        "record_count": len(records),
        "records": records,
    }
