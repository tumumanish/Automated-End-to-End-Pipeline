"""
Service: pipeline_service
Purpose:
    Business logic layer for pipeline-related API operations.
"""

import sys
from pathlib import Path
from typing import List, Optional

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipelines.pipeline_runner import PipelineRunner
from src.pipelines.pipeline_registry import PipelineRegistry


class PipelineService:
    """Wraps PipelineRunner and PipelineRegistry for API consumption."""

    def __init__(self):
        self._runner = PipelineRunner()

    def list_pipelines(self) -> List[dict]:
        """List all registered pipelines."""
        pipelines = PipelineRegistry.list_pipelines()
        return [
            {"name": name, "class_name": cls_name, "enabled": True}
            for name, cls_name in pipelines.items()
        ]

    def get_pipeline(self, name: str) -> Optional[dict]:
        """Get details of a specific pipeline."""
        if not PipelineRegistry.is_registered(name):
            return None
        pipelines = PipelineRegistry.list_pipelines()
        return {
            "name": name,
            "class_name": pipelines[name],
            "enabled": True,
        }

    def run_pipeline(
        self,
        pipeline_name: str,
        source: str,
        dataset: str,
        contract_version: str,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
    ) -> dict:
        """
        Execute a pipeline and return the result.

        Args:
            pipeline_name: Name of the pipeline to execute.
            source: Source type (csv, excel, api, database).
            dataset: Dataset name.
            contract_version: Contract version.
            file_path: File path (for csv/excel sources).
            url: URL (for api source).

        Returns:
            Execution result dictionary.
        """
        kwargs = {}
        if file_path:
            kwargs["file_path"] = file_path
        if url:
            kwargs["url"] = url

        return self._runner.run(
            pipeline_name=pipeline_name,
            source=source,
            dataset=dataset,
            contract_version=contract_version,
            **kwargs,
        )
