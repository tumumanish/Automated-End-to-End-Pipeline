#!/usr/bin/env python
"""
Script: export_bi_data.py
Purpose:
    Export BI-ready datasets from the warehouse analytical views and monitoring
    tables into dashboard/exports/ as CSV files, together with a KPI summary
    (kpi_summary.json) and a manifest (manifest.json).

Usage:
    python scripts/export_bi_data.py
    python scripts/export_bi_data.py --output-dir dashboard/exports --limit 5000
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bi.exporter import DEFAULT_OUTPUT_DIR, BIExporter
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger("bi.export")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export BI datasets from the warehouse.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Destination directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional row limit per dataset (0 = all rows)",
    )
    args = parser.parse_args()

    exporter = BIExporter(output_dir=args.output_dir)
    manifest = exporter.export(limit=args.limit)

    print(f"\n{'=' * 64}")
    print(" BI DATA EXPORT COMPLETE")
    print(f"{'=' * 64}")
    print(f" Backend : {manifest['backend']}")
    print(f" Output  : {manifest['output_dir']}")
    print(f"{'-' * 64}")
    for dataset in manifest["datasets"]:
        status = dataset["status"].upper()
        print(f"  {dataset['schema'] + '.' + dataset['name']:<42} {dataset['rows']:>8,} rows  {status}")
    if manifest["errors"]:
        print(f"{'-' * 64}")
        for error in manifest["errors"]:
            print(f"  ! {error['dataset']}: {error['error'][:80]}")
    print(f"{'=' * 64}")
    print(" KPI summary : kpi_summary.json")
    print(" Manifest    : manifest.json")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
