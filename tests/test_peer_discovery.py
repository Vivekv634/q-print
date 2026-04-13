"""
Tests for PeerDiscovery — ServiceBrowser and Zeroconf are mocked.
After the grace-period fix, Removed marks peers offline instead of deleting them.
"""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from zeroconf import ServiceStateChange

from server.src.peer_discovery import (
    PeerDiscovery,
    PEER_OFFLINE_GRACE_SECONDS,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mock_info(server: str, shop_name: str, port: int = 3000) -> MagicMock:
    info = MagicMock()
    info.server = server
    info.port = port
    info.properties = {b"shop_name": shop_name.encode()}
    return info


def make_pd(own_hostname: str, peers_file: str, mock_zc: MagicMock) -> PeerDiscovery:
    with patch("server.src.peer_discovery.ServiceBrowser"):
        with patch("server.src.peer_discovery.threading.Timer") as mock_timer:
            mock_timer.return_value = MagicMock()
            return PeerDiscovery(own_hostname, peers_file, mock_zc)


def fire_added(pd: PeerDiscovery, mock_zc: MagicMock, service_name: str, info: MagicMock) -> None:
    mock_zc.get_service_info.return_value = info
    pd._on_change(mock_zc, "_qprint._tcp.local.", service_name, ServiceStateChange.Added)


def fire_updated(pd: PeerDiscovery, mock_zc: MagicMock, service_name: str, info: MagicMock) -> None:
    mock_zc.get_service_info.return_value = info
    pd._on_change(mock_zc, "_qprint._tcp.local.", service_name, ServiceStateChange.Updated)


def fire_removed(pd: PeerDiscovery, mock_zc: MagicMock, service_name: str) -> None:
    pd._on_change(mock_zc, "_qprint._tcp.local.", service_name, ServiceStateChange.Removed)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPeerDiscoveryPersistence:
    def test_peers_file_written_when_peer_added(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        fire_added(pd, mock_zc, "qprint-lib._qprint._tcp.local.",
                   make_mock_info("qprint-lib.local.", "Library Shop"))

        peers = json.loads(Path(peers_file).read_text())
        assert len(peers) == 1
        assert peers[0]["shop_name"] == "Library Shop"
        assert peers[0]["host"] == "qprint-lib.local"
        assert peers[0]["port"] == 3000
        assert peers[0]["status"] == "online"
        assert "last_seen" in peers[0]

    def test_self_is_excluded_from_peers_file(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        own_info = make_mock_info("qprint-main.local.", "Main Shop")
        fire_added(pd, mock_zc, "qprint-main._qprint._tcp.local.", own_info)

        if Path(peers_file).exists():
            peers = json.loads(Path(peers_file).read_text())
            assert peers == []

    def test_removed_peer_marked_offline_not_deleted(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        svc = "qprint-lib._qprint._tcp.local."
        fire_added(pd, mock_zc, svc, make_mock_info("qprint-lib.local.", "Library Shop"))
        fire_removed(pd, mock_zc, svc)

        peers = json.loads(Path(peers_file).read_text())
        assert len(peers) == 1
        assert peers[0]["status"] == "offline"

    def test_updated_peer_refreshes_to_online(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        svc = "qprint-lib._qprint._tcp.local."
        info = make_mock_info("qprint-lib.local.", "Library Shop")
        fire_added(pd, mock_zc, svc, info)
        fire_removed(pd, mock_zc, svc)
        fire_updated(pd, mock_zc, svc, info)

        peers = json.loads(Path(peers_file).read_text())
        assert peers[0]["status"] == "online"

    def test_multiple_peers_all_written(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        fire_added(pd, mock_zc, "qprint-lib._qprint._tcp.local.",
                   make_mock_info("qprint-lib.local.", "Library Shop"))
        fire_added(pd, mock_zc, "qprint-csb._qprint._tcp.local.",
                   make_mock_info("qprint-csb.local.", "CSB Shop"))

        peers = json.loads(Path(peers_file).read_text())
        names = {p["shop_name"] for p in peers}
        assert names == {"Library Shop", "CSB Shop"}

    def test_removing_one_peer_leaves_others_online(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        fire_added(pd, mock_zc, "qprint-lib._qprint._tcp.local.",
                   make_mock_info("qprint-lib.local.", "Library Shop"))
        fire_added(pd, mock_zc, "qprint-csb._qprint._tcp.local.",
                   make_mock_info("qprint-csb.local.", "CSB Shop"))
        fire_removed(pd, mock_zc, "qprint-lib._qprint._tcp.local.")

        peers = json.loads(Path(peers_file).read_text())
        statuses = {p["shop_name"]: p["status"] for p in peers}
        assert statuses["Library Shop"] == "offline"
        assert statuses["CSB Shop"] == "online"

    def test_prune_removes_stale_offline_peers(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        svc = "qprint-lib._qprint._tcp.local."
        fire_added(pd, mock_zc, svc, make_mock_info("qprint-lib.local.", "Library Shop"))
        fire_removed(pd, mock_zc, svc)

        # Backdate the last_seen past the grace period
        with pd._lock:
            pd._peers[svc]["last_seen"] = time.time() - PEER_OFFLINE_GRACE_SECONDS - 1

        pd._prune_stale()

        peers = json.loads(Path(peers_file).read_text())
        assert peers == []

    def test_prune_keeps_recently_offline_peers(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        svc = "qprint-lib._qprint._tcp.local."
        fire_added(pd, mock_zc, svc, make_mock_info("qprint-lib.local.", "Library Shop"))
        fire_removed(pd, mock_zc, svc)

        # last_seen is recent — should not be pruned
        pd._prune_stale()

        peers = json.loads(Path(peers_file).read_text())
        assert len(peers) == 1
        assert peers[0]["status"] == "offline"

    def test_no_service_info_does_not_create_file(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        mock_zc.get_service_info.return_value = None
        pd = make_pd("qprint-main", peers_file, mock_zc)

        pd._on_change(mock_zc, "_qprint._tcp.local.",
                      "qprint-lib._qprint._tcp.local.", ServiceStateChange.Added)

        assert not Path(peers_file).exists()
