#!/usr/bin/env python
"""
Script: generate_project_report.py
Purpose:
    Generate a standalone HTML report that depicts the outcome of the project
    from the BI exports in dashboard/exports/.

Usage:
    python scripts/generate_project_report.py
    python scripts/generate_project_report.py --open
    python scripts/generate_project_report.py --exports-dir dashboard/exports \
        --output dashboard/reports/project_outcome.html
"""

import argparse
import sys
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bi.exporter import DEFAULT_OUTPUT_DIR
from src.bi.report import DEFAULT_REPORT_PATH, OutcomeReportBuilder
from src.utils.logger import setup_logging

setup_logging()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the project outcome HTML report.")
    parser.add_argument(
        "--exports-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Directory containing BI exports (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT_PATH),
        help=f"Report output path (default: {DEFAULT_REPORT_PATH})",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated report in the default browser",
    )
    args = parser.parse_args()

    exports_dir = Path(args.exports_dir)
    if not (exports_dir / "manifest.json").exists():
        print(
            f"[!] No manifest found in {exports_dir}. "
            "Run `python scripts/export_bi_data.py` first for complete results."
        )

    builder = OutcomeReportBuilder(exports_dir=exports_dir)
    output = builder.write(args.output)

    print(f"\n{'=' * 64}")
    print(" PROJECT OUTCOME REPORT GENERATED")
    print(f"{'=' * 64}")
    print(f" Source : {exports_dir}")
    print(f" Report : {output}")
    print(f" Size   : {output.stat().st_size:,} bytes")
    print(f"{'=' * 64}\n")

    if args.open:
        webbrowser.open(output.resolve().as_uri())


if __name__ == "__main__":
    main()
