import logging

from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QStatusBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from server.src.queue_manager import QueueManager
from server.src.printer_manager import PrinterManager
from server.utils.constants import (
    PRINT_QUEUE_FILE_PATH,
    COST_FILE_PATH,
    FILE_STORAGE_PATH,
)
from server.ui.widgets.queue_panel import QueuePanel
from server.ui.widgets.printer_panel import PrinterPanel
from server.ui.widgets.job_detail_dialog import JobDetailDialog
from server.ui.widgets.cost_settings_dialog import CostSettingsDialog

logger = logging.getLogger(__name__)


class AdminWindow(QMainWindow):
    def __init__(self, queue_manager: QueueManager, parent: QMainWindow | None = None) -> None:
        super().__init__(parent)
        self.queue_manager: QueueManager = queue_manager
        self.printer_manager: PrinterManager = PrinterManager()
        self.setWindowTitle("Q-Print Admin")
        self.setMinimumSize(1000, 600)
        self._build_menu()
        self._build_central()
        self._build_status_bar()

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        settings_menu = menu_bar.addMenu("Settings")
        cost_action = QAction("Edit Print Cost…", self)
        cost_action.triggered.connect(self._open_cost_settings)
        settings_menu.addAction(cost_action)

    def _build_central(self) -> None:
        splitter: QSplitter = QSplitter(Qt.Orientation.Horizontal)

        self.queue_panel: QueuePanel = QueuePanel(
            queue_manager=self.queue_manager,
            queue_file_path=PRINT_QUEUE_FILE_PATH,
            cost_file_path=COST_FILE_PATH,
        )
        self.queue_panel.job_selected.connect(self._open_job_detail)

        self.printer_panel: PrinterPanel = PrinterPanel(printer_manager=self.printer_manager)

        splitter.addWidget(self.queue_panel)
        splitter.addWidget(self.printer_panel)
        splitter.setSizes([650, 350])

        self.setCentralWidget(splitter)

    def _build_status_bar(self) -> None:
        self.status_bar: QStatusBar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Q-Print Admin ready.")

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

    def _open_cost_settings(self) -> None:
        dialog: CostSettingsDialog = CostSettingsDialog(
            cost_file_path=COST_FILE_PATH, parent=self
        )
        dialog.exec()
