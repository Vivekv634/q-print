import sys
import logging
from threading import Thread
from subprocess import Popen

from ip_config import load_shop_config, is_setup_required, register_mdns
from server.logs.app_logs import configureAppLogger
from port_killer import free_port
from server.utils.constants import (
    PORT,
    PRINT_QUEUE_FILE_PATH,
    FILE_STORAGE_PATH,
    DISCOVERED_PEERS_PATH,
    SHOP_CONFIG_PATH,
    PYTHON_API_PORT,
)
from server.src.queue_manager import QueueManager
from server.src.api_server import start as start_api_server
from server.src.analytics_sync import run_sync
from server.src.peer_discovery import PeerDiscovery

from PySide6.QtWidgets import QApplication, QDialog
from server.ui.main_window import AdminWindow

logger = logging.getLogger(__name__)


def start_web_app() -> None:
    Popen(["npm", "run", "dev"], cwd="client")


def wait_for_api(port: int, timeout: float = 15.0) -> None:
    """Block until the Python API is accepting connections.

    Polls GET /health every 100ms. Raises RuntimeError if timeout exceeded.
    """
    import time
    import urllib.request
    import urllib.error

    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"Python API did not start within {timeout}s")


def shutdown_api(port: int) -> None:
    """Ask the Python API to drain writes and stop cleanly."""
    import urllib.request
    import urllib.error
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                f"http://127.0.0.1:{port}/shutdown",
                method="POST",
            ),
            timeout=10,
        )
    except Exception:
        pass  # server may already be down


if __name__ == "__main__":
    configureAppLogger()
    free_port(PORT)

    app = QApplication(sys.argv)

    shop_config = load_shop_config()
    if is_setup_required(shop_config):
        from server.ui.widgets.setup_dialog import SetupDialog

        dialog = SetupDialog(SHOP_CONFIG_PATH)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        shop_config = load_shop_config()

    zeroconf, own_hostname, service_info = register_mdns(shop_config)
    peer_discovery = PeerDiscovery(own_hostname, DISCOVERED_PEERS_PATH, zeroconf)

    queue_manager = QueueManager(
        queue_file_path=PRINT_QUEUE_FILE_PATH,
        file_storage_path=FILE_STORAGE_PATH,
    )

    api_thread = Thread(target=start_api_server, daemon=True)
    api_thread.start()

    wait_for_api(PYTHON_API_PORT)
    run_sync()

    client_thread = Thread(target=start_web_app, daemon=True)
    client_thread.start()

    window = AdminWindow(
        queue_manager,
        zeroconf=zeroconf,
        service_info=service_info,
        peer_discovery=peer_discovery,
    )
    window.show()
    exit_code = app.exec()
    zeroconf.unregister_all_services()
    zeroconf.close()
    shutdown_api(PYTHON_API_PORT)
    sys.exit(exit_code)
