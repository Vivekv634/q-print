import netifaces
import json
from server.utils.constants import IP_FILE_PATH
import logging

logger = logging.getLogger(__name__)


def get_local_ip() -> str:
    for interface in netifaces.interfaces():
        # Skip loopback
        if interface == "lo":
            continue

        addrs = netifaces.ifaddresses(interface)

        # AF_INET = IPv4
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                ip = addr["addr"]
                if not ip.startswith("127."):
                    return ip
    return "127.0.0.1"  # fallback


def set_ip_config():
    local_ip = get_local_ip()

    with open(IP_FILE_PATH, "w") as f:
        json.dump({"ip_address": local_ip}, f)

    logger.info("IP address configured and saved in ip.json file")
