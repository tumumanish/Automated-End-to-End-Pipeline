import pandas as pd
from src.utils.logger import get_logger
from src.transformation.cleaning import DataCleaner
from src.transformation.normalization import DataNormalizer
from src.transformation.deduplication import Deduplicator
from src.transformation.business_rules import BusinessRuleEngine

logger = get_logger("transformation.service")

class TransformationService:
    """Orchestrates the T2 Business Transformation steps."""
    
    @staticmethod
    def transform(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """
        Executes the full T2 transformation pipeline on valid data.
        """
        logger.info(f"Starting T2 transformations for dataset: {dataset_name}")
        
        # 1. Clean (Structural strings)
        df_clean = DataCleaner.clean(df)
        
        # 2. Normalize (Format standardization)
        df_norm = DataNormalizer.normalize(df_clean, dataset_name)
        
        # 3. Deduplicate (Business keys)
        df_dedup = Deduplicator.deduplicate(df_norm, dataset_name)
        
        # 4. Apply Business Rules (Derivations, enrichments)
        df_final = BusinessRuleEngine.apply_rules(df_dedup, dataset_name)
        
        logger.info(f"Completed T2 transformations. Final record count: {len(df_final)}")
        return df_final
