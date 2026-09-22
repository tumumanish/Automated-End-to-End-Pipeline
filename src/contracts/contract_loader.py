"""
Module: contract_loader
Purpose:
    Load, parse, and strictly validate the JSON contract files against 
    the expected meta-structure before returning them for validation.
"""

import json
from pathlib import Path
from typing import Any

from src.errors.exceptions import ContractNotFoundError, ContractValidationError
from src.utils.logger import get_logger

logger = get_logger("validation")


class ContractLoader:
    """Loads and verifies structural integrity of data contracts."""

    @staticmethod
    def load(file_path: Path) -> dict[str, Any]:
        """
        Read and parse a JSON contract file.

        Args:
            file_path: Path to the JSON contract.

        Raises:
            ContractNotFoundError: If the file does not exist.
            ContractValidationError: If the JSON is invalid or missing required meta-fields.

        Returns:
            The parsed contract as a dictionary.
        """
        if not file_path.exists():
            raise ContractNotFoundError(
                f"Contract file not found: {file_path}",
                details={"path": str(file_path)}
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                contract = json.load(f)
        except json.JSONDecodeError as exc:
            raise ContractValidationError(
                f"Failed to parse contract JSON: {file_path} - {exc}",
                details={"path": str(file_path)}
            ) from exc

        ContractLoader._verify_meta_structure(contract, file_path)
        
        logger.debug("Loaded contract '%s' (v%s) from %s", 
                     contract.get("dataset"), contract.get("version"), file_path)
        return contract

    @staticmethod
    def _verify_meta_structure(contract: dict[str, Any], path: Path) -> None:
        """Validate that the contract itself is structurally usable."""
        required_keys = {"dataset", "version", "fields"}
        missing = required_keys - set(contract.keys())
        
        if missing:
            raise ContractValidationError(
                f"Contract missing required meta-fields {missing}",
                details={"path": str(path), "missing": list(missing)}
            )
            
        if not isinstance(contract["fields"], dict):
            raise ContractValidationError(
                "Contract 'fields' must be an object (dict).",
                details={"path": str(path)}
            )
