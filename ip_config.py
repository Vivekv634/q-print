import socket
import netifaces
import logging
from zeroconf import Zeroconf, ServiceInfo
from server.utils.constants import PORT

logger = logging.getLogger(__name__)

MDNS_HOSTNAME = "qprint"


def get_local_ip() -> str:
    try:
        for interface in netifaces.interfaces():
            if interface == "lo":
                continue
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip: str = addr.get("addr", "")
                    if ip and not ip.startswith("127."):
                        return ip
    except Exception as e:
        logger.warning(f"Failed to detect local IP via netifaces: {e}")
    return "127.0.0.1"


def register_mdns() -> Zeroconf:
    local_ip = get_local_ip()
    zc = Zeroconf()
    info = ServiceInfo(
        "_http._tcp.local.",
        "Q-Print._http._tcp.local.",
        addresses=[socket.inet_aton(local_ip)],
        port=PORT,
        server=f"{MDNS_HOSTNAME}.local.",
        properties={"path": "/"},
    )
    zc.register_service(info)
    logger.info(f"mDNS registered: {MDNS_HOSTNAME}.local → {local_ip}:{PORT}")
    return zc
