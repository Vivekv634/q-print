# server/ui/widgets/quick_print_menu.py
"""Cursor-position printer context menu for quick single-click printing.

Usage:
    menu = QuickPrintMenu(job, queue_manager, printer_manager,
                          file_storage_path, cost_file_path, parent=self)
    menu.show_at(btn.mapToGlobal(btn.rect().bottomLeft()))
"""

import json
import logging
from typing import Any

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QMenu, QMessageBox, QWidget

from server.src.printer_manager import PrinterManager
from server.src.queue_manager import QueueManager

logger = logging.getLogger(__name__)

_DISABLED_STATUSES = {"Offline", "Error", "Unavailable"}


class QuickPrintMenu(QMenu):
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
        self._job = job
        self._queue_manager = queue_manager
        self._printer_manager = printer_manager
        self._file_storage_path = file_storage_path
        self._cost_file_path = cost_file_path
        self._build_menu()

    def _build_menu(self) -> None:
        # Use the cached status list — populated by PrinterPanel's background poll.
        # This avoids any subprocess/I/O calls on the Qt main thread.
        cached = self._printer_manager.get_cached_status()
        if not cached:
            action = self.addAction("No printers available (refresh printer panel)")
            action.setEnabled(False)
            return

        for info in cached:
            name = info.get("name", "Unknown")
            status = info.get("status", "Unknown")
            is_disabled = any(s in status for s in _DISABLED_STATUSES)
            label = f"{name}  [{status}]" if is_disabled else name
            action = self.addAction(label)
            action.setEnabled(not is_disabled)
            if not is_disabled:
                action.triggered.connect(
                    lambda checked=False, p=name: self._send_to_printer(p)
                )

    def _calculate_revenue(self) -> float:
        try:
            with open(self._cost_file_path, encoding="utf-8") as f:
                cost = json.load(f)
        except Exception:
            cost = {"bw_per_page": 1.5, "color_per_page": 5.0}

        total = 0.0
        for fd in self._job.get("filedataArray", []):
            if not isinstance(fd, dict):
                continue
            pages = int(fd.get("page_count", 1))
            copies = int(fd.get("no_of_copies", 1))
            rate = (
                float(cost.get("color_per_page", 5.0))
                if fd.get("color_mode") == "color"
                else float(cost.get("bw_per_page", 1.5))
            )
            total += pages * copies * rate
        return total

    def _send_to_printer(self, printer_name: str) -> None:
        success = self._printer_manager.print_job(
            self._job, printer_name, self._file_storage_path
        )
        if success:
            revenue = self._calculate_revenue()
            self._queue_manager.complete_job(
                self._job["_id"],
                revenue=revenue,
                event_type="completed",
            )
            logger.info("Quick-print sent job %s to %s", self._job.get("_id"), printer_name)
        else:
            QMessageBox.critical(
                self.parentWidget(),
                "Print Error",
                f"Failed to send job to {printer_name}. Check logs.",
            )

    def show_at(self, pos: QPoint) -> None:
        self.exec(pos)
