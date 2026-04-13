import os
import json
import time
import logging
import threading
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import (
    DirCreatedEvent,
    FileCreatedEvent,
    FileSystemEventHandler,
    FileModifiedEvent,
    DirModifiedEvent,
    DirDeletedEvent,
    FileDeletedEvent,
)
from server.utils.constants import DATA_FOLDER_PATH, USER_RECORD_FILE_PATH
from server.src.queue_manager import QueueManager

logger = logging.getLogger(__name__)


class Handler(FileSystemEventHandler):
    def __init__(self, path: str, queue_manager: QueueManager) -> None:
        super().__init__()
        self.path: str = path
        self.queue_manager: QueueManager = queue_manager
        self._previous_records: dict[str, dict] = {}
        # Watchdog can fire on_modified from multiple threads concurrently;
        # this lock serializes diff-and-update to prevent double-processing.
        self._records_lock = threading.Lock()
        self._load_initial_state()

    def _load_initial_state(self) -> None:
        try:
            if Path(USER_RECORD_FILE_PATH).is_file():
                with open(USER_RECORD_FILE_PATH, "r") as f:
                    content: str = f.read().strip()
                    self._previous_records = json.loads(content) if content else {}
        except (json.JSONDecodeError, FileNotFoundError):
            self._previous_records = {}
        logger.info(f"Observer initialized with {len(self._previous_records)} existing record(s).")

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        logger.debug(f"on_created: {event}")
        return super().on_created(event)

    def on_modified(self, event: FileModifiedEvent | DirModifiedEvent) -> None:
        if not event.is_directory:
            if os.path.normpath(event.src_path) == os.path.normpath(USER_RECORD_FILE_PATH):
                self._handle_user_records_change()
        return super().on_modified(event)

    def _handle_user_records_change(self) -> None:
        with self._records_lock:
            try:
                with open(USER_RECORD_FILE_PATH, "r") as f:
                    content: str = f.read().strip()
                    current_records: dict[str, dict] = json.loads(content) if content else {}
            except (json.JSONDecodeError, FileNotFoundError):
                return

            for user_id, user_data in current_records.items():
                if user_id not in self._previous_records:
                    logger.info(f"New record detected: {user_id}")
                    self.queue_manager.add_job(user_data)

            for user_id in list(self._previous_records.keys()):
                if user_id not in current_records:
                    logger.info(f"Record removed: {user_id}")
                    self.queue_manager.remove_job(user_id)

            self._previous_records = current_records

    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        logger.debug(f"on_deleted: {event}")
        if not event.is_directory:
            if os.path.normpath(event.src_path) == os.path.normpath(USER_RECORD_FILE_PATH):
                try:
                    with open(USER_RECORD_FILE_PATH, "x") as f:
                        f.write("{}")
                except FileExistsError:
                    pass  # another event already recreated the file
        return super().on_deleted(event)


class FileObserver:
    def __init__(self, path: str, queue_manager: QueueManager) -> None:
        self.path: str = path
        self.queue_manager: QueueManager = queue_manager

    def startObserving(self) -> None:
        logger.info("START observing client/data/ ...")
        observer: Observer = Observer()
        handler: Handler = Handler(self.path, self.queue_manager)
        observer.schedule(handler, path=self.path, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("STOP observing.")
            observer.stop()
        observer.join()


if __name__ == "__main__":
    from server.src.queue_manager import QueueManager
    from server.utils.constants import PRINT_QUEUE_FILE_PATH, USER_RECORD_FILE_PATH, FILE_STORAGE_PATH
    qm = QueueManager(PRINT_QUEUE_FILE_PATH, USER_RECORD_FILE_PATH, FILE_STORAGE_PATH)
    fo = FileObserver(DATA_FOLDER_PATH, qm)
    fo.startObserving()
