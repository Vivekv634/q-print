import logging
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QFrame,
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QColor

from server.src.printer_manager import PrinterManager

logger = logging.getLogger(__name__)

STATUS_COLORS: dict[str, str] = {
    "Ready":       "#2ecc71",
    "Printing":    "#f39c12",
    "Busy":        "#f39c12",
    "Offline":     "#e74c3c",
    "Error":       "#e74c3c",
    "Unavailable": "#95a5a6",
}


class _PrinterWorker(QObject):
    """Fetches printer list + statuses off the main thread."""
    finished = Signal(list)  # list[dict[str, Any]]

    def __init__(self, printer_manager: PrinterManager) -> None:
        super().__init__()
        self._pm = printer_manager

    def run(self) -> None:
        results: list[dict[str, Any]] = []
        try:
            for name in self._pm.get_printers():
                info = self._pm.get_printer_status(name)
                results.append(info)
        except Exception as exc:
            logger.error("PrinterWorker error: %s", exc)
        self.finished.emit(results)


class PrinterPanel(QWidget):
    def __init__(
        self,
        printer_manager: PrinterManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.printer_manager: PrinterManager = printer_manager
        self._fetch_thread: QThread | None = None
        self._build_ui()
        self._start_polling()

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header_row: QHBoxLayout = QHBoxLayout()
        title: QLabel = QLabel("Printers")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn: QPushButton = QPushButton("Refresh")
        refresh_btn.setFixedWidth(80)
        refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        sep: QFrame = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        self.printer_list: QListWidget = QListWidget()
        self.printer_list.setAlternatingRowColors(True)
        layout.addWidget(self.printer_list)

        self.status_label: QLabel = QLabel("Auto-refreshing every 10s")
        self.status_label.setStyleSheet("color: grey; font-size: 11px;")
        layout.addWidget(self.status_label)

    def _start_polling(self) -> None:
        self.timer: QTimer = QTimer(self)
        self.timer.setInterval(10_000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
        # Avoid stacking fetches if a previous one is still running
        if self._fetch_thread is not None and self._fetch_thread.isRunning():
            return

        self.status_label.setText("Refreshing…")
        thread = QThread(self)
        worker = _PrinterWorker(self.printer_manager)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_printer_data)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._fetch_thread = thread
        thread.start()

    def _on_printer_data(self, results: list[dict[str, Any]]) -> None:
        # Keep the shared cache up-to-date so QuickPrintMenu can read it without I/O.
        self.printer_manager.update_status_cache(results)

        self.printer_list.clear()
        if not results:
            item: QListWidgetItem = QListWidgetItem("No printers detected")
            item.setForeground(QColor("#95a5a6"))
            self.printer_list.addItem(item)
            self.status_label.setText("Auto-refreshing every 10s")
            return

        for info in results:
            name: str = info.get("name", "Unknown")
            status: str = info.get("status", "Unknown")
            jobs: int = info.get("jobs", 0)
            text: str = f"{name}  —  {status}  ({jobs} job(s) in queue)"
            item = QListWidgetItem(text)
            color: str = STATUS_COLORS.get(status, "#555555")
            item.setForeground(QColor(color))
            self.printer_list.addItem(item)
        self.status_label.setText("Auto-refreshing every 10s")
