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
)
from server.src.queue_manager import QueueManager
from server.src.api_server import start as start_api_server
from server.src.peer_discovery import PeerDiscovery

from PySide6.QtWidgets import QApplication, QDialog
from server.ui.main_window import AdminWindow

logger = logging.getLogger(__name__)


def start_web_app() -> None:
    Popen(["npm", "run", "dev"], cwd="client")


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

    zeroconf, own_hostname = register_mdns(shop_config)
    PeerDiscovery(own_hostname, DISCOVERED_PEERS_PATH, zeroconf)

    queue_manager = QueueManager(
        queue_file_path=PRINT_QUEUE_FILE_PATH,
        file_storage_path=FILE_STORAGE_PATH,
    )

    client_thread = Thread(target=start_web_app, daemon=True)
    client_thread.start()

    api_thread = Thread(target=start_api_server, daemon=True)
    api_thread.start()

    window = AdminWindow(queue_manager)
    window.show()
    exit_code = app.exec()
    zeroconf.unregister_all_services()
    zeroconf.close()
    sys.exit(exit_code)
