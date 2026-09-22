from typing import Dict, Type, Any
from src.utils.logger import get_logger

logger = get_logger("pipeline_registry")

class PipelineRegistry:
    """Registry to map pipeline names to their implementation classes dynamically."""
    
    _registry: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, name: str, pipeline_class: Type[Any]) -> None:
        """Register a pipeline class under a specific name."""
        cls._registry[name] = pipeline_class
        logger.debug(f"Registered pipeline '{name}' -> {pipeline_class.__name__}")

    @classmethod
    def get_pipeline(cls, name: str) -> Type[Any]:
        """Retrieve a pipeline class by name."""
        if name not in cls._registry:
            raise ValueError(f"Pipeline '{name}' not found in registry. Available: {list(cls._registry.keys())}")
        return cls._registry[name]

# Standard registration
from src.pipelines.etlt_plus_plus import ETLTPlusPlusPipeline

PipelineRegistry.register("etlt_plus_plus", ETLTPlusPlusPipeline)
