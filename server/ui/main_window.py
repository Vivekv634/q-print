import json
import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QAction

from server.src.queue_manager import QueueManager
from server.src.printer_manager import PrinterManager
from server.utils.constants import (
    PRINT_QUEUE_FILE_PATH,
    COST_FILE_PATH,
    FILE_STORAGE_PATH,
    DISCOVERED_PEERS_PATH,
    SHOP_CONFIG_PATH,
    ASSETS_PATH,
    PORT,
)
from server.utils.wifi_utils import get_ssid
from server.ui import keybindings
from server.ui.widgets.queue_panel import QueuePanel
from server.ui.widgets.printer_panel import PrinterPanel
from server.ui.widgets.job_detail_dialog import JobDetailDialog
from server.ui.widgets.cost_settings_dialog import CostSettingsDialog
from server.ui.widgets.qr_dialog import QRDialog

if TYPE_CHECKING:
    from zeroconf import ServiceInfo, Zeroconf
    from server.src.peer_discovery import PeerDiscovery

logger = logging.getLogger(__name__)


def _load_hostname() -> str:
    try:
        with open(SHOP_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f).get("mdns_hostname", "qprint-shop")
    except Exception:
        return "qprint-shop"


class AdminWindow(QMainWindow):
    # Emitted from the mDNS re-registration daemon thread to update the main thread
    _mdns_success = Signal(str)   # new_hostname
    _mdns_error   = Signal(str)   # error message

    def __init__(
        self,
        queue_manager: QueueManager,
        zeroconf: "Zeroconf | None" = None,
        service_info: "ServiceInfo | None" = None,
        peer_discovery: "PeerDiscovery | None" = None,
        parent: QMainWindow | None = None,
    ) -> None:
        super().__init__(parent)
        self.queue_manager: QueueManager = queue_manager
        self.printer_manager: PrinterManager = PrinterManager()
        self._zc = zeroconf
        self._service_info = service_info
        self._peer_discovery = peer_discovery
        self._mdns_success.connect(self._on_reregister_success)
        self._mdns_error.connect(self._on_reregister_error)
        self.setWindowTitle("Q-Print Admin")
        self.setMinimumSize(1280, 720)
        self._build_menu()
        self._build_central()
        self._build_status_bar()

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        # File
        file_menu = menu_bar.addMenu("File")
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(keybindings.QUIT)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Settings
        settings_menu = menu_bar.addMenu("Settings")
        cost_action = QAction("Edit Print Cost…", self)
        cost_action.setShortcut(keybindings.EDIT_COST)
        cost_action.triggered.connect(self._open_cost_settings)
        settings_menu.addAction(cost_action)

        shop_action = QAction("Edit Name && Hostname…", self)
        shop_action.triggered.connect(self._open_edit_shop)
        settings_menu.addAction(shop_action)

        # Network
        network_menu = menu_bar.addMenu("Network")
        qr_action = QAction("Show QR Code…", self)
        qr_action.setShortcut(keybindings.SHOW_QR_CODE)
        qr_action.triggered.connect(self._open_qr_dialog)
        network_menu.addAction(qr_action)

        nearby_action = QAction("Find Shops Nearby…", self)
        nearby_action.setShortcut(keybindings.FIND_NEARBY_SHOPS)
        nearby_action.triggered.connect(self._open_nearby_shops)
        network_menu.addAction(nearby_action)

    def _build_central(self) -> None:
        splitter: QSplitter = QSplitter(Qt.Orientation.Horizontal)

        self.queue_panel: QueuePanel = QueuePanel(
            queue_manager=self.queue_manager,
            printer_manager=self.printer_manager,
            queue_file_path=PRINT_QUEUE_FILE_PATH,
            cost_file_path=COST_FILE_PATH,
            file_storage_path=FILE_STORAGE_PATH,
        )
        self.queue_panel.job_selected.connect(self._open_job_detail)

        self.printer_panel: PrinterPanel = PrinterPanel(printer_manager=self.printer_manager)

        splitter.addWidget(self.queue_panel)
        splitter.addWidget(self.printer_panel)
        splitter.setSizes([800, 480])

        self.setCentralWidget(splitter)

    def _build_status_bar(self) -> None:
        self.status_bar: QStatusBar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Q-Print Admin ready.")

        self._wifi_label: QLabel = QLabel()
        self._wifi_label.setStyleSheet("padding: 0 8px; color: #ccc;")
        self.status_bar.addPermanentWidget(self._wifi_label)
        self._update_wifi_label()

        self._wifi_timer: QTimer = QTimer(self)
        self._wifi_timer.setInterval(30_000)
        self._wifi_timer.timeout.connect(self._update_wifi_label)
        self._wifi_timer.start()

    def _update_wifi_label(self) -> None:
        self._wifi_label.setText(f"📶 {get_ssid()}")

    # ── Menu handlers ──────────────────────────────────────────────────────────

    def _open_qr_dialog(self) -> None:
        hostname = _load_hostname()
        dialog = QRDialog(
            hostname=hostname,
            port=PORT,
            assets_path=ASSETS_PATH,
            parent=self,
        )
        dialog.exec()

    def _open_nearby_shops(self) -> None:
        from server.ui.widgets.nearby_shops_dialog import NearbyShopsDialog
        dialog = NearbyShopsDialog(peers_file_path=DISCOVERED_PEERS_PATH, parent=self)
        dialog.exec()

    def _open_job_detail(self, job: dict) -> None:
        dialog: JobDetailDialog = JobDetailDialog(
            job=job,
            queue_manager=self.queue_manager,
            printer_manager=self.printer_manager,
            file_storage_path=FILE_STORAGE_PATH,
            cost_file_path=COST_FILE_PATH,
            parent=self,
        )
        dialog.exec()
        self.queue_panel.refresh()

    def _open_edit_shop(self) -> None:
        from server.ui.widgets.edit_shop_dialog import EditShopDialog
        dialog = EditShopDialog(config_path=SHOP_CONFIG_PATH, parent=self)
        dialog.config_saved.connect(self._on_config_saved)
        dialog.exec()

    def _on_config_saved(self, new_config: dict) -> None:
        if not self._zc or not self._service_info:
            return
        # mDNS network I/O must NOT run on the Qt main thread — use a daemon thread.
        self.status_bar.showMessage("Re-registering mDNS hostname…")
        import threading
        threading.Thread(
            target=self._reregister_mdns_thread,
            args=(new_config,),
            daemon=True,
        ).start()

    def _reregister_mdns_thread(self, new_config: dict) -> None:
        from ip_config import reregister_mdns
        try:
            new_info, new_hostname = reregister_mdns(
                self._zc, self._service_info, new_config
            )
            self._service_info = new_info
            if self._peer_discovery:
                self._peer_discovery.update_own_hostname(new_hostname)
            # Signal delivers to main thread via QueuedConnection automatically
            self._mdns_success.emit(new_hostname)
        except Exception as exc:
            logger.error("mDNS re-registration failed: %s", exc)
            self._mdns_error.emit(str(exc))

    @Slot(str)
    def _on_reregister_success(self, new_hostname: str) -> None:
        self.status_bar.showMessage("mDNS hostname updated.", 5000)
        QMessageBox.information(
            self,
            "Hostname Updated",
            f"mDNS re-registered successfully.\n\n"
            f"New URL:  http://{new_hostname}.local:{PORT}\n\n"
            "Share this URL with your customers — anyone on the old URL will "
            "need to use the new one.",
        )

    @Slot(str)
    def _on_reregister_error(self, error_msg: str) -> None:
        self.status_bar.showMessage("mDNS re-registration failed.", 5000)
        QMessageBox.warning(
            self,
            "mDNS Error",
            f"Config saved but mDNS re-registration failed:\n{error_msg}\n\n"
            "Restart the app to apply the new hostname.",
        )

    def _open_cost_settings(self) -> None:
        dialog: CostSettingsDialog = CostSettingsDialog(
            cost_file_path=COST_FILE_PATH, parent=self
        )
        dialog.exec()
