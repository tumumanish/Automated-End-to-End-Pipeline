import pandas as pd
from src.utils.logger import get_logger

logger = get_logger("transformation.normalization")

class DataNormalizer:
    """T2 Component: Standardizes and normalizes data values."""
    
    @staticmethod
    def normalize(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        logger.debug(f"Starting data normalization for dataset {dataset_name}...")
        df_norm = df.copy()
        
        # Dataset-specific normalization rules
        if dataset_name == "transactions":
            if "location" in df_norm.columns:
                df_norm["location"] = df_norm["location"].str.title()
                
            if "transaction_id" in df_norm.columns:
                df_norm["transaction_id"] = df_norm["transaction_id"].str.upper()
                
            if "transaction_date" in df_norm.columns:
                # Ensure it's a valid pandas datetime object
                df_norm["transaction_date"] = pd.to_datetime(df_norm["transaction_date"], errors="coerce")

        logger.debug("Data normalization complete.")
        return df_norm
