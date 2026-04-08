import json
import logging
import threading
import time
import urllib.request
import urllib.error
from typing import Any

from server.src import database as db
from server.utils.constants import ANALYTICS_CLOUD_URL, SHOP_CONFIG_PATH

logger = logging.getLogger(__name__)

_RETRY_INTERVAL = 300  # 5 minutes


def run_sync() -> None:
    """Called from main.py after the API server is up. Non-blocking."""
    if not ANALYTICS_CLOUD_URL:
        logger.info("ANALYTICS_CLOUD_URL not set — skipping analytics sync.")
        return
    config = _load_config()
    threading.Thread(target=_sync_worker, args=(config,), daemon=True).start()


def _load_config() -> dict[str, Any]:
    try:
        with open(SHOP_CONFIG_PATH) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"analytics_sync: failed to load shop_config.json: {e}")
        return {}


def _save_credentials(config: dict[str, Any], shop_id: str, api_key: str) -> None:
    config["analytics_shop_id"] = shop_id
    config["analytics_api_key"] = api_key
    try:
        with open(SHOP_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Analytics credentials saved (shop_id={shop_id})")
    except Exception as e:
        logger.error(f"analytics_sync: failed to save credentials: {e}")


def _register_shop(config: dict[str, Any]) -> dict[str, Any] | None:
    payload = json.dumps({
        "shop_name":    config.get("shop_name", ""),
        "hostname":     config.get("mdns_hostname", ""),
        "college_name": config.get("college_name", ""),
    }).encode()
    try:
        req = urllib.request.Request(
            f"{ANALYTICS_CLOUD_URL}/api/shops/register",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.warning(f"analytics_sync: shop registration failed: {e}")
        return None


def _sync_once(shop_id: str, api_key: str) -> bool:
    """Aggregate and push all pending dates. Returns True on success (or nothing pending)."""
    dates = db.get_pending_sync_dates()
    if not dates:
        return True

    try:
        days = [db.aggregate_day_analytics(d) for d in dates]
        payload = json.dumps({"shop_id": shop_id, "days": days}).encode()
        req = urllib.request.Request(
            f"{ANALYTICS_CLOUD_URL}/api/analytics/sync",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            synced = result.get("dates", dates)
            db.mark_dates_synced(synced)
            logger.info(f"Analytics synced: {len(synced)} day(s) → {synced}")
            return True
    except Exception as e:
        logger.warning(f"analytics_sync: sync failed: {e}")
        return False


def _sync_worker(config: dict[str, Any]) -> None:
    """Runs in a daemon thread. Handles first-run registration + initial sync + retry."""
    shop_id: str = config.get("analytics_shop_id", "")
    api_key: str = config.get("analytics_api_key", "")

    while True:
        if not shop_id:
            result = _register_shop(config)
            if not result:
                time.sleep(_RETRY_INTERVAL)
                continue
            shop_id = result["shop_id"]
            api_key = result["api_key"]
            _save_credentials(config, shop_id, api_key)

        if _sync_once(shop_id, api_key):
            return  # all pending dates pushed — done

        time.sleep(_RETRY_INTERVAL)
