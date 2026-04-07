import json
import logging
from datetime import datetime
from typing import Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QFrame, QWidget, QMessageBox, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from server.src.queue_manager import QueueManager
from server.src.printer_manager import PrinterManager

logger = logging.getLogger(__name__)


class JobDetailDialog(QDialog):
    def __init__(
        self,
        job: dict[str, Any],
        queue_manager: QueueManager,
        printer_manager: PrinterManager,
        file_storage_path: str,
        cost_file_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.job: dict[str, Any] = job
        self.queue_manager: QueueManager = queue_manager
        self.printer_manager: PrinterManager = printer_manager
        self.file_storage_path: str = file_storage_path
        self.cost_file_path: str = cost_file_path
        self.cost: dict[str, float] = self._load_cost()
        self.setWindowTitle(f"Job Details — {job.get('name', '')}")
        self.setMinimumSize(640, 480)
        self._build_ui()

    def _load_cost(self) -> dict[str, float]:
        try:
            with open(self.cost_file_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"bw_per_page": 1.5, "color_per_page": 5.0}

    def _calculate_total(self) -> float:
        total: float = 0.0
        for fd in self.job.get("filedataArray", []):
            if not isinstance(fd, dict):
                continue
            pages: int = int(fd.get("page_count", 1))
            copies: int = int(fd.get("no_of_copies", 1))
            rate: float = (
                float(self.cost.get("color_per_page", 5.0))
                if fd.get("color_mode") == "color"
                else float(self.cost.get("bw_per_page", 1.5))
            )
            total += pages * copies * rate
        return total

    def _build_ui(self) -> None:
        main_layout: QVBoxLayout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        ts: int = self.job.get("timestamp", 0)
        dt_str: str = (
            datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"
        )

        header: QLabel = QLabel(
            f"<b>{self.job.get('name', 'Unknown')}</b> &nbsp;·&nbsp; "
            f"Position #{self.job.get('position', '?')} &nbsp;·&nbsp; {dt_str}"
        )
        header.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(header)

        id_label: QLabel = QLabel(f"<small>ID: {self.job.get('_id', '')}</small>")
        id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        main_layout.addWidget(id_label)

        sep: QFrame = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(sep)

        # Files table
        files: list[dict[str, Any]] = self.job.get("filedataArray", [])
        table: QTableWidget = QTableWidget(len(files), 7)
        table.setHorizontalHeaderLabels(
            ["File", "Pages", "Copies", "Mode", "Layout", "Paper", "Cost"]
        )
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)

        for row, fd in enumerate(files):
            if not isinstance(fd, dict):
                continue
            pages: int = int(fd.get("page_count", 1))
            copies: int = int(fd.get("no_of_copies", 1))
            rate: float = (
                float(self.cost.get("color_per_page", 5.0))
                if fd.get("color_mode") == "color"
                else float(self.cost.get("bw_per_page", 1.5))
            )
            file_cost: float = pages * copies * rate

            table.setItem(row, 0, QTableWidgetItem(str(fd.get("file_name", ""))))
            table.setItem(row, 1, QTableWidgetItem(str(pages)))
            table.setItem(row, 2, QTableWidgetItem(str(copies)))
            table.setItem(row, 3, QTableWidgetItem(str(fd.get("color_mode", "")).replace("_", " ")))
            table.setItem(row, 4, QTableWidgetItem(str(fd.get("layout", ""))))
            table.setItem(row, 5, QTableWidgetItem(str(fd.get("paper_size", "")).upper()))
            table.setItem(row, 6, QTableWidgetItem(f"₹{file_cost:.2f}"))

            if fd.get("color_mode") == "color":
                for col in range(7):
                    item = table.item(row, col)
                    if item:
                        item.setForeground(QColor("#c85a00"))

        main_layout.addWidget(table)

        # Total cost
        total: float = self._calculate_total()
        total_label: QLabel = QLabel(f"<b>Total Estimated Cost: ₹{total:.2f}</b>")
        total_label.setStyleSheet("font-size: 13px; padding: 4px 0;")
        main_layout.addWidget(total_label)

        sep2: QFrame = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(sep2)

        # Printer selection + actions
        action_row: QHBoxLayout = QHBoxLayout()

        printer_label: QLabel = QLabel("Printer:")
        action_row.addWidget(printer_label)

        self.printer_combo: QComboBox = QComboBox()
        printers: list[str] = self.printer_manager.get_printers()
        if printers:
            self.printer_combo.addItems(printers)
        else:
            self.printer_combo.addItem("No printers found")
        self.printer_combo.setMinimumWidth(220)
        action_row.addWidget(self.printer_combo)

        action_row.addStretch()

        self.print_btn: QPushButton = QPushButton("Print")
        self.print_btn.setStyleSheet(
            "background-color: #2ecc71; color: white; font-weight: bold; "
            "padding: 6px 18px; border-radius: 5px;"
        )
        self.print_btn.clicked.connect(self._handle_print)
        if not printers:
            self.print_btn.setEnabled(False)
        action_row.addWidget(self.print_btn)

        cancel_btn: QPushButton = QPushButton("Cancel Job")
        cancel_btn.setStyleSheet(
            "background-color: #e74c3c; color: white; font-weight: bold; "
            "padding: 6px 18px; border-radius: 5px;"
        )
        cancel_btn.clicked.connect(self._handle_cancel)
        action_row.addWidget(cancel_btn)

        close_btn: QPushButton = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        action_row.addWidget(close_btn)

        main_layout.addLayout(action_row)

    def _handle_print(self) -> None:
        printer: str = self.printer_combo.currentText()
        confirm: QMessageBox.StandardButton = QMessageBox.question(
            self,
            "Confirm Print",
            f"Send job for <b>{self.job.get('name', '')}</b> to <b>{printer}</b>?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.print_btn.setEnabled(False)
        self.print_btn.setText("Printing…")

        success: bool = self.printer_manager.print_job(
            self.job, printer, self.file_storage_path
        )
        if success:
            self.queue_manager.complete_job(
                self.job["_id"],
                revenue=self._calculate_total(),
                event_type="completed",
            )
            QMessageBox.information(self, "Done", "Job sent to printer and removed from queue.")
            self.accept()
        else:
            self.print_btn.setEnabled(True)
            self.print_btn.setText("Print")
            QMessageBox.critical(self, "Error", "Failed to send job to printer. Check logs.")

    def _handle_cancel(self) -> None:
        confirm: QMessageBox.StandardButton = QMessageBox.question(
            self,
            "Cancel Job",
            f"Cancel and remove job for <b>{self.job.get('name', '')}</b>?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.queue_manager.complete_job(
            self.job["_id"],
            revenue=0.0,
            event_type="dropped",
        )
        self.accept()
