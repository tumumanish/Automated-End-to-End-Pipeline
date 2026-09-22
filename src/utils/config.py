"""
Module: config
Purpose:
    Load application configuration from YAML files and environment variables.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env file if it exists
_env_path = PROJECT_ROOT / ".env"
load_dotenv(_env_path)


def load_yaml(file_path: Path) -> dict:
    """
    Load a YAML configuration file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Parsed YAML as a dictionary.
    """
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_settings() -> dict:
    """Load config/settings.yaml."""
    return load_yaml(PROJECT_ROOT / "config" / "settings.yaml")


def get_env(key: str, default: Any = None) -> Any:
    """
    Get an environment variable with an optional default.

    Args:
        key: Environment variable name.
        default: Fallback value if not set.

    Returns:
        The environment variable value or default.
    """
    return os.getenv(key, default)


def get_postgres_config() -> dict:
    """
    Build PostgreSQL connection configuration from environment variables.

    Returns:
        Dictionary with host, port, database, user, password.
    """
    return {
        "host": get_env("POSTGRES_HOST", "localhost"),
        "port": int(get_env("POSTGRES_PORT", "5432")),
        "database": get_env("POSTGRES_DB", "pipeline_warehouse"),
        "user": get_env("POSTGRES_USER", "pipeline_user"),
        "password": get_env("POSTGRES_PASSWORD", "pipeline_password"),
    }


def get_connection_string() -> str:
    """
    Build a SQLAlchemy-compatible PostgreSQL connection string.

    Returns:
        Connection string in the format: postgresql+psycopg2://user:pass@host:port/db
    """
    cfg = get_postgres_config()
    return (
        f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )
