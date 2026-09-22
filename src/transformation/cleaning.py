import pandas as pd
from src.utils.logger import get_logger

logger = get_logger("transformation.cleaning")

class DataCleaner:
    """T2 Component: Cleans data by stripping whitespace and handling basic structural anomalies."""
    
    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Starting data cleaning...")
        df_clean = df.copy()
        
        # 1. Strip whitespace from string columns
        str_cols = df_clean.select_dtypes(include=['object', 'string']).columns
        for col in str_cols:
            df_clean[col] = df_clean[col].astype(str).str.strip()
            
            # Convert literal 'nan' or empty strings back to real NaN
            df_clean.loc[df_clean[col].isin(['', 'nan', 'None', 'null']), col] = None

        logger.debug("Data cleaning complete.")
        return df_clean
