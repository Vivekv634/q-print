# server/ui/widgets/qr_dialog.py
"""QR Code dialog.

Shows the shop's mDNS URL as a scannable QR code.
Provides Download (→ server/assets/) and Print actions.
"""

import io
import logging
import os
from pathlib import Path

import qrcode  # type: ignore
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from server.utils.wifi_utils import get_ssid

logger = logging.getLogger(__name__)


class QRDialog(QDialog):
    def __init__(
        self,
        hostname: str,
        port: int,
        assets_path: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._hostname = hostname
        self._port = port
        self._assets_path = assets_path
        self._url = f"http://{hostname}.local:{port}"
        self._ssid = get_ssid()
        self._qr_pixmap = self._make_qr_pixmap(self._url)
        self.setWindowTitle("Shop QR Code")
        self.setFixedSize(380, 460)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        title = QLabel("Shop QR Code")
        title.setStyleSheet("font-size:15px;font-weight:bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title)

        layout.addSpacing(16)

        qr_label = QLabel()
        qr_label.setPixmap(self._qr_pixmap.scaled(
            220, 220,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        qr_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(qr_label)

        layout.addSpacing(14)

        url_label = QLabel(self._url)
        url_label.setStyleSheet("font-size:12px;font-weight:bold;")
        url_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(url_label)

        layout.addSpacing(6)

        wifi_label = QLabel(f"📶 Connected: {self._ssid}")
        wifi_label.setStyleSheet("font-size:11px;color:#555;")
        wifi_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(wifi_label)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        download_btn = QPushButton("⬇ Download")
        download_btn.setStyleSheet(
            "background:#2980b9;color:white;padding:8px 16px;border-radius:4px;font-weight:bold;"
        )
        download_btn.clicked.connect(self._handle_download)

        print_btn = QPushButton("🖨 Print")
        print_btn.setStyleSheet(
            "background:#555;color:white;padding:8px 16px;border-radius:4px;font-weight:bold;"
        )
        print_btn.clicked.connect(self._handle_print)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding:8px 16px;border-radius:4px;")
        close_btn.clicked.connect(self.reject)

        btn_row.addWidget(download_btn)
        btn_row.addWidget(print_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _make_qr_pixmap(self, url: str) -> QPixmap:
        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        pil_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)
        qimage = QImage.fromData(buf.read())
        return QPixmap.fromImage(qimage)

    def _handle_download(self) -> None:
        Path(self._assets_path).mkdir(parents=True, exist_ok=True)
        safe_name = self._hostname.replace(".", "_").replace(":", "_")
        dest = os.path.join(self._assets_path, f"qr_{safe_name}.png")
        try:
            self._qr_pixmap.save(dest, "PNG")
            QMessageBox.information(self, "Saved", f"QR code saved to:\n{dest}")
            logger.info("QR code saved: %s", dest)
        except Exception as exc:
            logger.error("QR download failed: %s", exc)
            QMessageBox.critical(self, "Error", f"Could not save QR code:\n{exc}")

    def _handle_print(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Print Error", "Could not initialise painter for printing.")
            return
        try:
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            target_w = int(page_rect.width() * 0.55)
            scaled = self._qr_pixmap.scaled(
                target_w, target_w,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = int((page_rect.width() - scaled.width()) / 2)
            painter.drawPixmap(x, 60, scaled)

            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(
                0,
                60 + scaled.height() + 30,
                int(page_rect.width()),
                40,
                Qt.AlignmentFlag.AlignHCenter,
                self._url,
            )
        finally:
            painter.end()
        logger.info("QR code sent to printer.")
