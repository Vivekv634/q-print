# server/utils/wifi_utils.py
"""Cross-platform WiFi SSID detection.

Detection order:
  1. pywifi  (cross-platform)
  2. nmcli   (Linux fallback)
  3. netsh   (Windows fallback)
  4. "Unknown network" if all fail
"""

import logging
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def get_ssid() -> str:
    """Return the connected WiFi SSID, or 'Unknown network' if detection fails."""
    ssid = _try_pywifi()
    if ssid:
        return ssid

    if sys.platform.startswith("linux"):
        ssid = _try_nmcli()
    elif sys.platform == "win32":
        ssid = _try_netsh()

    return ssid or "Unknown network"


def _try_pywifi() -> Optional[str]:
    try:
        import pywifi  # type: ignore
        wifi = pywifi.PyWiFi()
        ifaces = wifi.interfaces()
        if not ifaces:
            return None
        iface = ifaces[0]
        if iface.status() != pywifi.const.IFACE_CONNECTED:
            return None
        profiles = iface.network_profiles()
        if profiles:
            name = profiles[0].ssid
            if name:
                return name
    except Exception as exc:
        logger.debug("pywifi SSID detection failed: %s", exc)
    return None


def _try_nmcli() -> Optional[str]:
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        for line in result.stdout.splitlines():
            if line.startswith("yes:"):
                ssid = line.split(":", 1)[1].strip().replace("\\:", ":")
                if ssid:
                    return ssid
    except Exception as exc:
        logger.debug("nmcli SSID detection failed: %s", exc)
    return None


def _try_netsh() -> Optional[str]:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("SSID") and "BSSID" not in stripped:
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    ssid = parts[1].strip()
                    if ssid:
                        return ssid
    except Exception as exc:
        logger.debug("netsh SSID detection failed: %s", exc)
    return None
