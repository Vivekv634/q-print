import json
import re
import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ip_config import generate_hostname

logger = logging.getLogger(__name__)

# Valid hostname: starts with qprint-, followed by 1+ lowercase alnum or hyphen chars,
# must not end with a hyphen, total slug length 1-31.
_HOSTNAME_RE = re.compile(r"^qprint-[a-z0-9]([a-z0-9\-]{0,29}[a-z0-9])?$")


class SetupDialog(QDialog):
    """
    First-run dialog that collects shop name and mDNS hostname.
    Writes the result to shop_config.json and accepts the dialog.
    """

    def __init__(self, config_path: str, parent=None) -> None:
        super().__init__(parent)
        self._config_path = config_path
        self._hostname_manually_edited = False

        self.setWindowTitle("Q-Print — Shop Setup")
        self.setMinimumWidth(500)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        # Prevent closing via the window X without going through _reject
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self._build_ui()
        self._validate()

    # ── UI construction ────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(28, 28, 28, 28)

        # Title
        title = QLabel("Welcome to Q-Print")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title.setFont(title_font)
        root.addWidget(title)

        subtitle = QLabel(
            "Configure this shop's identity before starting. "
            "This dialog will not appear again once saved."
        )
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line)

        # Shop name
        root.addWidget(QLabel("Shop Name"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g.  Library Shop,  CSB Block Shop")
        self._name_input.textChanged.connect(self._on_name_changed)
        root.addWidget(self._name_input)

        # Hostname
        root.addWidget(QLabel("mDNS Hostname  (auto-generated — you can change it)"))
        self._host_input = QLineEdit()
        self._host_input.setPlaceholderText("qprint-...")
        # textEdited fires only on user keystrokes, not programmatic setText
        self._host_input.textEdited.connect(self._on_hostname_edited)
        self._host_input.textChanged.connect(self._validate)
        root.addWidget(self._host_input)

        hint = QLabel("Users will connect to  http://<hostname>.local:3000")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(hint)

        # Error / status message
        self._msg_label = QLabel("")
        self._msg_label.setStyleSheet("color: #c0392b; font-size: 11px;")
        self._msg_label.setWordWrap(True)
        root.addWidget(self._msg_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._save_btn = QPushButton("Save && Continue")
        self._save_btn.setEnabled(False)
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self._save)
        btn_row.addWidget(self._save_btn)
        root.addLayout(btn_row)

    # ── Slots ──────────────────────────────────────────────────────────

    def _on_name_changed(self, text: str) -> None:
        if not self._hostname_manually_edited:
            auto = generate_hostname(text)
            # Block signals so textEdited doesn't fire (it's programmatic)
            self._host_input.blockSignals(True)
            self._host_input.setText(auto)
            self._host_input.blockSignals(False)
        self._validate()

    def _on_hostname_edited(self) -> None:
        # User typed in the hostname field — stop tracking name changes
        expected = generate_hostname(self._name_input.text())
        if self._host_input.text() != expected:
            self._hostname_manually_edited = True

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

    def _save(self) -> None:
        name = self._name_input.text().strip()
        host = self._host_input.text().strip()

        try:
            with open(self._config_path, "w") as f:
                json.dump({"shop_name": name, "mdns_hostname": host}, f, indent=2)
            logger.info(f"Shop configured: '{name}' as {host}.local")
            self.accept()
        except Exception as e:
            self._msg_label.setStyleSheet("color: #c0392b; font-size: 11px;")
            self._msg_label.setText(f"Failed to save config: {e}")
