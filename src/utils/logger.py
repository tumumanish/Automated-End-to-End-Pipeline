"""
Module: logger
Purpose:
    Centralized logging setup using config/logging.yaml.
    Provides named loggers for each subsystem.
"""

import logging
import logging.config
from pathlib import Path

import yaml

# Project root — resolved relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _ensure_log_directories() -> None:
    """Create log directories if they do not exist."""
    log_dirs = [
        PROJECT_ROOT / "logs" / "pipeline",
        PROJECT_ROOT / "logs" / "validation",
        PROJECT_ROOT / "logs" / "lineage",
        PROJECT_ROOT / "logs" / "errors",
    ]
    for d in log_dirs:
        d.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Load logging configuration from config/logging.yaml."""
    _ensure_log_directories()

    config_path = PROJECT_ROOT / "config" / "logging.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Resolve log file paths relative to project root
        for handler in config.get("handlers", {}).values():
            if "filename" in handler:
                handler["filename"] = str(PROJECT_ROOT / handler["filename"])

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    Args:
        name: Logger name (e.g., 'pipeline', 'validation', 'lineage', 'errors').

    Returns:
        Configured logging.Logger instance.
    """
    return logging.getLogger(name)
