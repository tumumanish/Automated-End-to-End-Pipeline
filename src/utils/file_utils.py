"""
Module: file_utils
Purpose:
    File I/O utilities — path construction, file discovery, directory management.
"""

from pathlib import Path


# Project root — resolved relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return PROJECT_ROOT


def ensure_directory(path: Path) -> Path:
    """
    Create a directory (and parents) if it does not exist.

    Args:
        path: Directory path to create.

    Returns:
        The resolved path.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_raw_path(
    source_type: str,
    dataset_name: str,
    batch_id: str,
    extension: str = ".csv",
) -> Path:
    """
    Build the raw data storage path for a batch.

    Pattern: data/raw/<source_type>/<dataset_name>/<batch_id><extension>

    Args:
        source_type: Source category (api, csv, excel, database).
        dataset_name: Logical dataset name.
        batch_id: Unique batch identifier.
        extension: File extension (default: .csv).

    Returns:
        Absolute path where the raw data file should be stored.
    """
    raw_dir = PROJECT_ROOT / "data" / "raw" / source_type / dataset_name
    ensure_directory(raw_dir)
    return raw_dir / f"{batch_id}{extension}"


def file_exists(path: Path) -> bool:
    """Check if a file exists and is a file (not directory)."""
    return path.is_file()
