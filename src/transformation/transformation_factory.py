import pandas as pd
from src.utils.logger import get_logger
from src.transformation.cleaning import DataCleaner
from src.transformation.normalization import DataNormalizer
from src.transformation.deduplication import Deduplicator
from src.transformation.business_rules import BusinessRuleEngine
from src.transformation.enrichment import DataEnricher
from src.transformation.type_conversion import TypeConverter

logger = get_logger("transformation.service")

# Default type specifications per dataset for type enforcement
_DATASET_TYPE_SPECS = {
    "transactions": {
        "transaction_id": "string",
        "customer_id": "string",
        "product_id": "string",
        "transaction_date": "date",
        "quantity": "integer",
        "unit_price": "number",
        "total_amount": "number",
        "location": "string",
    },
}


class TransformationService:
    """Orchestrates the T2 Business Transformation steps."""
    
    @staticmethod
    def transform(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """
        Executes the full T2 transformation pipeline on valid data.

        Steps:
            1. Clean — strip whitespace, normalise null sentinels
            2. Normalize — format standardisation (casing, dates)
            3. Deduplicate — remove duplicate records by business key
            4. Business Rules — derive calculated fields, flag anomalies
            5. Enrich — add computed analytical columns
            6. Type Conversion — enforce pandas dtypes per contract spec
        """
        logger.info(f"Starting T2 transformations for dataset: {dataset_name}")
        
        # 1. Clean (Structural strings)
        df_clean = DataCleaner.clean(df)
        
        # 2. Normalize (Format standardization)
        df_norm = DataNormalizer.normalize(df_clean, dataset_name)
        
        # 3. Deduplicate (Business keys)
        df_dedup = Deduplicator.deduplicate(df_norm, dataset_name)
        
        # 4. Apply Business Rules (Derivations, enrichments)
        df_rules = BusinessRuleEngine.apply_rules(df_dedup, dataset_name)

        # 5. Enrich (Derived analytical columns)
        df_enriched = DataEnricher.add_computed_fields(df_rules, dataset_name)

        # 6. Type Conversion (Enforce pandas dtypes)
        type_spec = _DATASET_TYPE_SPECS.get(dataset_name, {})
        if type_spec:
            df_final = TypeConverter.convert(df_enriched, type_spec)
        else:
            df_final = TypeConverter.infer_and_convert(df_enriched)
        
        logger.info(f"Completed T2 transformations. Final record count: {len(df_final)}")
        return df_final
