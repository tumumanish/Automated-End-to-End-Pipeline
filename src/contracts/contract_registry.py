"""
Module: contract_registry
Purpose:
    Resolves and retrieves data contracts dynamically from the file system 
    by dataset name and version.
"""

from pathlib import Path
from typing import Any

from src.contracts.contract_loader import ContractLoader
from src.errors.exceptions import ContractNotFoundError
from src.utils.file_utils import get_project_root


class ContractRegistry:
    """Registry to locate data contracts without hardcoding paths."""

    def __init__(self, contracts_dir: Path | None = None):
        """
        Initialize the registry.
        
        Args:
            contracts_dir: Optional override for the contracts root directory.
        """
        self._root = contracts_dir or (get_project_root() / "contracts")
        self._loader = ContractLoader()
        
        # Cache of loaded contracts: (dataset, version) -> dict
        self._cache: dict[tuple[str, str], dict[str, Any]] = {}

    def get_contract(self, dataset: str, version: str) -> dict[str, Any]:
        """
        Locate and load a data contract by dataset name and version.

        Args:
            dataset: The logical dataset name (e.g., 'transactions').
            version: The contract version (e.g., '1.0'). "latest" is not currently supported.

        Raises:
            ContractNotFoundError: If the requested contract cannot be found.
            ContractValidationError: If the contract is structurally invalid.

        Returns:
            The loaded contract dictionary.
        """
        cache_key = (dataset, version)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Map semantic version (e.g., "1.0") to folder (e.g., "v1")
        major_version = version.split(".")[0]
        v_folder = f"v{major_version}"
        
        # Expected pattern: contracts/versions/v1/transaction_contract.json
        # Stripping trailing 's' if dataset is plural to match standard filename practices
        # (e.g. transactions -> transaction_contract.json)
        base_name = dataset[:-1] if dataset.endswith('s') else dataset
        filename = f"{base_name}_contract.json"
        
        contract_path = self._root / "versions" / v_folder / filename
        
        # Fallback to schemas directory if exact version structure is missing
        if not contract_path.exists():
            contract_path = self._root / "schemas" / filename
            
        if not contract_path.exists():
            raise ContractNotFoundError(
                f"Contract not found for dataset '{dataset}' version '{version}'.",
                details={
                    "dataset": dataset,
                    "version": version,
                    "searched_paths": [
                        str(self._root / "versions" / v_folder / filename),
                        str(self._root / "schemas" / filename)
                    ]
                }
            )

        contract = self._loader.load(contract_path)
        self._cache[cache_key] = contract
        return contract
