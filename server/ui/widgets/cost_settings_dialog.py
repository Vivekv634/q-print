import json
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QDialogButtonBox, QFrame, QWidget,
)

logger = logging.getLogger(__name__)


class CostSettingsDialog(QDialog):
    def __init__(
        self,
        cost_file_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.cost_file_path: str = cost_file_path
        self.setWindowTitle("Cost Settings")
        self.setMinimumWidth(340)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title: QLabel = QLabel("Per-Page Printing Cost")
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(title)

        sep: QFrame = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        bw_row: QHBoxLayout = QHBoxLayout()
        bw_row.addWidget(QLabel("B&W (per page):"))
        self.bw_spin: QDoubleSpinBox = QDoubleSpinBox()
        self.bw_spin.setRange(0.0, 9999.0)
        self.bw_spin.setDecimals(2)
        self.bw_spin.setSingleStep(0.5)
        self.bw_spin.setMinimumWidth(100)
        bw_row.addWidget(self.bw_spin)
        layout.addLayout(bw_row)

        color_row: QHBoxLayout = QHBoxLayout()
        color_row.addWidget(QLabel("Color (per page):"))
        self.color_spin: QDoubleSpinBox = QDoubleSpinBox()
        self.color_spin.setRange(0.0, 9999.0)
        self.color_spin.setDecimals(2)
        self.color_spin.setSingleStep(0.5)
        self.color_spin.setMinimumWidth(100)
        color_row.addWidget(self.color_spin)
        layout.addLayout(color_row)

        buttons: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self) -> None:
        try:
            with open(self.cost_file_path, "r") as f:
                data: dict = json.load(f)
            self.bw_spin.setValue(float(data.get("bw_per_page", 1.5)))
            self.color_spin.setValue(float(data.get("color_per_page", 5.0)))
        except Exception as e:
            logger.warning(f"Could not load cost.json: {e}")

    def _save(self) -> None:
        data: dict[str, float] = {
            "bw_per_page": self.bw_spin.value(),
            "color_per_page": self.color_spin.value(),
        }
        try:
            Path(self.cost_file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.cost_file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cost settings saved: {data}")
            self.accept()
        except Exception as e:
            logger.error(f"Failed to save cost.json: {e}")
