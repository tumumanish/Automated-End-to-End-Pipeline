#!/usr/bin/env python
"""
Script: generate_sample_data
Purpose:
    Generate synthetic transaction data for development and testing.

Usage:
    python scripts/generate_sample_data.py                  # default 250 records
    python scripts/generate_sample_data.py --records 500
"""

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Project root resolution (works when invoked from project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"

# ---------------------------------------------------------------------------
# Reference data for synthetic generation
# ---------------------------------------------------------------------------
LOCATIONS = [
    "Hyderabad", "Mumbai", "Delhi", "Bangalore", "Chennai",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow",
    "Chandigarh", "Bhopal", "Indore", "Nagpur", "Coimbatore",
]

PRODUCTS = {
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
    "PROD-011": ("External SSD", 5500.00),
    "PROD-012": ("USB Hub", 1200.00),
}


def generate_transactions(count: int, seed: int = 2024) -> pd.DataFrame:
    """
    Generate a DataFrame of synthetic transaction records.

    Args:
        count: Number of records to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: transaction_id, customer_id, product_id,
        transaction_date, quantity, unit_price, total_amount, location.
    """
    rng = random.Random(seed)
    base_date = date(2024, 1, 1)
    product_ids = list(PRODUCTS.keys())

    rows = []
    for i in range(1, count + 1):
        pid = rng.choice(product_ids)
        _, unit_price = PRODUCTS[pid]
        qty = rng.randint(1, 10)
        txn_date = base_date + timedelta(days=rng.randint(0, 545))

        rows.append({
            "transaction_id": f"TXN-{txn_date.strftime('%Y%m%d')}-{i:05d}",
            "customer_id": f"CUST-{rng.randint(1000, 5000):04d}",
            "product_id": pid,
            "transaction_date": txn_date.isoformat(),
            "quantity": qty,
            "unit_price": unit_price,
            "total_amount": round(unit_price * qty, 2),
            "location": rng.choice(LOCATIONS),
        })

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic transaction data."
    )
    parser.add_argument(
        "--records", type=int, default=250,
        help="Number of records to generate (default: 250)",
    )
    args = parser.parse_args()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = FIXTURES_DIR / "sample_transactions.csv"
    xlsx_path = FIXTURES_DIR / "sample_transactions.xlsx"

    df = generate_transactions(args.records)

    # --- CSV ---
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"CSV  created: {csv_path}  ({len(df)} records)")

    # --- Excel ---
    df.to_excel(xlsx_path, index=False, sheet_name="transactions", engine="openpyxl")
    print(f"XLSX created: {xlsx_path}  ({len(df)} records)")

    print(f"\nSample data (first 5 rows):\n{df.head().to_string(index=False)}")


if __name__ == "__main__":
    main()
