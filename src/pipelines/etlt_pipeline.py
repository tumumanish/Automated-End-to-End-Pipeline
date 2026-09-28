"""
Module: etlt_pipeline
Purpose:
    Basic ETLT (Extract-Transform-Load-Transform) pipeline.

Pattern:
    Extract → T1 (Clean/Validate) → Load (Raw) → T2 (Business) → Curated
    
    A simplified version of ETLT++ without lineage or monitoring hooks.
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

logger = get_logger("pipeline.etlt")


class ETLTPipeline:
    """
    Basic ETLT Pipeline (without ++ enhancements):
    Extract → Validate → Raw Store → Transform → Curated Store
    """

    def execute(self, execution_id: str, source: str, dataset: str, contract_version: str, **kwargs) -> Dict[str, Any]:
        start_time = time.time()

        logger.info(f"ETLT Pipeline Started | ID: {execution_id}")

        # 1. Extract
        adapter = create_ingestion(source, **kwargs)
        df_raw = adapter.extract()
        extracted_count = len(df_raw)
        logger.info(f"Extracted {extracted_count} records from {source}")

        # 2. T1 — Validate
        validator = ValidationService()
        df_valid, df_invalid, val_result = validator.run_validation(
            df=df_raw,
            dataset_name=dataset,
            contract_version=contract_version,
            batch_id=execution_id,
        )

        # 3. Load to raw
        raw_path = save_raw_data(df_raw, source, dataset, execution_id)

        if len(df_valid) == 0:
            logger.warning("No valid records. Pipeline stopping.")
            return {
                "extracted": extracted_count,
                "raw_path": str(raw_path),
                "validation_status": val_result.status,
                "valid_records": 0,
                "invalid_records": len(df_invalid),
                "curated_path": None,
                "transformed_records": 0,
            }

        # 4. T2 — Transform
        df_transformed = TransformationService.transform(df_valid, dataset)

        # 5. Store curated
        curated_path = save_curated_data(df_transformed, dataset, execution_id)

        duration = time.time() - start_time
        logger.info(f"ETLT Pipeline Completed | ID: {execution_id} | duration={duration:.2f}s")

        return {
            "extracted": extracted_count,
            "raw_path": str(raw_path),
            "validation_status": val_result.status,
            "valid_records": len(df_valid),
            "invalid_records": len(df_invalid),
            "transformed_records": len(df_transformed),
            "curated_path": str(curated_path) if curated_path else None,
        }
