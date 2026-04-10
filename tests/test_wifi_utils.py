# tests/test_wifi_utils.py
from unittest.mock import patch, MagicMock
from server.utils.wifi_utils import get_ssid, _try_nmcli, _try_netsh


def test_get_ssid_returns_string():
    result = get_ssid()
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_ssid_falls_back_to_unknown_when_all_fail():
    with (
        patch("server.utils.wifi_utils._try_pywifi", return_value=None),
        patch("server.utils.wifi_utils._try_nmcli", return_value=None),
        patch("server.utils.wifi_utils._try_netsh", return_value=None),
        patch("server.utils.wifi_utils.sys") as mock_sys,
    ):
        mock_sys.platform = "linux"
        result = get_ssid()
    assert result == "Unknown network"


def test_try_nmcli_parses_active_ssid():
    mock_output = "no:OtherNet\nyes:MyHomeWiFi\nno:AnotherNet"
    with patch("server.utils.wifi_utils.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
        result = _try_nmcli()
    assert result == "MyHomeWiFi"


def test_try_nmcli_unescapes_colons_in_ssid():
    mock_output = "yes:Campus\\:Net"
    with patch("server.utils.wifi_utils.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
        result = _try_nmcli()
    assert result == "Campus:Net"


def test_try_nmcli_returns_none_when_no_active():
    mock_output = "no:OtherNet\nno:AnotherNet"
    with patch("server.utils.wifi_utils.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
        result = _try_nmcli()
    assert result is None


def test_try_netsh_parses_ssid():
    mock_output = (
        "   SSID                   : CampusNet\n"
        "   BSSID                  : aa:bb:cc:dd:ee:ff\n"
    )
    with patch("server.utils.wifi_utils.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
        result = _try_netsh()
    assert result == "CampusNet"


def test_try_nmcli_returns_none_on_exception():
    with patch("server.utils.wifi_utils.subprocess.run", side_effect=FileNotFoundError):
        result = _try_nmcli()
    assert result is None


def test_get_ssid_falls_back_to_unknown_on_windows():
    with (
        patch("server.utils.wifi_utils._try_pywifi", return_value=None),
        patch("server.utils.wifi_utils._try_nmcli", return_value=None),
        patch("server.utils.wifi_utils._try_netsh", return_value=None),
        patch("server.utils.wifi_utils.sys") as mock_sys,
    ):
        mock_sys.platform = "win32"
        result = get_ssid()
    assert result == "Unknown network"
