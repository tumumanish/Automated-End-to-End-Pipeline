"""
Module: eltl_plus_plus
Purpose:
    Enhanced ELTL++ pipeline with immutable raw zone, managed raw layer,
    semantic layer, and full observability.

Pattern:
    Extract -> Raw Load (Immutable) -> Managed Raw (Clean/Standardise)
       -> Transform -> Curated Semantic -> BI
"""

from typing import Dict, Any
import time

from src.utils.logger import get_logger
from src.utils.timestamps import utc_now
from src.ingestion.ingestion_factory import create_ingestion
from src.storage.raw_storage import save_raw_data
from src.storage.curated_storage import save_curated_data
from src.contracts.validation_service import ValidationService
from src.transformation.transformation_factory import TransformationService
from src.transformation.cleaning import DataCleaner
from src.lineage.lineage_tracker import LineageTracker
from src.lineage.lineage_store import LineageStore
from src.monitoring.quality_metrics import QualityMetricsCalculator
from src.monitoring.pipeline_metrics import PipelineMetricsTracker
from src.monitoring.monitoring_logger import MonitoringLogger
from src.storage.checkpoint_manager import CheckpointManager

logger = get_logger("pipeline.eltl_plus_plus")

_pipeline_metrics = PipelineMetricsTracker()
_monitoring_logger = MonitoringLogger()
_lineage_store = LineageStore()
_checkpoint_mgr = CheckpointManager()


class ELTLPlusPlusPipeline:
    """
    ELTL++ Pipeline: Extract → Raw Load → Managed Raw → Transform → Curated Semantic

    Key difference from ETLT++:
      - Data is loaded to raw BEFORE any validation
      - Validation happens in the "Managed Raw" stage
      - Focuses on immutability and raw preservation first
    """

    def execute(self, execution_id: str, source: str, dataset: str, contract_version: str, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        ingestion_time = utc_now()

        logger.info(f"ELTL++ Pipeline Execution Started | ID: {execution_id}")

        tracker = LineageTracker(
            batch_id=execution_id,
            pipeline_name="eltl_plus_plus",
            dataset_name=dataset,
            source_system=source,
            contract_version=contract_version,
        )

        # ──────────────────────────────────────────────
        # 1. EXTRACT
        # ──────────────────────────────────────────────
        logger.info(f"Step 1: Extracting from {source}...")
        adapter = create_ingestion(source, **kwargs)
        df_raw = adapter.extract()
        extracted_count = len(df_raw)

        tracker.record("extract", input_count=0, output_count=extracted_count, metadata={
            "source_type": source,
            "source_name": adapter.source_name,
        })

        # ──────────────────────────────────────────────
        # 2. RAW LOAD (Immutable — BEFORE validation)
        # ──────────────────────────────────────────────
        logger.info("Step 2: Loading to Immutable Raw Zone...")
        raw_path = save_raw_data(df_raw, source, dataset, execution_id)

        tracker.record("raw_load", input_count=extracted_count, output_count=extracted_count, metadata={
            "raw_path": str(raw_path),
            "note": "Immutable raw load — no validation applied yet",
        })
        _checkpoint_mgr.save(execution_id, "eltl_plus_plus", "raw_load", {
            "extracted_count": extracted_count,
            "raw_path": str(raw_path),
        })

        # ──────────────────────────────────────────────
        # 3. MANAGED RAW (Clean + Validate)
        # ──────────────────────────────────────────────
        logger.info("Step 3: Managed Raw — Cleaning and Validation...")

        # 3a. Minimal cleaning (whitespace, encoding)
        df_cleaned = DataCleaner.clean(df_raw)

        # 3b. Contract validation
        validator = ValidationService()
        df_valid, df_invalid, val_result = validator.run_validation(
            df=df_cleaned,
            dataset_name=dataset,
            contract_version=contract_version,
            batch_id=execution_id,
        )

        tracker.record("managed_raw", input_count=extracted_count, output_count=len(df_valid), metadata={
            "cleaned": True,
            "valid": len(df_valid),
            "invalid": len(df_invalid),
            "validation_status": val_result.status,
        })
        _checkpoint_mgr.save(execution_id, "eltl_plus_plus", "managed_raw", {
            "extracted_count": extracted_count,
            "valid_count": len(df_valid),
            "invalid_count": len(df_invalid),
        })

        # Quality metrics
        quality_calc = QualityMetricsCalculator()
        quality_metrics = quality_calc.calculate(
            batch_id=execution_id,
            dataset_name=dataset,
            source=source,
            df=df_raw,
            validation_result=val_result,
            ingestion_time=ingestion_time,
            duration=time.time() - start_time,
            pipeline_status="RUNNING",
        )

        if len(df_valid) == 0:
            logger.warning("No valid records in Managed Raw stage. Pipeline stopping.")
            quality_metrics.pipeline_status = "PARTIAL"
            _monitoring_logger.log_quality_metrics(quality_metrics)
            _lineage_store.save_events(tracker.get_events())

            duration = time.time() - start_time
            _pipeline_metrics.record_execution(
                pipeline_name="eltl_plus_plus",
                execution_id=execution_id,
                status="PARTIAL",
                started_at=ingestion_time.isoformat(),
                duration=duration,
                records_extracted=extracted_count,
                records_valid=0,
                records_invalid=extracted_count,
            )

            return {
                "extracted": extracted_count,
                "raw_path": str(raw_path),
                "validation_status": val_result.status,
                "valid_records": 0,
                "invalid_records": extracted_count,
                "curated_path": None,
                "transformed_records": 0,
            }

        # ──────────────────────────────────────────────
        # 4. TRANSFORMATION
        # ──────────────────────────────────────────────
        logger.info(f"Step 4: Transformation on {len(df_valid)} valid records...")
        df_transformed = TransformationService.transform(df_valid, dataset)
        transformed_count = len(df_transformed)

        tracker.record("transformation", input_count=len(df_valid), output_count=transformed_count, metadata={
            "transformations": ["cleaning", "normalization", "deduplication", "business_rules"],
        })
        _checkpoint_mgr.save(execution_id, "eltl_plus_plus", "transformation", {
            "transformed_count": transformed_count,
        })

        # ──────────────────────────────────────────────
        # 5. CURATED SEMANTIC LAYER
        # ──────────────────────────────────────────────
        logger.info("Step 5: Saving to Curated Semantic Layer...")
        curated_path = save_curated_data(df_transformed, dataset, execution_id)

        tracker.record("curated_semantic", input_count=transformed_count, output_count=transformed_count, metadata={
            "curated_path": str(curated_path) if curated_path else None,
        })

        # ──────────────────────────────────────────────
        # FINALISE
        # ──────────────────────────────────────────────
        duration = time.time() - start_time

        _lineage_store.save_events(tracker.get_events())

        quality_metrics.pipeline_status = "SUCCESS"
        quality_metrics.processing_duration_seconds = round(duration, 2)
        _monitoring_logger.log_quality_metrics(quality_metrics)

        pipeline_metric = _pipeline_metrics.record_execution(
            pipeline_name="eltl_plus_plus",
            execution_id=execution_id,
            status="SUCCESS",
            started_at=ingestion_time.isoformat(),
            duration=duration,
            records_extracted=extracted_count,
            records_valid=len(df_valid),
            records_invalid=len(df_invalid),
            records_transformed=transformed_count,
        )
        _monitoring_logger.log_pipeline_metrics(pipeline_metric)

        _checkpoint_mgr.cleanup("eltl_plus_plus", keep_last=10)

        logger.info(f"ELTL++ Pipeline Execution Completed | ID: {execution_id}")
        return {
            "extracted": extracted_count,
            "raw_path": str(raw_path),
            "validation_status": val_result.status,
            "valid_records": len(df_valid),
            "invalid_records": len(df_invalid),
            "transformed_records": transformed_count,
            "curated_path": str(curated_path) if curated_path else None,
            "quality_metrics": quality_metrics.to_dict(),
            "lineage_summary": tracker.get_lineage_summary(),
        }
