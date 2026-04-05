"""
Package and environment verification tests for Q-Print.
Run via:  pytest tests/test_verify_packages.py -v
"""

import importlib.metadata
import subprocess
import sys
import platform
from pathlib import Path

import pytest

ROOT   = Path(__file__).resolve().parent.parent
CLIENT = ROOT / "client"
SERVER = ROOT / "server"
IS_WIN = platform.system() == "Windows"


class TestSystemRequirements:
    """Verify Python, Node.js, and npm are present and meet minimum versions."""

    def test_python_version(self):
        v = sys.version_info
        assert (v.major, v.minor) >= (3, 12), (
            f"Python 3.12+ required, found {v.major}.{v.minor}"
        )

    def test_node_in_path(self):
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True
            )
        except FileNotFoundError:
            pytest.fail("node not found in PATH — install Node.js 18+ from https://nodejs.org")
        assert result.returncode == 0, f"node exited {result.returncode}: {result.stderr.strip()}"
        ver = result.stdout.strip().lstrip("v")
        major = int(ver.split(".")[0])
        assert major >= 18, f"Node.js 18+ required, found v{ver}"

    def test_npm_in_path(self):
        try:
            result = subprocess.run(
                ["npm", "--version"], capture_output=True, text=True
            )
        except FileNotFoundError:
            pytest.fail("npm not found in PATH — reinstall Node.js from https://nodejs.org")
        assert result.returncode == 0, f"npm exited {result.returncode}: {result.stderr.strip()}"


class TestPythonPackages:
    """Import every package from requirements.txt and spot-check a key attribute."""

    def test_zeroconf(self):
        import zeroconf
        assert hasattr(zeroconf, "Zeroconf")

    def test_anyio(self):
        import anyio  # noqa: F401
        assert importlib.metadata.version("anyio")

    def test_idna(self):
        import idna
        assert idna.__version__

    def test_netifaces(self):
        import netifaces
        assert hasattr(netifaces, "interfaces")

    def test_psutil(self):
        import psutil
        assert psutil.__version__

    def test_watchdog(self):
        from watchdog.observers import Observer  # noqa: F401

    def test_watchfiles(self):
        import watchfiles
        assert watchfiles.__version__

    def test_pyside6_qtwidgets(self):
        from PySide6.QtWidgets import QApplication  # noqa: F401

    def test_pyside6_qtcore(self):
        from PySide6.QtCore import QTimer  # noqa: F401

    def test_pymupdf(self):
        import fitz
        assert fitz.__version__

    def test_pillow(self):
        from PIL import Image  # noqa: F401

    def test_pytest_installed(self):
        import pytest as _pytest
        assert _pytest.__version__

    @pytest.mark.skipif(not IS_WIN, reason="pywin32 is Windows-only")
    def test_pywin32(self):
        import win32print
        assert hasattr(win32print, "OpenPrinter")


_REQUIRED_NODE_PACKAGES = [
    "next",
    "react",
    "react-dom",
    "zod",
    "pdf-lib",
    "sonner",
    "lucide-react",
    "tailwindcss",
]


class TestNodePackages:
    """Verify key Node packages exist inside client/node_modules."""

    def test_node_modules_exists(self):
        assert (CLIENT / "node_modules").is_dir(), (
            "client/node_modules not found — run: cd client && npm install"
        )

    @pytest.mark.parametrize("package", _REQUIRED_NODE_PACKAGES)
    def test_node_package_installed(self, package):
        pkg_dir = CLIENT / "node_modules" / package
        assert pkg_dir.is_dir(), (
            f"Node package '{package}' missing from node_modules"
        )


class TestProjectConfig:
    """Verify runtime files and directories created by setup.py exist."""

    def test_shop_config_exists(self):
        assert (CLIENT / "shop_config.json").exists(), (
            "client/shop_config.json missing — run: python setup.py"
        )

    def test_cost_json_exists(self):
        assert (CLIENT / "public" / "cost.json").exists(), (
            "client/public/cost.json missing — run: python setup.py"
        )

    def test_data_dir_exists(self):
        assert (CLIENT / "data").is_dir(), (
            "client/data/ missing — run: python setup.py"
        )

    def test_file_storage_dir_exists(self):
        assert (CLIENT / "data" / "print_job_file_storage").is_dir(), (
            "client/data/print_job_file_storage/ missing — run: python setup.py"
        )

    def test_requirements_txt_exists(self):
        assert (SERVER / "requirements.txt").exists(), (
            "server/requirements.txt not found"
        )

    def test_package_json_exists(self):
        assert (CLIENT / "package.json").exists(), (
            "client/package.json not found"
        )
