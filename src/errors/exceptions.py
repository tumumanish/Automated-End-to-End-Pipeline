"""
Module: exceptions
Purpose:
    Custom exception classes for the data pipeline.
"""


class PipelineError(Exception):
    """Base exception for all pipeline errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


class IngestionError(PipelineError):
    """Raised when data extraction/ingestion fails."""
    pass


class StorageError(PipelineError):
    """Raised when data storage (file or database) operations fail."""
    pass


class DatabaseConnectionError(StorageError):
    """Raised when a database connection cannot be established."""
    pass


class ValidationError(PipelineError):
    """Raised when data fails contract or schema validation."""
    pass


class ContractError(PipelineError):
    """Raised when a data contract cannot be loaded or parsed."""
    pass


class TransformationError(PipelineError):
    """Raised when a data transformation step fails."""
    pass


class QuarantineError(PipelineError):
    """Raised when quarantine operations fail."""
    pass


class ConfigurationError(PipelineError):
    """Raised when required configuration is missing or invalid."""
    pass


class ContractNotFoundError(PipelineError):
    """Raised when a requested data contract cannot be found."""
    pass


class ContractValidationError(PipelineError):
    """Raised when a data contract JSON itself is malformed or invalid."""
    pass


class SchemaValidationError(PipelineError):
    """Raised when a dataset fails structural schema validation (e.g. missing columns)."""
    pass


class DataValidationError(PipelineError):
    """Raised when a dataset contains row-level data validation errors."""
    pass
