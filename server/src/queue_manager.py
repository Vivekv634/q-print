import json
import logging
import threading
from pathlib import Path
from typing import Any

from server.src import database as db
from server.utils.constants import PRINT_QUEUE_FILE_PATH

logger = logging.getLogger(__name__)


class QueueManager:
    def __init__(
        self,
        queue_file_path: str,
        file_storage_path: str,
    ) -> None:
        self.queue_file_path = queue_file_path
        self._lock = threading.Lock()
        db.init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _mirror_queue(self) -> None:
        """Write print_queue.json so QFileSystemWatcher in AdminWindow still fires."""
        try:
            queue = db.get_all_jobs()
            path = Path(self.queue_file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.queue_file_path, "w") as f:
                json.dump(queue, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to mirror print_queue.json: {e}")

    # ------------------------------------------------------------------
    # Public API (called by AdminWindow / JobDetailDialog)
    # ------------------------------------------------------------------

    def add_job(self, user_data: dict[str, Any]) -> None:
        with self._lock:
            db.insert_job(user_data)
            db.reassign_positions()
            self._mirror_queue()
            logger.info(f"Job queued: {user_data.get('_id')} ({user_data.get('name', '')})")

    def remove_job(self, user_id: str) -> None:
        """User-initiated delete: record as dropped, remove from queue and delete uploaded files."""
        from datetime import datetime
        with self._lock:
            job = db.get_job(user_id)
            if job:
                now = datetime.now()
                db.insert_analytics_event(
                    event_type="dropped",
                    job_id=user_id,
                    files_count=len(job.get("filedataArray", [])),
                    pages_color=sum(
                        fd.get("page_count", 0) * fd.get("no_of_copies", 1)
                        for fd in job.get("filedataArray", [])
                        if isinstance(fd, dict) and fd.get("color_mode") == "color"
                    ),
                    pages_bw=sum(
                        fd.get("page_count", 0) * fd.get("no_of_copies", 1)
                        for fd in job.get("filedataArray", [])
                        if isinstance(fd, dict) and fd.get("color_mode") != "color"
                    ),
                    revenue=0.0,
                    hour=now.hour,
                    date=now.strftime("%Y-%m-%d"),
                )
                db.delete_job_files(job)
            db.delete_job(user_id)
            db.reassign_positions()
            self._mirror_queue()
            logger.info(f"Job removed: {user_id}")


    def complete_job(
        self,
        user_id: str,
        revenue: float = 0.0,
        event_type: str = "completed",
    ) -> None:
        """Admin action (print done / cancel): record analytics, delete files, remove from queue."""
        from datetime import datetime
        with self._lock:
            job = db.get_job(user_id)
            if job:
                now = datetime.now()
                db.insert_analytics_event(
                    event_type=event_type,
                    job_id=user_id,
                    files_count=len(job.get("filedataArray", [])),
                    pages_color=sum(
                        fd.get("page_count", 0) * fd.get("no_of_copies", 1)
                        for fd in job.get("filedataArray", [])
                        if isinstance(fd, dict) and fd.get("color_mode") == "color"
                    ),
                    pages_bw=sum(
                        fd.get("page_count", 0) * fd.get("no_of_copies", 1)
                        for fd in job.get("filedataArray", [])
                        if isinstance(fd, dict) and fd.get("color_mode") != "color"
                    ),
                    revenue=revenue,
                    hour=now.hour,
                    date=now.strftime("%Y-%m-%d"),
                )
                db.delete_job_files(job)
            if event_type == "dropped":
                db.insert_rejection(user_id)
            db.delete_job(user_id)
            db.reassign_positions()
            self._mirror_queue()
            logger.info(f"Job completed ({event_type}): {user_id}")

    def get_queue(self) -> list[dict[str, Any]]:
        with self._lock:
            return db.get_all_jobs()
