from typing import Dict, Any
from src.utils.logger import get_logger
from src.ingestion.ingestion_factory import create_ingestion
from src.storage.raw_storage import save_raw_data
from src.storage.curated_storage import save_curated_data
from src.contracts.validation_service import ValidationService
from src.transformation.transformation_factory import TransformationService

logger = get_logger("pipeline.etlt_plus_plus")

class ETLTPlusPlusPipeline:
    """
    Phase 4 ETLT++ Implementation:
    Extract -> Raw Storage -> T1 Validation (Contracts) -> T2 Transformation (Business) -> Curated Storage
    """
    
    def execute(self, execution_id: str, source: str, dataset: str, contract_version: str, **kwargs) -> Dict[str, Any]:
        logger.info(f"ETLT++ Pipeline Execution Started | ID: {execution_id}")
        
        # 1. EXTRACT
        logger.info(f"Step 1: Extracting from {source}...")
        adapter = create_ingestion(source, **kwargs)
        df_raw = adapter.extract()
        extracted_count = len(df_raw)
        
        # 2. RAW STORAGE (Immutable)
        logger.info("Step 2: Saving to Raw Storage...")
        raw_path = save_raw_data(df_raw, source, dataset, execution_id)
        
        # 3. T1 - SCHEMA/CONTRACT VALIDATION
        logger.info(f"Step 3: T1 Validation (Contract {contract_version})...")
        validator = ValidationService()
        df_valid, df_invalid, val_result = validator.run_validation(
            df=df_raw,
            dataset_name=dataset,
            contract_version=contract_version,
            batch_id=execution_id
        )
        
        if len(df_valid) == 0:
            logger.warning("No valid records passed T1 Validation. Terminating pipeline execution early.")
            return {
                "extracted": extracted_count,
                "raw_path": str(raw_path),
                "validation_status": val_result.status,
                "valid_records": 0,
                "invalid_records": extracted_count,
                "curated_path": None,
                "transformed_records": 0
            }
            
        # 4. T2 - BUSINESS TRANSFORMATION
        logger.info(f"Step 4: T2 Transformation on {len(df_valid)} valid records...")
        df_transformed = TransformationService.transform(df_valid, dataset)
        transformed_count = len(df_transformed)
        
        # 5. CURATED STORAGE
        logger.info("Step 5: Saving to Curated Storage...")
        curated_path = save_curated_data(df_transformed, dataset, execution_id)
        
        logger.info(f"ETLT++ Pipeline Execution Completed | ID: {execution_id}")
        return {
            "extracted": extracted_count,
            "raw_path": str(raw_path),
            "validation_status": val_result.status,
            "valid_records": len(df_valid),
            "invalid_records": len(df_invalid),
            "transformed_records": transformed_count,
            "curated_path": str(curated_path) if curated_path else None
        }
