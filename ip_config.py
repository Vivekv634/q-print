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
    return (
        shop_config.get("shop_name", SETUP_SENTINEL) == SETUP_SENTINEL
        or shop_config.get("college_name", SETUP_SENTINEL) == SETUP_SENTINEL
    )


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


def _build_service_info(hostname: str, shop_name: str, local_ip: str) -> ServiceInfo:
    return ServiceInfo(
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


def register_mdns(shop_config: dict) -> tuple[Zeroconf, str, ServiceInfo]:
    local_ip = get_local_ip()
    hostname: str = shop_config["mdns_hostname"]
    shop_name: str = shop_config["shop_name"]

    zc = Zeroconf()
    info = _build_service_info(hostname, shop_name, local_ip)
    zc.register_service(info)
    logger.info(
        f"mDNS registered: {hostname}.local → {local_ip}:{PORT} ('{shop_name}')"
    )
    return zc, hostname, info


def reregister_mdns(zc: Zeroconf, old_info: ServiceInfo, new_config: dict) -> tuple[ServiceInfo, str]:
    """Unregister old service, register with new hostname/name. Returns (new_info, new_hostname)."""
    try:
        zc.unregister_service(old_info)
    except Exception as exc:
        logger.warning(f"Failed to unregister old mDNS service: {exc}")

    local_ip = get_local_ip()
    new_hostname: str = new_config["mdns_hostname"]
    new_name: str = new_config["shop_name"]
    new_info = _build_service_info(new_hostname, new_name, local_ip)
    zc.register_service(new_info)
    logger.info(
        f"mDNS re-registered: {new_hostname}.local → {local_ip}:{PORT} ('{new_name}')"
    )
    return new_info, new_hostname
