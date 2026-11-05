#!/usr/bin/env python
"""
Script: showcase.py
Purpose:
    One-click launcher to run and showcase the Automated Data Pipeline & BI Architecture.
    
    1. Validates prerequisites and environment
    2. Ensures sample datasets are populated
    3. Runs an initial ETLT++ pipeline to produce fresh curated data & lineage
    4. Ensures the warehouse is populated and analytical views are current
    5. Exports BI datasets and generates the outcome report
    6. Launches the FastAPI Web Showcase Dashboard on http://localhost:8000
"""

import sys
import webbrowser
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def print_banner():
    banner = """
======================================================================
  AUTOMATED DATA PIPELINE & BI ARCHITECTURE — SHOWCASE LAUNCHER
======================================================================
  Major Project Batch 19
  Architecture : ETLT++ & ELTL++ Multi-Hop Lakehouse
  Storage      : Raw (CSV/Excel) -> SCD2 -> Curated (Parquet)
  Monitoring   : Freshness, Completeness, Accuracy, Contract Rules
======================================================================
"""
    print(banner)

def main():
    print_banner()

    # Step 1: Ensure sample fixtures exist
    fixture_csv = PROJECT_ROOT / "tests" / "fixtures" / "sample_transactions.csv"
    if not fixture_csv.exists():
        print("[*] Generating synthetic transactions fixture...")
        from scripts.generate_sample_data import generate_dataset
        generate_dataset(num_records=100)
    else:
        print(f"[OK] Fixtures verified ({fixture_csv})")

    # Step 2: Run an initial pipeline execution to populate live metrics
    print("\n[*] Running initial baseline pipeline (ETLT++ on CSV)...")
    from src.pipelines.pipeline_runner import PipelineRunner
    runner = PipelineRunner()
    result = runner.run(
        pipeline_name="etlt_plus_plus",
        source="csv",
        dataset="transactions",
        contract_version="1.0",
        file_path=str(fixture_csv),
    )
    print(f"[OK] Initial execution: {result.get('execution_id')} | Status: {result.get('status')} | Duration: {result.get('duration_seconds')}s")

    # Step 3: Ensure the warehouse is populated and views are current
    from src.storage.postgres.pg_loader import PostgresLoader
    from src.warehouse.staging.staging_loader import StagingLoader
    from src.warehouse.views.view_manager import ViewManager

    loader = PostgresLoader()
    try:
        fact_rows = loader.table_row_count("fact_transactions", "warehouse")
    except Exception:
        fact_rows = 0

    if fact_rows == 0:
        print("\n[*] Warehouse is empty — loading curated data into the star schema...")
        load_result = StagingLoader(loader).run(dataset="transactions")
        print(f"[OK] Warehouse load: {load_result.get('status')} | Staged: {load_result.get('records_staged', 0)}")
    else:
        print(f"\n[OK] Warehouse already populated ({fact_rows:,} fact rows); skipping reload.")

    ViewManager(loader).refresh_views()

    # Step 4: Build BI deliverables and the outcome report
    from src.bi.exporter import BIExporter
    from src.bi.report import OutcomeReportBuilder

    print("\n[*] Exporting BI datasets...")
    manifest = BIExporter(loader=loader).export()
    exported = sum(1 for item in manifest["datasets"] if item["rows"] > 0)
    print(f"[OK] BI exports: {exported} populated datasets -> {manifest['output_dir']}")

    print("[*] Generating project outcome report...")
    report_path = OutcomeReportBuilder().write()
    print(f"[OK] Outcome report: {report_path}")

    # Step 5: Print Showcase Links
    host = "127.0.0.1"
    port = 8000
    print("\n" + "=" * 70)
    print("  SHOWCASE WEB INTERFACES READY")
    print("=" * 70)
    print(f"  * Control Center Web Dashboard : http://{host}:{port}/")
    print(f"  * Project Outcome Report       : http://{host}:{port}/reports/project-outcome")
    print(f"  * BI Exports (manifest)        : http://{host}:{port}/api/v1/bi/exports")
    print(f"  * Interactive Swagger API Docs : http://{host}:{port}/docs")
    print(f"  * Alternative ReDoc Reference  : http://{host}:{port}/redoc")
    print("=" * 70)
    print("\nStarting Uvicorn web server... (Press Ctrl+C to terminate)\n")

    # Auto-open browser
    try:
        webbrowser.open(f"http://{host}:{port}/")
    except Exception:
        pass

    import uvicorn
    uvicorn.run("api.main:app", host=host, port=port, reload=False, log_level="info")

if __name__ == "__main__":
    main()
