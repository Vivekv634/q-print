import json
import logging
import os
import threading
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo

logger = logging.getLogger(__name__)

QPRINT_SERVICE_TYPE = "_qprint._tcp.local."


class PeerDiscovery:
    """
    Browses the local network for other Q-Print shops advertising
    _qprint._tcp.local. and maintains a discovered_peers.json file
    that the Next.js API layer reads to build the campus overview.
    """

    def __init__(self, own_hostname: str, peers_file_path: str, zeroconf: Zeroconf):
        self._own_server = f"{own_hostname}.local."
        self._peers_file_path = peers_file_path
        self._zc = zeroconf
        self._peers: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._browser = ServiceBrowser(
            self._zc, QPRINT_SERVICE_TYPE, handlers=[self._on_change]
        )
        logger.info("PeerDiscovery started — browsing for %s", QPRINT_SERVICE_TYPE)

    def _on_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        if state_change == ServiceStateChange.Added:
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
            }
            with self._lock:
                self._peers[name] = peer
            self._write_peers()
            logger.info("Peer discovered: %s → %s:%d", peer["shop_name"], peer["host"], peer["port"])

        elif state_change == ServiceStateChange.Removed:
            with self._lock:
                removed = self._peers.pop(name, None)
            if removed:
                self._write_peers()
                logger.info("Peer removed: %s", removed.get("shop_name", name))

    def _write_peers(self) -> None:
        with self._lock:
            peers_list = list(self._peers.values())
        try:
            os.makedirs(os.path.dirname(self._peers_file_path), exist_ok=True)
            with open(self._peers_file_path, "w") as f:
                json.dump(peers_list, f, indent=2)
        except Exception as e:
            logger.warning("Failed to write discovered_peers.json: %s", e)
