"""
Persistence tests for PeerDiscovery.
ServiceBrowser and Zeroconf are mocked so no real network traffic occurs.
The tests verify that discovered_peers.json is written correctly.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from zeroconf import ServiceStateChange

from server.src.peer_discovery import PeerDiscovery


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mock_info(server: str, shop_name: str, port: int = 3000) -> MagicMock:
    info = MagicMock()
    info.server = server
    info.port = port
    info.properties = {b"shop_name": shop_name.encode()}
    return info


def make_pd(own_hostname: str, peers_file: str, mock_zc: MagicMock) -> PeerDiscovery:
    """Create a PeerDiscovery instance with ServiceBrowser patched out."""
    with patch("server.src.peer_discovery.ServiceBrowser"):
        return PeerDiscovery(own_hostname, peers_file, mock_zc)


def fire_added(pd: PeerDiscovery, mock_zc: MagicMock, service_name: str, info: MagicMock) -> None:
    mock_zc.get_service_info.return_value = info
    pd._on_change(mock_zc, "_qprint._tcp.local.", service_name, ServiceStateChange.Added)


def fire_removed(pd: PeerDiscovery, mock_zc: MagicMock, service_name: str) -> None:
    pd._on_change(mock_zc, "_qprint._tcp.local.", service_name, ServiceStateChange.Removed)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPeerDiscoveryPersistence:
    def test_peers_file_written_when_peer_added(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        info = make_mock_info("qprint-lib.local.", "Library Shop")
        fire_added(pd, mock_zc, "qprint-lib._qprint._tcp.local.", info)

        peers = json.loads(Path(peers_file).read_text())
        assert len(peers) == 1
        assert peers[0]["shop_name"] == "Library Shop"
        assert peers[0]["host"] == "qprint-lib.local"
        assert peers[0]["port"] == 3000

    def test_self_is_excluded_from_peers_file(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        # Simulate own service being discovered (same hostname)
        own_info = make_mock_info("qprint-main.local.", "Main Shop")
        fire_added(pd, mock_zc, "qprint-main._qprint._tcp.local.", own_info)

        # File should either not exist or be empty
        if Path(peers_file).exists():
            peers = json.loads(Path(peers_file).read_text())
            assert peers == []

    def test_peer_removed_from_file(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        svc_name = "qprint-lib._qprint._tcp.local."
        fire_added(pd, mock_zc, svc_name, make_mock_info("qprint-lib.local.", "Library Shop"))
        fire_removed(pd, mock_zc, svc_name)

        peers = json.loads(Path(peers_file).read_text())
        assert peers == []

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

    def test_removing_one_peer_leaves_others(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", peers_file, mock_zc)

        fire_added(pd, mock_zc, "qprint-lib._qprint._tcp.local.",
                   make_mock_info("qprint-lib.local.", "Library Shop"))
        fire_added(pd, mock_zc, "qprint-csb._qprint._tcp.local.",
                   make_mock_info("qprint-csb.local.", "CSB Shop"))
        fire_removed(pd, mock_zc, "qprint-lib._qprint._tcp.local.")

        peers = json.loads(Path(peers_file).read_text())
        assert len(peers) == 1
        assert peers[0]["shop_name"] == "CSB Shop"

    def test_no_service_info_does_not_create_file(self, tmp_path):
        peers_file = str(tmp_path / "discovered_peers.json")
        mock_zc = MagicMock()
        mock_zc.get_service_info.return_value = None  # info unavailable
        pd = make_pd("qprint-main", peers_file, mock_zc)

        pd._on_change(mock_zc, "_qprint._tcp.local.",
                      "qprint-lib._qprint._tcp.local.", ServiceStateChange.Added)

        assert not Path(peers_file).exists()

    def test_peers_file_created_in_nonexistent_directory(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c" / "discovered_peers.json"
        mock_zc = MagicMock()
        pd = make_pd("qprint-main", str(nested), mock_zc)

        fire_added(pd, mock_zc, "qprint-lib._qprint._tcp.local.",
                   make_mock_info("qprint-lib.local.", "Library Shop"))

        assert nested.exists()
