import json
import logging
from datetime import datetime
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal, QFileSystemWatcher, QModelIndex
from PySide6.QtGui import QColor

from server.src.queue_manager import QueueManager

logger = logging.getLogger(__name__)


class QueuePanel(QWidget):
    job_selected = Signal(dict)

    def __init__(
        self,
        queue_manager: QueueManager,
        queue_file_path: str,
        cost_file_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.queue_manager: QueueManager = queue_manager
        self.cost_file_path: str = cost_file_path
        self._queue_data: list[dict[str, Any]] = []
        self._build_ui()
        self._watch_files(queue_file_path, cost_file_path)
        self.refresh()

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header_row: QHBoxLayout = QHBoxLayout()
        title: QLabel = QLabel("Print Queue")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_row.addWidget(title)
        header_row.addStretch()

        self.count_label: QLabel = QLabel("0 job(s)")
        self.count_label.setStyleSheet("color: grey;")
        header_row.addWidget(self.count_label)
        layout.addLayout(header_row)

        sep: QFrame = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        self.table: QTableWidget = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "Name", "Files", "Pages", "Est. Cost", "Time"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        hint: QLabel = QLabel("Double-click a row to view details / print / cancel")
        hint.setStyleSheet("color: grey; font-size: 11px;")
        layout.addWidget(hint)

    def _watch_files(self, queue_path: str, cost_path: str) -> None:
        self._watcher: QFileSystemWatcher = QFileSystemWatcher([queue_path, cost_path], self)
        self._watcher.fileChanged.connect(self._on_file_changed)

    def _on_file_changed(self, path: str) -> None:
        # Re-add after each change: edit-json-file replaces files atomically,
        # which removes the inode the watcher holds.
        self._watcher.addPath(path)
        self.refresh()

    def _load_cost(self) -> dict[str, float]:
        try:
            with open(self.cost_file_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"bw_per_page": 1.5, "color_per_page": 5.0}

    def _calculate_job_cost(self, job: dict[str, Any], cost: dict[str, float]) -> float:
        total: float = 0.0
        for fd in job.get("filedataArray", []):
            if not isinstance(fd, dict):
                continue
            pages: int = int(fd.get("page_count", 1))
            copies: int = int(fd.get("no_of_copies", 1))
            rate: float = (
                float(cost.get("color_per_page", 5.0))
                if fd.get("color_mode") == "color"
                else float(cost.get("bw_per_page", 1.5))
            )
            total += pages * copies * rate
        return total

    def refresh(self) -> None:
        queue: list[dict[str, Any]] = self.queue_manager.get_queue()
        self._queue_data = queue
        cost: dict[str, float] = self._load_cost()

        self.count_label.setText(f"{len(queue)} job(s)")
        self.table.setRowCount(len(queue))

        for row, job in enumerate(queue):
            files: list[dict[str, Any]] = job.get("filedataArray", [])
            total_pages: int = sum(
                int(fd.get("page_count", 1)) * int(fd.get("no_of_copies", 1))
                for fd in files
                if isinstance(fd, dict)
            )
            job_cost: float = self._calculate_job_cost(job, cost)
            ts: int = job.get("timestamp", 0)
            dt_str: str = (
                datetime.fromtimestamp(ts / 1000).strftime("%H:%M:%S") if ts else ""
            )

            self.table.setItem(row, 0, QTableWidgetItem(str(job.get("position", row + 1))))
            self.table.setItem(row, 1, QTableWidgetItem(str(job.get("name", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(len(files))))
            self.table.setItem(row, 3, QTableWidgetItem(str(total_pages)))
            self.table.setItem(row, 4, QTableWidgetItem(f"\u20b9{job_cost:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(dt_str))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _on_double_click(self, index: QModelIndex) -> None:
        row: int = index.row()
        if 0 <= row < len(self._queue_data):
            self.job_selected.emit(self._queue_data[row])
