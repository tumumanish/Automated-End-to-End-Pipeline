import os
from pathlib import Path
import pandas as pd
from src.utils.logger import get_logger
from src.utils.file_utils import get_project_root

logger = get_logger("curated_storage")

def save_curated_data(df: pd.DataFrame, dataset_name: str, batch_id: str) -> Path:
    """
    Saves the T2 transformed data to the curated storage zone.
    Format: parquet (preferred for analytics/staging) or csv.
    """
    if df.empty:
        logger.warning(f"No curated data to save for batch {batch_id}.")
        return None
        
    root = get_project_root()
    # Path: data/curated/<dataset_name>/<batch_id>.parquet
    out_dir = root / "data" / "curated" / dataset_name
    out_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = out_dir / f"{batch_id}.parquet"
    
    try:
        # Save as parquet for analytics readiness
        df.to_parquet(file_path, index=False)
        logger.info(f"Curated data saved to {file_path}")
    except ImportError:
        # Fallback to CSV if pyarrow/fastparquet is not installed
        file_path = out_dir / f"{batch_id}.csv"
        df.to_csv(file_path, index=False)
        logger.info(f"Curated data saved to {file_path} (fallback CSV)")
        
    return file_path
