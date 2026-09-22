import pandas as pd
from src.utils.logger import get_logger

logger = get_logger("transformation.business_rules")

class BusinessRuleEngine:
    """T2 Component: Applies dataset-specific business logic, derivations, and enrichments."""
    
    @staticmethod
    def apply_rules(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        logger.debug(f"Applying business rules for dataset {dataset_name}...")
        df_biz = df.copy()
        
        if dataset_name == "transactions":
            # Rule 1: Calculate net_amount if not present or override it
            if "quantity" in df_biz.columns and "unit_price" in df_biz.columns:
                # Assuming valid types from T1 validation
                df_biz["calculated_total"] = df_biz["quantity"] * df_biz["unit_price"]
                
            # Rule 2: Flag high-value transactions
            if "total_amount" in df_biz.columns:
                df_biz["is_high_value"] = df_biz["total_amount"] >= 1000.0
                
            # Rule 3: Flag missing locations (which might be allowed by contract, but business wants them flagged)
            if "location" in df_biz.columns:
                df_biz["needs_location_review"] = df_biz["location"].isna()

        logger.debug("Business rules applied.")
        return df_biz
