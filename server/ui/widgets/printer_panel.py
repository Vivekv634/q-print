import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QFrame,
)
from PySide6.QtCore import Qt, QTimer
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


class PrinterPanel(QWidget):
    def __init__(
        self,
        printer_manager: PrinterManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.printer_manager: PrinterManager = printer_manager
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
        self.printer_list.clear()
        printers: list[str] = self.printer_manager.get_printers()
        if not printers:
            item: QListWidgetItem = QListWidgetItem("No printers detected")
            item.setForeground(QColor("#95a5a6"))
            self.printer_list.addItem(item)
            return

        for name in printers:
            info: dict = self.printer_manager.get_printer_status(name)
            status: str = info.get("status", "Unknown")
            jobs: int = info.get("jobs", 0)
            text: str = f"{name}  —  {status}  ({jobs} job(s) in queue)"
            item = QListWidgetItem(text)
            color: str = STATUS_COLORS.get(status, "#555555")
            item.setForeground(QColor(color))
            self.printer_list.addItem(item)
