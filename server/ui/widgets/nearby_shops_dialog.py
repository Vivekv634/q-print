# server/ui/widgets/nearby_shops_dialog.py
"""Nearby Shops dialog — real-time edition.

Updates are driven by three mechanisms, in order of latency:
  1. PeerDiscovery.force_refresh() — clears stale state and fires fresh mDNS
     queries; responses arrive within 1–3 s and update discovered_peers.json.
  2. QFileSystemWatcher on discovered_peers.json (instant when mDNS fires)
  3. QTimer every 5 s as a fallback (handles missed file events)
  4. Background HTTP probe thread — overrides mDNS status with live reachability
     so the UI reflects actual shop availability within ~2 s of a status change.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt, QFileSystemWatcher, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from server.src.peer_discovery import PeerDiscovery

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT_S: float = 2.0   # per-peer HTTP timeout
_AUTO_REFRESH_MS: int   = 5_000  # fallback timer interval


class NearbyShopsDialog(QDialog):
    # Emitted from the probe thread; carries list of {host, online} dicts
    _probe_done = Signal(list)

    def __init__(
        self,
        peers_file_path: str,
        peer_discovery: "PeerDiscovery | None" = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._peers_file_path = peers_file_path
        self._peer_discovery = peer_discovery
        self._peers: list[dict[str, Any]] = []
        # Guards the probe thread: set in closeEvent so the thread doesn't
        # emit on an already-destroyed C++ Qt object (crash prevention).
        self._stop_probe = threading.Event()
        self.setWindowTitle("Shops on this Network")
        self.setMinimumSize(520, 420)
        self._build_ui()
        self._setup_watchers()
        # Trigger a live mDNS scan rather than reading potentially stale data.
        self._trigger_refresh()

    # ── UI skeleton ────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("Shops on this Network")
        title.setStyleSheet("font-size:15px;font-weight:bold;")
        header_row.addWidget(title)
        header_row.addStretch()

        self._probe_label = QLabel("🔍 Probing…")
        self._probe_label.setStyleSheet("font-size:11px;color:#888;")
        self._probe_label.setVisible(False)
        header_row.addWidget(self._probe_label)

        refresh_btn = QPushButton("↺ Refresh")
        refresh_btn.clicked.connect(self._trigger_refresh)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self._scroll_area)

        bottom_row = QHBoxLayout()
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color:grey;font-size:11px;")
        bottom_row.addWidget(self._count_label)
        bottom_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        bottom_row.addWidget(close_btn)
        layout.addLayout(bottom_row)

    # ── Watchers ───────────────────────────────────────────────────────────────

    def _setup_watchers(self) -> None:
        # 1 — file watcher: fires when PeerDiscovery writes discovered_peers.json
        self._file_watcher = QFileSystemWatcher(self)
        path = self._peers_file_path
        self._file_watcher.addPath(path)
        self._file_watcher.fileChanged.connect(self._on_peers_file_changed)

        # 2 — fallback timer: catches missed file events and keeps display fresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(_AUTO_REFRESH_MS)
        self._refresh_timer.timeout.connect(self._load_peers)
        self._refresh_timer.start()

        # 3 — probe signal: background thread emits this to update live status
        self._probe_done.connect(self._apply_probe_results)

    def _on_peers_file_changed(self, path: str) -> None:
        # Re-add the path (some editors/OS replace the file instead of modifying it)
        self._file_watcher.addPath(path)
        self._load_peers()

    # ── Refresh trigger ────────────────────────────────────────────────────────

    def _trigger_refresh(self) -> None:
        """Ask PeerDiscovery for a fresh network scan, then show scanning state.

        If no PeerDiscovery instance was provided, falls back to reading the
        current file content immediately.
        """
        if self._peer_discovery is not None:
            # Clear the display and signal that we're scanning.
            self._peers = []
            self._render_peers([])
            self._probe_label.setText("📡 Scanning network…")
            self._probe_label.setVisible(True)
            # force_refresh() clears in-memory peers, writes [] to the file,
            # and restarts the ServiceBrowser so mDNS queries go out now.
            # The QFileSystemWatcher will call _load_peers() as peers respond.
            self._peer_discovery.force_refresh()
        else:
            self._load_peers()

    # ── Data loading ───────────────────────────────────────────────────────────

    def _load_peers(self) -> None:
        try:
            data: list[dict[str, Any]] = json.loads(
                Path(self._peers_file_path).read_text(encoding="utf-8")
            )
        except Exception:
            data = []

        self._peers = data
        self._render_peers(data)

        # Kick off a background HTTP probe for live reachability
        if data:
            self._probe_label.setText("🔍 Probing…")
            self._probe_label.setVisible(True)
            t = threading.Thread(target=self._probe_peers_thread, args=(list(data),), daemon=True)
            t.start()
        else:
            # No peers yet — keep showing the scan label if a refresh is in
            # progress, otherwise hide it.
            if self._probe_label.text() != "📡 Scanning network…":
                self._probe_label.setVisible(False)

    def _render_peers(self, data: list[dict[str, Any]]) -> None:
        now = time.time()
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(8)
        vbox.setContentsMargins(0, 0, 8, 0)

        if not data:
            empty = QLabel("No other Q-Print shops discovered on this network.")
            empty.setStyleSheet("color:grey;padding:20px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(empty)
        else:
            for peer in data:
                vbox.addWidget(self._make_peer_card(peer, now))
        vbox.addStretch()

        self._scroll_area.setWidget(container)
        online_count = sum(1 for p in data if p.get("status") == "online")
        self._count_label.setText(
            f"{len(data)} shop(s) discovered · {online_count} online · mDNS + live probe"
        )

    # ── Background HTTP probe ──────────────────────────────────────────────────

    def _probe_peers_thread(self, peers: list[dict[str, Any]]) -> None:
        results: list[dict[str, Any]] = []
        for peer in peers:
            if self._stop_probe.is_set():
                return  # dialog closed — do NOT touch Qt objects
            host = peer.get("host", "")
            port = peer.get("port", 3000)
            online = self._http_probe(host, port)
            results.append({"host": host, "online": online})
        if not self._stop_probe.is_set():
            self._probe_done.emit(results)  # safe: dialog still alive

    @staticmethod
    def _http_probe(host: str, port: int) -> bool:
        try:
            url = f"http://{host}:{port}/api/status"
            req = urllib.request.urlopen(url, timeout=_PROBE_TIMEOUT_S)
            return req.status == 200
        except Exception:
            return False

    def _apply_probe_results(self, results: list[dict[str, Any]]) -> None:
        self._probe_label.setVisible(False)
        probe_map: dict[str, bool] = {r["host"]: r["online"] for r in results}

        # Merge probe results into peer records and re-render
        updated: list[dict[str, Any]] = []
        for peer in self._peers:
            host = peer.get("host", "")
            p = dict(peer)
            if host in probe_map:
                p["status"] = "online" if probe_map[host] else "offline"
                if probe_map[host]:
                    p["last_seen"] = time.time()
            updated.append(p)

        self._peers = updated
        self._render_peers(updated)

    # ── Card builder ───────────────────────────────────────────────────────────

    def _make_peer_card(self, peer: dict[str, Any], now: float) -> QFrame:
        status = peer.get("status", "online")
        last_seen = float(peer.get("last_seen", now))
        is_online = status == "online"

        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        if is_online:
            card.setStyleSheet(
                "QFrame{border:1px solid #c8e6c9;border-radius:6px;background:#f9fff9;padding:4px;}"
            )
        else:
            card.setStyleSheet(
                "QFrame{border:1px solid #ddd;border-radius:6px;background:#fafafa;padding:4px;}"
            )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Title row
        title_row = QHBoxLayout()
        dot = QLabel("🟢" if is_online else "🔴")
        title_row.addWidget(dot)

        name_lbl = QLabel(f"<b>{peer.get('shop_name', 'Unknown Shop')}</b>")
        if not is_online:
            name_lbl.setStyleSheet("color:#999;")
        title_row.addWidget(name_lbl)
        title_row.addStretch()

        badge = QLabel("Online" if is_online else "Offline")
        badge.setStyleSheet(
            "background:#2ecc71;color:white;padding:1px 8px;border-radius:8px;font-size:10px;"
            if is_online else
            "background:#e74c3c;color:white;padding:1px 8px;border-radius:8px;font-size:10px;"
        )
        title_row.addWidget(badge)
        layout.addLayout(title_row)

        # Details row
        details_row = QHBoxLayout()
        host = peer.get("host", "")
        port = peer.get("port", 3000)
        host_lbl = QLabel(f"🌐 {host}:{port}")
        host_lbl.setStyleSheet("font-size:12px;color:#555;")
        details_row.addWidget(host_lbl)

        elapsed = int(now - last_seen)
        if elapsed < 5:
            seen_str = "just now"
        elif elapsed < 60:
            seen_str = f"{elapsed}s ago"
        elif elapsed < 3600:
            seen_str = f"{elapsed // 60}m ago"
        else:
            seen_str = f"{elapsed // 3600}h ago"
        seen_lbl = QLabel(f"⏱ Last seen: {seen_str}")
        seen_lbl.setStyleSheet("font-size:12px;color:#555;")
        details_row.addWidget(seen_lbl)
        details_row.addStretch()
        layout.addLayout(details_row)

        if not is_online:
            card.setEnabled(False)

        return card

    def closeEvent(self, event: Any) -> None:
        # Signal the probe thread to stop and not emit on this (soon-deleted) object
        self._stop_probe.set()
        self._refresh_timer.stop()
        super().closeEvent(event)
