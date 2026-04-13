# server/ui/widgets/edit_shop_dialog.py
"""Edit Shop Name & Hostname dialog.

Reads the current shop_config.json, lets the admin change the shop name
and mDNS hostname, and writes the updated values back on save.
Other keys (college_name, analytics_*) are preserved unchanged.
"""

import json
import logging
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

_HOSTNAME_RE = re.compile(r"^qprint-[a-z0-9]([a-z0-9\-]{0,29}[a-z0-9])?$")


class EditShopDialog(QDialog):
    config_saved = Signal(dict)  # emits the full updated config on save

    def __init__(self, config_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config_path = config_path
        self._config: dict = self._load_config()
        self.setWindowTitle("Edit Name & Hostname")
        self.setMinimumWidth(480)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._build_ui()
        self._validate()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _load_config(self) -> dict:
        try:
            with open(self._config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(0)

        title = QLabel("Edit Name & Hostname")
        title.setStyleSheet("font-size:15px;font-weight:bold;")
        layout.addWidget(title)

        layout.addSpacing(6)

        subtitle = QLabel("Changes take effect on next app restart for the hostname.")
        subtitle.setStyleSheet("font-size:11px;color:#888;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        layout.addSpacing(20)

        # Shop name
        layout.addWidget(QLabel("Shop Name"))
        layout.addSpacing(6)
        self._name_input = QLineEdit()
        self._name_input.setText(self._config.get("shop_name", ""))
        self._name_input.setPlaceholderText("e.g. Library Shop")
        self._name_input.textChanged.connect(self._validate)
        layout.addWidget(self._name_input)

        layout.addSpacing(18)

        # Hostname
        layout.addWidget(QLabel("mDNS Hostname"))
        layout.addSpacing(6)
        self._host_input = QLineEdit()
        self._host_input.setText(self._config.get("mdns_hostname", ""))
        self._host_input.setPlaceholderText("qprint-...")
        self._host_input.textChanged.connect(self._validate)
        layout.addWidget(self._host_input)

        layout.addSpacing(4)
        hint = QLabel("Must start with 'qprint-' and use only lowercase letters, digits, hyphens.")
        hint.setStyleSheet("font-size:11px;color:#888;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addSpacing(10)

        self._msg_label = QLabel("")
        self._msg_label.setStyleSheet("font-size:11px;color:#c0392b;")
        self._msg_label.setWordWrap(True)
        layout.addWidget(self._msg_label)

        layout.addSpacing(24)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self._save_btn = QPushButton("Save Edit")
        self._save_btn.setDefault(True)
        self._save_btn.setStyleSheet(
            "QPushButton{background:#2980b9;color:white;padding:8px 20px;"
            "border-radius:4px;font-weight:bold;}"
            "QPushButton:disabled{background:#aaa;}"
        )
        self._save_btn.clicked.connect(self._save)
        btn_row.addWidget(self._save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding:8px 16px;border-radius:4px;")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    # ── Validation ─────────────────────────────────────────────────────────────

    def _validate(self) -> None:
        name = self._name_input.text().strip()
        host = self._host_input.text().strip()

        if not name:
            self._msg_label.setText("Shop name cannot be empty.")
            self._save_btn.setEnabled(False)
            return

        if not _HOSTNAME_RE.match(host):
            self._msg_label.setText(
                "Hostname must start with 'qprint-' and use only lowercase "
                "letters, digits, and hyphens (no leading/trailing hyphens)."
            )
            self._save_btn.setEnabled(False)
            return

        self._msg_label.setText("")
        self._save_btn.setEnabled(True)

    # ── Save ───────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        updated = {
            **self._config,
            "shop_name": self._name_input.text().strip(),
            "mdns_hostname": self._host_input.text().strip(),
        }
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(updated, f, indent=2)
            logger.info(
                "Shop config updated: name=%r hostname=%r",
                updated["shop_name"],
                updated["mdns_hostname"],
            )
            self.config_saved.emit(updated)
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Could not save config:\n{exc}")
