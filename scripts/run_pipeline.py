#!/usr/bin/env python
"""
Script: run_pipeline
Purpose:
    Execute a data ingestion pipeline from the command line.

Usage:
    python scripts/run_pipeline.py --source csv   --file tests/fixtures/sample_transactions.csv
    python scripts/run_pipeline.py --source excel --file tests/fixtures/sample_transactions.xlsx
    python scripts/run_pipeline.py --source api   --url  http://localhost:8000/api/v1/sample/transactions
    python scripts/run_pipeline.py --source api   --url  http://localhost:8000/api/v1/sample/transactions?limit=100
"""

import argparse
import sys
import time
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import setup_logging, get_logger
from src.ingestion.ingestion_factory import create_ingestion
from src.storage.raw_storage import save_raw_data
from src.errors.error_handler import handle_ingestion_error
from src.contracts.validation_service import ValidationService

setup_logging()
logger = get_logger("pipeline")

DATASET_NAME = "transactions"


def generate_batch_id() -> str:
    """Generate a unique batch identifier."""
    return f"batch_{uuid.uuid4().hex[:12]}"


def try_db_operations(batch_id, source_type, source_name, df, raw_path):
    """
    Attempt PostgreSQL operations. Returns True on success, False if DB unavailable.
    """
    try:
        from src.storage.postgres.loader import (
            create_batch_record,
            complete_batch,
            insert_audit_event,
            load_dataframe,
        )

        # --- Create batch record ---
        create_batch_record(
            batch_id=batch_id,
            source_type=source_type,
            source_name=source_name,
            dataset_name=DATASET_NAME,
        )
        insert_audit_event(batch_id, "extract", "COMPLETED",
                           f"Extracted {len(df)} records from {source_type}",
                           record_count=len(df))

        # --- Prepare DataFrame for raw table ---
        db_df = df.copy()
        db_df["source_system"] = source_type
        db_df["ingestion_batch_id"] = batch_id

        # --- Load into PostgreSQL ---
        insert_audit_event(batch_id, "db_load", "STARTED",
                           f"Loading {len(db_df)} records into raw.transactions")
        load_dataframe(db_df, table_name="transactions", schema="raw")
        insert_audit_event(batch_id, "db_load", "COMPLETED",
                           f"Loaded {len(db_df)} records", record_count=len(db_df))

        # --- Mark batch SUCCESS ---
        complete_batch(batch_id, record_count=len(df),
                       file_path=str(raw_path))
        return True

    except Exception as exc:
        logger.warning("PostgreSQL operations skipped: %s", exc)
        # Try to mark batch as failed if possible
        try:
            from src.storage.postgres.loader import fail_batch
            fail_batch(batch_id, str(exc))
        except Exception:
            pass
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Run data ingestion pipeline.")
    parser.add_argument("--source", required=True,
                        choices=["csv", "excel", "api", "database"],
                        help="Source type")
    parser.add_argument("--file", help="File path (for csv/excel)")
    parser.add_argument("--url", help="API URL (for api source)")
    parser.add_argument("--dataset", default=DATASET_NAME,
                        help="Dataset name (default: transactions)")
    parser.add_argument("--contract-version", default=None,
                        help="Version of the data contract to validate against")
    args = parser.parse_args()

    batch_id = generate_batch_id()
    dataset_name = args.dataset
    start_time = time.time()

    # --- Resolve source arguments ---
    kwargs = {}
    source_name = ""
    if args.source in ("csv", "excel"):
        if not args.file:
            print("ERROR: --file is required for csv/excel source.")
            sys.exit(1)
        kwargs["file_path"] = args.file
        source_name = args.file
    elif args.source == "api":
        if not args.url:
            print("ERROR: --url is required for api source.")
            sys.exit(1)
        kwargs["url"] = args.url
        source_name = args.url
    elif args.source == "database":
        print("ERROR: database source requires --connection-string and --query (not yet exposed via CLI).")
        sys.exit(1)

    print(f"\n{'=' * 50}")
    print(f" INGESTION PIPELINE — Phase 2")
    print(f"{'=' * 50}")
    print(f" Batch ID  : {batch_id}")
    print(f" Source    : {args.source}")
    print(f" Dataset   : {dataset_name}")
    print(f" Input     : {source_name}")
    print(f"{'=' * 50}\n")

    logger.info("Pipeline started | batch_id=%s source=%s dataset=%s",
                batch_id, args.source, dataset_name)

    # ------------------------------------------------------------------
    # STEP 1: Extract
    # ------------------------------------------------------------------
    try:
        adapter = create_ingestion(args.source, **kwargs)
        df = adapter.extract()
    except Exception as exc:
        handle_ingestion_error(exc, batch_id, args.source, source_name)
        print(f"INGESTION FAILED: {exc}")
        sys.exit(1)

    print(f"[1/3] Extracted {len(df)} records from {args.source}")

    # ------------------------------------------------------------------
    # STEP 2: Save raw file
    # ------------------------------------------------------------------
    raw_path = save_raw_data(df, args.source, dataset_name, batch_id)
    print(f"[2/3] Raw data saved -> {raw_path}")

    # ------------------------------------------------------------------
    # STEP 3: Load into PostgreSQL (best-effort)
    # ------------------------------------------------------------------
    db_success = try_db_operations(batch_id, args.source, source_name, df, raw_path)

    if db_success:
        print(f"[3/4] Loaded into PostgreSQL raw.transactions")
    else:
        print(f"[3/4] PostgreSQL load skipped (database unavailable)")

    # ------------------------------------------------------------------
    # STEP 4: Validation (Phase 3)
    # ------------------------------------------------------------------
    validation_status = "N/A"
    valid_count = len(df)
    invalid_count = 0
    if args.contract_version:
        print(f"\n[4/4] Validating against contract version {args.contract_version}...")
        try:
            validator = ValidationService()
            df_valid, df_invalid, val_result = validator.run_validation(
                df=df,
                dataset_name=dataset_name,
                contract_version=args.contract_version,
                batch_id=batch_id
            )
            validation_status = val_result.status
            valid_count = val_result.valid_records
            invalid_count = val_result.invalid_records

            print(f"\n{'=' * 40}")
            print(f" DATA VALIDATION SUMMARY")
            print(f"{'=' * 40}")
            print(f" Dataset          : {dataset_name}")
            print(f" Contract Version : {args.contract_version}")
            print(f" Batch ID         : {batch_id}")
            print(f" Total Records    : {val_result.total_records}")
            print(f" Valid Records    : {val_result.valid_records}")
            print(f" Invalid Records  : {val_result.invalid_records}")
            print(f" Status           : {val_result.status}")
            print(f"{'=' * 40}\n")
            
            if invalid_count > 0:
                print(f" -> {invalid_count} records were quarantined.")

        except Exception as exc:
            logger.error("Validation failed: %s", exc)
            print(f"VALIDATION FAILED: {exc}")
    else:
        print(f"[4/4] Validation skipped (no --contract-version provided)")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    duration = time.time() - start_time
    status = "SUCCESS" if db_success else "SUCCESS (raw file only - DB unavailable)"

    print(f"\n{'—' * 50}")
    print(f" INGESTION COMPLETED")
    print(f"{'—' * 50}")
    print(f" Batch ID       : {batch_id}")
    print(f" Source          : {args.source.upper()}")
    print(f" Dataset         : {dataset_name}")
    print(f" Records         : {len(df)}")
    print(f" Status          : {status}")
    print(f" Duration        : {duration:.2f}s")
    print(f" Raw File        : {raw_path}")
    if db_success:
        print(f" DB Table        : raw.transactions")
        print(f" Batch Metadata  : metadata.ingestion_batches")
    print(f"{'—' * 50}\n")

    logger.info("Pipeline completed | batch_id=%s records=%d status=%s duration=%.2fs",
                batch_id, len(df), status, duration)


if __name__ == "__main__":
    main()
