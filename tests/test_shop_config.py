"""
Tests for shop config loading, sentinel detection, and hostname generation.
"""

import json
import pytest
from pathlib import Path

from ip_config import (
    generate_hostname,
    is_setup_required,
    load_shop_config,
    SETUP_SENTINEL,
)


# ── generate_hostname ─────────────────────────────────────────────────────────

class TestGenerateHostname:
    def test_basic_two_word_name(self):
        assert generate_hostname("Library Shop") == "qprint-library-shop"

    def test_single_word(self):
        assert generate_hostname("main") == "qprint-main"

    def test_uppercased_name(self):
        assert generate_hostname("CSB Block") == "qprint-csb-block"

    def test_special_characters_replaced_with_hyphen(self):
        assert generate_hostname("Shop #1 (North)") == "qprint-shop-1-north"

    def test_consecutive_specials_produce_single_hyphen(self):
        # "A  &  B" → "a-b" slug → "qprint-a-b"
        assert generate_hostname("A  &  B") == "qprint-a-b"

    def test_empty_string_returns_fallback(self):
        assert generate_hostname("") == "qprint-shop"

    def test_only_special_chars_returns_fallback(self):
        assert generate_hostname("!!!###") == "qprint-shop"

    def test_long_name_slug_is_truncated_to_30_chars(self):
        long_name = "A" * 40
        result = generate_hostname(long_name)
        # prefix is "qprint-" (7 chars) + slug max 30
        assert len(result) <= 7 + 30

    def test_result_always_starts_with_qprint_prefix(self):
        for name in ["shop", "My Shop", "x" * 50, "123"]:
            assert generate_hostname(name).startswith("qprint-")

    def test_result_contains_no_uppercase(self):
        assert generate_hostname("UPPER CASE SHOP") == generate_hostname("upper case shop")


# ── is_setup_required ─────────────────────────────────────────────────────────

class TestIsSetupRequired:
    def test_returns_true_for_sentinel(self):
        assert is_setup_required({"shop_name": SETUP_SENTINEL}) is True

    def test_returns_false_for_real_name(self):
        assert is_setup_required({"shop_name": "Library Shop"}) is False

    def test_returns_false_for_empty_string(self):
        # Empty string is not the sentinel — it's a different (also invalid) state
        assert is_setup_required({"shop_name": ""}) is False

    def test_returns_true_when_key_missing(self):
        # Missing key means config is broken — treat as setup required
        assert is_setup_required({}) is True

    def test_hostname_sentinel_does_not_affect_result(self):
        # Only shop_name drives the check
        cfg = {"shop_name": "Real Shop", "mdns_hostname": SETUP_SENTINEL}
        assert is_setup_required(cfg) is False


# ── load_shop_config ──────────────────────────────────────────────────────────

class TestLoadShopConfig:
    def test_reads_valid_config(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "shop_config.json"
        cfg_file.write_text(json.dumps({
            "shop_name": "Library Shop",
            "mdns_hostname": "qprint-library",
        }))
        monkeypatch.setattr("ip_config.SHOP_CONFIG_PATH", str(cfg_file))
        result = load_shop_config()
        assert result["shop_name"] == "Library Shop"
        assert result["mdns_hostname"] == "qprint-library"

    def test_returns_sentinel_defaults_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ip_config.SHOP_CONFIG_PATH", str(tmp_path / "nonexistent.json"))
        result = load_shop_config()
        assert result["shop_name"] == SETUP_SENTINEL

    def test_returns_sentinel_defaults_on_invalid_json(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "shop_config.json"
        cfg_file.write_text("not json {{")
        monkeypatch.setattr("ip_config.SHOP_CONFIG_PATH", str(cfg_file))
        result = load_shop_config()
        assert result["shop_name"] == SETUP_SENTINEL

    def test_preserves_extra_keys(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "shop_config.json"
        cfg_file.write_text(json.dumps({
            "shop_name": "Shop A",
            "mdns_hostname": "qprint-a",
            "extra_key": "extra_value",
        }))
        monkeypatch.setattr("ip_config.SHOP_CONFIG_PATH", str(cfg_file))
        result = load_shop_config()
        assert result.get("extra_key") == "extra_value"


# ── SetupDialog._save integration (file-write only, no Qt) ───────────────────

class TestSetupDialogFilePersistence:
    """
    Directly exercise the file-write logic without instantiating the Qt dialog.
    """

    def _write_config(self, path: str, name: str, host: str) -> None:
        with open(path, "w") as f:
            json.dump({"shop_name": name, "mdns_hostname": host}, f, indent=2)

    def test_written_config_is_readable_by_load_shop_config(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "shop_config.json"
        monkeypatch.setattr("ip_config.SHOP_CONFIG_PATH", str(cfg_file))
        self._write_config(str(cfg_file), "CSB Shop", "qprint-csb")
        result = load_shop_config()
        assert result["shop_name"] == "CSB Shop"
        assert result["mdns_hostname"] == "qprint-csb"

    def test_is_setup_required_false_after_save(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "shop_config.json"
        monkeypatch.setattr("ip_config.SHOP_CONFIG_PATH", str(cfg_file))
        self._write_config(str(cfg_file), "Main Shop", "qprint-main")
        assert is_setup_required(load_shop_config()) is False

    def test_overwrite_sentinel_with_real_config(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "shop_config.json"
        # Start with sentinel
        cfg_file.write_text(json.dumps({
            "shop_name": SETUP_SENTINEL,
            "mdns_hostname": SETUP_SENTINEL,
        }))
        monkeypatch.setattr("ip_config.SHOP_CONFIG_PATH", str(cfg_file))
        assert is_setup_required(load_shop_config()) is True
        # Simulate dialog save
        self._write_config(str(cfg_file), "New Shop", "qprint-new")
        assert is_setup_required(load_shop_config()) is False
