import time
import uuid
from typing import Dict, Any
from src.utils.logger import get_logger
from src.pipelines.pipeline_registry import PipelineRegistry

logger = get_logger("pipeline_runner")

class PipelineRunner:
    """Unified engine to run any registered pipeline."""
    
    @staticmethod
    def generate_execution_id() -> str:
        return f"exec_{uuid.uuid4().hex[:12]}"

    def run(self, pipeline_name: str, **kwargs) -> Dict[str, Any]:
        """
        Executes a pipeline by name with the given kwargs.
        Returns a structured dictionary with execution results.
        """
        execution_id = self.generate_execution_id()
        start_time = time.time()
        
        logger.info(f"Starting pipeline '{pipeline_name}' | exec_id={execution_id}")
        
        try:
            # 1. Resolve pipeline class
            pipeline_class = PipelineRegistry.get_pipeline(pipeline_name)
            
            # 2. Instantiate pipeline
            pipeline_instance = pipeline_class()
            
            # 3. Execute
            # Pass the execution_id down to the pipeline so it can use it as batch_id
            kwargs["execution_id"] = execution_id
            result = pipeline_instance.execute(**kwargs)
            
            duration = time.time() - start_time
            logger.info(f"Pipeline '{pipeline_name}' completed successfully | exec_id={execution_id} | duration={duration:.2f}s")
            
            return {
                "pipeline": pipeline_name,
                "execution_id": execution_id,
                "status": "SUCCESS",
                "duration_seconds": round(duration, 2),
                "details": result
            }
            
        except Exception as exc:
            duration = time.time() - start_time
            logger.error(f"Pipeline '{pipeline_name}' FAILED | exec_id={execution_id} | error={exc}", exc_info=True)
            
            return {
                "pipeline": pipeline_name,
                "execution_id": execution_id,
                "status": "FAILED",
                "duration_seconds": round(duration, 2),
                "error": str(exc),
                "details": {}
            }
