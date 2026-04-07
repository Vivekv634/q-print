import importlib
import json
import os
from unittest.mock import patch

import pytest


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr("server.utils.constants.DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr("server.utils.constants.FILE_STORAGE_PATH", str(tmp_path / "storage"))
    os.makedirs(str(tmp_path / "storage"))
    import server.src.database as database
    importlib.reload(database)
    database.init_db()
    return database


@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "shop_config.json"
    path.write_text(json.dumps({
        "shop_name": "Test Shop",
        "mdns_hostname": "qprint-test",
        "college_name": "Test University",
        "analytics_shop_id": "shop-uuid-1234",
        "analytics_api_key": "secret-key-abc",
    }))
    return str(path)


def test_sync_skipped_when_no_url(db, config_file, monkeypatch):
    monkeypatch.setattr("server.utils.constants.ANALYTICS_CLOUD_URL", "")
    monkeypatch.setattr("server.utils.constants.SHOP_CONFIG_PATH", config_file)
    import server.src.analytics_sync as sync_mod
    importlib.reload(sync_mod)

    called = []
    with patch.object(sync_mod, "_sync_worker", side_effect=lambda c: called.append(True)):
        sync_mod.run_sync()
    assert called == []


def test_sync_once_posts_pending_dates(db, config_file, monkeypatch, tmp_path):
    monkeypatch.setattr("server.utils.constants.ANALYTICS_CLOUD_URL", "http://fake-cloud")
    monkeypatch.setattr("server.utils.constants.SHOP_CONFIG_PATH", config_file)
    monkeypatch.setattr("server.utils.constants.DB_PATH", str(tmp_path / "test.db"))
    import server.src.analytics_sync as sync_mod
    importlib.reload(sync_mod)

    # Insert a pending analytics event so get_pending_sync_dates returns something
    db.insert_analytics_event("completed", "job1234567x", 1, 0, 2, 3.0, 10, "2026-04-07")

    captured = {}

    class FakeResponse:
        def read(self): return json.dumps({"synced": 1, "dates": ["2026-04-07"]}).encode()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data)
        captured["auth"] = req.get_header("Authorization")
        return FakeResponse()

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = sync_mod._sync_once("shop-uuid-1234", "secret-key-abc")

    assert result is True
    assert captured["url"] == "http://fake-cloud/api/analytics/sync"
    assert captured["auth"] == "Bearer secret-key-abc"
    assert captured["body"]["shop_id"] == "shop-uuid-1234"
    assert len(captured["body"]["days"]) == 1
    assert captured["body"]["days"][0]["date"] == "2026-04-07"
    assert db.get_pending_sync_dates() == []


def test_sync_once_returns_false_on_network_error(db, monkeypatch, tmp_path):
    monkeypatch.setattr("server.utils.constants.DB_PATH", str(tmp_path / "test.db"))
    import server.src.analytics_sync as sync_mod
    importlib.reload(sync_mod)

    db.insert_analytics_event("completed", "job1234567x", 1, 0, 2, 3.0, 10, "2026-04-07")

    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no route")):
        result = sync_mod._sync_once("shop-id", "key")

    assert result is False
    # Dates remain pending after failure
    assert "2026-04-07" in db.get_pending_sync_dates()


def test_sync_once_skips_when_no_pending_dates(db, monkeypatch, tmp_path):
    monkeypatch.setattr("server.utils.constants.DB_PATH", str(tmp_path / "test.db"))
    import server.src.analytics_sync as sync_mod
    importlib.reload(sync_mod)

    called = []
    with patch("urllib.request.urlopen", side_effect=lambda *a, **kw: called.append(True)):
        result = sync_mod._sync_once("shop-id", "key")

    assert result is True
    assert called == []
