# server/src/peer_discovery.py
"""mDNS peer discovery for Q-Print shops.

Peers are kept in memory with an online/offline status.
On ServiceStateChange.Removed the peer is marked offline (not deleted).
Peers offline longer than PEER_OFFLINE_GRACE_SECONDS are pruned every
PEER_PRUNE_INTERVAL_SECONDS by a background timer.
"""

import json
import logging
import os
import threading
import time

from zeroconf import ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf

logger = logging.getLogger(__name__)

QPRINT_SERVICE_TYPE = "_qprint._tcp.local."
PEER_OFFLINE_GRACE_SECONDS: int = 300   # 5 minutes
PEER_PRUNE_INTERVAL_SECONDS: int = 60   # check every 1 minute


class PeerDiscovery:
    """
    Browses the local network for other Q-Print shops advertising
    _qprint._tcp.local. and maintains a discovered_peers.json file.

    Peer record schema:
        {
            "shop_name": str,
            "host":      str,   # e.g. "qprint-lib.local"
            "port":      int,
            "status":    "online" | "offline",
            "last_seen": float   # Unix timestamp
        }
    """

    def __init__(self, own_hostname: str, peers_file_path: str, zeroconf: Zeroconf) -> None:
        self._own_server = f"{own_hostname}.local."
        self._peers_file_path = peers_file_path
        self._zc = zeroconf
        self._peers: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._browser = ServiceBrowser(
            self._zc, QPRINT_SERVICE_TYPE, handlers=[self._on_change]
        )
        self._schedule_prune()
        logger.info("PeerDiscovery started — browsing for %s", QPRINT_SERVICE_TYPE)

    def update_own_hostname(self, new_hostname: str) -> None:
        """Update the filter that prevents advertising self as a peer."""
        self._own_server = f"{new_hostname}.local."
        logger.info("PeerDiscovery own_server updated to %s", self._own_server)

    # ── mDNS callbacks ─────────────────────────────────────────────────────────

    def _on_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        if state_change in (ServiceStateChange.Added, ServiceStateChange.Updated):
            self._handle_added(zeroconf, service_type, name)
        elif state_change == ServiceStateChange.Removed:
            self._handle_removed(name)

    def _handle_added(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        info: ServiceInfo | None = zeroconf.get_service_info(service_type, name)
        if not info:
            return
        if info.server == self._own_server:
            return  # skip self

        raw_name = info.properties.get(b"shop_name") or b""
        shop_name = raw_name.decode() if isinstance(raw_name, bytes) else str(raw_name)
        peer = {
            "shop_name": shop_name or name.split(".")[0],
            "host": info.server.rstrip("."),
            "port": info.port,
            "status": "online",
            "last_seen": time.time(),
        }
        with self._lock:
            self._peers[name] = peer
        self._write_peers()
        logger.info(
            "Peer online: %s → %s:%d", peer["shop_name"], peer["host"], peer["port"]
        )

    def _handle_removed(self, name: str) -> None:
        with self._lock:
            peer = self._peers.get(name)
            if not peer:
                return
            peer["status"] = "offline"
            peer["last_seen"] = time.time()
        self._write_peers()
        logger.info("Peer marked offline: %s", self._peers[name].get("shop_name", name))

    # ── Stale-peer pruning ─────────────────────────────────────────────────────

    def _schedule_prune(self) -> None:
        self._prune_timer = threading.Timer(PEER_PRUNE_INTERVAL_SECONDS, self._prune_stale)
        self._prune_timer.daemon = True
        self._prune_timer.start()

    def _prune_stale(self) -> None:
        cutoff = time.time() - PEER_OFFLINE_GRACE_SECONDS
        pruned = []
        with self._lock:
            for name, peer in list(self._peers.items()):
                if peer.get("status") == "offline" and peer.get("last_seen", 0) < cutoff:
                    pruned.append(name)
            for name in pruned:
                del self._peers[name]
        if pruned:
            self._write_peers()
            logger.info("Pruned %d stale peer(s)", len(pruned))
        self._schedule_prune()

    # ── File I/O ───────────────────────────────────────────────────────────────

    def _write_peers(self) -> None:
        with self._lock:
            peers_list = list(self._peers.values())
        try:
            os.makedirs(os.path.dirname(self._peers_file_path), exist_ok=True)
            with open(self._peers_file_path, "w", encoding="utf-8") as f:
                json.dump(peers_list, f, indent=2)
        except Exception as exc:
            logger.warning("Failed to write discovered_peers.json: %s", exc)
