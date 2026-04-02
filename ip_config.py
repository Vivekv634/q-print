import re
import socket
import json
import netifaces
import logging
from zeroconf import Zeroconf, ServiceInfo
from server.utils.constants import PORT, SHOP_CONFIG_PATH

logger = logging.getLogger(__name__)

QPRINT_SERVICE_TYPE = "_qprint._tcp.local."
SETUP_SENTINEL = "__setup_required__"


def generate_hostname(shop_name: str) -> str:
    """Convert a shop name to a valid mDNS hostname slug with qprint- prefix."""
    slug = re.sub(r"[^a-z0-9]+", "-", shop_name.lower()).strip("-")
    slug = slug[:30]
    return f"qprint-{slug}" if slug else "qprint-shop"


def load_shop_config() -> dict:
    try:
        with open(SHOP_CONFIG_PATH) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load shop_config.json: {e}. Using defaults.")
        return {"shop_name": SETUP_SENTINEL, "mdns_hostname": SETUP_SENTINEL}


def is_setup_required(shop_config: dict) -> bool:
    return shop_config.get("shop_name", SETUP_SENTINEL) == SETUP_SENTINEL


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


def register_mdns(shop_config: dict) -> tuple[Zeroconf, str]:
    local_ip = get_local_ip()
    hostname: str = shop_config["mdns_hostname"]
    shop_name: str = shop_config["shop_name"]

    zc = Zeroconf()
    info = ServiceInfo(
        QPRINT_SERVICE_TYPE,
        f"{hostname}.{QPRINT_SERVICE_TYPE}",
        addresses=[socket.inet_aton(local_ip)],
        port=PORT,
        server=f"{hostname}.local.",
        properties={
            b"shop_name": shop_name.encode(),
            b"path": b"/",
        },
    )
    zc.register_service(info)
    logger.info(
        f"mDNS registered: {hostname}.local → {local_ip}:{PORT} ('{shop_name}')"
    )
    return zc, hostname
