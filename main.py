import sys
import logging
from threading import Thread
from subprocess import Popen

from ip_config import register_mdns
from server.logs.app_logs import configureAppLogger
from port_killer import free_port
from server.utils.constants import (
    PORT, DATA_FOLDER_PATH,
    PRINT_QUEUE_FILE_PATH, USER_RECORD_FILE_PATH, FILE_STORAGE_PATH,
)
from server.src.queue_manager import QueueManager
from server.src.observer import FileObserver

from PySide6.QtWidgets import QApplication
from server.ui.main_window import AdminWindow

logger = logging.getLogger(__name__)


def start_web_app():
    Popen(["npm", "run", "dev"], cwd="client")


if __name__ == "__main__":
    configureAppLogger()
    free_port(PORT)
    zeroconf = register_mdns()

    queue_manager = QueueManager(
        queue_file_path=PRINT_QUEUE_FILE_PATH,
        user_record_file_path=USER_RECORD_FILE_PATH,
        file_storage_path=FILE_STORAGE_PATH,
    )

    client_thread = Thread(target=start_web_app, daemon=True)
    client_thread.start()

    observer = FileObserver(DATA_FOLDER_PATH, queue_manager)
    observer_thread = Thread(target=observer.startObserving, daemon=True)
    observer_thread.start()

    app = QApplication(sys.argv)
    window = AdminWindow(queue_manager)
    window.show()
    exit_code = app.exec()
    zeroconf.unregister_all_services()
    zeroconf.close()
    sys.exit(exit_code)
