"""
Module: eltl_pipeline
Purpose:
    Basic ELTL (Extract-Load-Transform-Load) pipeline.

Pattern:
    Extract → Load (Raw Immutable) → Transform → Load (Curated)

    A simplified version of ELTL++ without lineage or monitoring hooks.
    Key difference from ETLT: data is loaded to raw BEFORE any validation.
"""

from typing import Dict, Any
import time

from src.utils.logger import get_logger
from src.ingestion.ingestion_factory import create_ingestion
from src.storage.raw_storage import save_raw_data
from src.storage.curated_storage import save_curated_data
from src.contracts.validation_service import ValidationService
from src.transformation.transformation_factory import TransformationService
from src.transformation.cleaning import DataCleaner

logger = get_logger("pipeline.eltl")


class ELTLPipeline:
    """
    Basic ELTL Pipeline (without ++ enhancements):
    Extract → Raw Load (immutable) → Validate+Transform → Curated Store
    """

    def execute(self, execution_id: str, source: str, dataset: str, contract_version: str, **kwargs) -> Dict[str, Any]:
        start_time = time.time()

        logger.info(f"ELTL Pipeline Started | ID: {execution_id}")

        # 1. Extract
        adapter = create_ingestion(source, **kwargs)
        df_raw = adapter.extract()
        extracted_count = len(df_raw)
        logger.info(f"Extracted {extracted_count} records from {source}")

        # 2. Load to raw (BEFORE validation — immutable copy)
        raw_path = save_raw_data(df_raw, source, dataset, execution_id)
        logger.info(f"Raw data saved -> {raw_path}")

        # 3. Clean + Validate
        df_cleaned = DataCleaner.clean(df_raw)
        validator = ValidationService()
        df_valid, df_invalid, val_result = validator.run_validation(
            df=df_cleaned,
            dataset_name=dataset,
            contract_version=contract_version,
            batch_id=execution_id,
        )

        if len(df_valid) == 0:
            logger.warning("No valid records after validation. Pipeline stopping.")
            return {
                "extracted": extracted_count,
                "raw_path": str(raw_path),
                "validation_status": val_result.status,
                "valid_records": 0,
                "invalid_records": len(df_invalid),
                "curated_path": None,
                "transformed_records": 0,
            }

        # 4. Transform
        df_transformed = TransformationService.transform(df_valid, dataset)

        # 5. Load to curated
        curated_path = save_curated_data(df_transformed, dataset, execution_id)

        duration = time.time() - start_time
        logger.info(f"ELTL Pipeline Completed | ID: {execution_id} | duration={duration:.2f}s")

        return {
            "extracted": extracted_count,
            "raw_path": str(raw_path),
            "validation_status": val_result.status,
            "valid_records": len(df_valid),
            "invalid_records": len(df_invalid),
            "transformed_records": len(df_transformed),
            "curated_path": str(curated_path) if curated_path else None,
        }
