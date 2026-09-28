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

    @classmethod
    def list_pipelines(cls) -> Dict[str, str]:
        """List all registered pipelines with their class names."""
        return {name: klass.__name__ for name, klass in cls._registry.items()}

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a pipeline is registered."""
        return name in cls._registry


# ── Standard registrations ──
from src.pipelines.etlt_plus_plus import ETLTPlusPlusPipeline
from src.pipelines.eltl_plus_plus import ELTLPlusPlusPipeline
from src.pipelines.etlt_pipeline import ETLTPipeline
from src.pipelines.eltl_pipeline import ELTLPipeline

PipelineRegistry.register("etlt_plus_plus", ETLTPlusPlusPipeline)
PipelineRegistry.register("eltl_plus_plus", ELTLPlusPlusPipeline)
PipelineRegistry.register("etlt", ETLTPipeline)
PipelineRegistry.register("eltl", ELTLPipeline)
