import json
import os
import threading
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class QueueManager:
    def __init__(
        self,
        queue_file_path: str,
        user_record_file_path: str,
        file_storage_path: str,
    ) -> None:
        self.queue_file_path: str = queue_file_path
        self.user_record_file_path: str = user_record_file_path
        self.file_storage_path: str = file_storage_path
        self._lock: threading.Lock = threading.Lock()
        self._ensure_queue_file()

    def _ensure_queue_file(self) -> None:
        path: Path = Path(self.queue_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            self._write_queue([])

    def _read_queue(self) -> list[dict[str, Any]]:
        try:
            with open(self.queue_file_path, "r") as f:
                content: str = f.read().strip()
                data: Any = json.loads(content) if content else []
                if not isinstance(data, list):
                    logger.error("print_queue.json root is not a list — resetting to empty queue.")
                    return []
                # Discard any corrupted entries that are not dicts
                return [item for item in data if isinstance(item, dict)]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_queue(self, queue: list[dict[str, Any]]) -> None:
        with open(self.queue_file_path, "w") as f:
            json.dump(queue, f, indent=2)

    def _reassign_positions(self, queue: list[dict[str, Any]]) -> None:
        for i, job in enumerate(queue, 1):
            job["position"] = i

    def _delete_job_files(self, job: dict[str, Any]) -> None:
        if not os.path.exists(self.file_storage_path):
            return
        for filedata in job.get("filedataArray", []):
            if not isinstance(filedata, dict):
                continue
            file_id: str = filedata.get("_file_id", "")
            file_name: str = filedata.get("file_name", "")
            if not file_id or not file_name:
                continue
            try:
                for stored_file in os.listdir(self.file_storage_path):
                    if file_id in stored_file and file_name in stored_file:
                        file_path: str = os.path.join(self.file_storage_path, stored_file)
                        os.remove(file_path)
                        logger.info(f"Deleted file: {file_path}")
            except OSError as e:
                logger.error(f"Failed to delete files for job {job.get('_id', '')}: {e}")

    def _remove_user_record(self, user_id: str) -> None:
        try:
            with open(self.user_record_file_path, "r") as f:
                records: dict[str, Any] = json.load(f)
            if user_id in records:
                del records[user_id]
                with open(self.user_record_file_path, "w") as f:
                    json.dump(records, f, indent=2)
                logger.info(f"Removed user record: {user_id}")
        except Exception as e:
            logger.error(f"Failed to remove user record {user_id}: {e}")

    def add_job(self, user_data: dict[str, Any]) -> None:
        with self._lock:
            queue: list[dict[str, Any]] = self._read_queue()
            if any(job.get("_id") == user_data.get("_id") for job in queue):
                return
            queue.append(user_data)
            queue.sort(key=lambda x: x.get("timestamp", 0))
            self._reassign_positions(queue)
            self._write_queue(queue)
            logger.info(f"Job queued: {user_data.get('_id')} ({user_data.get('name', '')})")

    def remove_job(self, user_id: str) -> None:
        """Remove from queue and delete files (user-initiated delete)."""
        with self._lock:
            queue: list[dict[str, Any]] = self._read_queue()
            job: dict[str, Any] | None = next((j for j in queue if j.get("_id") == user_id), None)
            if job:
                self._delete_job_files(job)
            new_queue: list[dict[str, Any]] = [j for j in queue if j.get("_id") != user_id]
            if len(new_queue) < len(queue):
                self._reassign_positions(new_queue)
                self._write_queue(new_queue)
                logger.info(f"Job removed from queue: {user_id}")

    def complete_job(self, user_id: str) -> None:
        """Delete files, remove from queue and user_records (admin: done/cancel)."""
        with self._lock:
            queue: list[dict[str, Any]] = self._read_queue()
            job: dict[str, Any] | None = next((j for j in queue if j.get("_id") == user_id), None)
            if job:
                self._delete_job_files(job)
            new_queue: list[dict[str, Any]] = [j for j in queue if j.get("_id") != user_id]
            self._reassign_positions(new_queue)
            self._write_queue(new_queue)
            self._remove_user_record(user_id)
            logger.info(f"Job finalized: {user_id}")

    def get_queue(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._read_queue()
