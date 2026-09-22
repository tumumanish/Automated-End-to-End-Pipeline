import pandas as pd
from src.utils.logger import get_logger

logger = get_logger("transformation.deduplication")

class Deduplicator:
    """T2 Component: Removes duplicate records based on business keys."""
    
    @staticmethod
    def deduplicate(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        logger.debug(f"Starting deduplication for dataset {dataset_name}...")
        df_dedup = df.copy()
        
        initial_count = len(df_dedup)
        
        if dataset_name == "transactions":
            # Assume transaction_id is the primary business key
            if "transaction_id" in df_dedup.columns:
                # Sort by date descending (if we want to keep the latest in case of collisions)
                if "transaction_date" in df_dedup.columns:
                    df_dedup = df_dedup.sort_values("transaction_date", ascending=False)
                
                df_dedup = df_dedup.drop_duplicates(subset=["transaction_id"], keep="first")
        else:
            # Generic absolute row deduplication
            df_dedup = df_dedup.drop_duplicates()
            
        dropped = initial_count - len(df_dedup)
        if dropped > 0:
            logger.info(f"Deduplication removed {dropped} duplicate records.")
            
        return df_dedup
