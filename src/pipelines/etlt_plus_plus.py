from typing import Dict, Any
from src.utils.logger import get_logger
from src.ingestion.ingestion_factory import create_ingestion
from src.storage.raw_storage import save_raw_data
from src.storage.curated_storage import save_curated_data
from src.contracts.validation_service import ValidationService
from src.transformation.transformation_factory import TransformationService
from src.lineage.lineage_tracker import LineageTracker
from src.lineage.lineage_store import LineageStore
from src.lineage.metadata_collector import MetadataCollector
from src.monitoring.quality_metrics import QualityMetricsCalculator
from src.monitoring.pipeline_metrics import PipelineMetricsTracker
from src.monitoring.alert_manager import AlertManager
from src.monitoring.monitoring_logger import MonitoringLogger
from src.storage.checkpoint_manager import CheckpointManager
from src.utils.timestamps import utc_now

logger = get_logger("pipeline.etlt_plus_plus")

# Shared instances for cross-execution tracking
_pipeline_metrics = PipelineMetricsTracker()
_alert_manager = AlertManager()
_monitoring_logger = MonitoringLogger()
_lineage_store = LineageStore()
_checkpoint_mgr = CheckpointManager()

class ETLTPlusPlusPipeline:
    """
    Phase 4+ ETLT++ Implementation with full observability:
    Extract -> Raw Storage -> T1 Validation (Contracts) -> T2 Transformation (Business) -> Curated Storage

    Cross-cutting:
      - Lineage tracking at every stage
      - Quality metrics collection after validation
      - Alert evaluation after metrics
      - Checkpoint saving after each stage
      - Pipeline metrics recording on completion
    """
    
    def execute(self, execution_id: str, source: str, dataset: str, contract_version: str, **kwargs) -> Dict[str, Any]:
        import time
        start_time = time.time()
        ingestion_time = utc_now()

        logger.info(f"ETLT++ Pipeline Execution Started | ID: {execution_id}")
        
        # Initialise lineage tracker for this execution
        tracker = LineageTracker(
            batch_id=execution_id,
            pipeline_name="etlt_plus_plus",
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
        _checkpoint_mgr.save(execution_id, "etlt_plus_plus", "extract", {
            "extracted_count": extracted_count,
        })

        # ──────────────────────────────────────────────
        # 2. RAW STORAGE (Immutable)
        # ──────────────────────────────────────────────
        logger.info("Step 2: Saving to Raw Storage...")
        raw_path = save_raw_data(df_raw, source, dataset, execution_id)

        tracker.record("raw_storage", input_count=extracted_count, output_count=extracted_count, metadata={
            "raw_path": str(raw_path),
        })
        _checkpoint_mgr.save(execution_id, "etlt_plus_plus", "raw_storage", {
            "extracted_count": extracted_count,
            "raw_path": str(raw_path),
        })

        # ──────────────────────────────────────────────
        # 3. T1 - SCHEMA/CONTRACT VALIDATION
        # ──────────────────────────────────────────────
        logger.info(f"Step 3: T1 Validation (Contract {contract_version})...")
        validator = ValidationService()
        df_valid, df_invalid, val_result = validator.run_validation(
            df=df_raw,
            dataset_name=dataset,
            contract_version=contract_version,
            batch_id=execution_id
        )

        tracker.record("contract_validation", input_count=extracted_count, output_count=len(df_valid), metadata={
            "valid": len(df_valid),
            "invalid": len(df_invalid),
            "status": val_result.status,
        })
        _checkpoint_mgr.save(execution_id, "etlt_plus_plus", "contract_validation", {
            "extracted_count": extracted_count,
            "valid_count": len(df_valid),
            "invalid_count": len(df_invalid),
            "raw_path": str(raw_path),
        })

        # ── Quality metrics & alerts ──
        quality_calc = QualityMetricsCalculator()
        duration_so_far = time.time() - start_time
        quality_metrics = quality_calc.calculate(
            batch_id=execution_id,
            dataset_name=dataset,
            source=source,
            df=df_raw,
            validation_result=val_result,
            ingestion_time=ingestion_time,
            duration=duration_so_far,
            pipeline_status="RUNNING",
        )
        alerts = _alert_manager.evaluate(quality_metrics)

        if len(df_valid) == 0:
            logger.warning("No valid records passed T1 Validation. Terminating pipeline execution early.")
            quality_metrics.pipeline_status = "PARTIAL"
            _monitoring_logger.log_quality_metrics(quality_metrics)
            _lineage_store.save_events(tracker.get_events())

            duration = time.time() - start_time
            _pipeline_metrics.record_execution(
                pipeline_name="etlt_plus_plus",
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
                "quality_metrics": quality_metrics.to_dict(),
            }
            
        # ──────────────────────────────────────────────
        # 4. T2 - BUSINESS TRANSFORMATION
        # ──────────────────────────────────────────────
        logger.info(f"Step 4: T2 Transformation on {len(df_valid)} valid records...")
        df_transformed = TransformationService.transform(df_valid, dataset)
        transformed_count = len(df_transformed)

        tracker.record("business_transformation", input_count=len(df_valid), output_count=transformed_count, metadata={
            "transformations": ["cleaning", "normalization", "deduplication", "business_rules"],
        })
        _checkpoint_mgr.save(execution_id, "etlt_plus_plus", "business_transformation", {
            "extracted_count": extracted_count,
            "valid_count": len(df_valid),
            "transformed_count": transformed_count,
            "raw_path": str(raw_path),
        })

        # ──────────────────────────────────────────────
        # 5. CURATED STORAGE
        # ──────────────────────────────────────────────
        logger.info("Step 5: Saving to Curated Storage...")
        curated_path = save_curated_data(df_transformed, dataset, execution_id)

        tracker.record("curated_storage", input_count=transformed_count, output_count=transformed_count, metadata={
            "curated_path": str(curated_path) if curated_path else None,
            "format": "parquet",
        })

        # ──────────────────────────────────────────────
        # FINALISE: Lineage, Metrics, Alerts
        # ──────────────────────────────────────────────
        duration = time.time() - start_time

        # Save lineage
        _lineage_store.save_events(tracker.get_events())

        # Update quality metrics with final status
        quality_metrics.pipeline_status = "SUCCESS"
        quality_metrics.processing_duration_seconds = round(duration, 2)
        _monitoring_logger.log_quality_metrics(quality_metrics)

        # Record pipeline execution
        pipeline_metric = _pipeline_metrics.record_execution(
            pipeline_name="etlt_plus_plus",
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

        # Cleanup old checkpoints
        _checkpoint_mgr.cleanup("etlt_plus_plus", keep_last=10)

        logger.info(f"ETLT++ Pipeline Execution Completed | ID: {execution_id}")
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
