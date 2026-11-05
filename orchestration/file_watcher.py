"""
Module: file_watcher
Purpose:
    Event-driven automation using Watchdog to detect new incoming data files
    in data/raw/ directories and automatically trigger the ETLT++ pipeline.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from watchdog.observers import Observer

from src.utils.logger import get_logger, setup_logging
from src.pipelines.pipeline_runner import PipelineRunner

setup_logging()
logger = get_logger("orchestration.file_watcher")


class NewDataFileHandler(FileSystemEventHandler):
    """Watches for new CSV and Excel files and triggers the pipeline."""

    def __init__(self):
        super().__init__()
        self._runner = PipelineRunner()
        self._processed_files = set()

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix.lower() not in (".csv", ".xlsx"):
            return

        # Skip files that are inside temporary or quarantine directories
        path_str = str(file_path).replace("\\", "/")
        if "quarantine" in path_str or "archive" in path_str:
            return

        if file_path.name in self._processed_files:
            return

        # Wait briefly for file write to complete
        time.sleep(1)

        source_type = "csv" if file_path.suffix.lower() == ".csv" else "excel"
        logger.info("New data file detected: %s (Source: %s). Auto-triggering pipeline...", file_path, source_type)

        try:
            self._processed_files.add(file_path.name)
            result = self._runner.run(
                pipeline_name="etlt_plus_plus",
                source=source_type,
                dataset="transactions",
                contract_version="1.0",
                file_path=str(file_path),
            )
            logger.info(
                "Auto-triggered pipeline execution %s completed with status %s in %.2fs",
                result.get("execution_id"),
                result.get("status"),
                result.get("duration_seconds", 0.0),
            )
        except Exception as exc:
            logger.error("Error auto-processing file %s: %s", file_path, exc, exc_info=True)


def start_file_watcher(watch_dir: Path | None = None) -> None:
    """Start watching the data directory for incoming files."""
    if watch_dir is None:
        watch_dir = PROJECT_ROOT / "data" / "raw"

    watch_dir.mkdir(parents=True, exist_ok=True)
    event_handler = NewDataFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=str(watch_dir), recursive=True)

    logger.info("File watcher started on directory: %s", watch_dir)
    logger.info("Drop any CSV or Excel transaction file into data/raw/ to trigger auto-processing.")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_file_watcher()
