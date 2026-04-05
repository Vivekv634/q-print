#!/usr/bin/env python3
"""
Q-Print cross-platform launcher.
Invoked by launch.bat / launch.sh after Python >= 3.12 is confirmed.

Sequence:
  1. Check Node.js >= 18  (auto-install via winget / brew / apt / dnf)
  2. Check npm
  3. Run setup.py        (idempotent: venv, pip deps, npm install, configs, dirs)
  4. Run pytest suite    via venv Python
  5. Launch main.py      via venv Python
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parent
IS_WIN = platform.system() == "Windows"

# Enable ANSI escape codes on Windows 10+ console
if IS_WIN:
    os.system("")

VENV_PYTHON: Path = (
    ROOT / "server" / ".venv" / "Scripts" / "python.exe"
    if IS_WIN
    else ROOT / "server" / ".venv" / "bin" / "python"
)

# ── colour helpers (same palette as setup.py) ──────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[32m"
_RED    = "\033[31m"
_CYAN   = "\033[36m"
_YELLOW = "\033[33m"


def _ok(msg: str)     -> None: print(f"  {_GREEN}✓{_RESET}  {msg}")
def _fail(msg: str)   -> None: print(f"  {_RED}✗{_RESET}  {msg}"); sys.exit(1)
def _info(msg: str)   -> None: print(f"  {_CYAN}→{_RESET}  {msg}")
def _warn(msg: str)   -> None: print(f"  {_YELLOW}!{_RESET}  {msg}")
def _header(msg: str) -> None: print(f"\n{_BOLD}{msg}{_RESET}")


# ── Node.js auto-install ────────────────────────────────────────────────────────

def _try_install_node() -> bool:
    """Attempt to install Node.js LTS via the OS package manager.
    Returns True if `node` is in PATH afterwards, False otherwise."""
    _info("Attempting to install Node.js automatically …")
    try:
        if IS_WIN:
            subprocess.run(
                ["winget", "install", "--id", "OpenJS.NodeJS.LTS",
                 "-e", "--silent", "--accept-package-agreements",
                 "--accept-source-agreements"],
                check=True,
            )
        elif platform.system() == "Darwin":
            subprocess.run(["brew", "install", "node"], check=True)
        else:
            # Linux: probe for available package managers in priority order
            if shutil.which("apt-get"):
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "nodejs", "npm"],
                    check=True,
                )
            elif shutil.which("dnf"):
                subprocess.run(
                    ["sudo", "dnf", "install", "-y", "nodejs", "npm"],
                    check=True,
                )
            elif shutil.which("pacman"):
                subprocess.run(
                    ["sudo", "pacman", "-S", "--noconfirm", "nodejs", "npm"],
                    check=True,
                )
            else:
                return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

    return shutil.which("node") is not None


# ── checks ─────────────────────────────────────────────────────────────────────

def check_node() -> None:
    if shutil.which("node") is None:
        _warn("Node.js not found in PATH.")
        if not _try_install_node():
            _fail(
                "Could not install Node.js automatically.\n"
                "     Download: https://nodejs.org/en/download"
            )
        # On Windows, winget updates the registry PATH but not the current process.
        # The install succeeded, but we can't use node until a new terminal is opened.
        if shutil.which("node") is None:
            print(
                f"\n  {_YELLOW}!{_RESET}  Node.js was installed but requires a new terminal to appear in PATH.\n"
                f"       Close this window and run the launcher again."
            )
            sys.exit(0)

    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        _fail("node not found in PATH — install Node.js 18+ from https://nodejs.org/en/download")

    try:
        ver = result.stdout.strip().lstrip("v")
        major = int(ver.split(".")[0])
    except (ValueError, IndexError):
        _fail(f"Could not parse Node.js version from: {result.stdout.strip()!r}")

    if major < 18:
        _fail(
            f"Node.js 18+ required, found v{ver}.\n"
            "     Download: https://nodejs.org/en/download"
        )
    _ok(f"Node.js v{ver}")


def check_npm() -> None:
    if shutil.which("npm") is None:
        _fail(
            "npm not found. It ships with Node.js — reinstall Node.js.\n"
            "     Download: https://nodejs.org/en/download"
        )
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        _fail("npm not found in PATH — reinstall Node.js from https://nodejs.org/en/download")
    _ok(f"npm {result.stdout.strip()}")


def run_setup() -> None:
    _info("Running setup.py (idempotent) …")
    subprocess.run(
        [sys.executable, str(ROOT / "setup.py")],
        check=True,
        cwd=str(ROOT),
    )


def run_tests() -> None:
    if not VENV_PYTHON.exists():
        _fail(
            f"Venv Python not found at {VENV_PYTHON}.\n"
            "     setup.py may have failed — check output above."
        )
    _info("Running package verification tests …")
    result = subprocess.run(
        [str(VENV_PYTHON), "-m", "pytest",
         "tests/test_verify_packages.py", "-v", "--tb=short"],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        _fail(
            "One or more verification tests failed.\n"
            "     Fix the issues shown above before starting the app."
        )
    _ok("All verification tests passed")


def launch_app() -> None:
    _info("Starting Q-Print …")
    # subprocess.run blocks until the Qt app exits — keeps the terminal live.
    result = subprocess.run(
        [str(VENV_PYTHON), str(ROOT / "main.py")],
        cwd=str(ROOT),
    )
    sys.exit(result.returncode)


# ── entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"\n{_BOLD}╔══════════════════════════════╗")
    print(f"║      Q-Print  Launcher       ║")
    print(f"╚══════════════════════════════╝{_RESET}")

    _header("1 · Checking Node.js")
    check_node()
    check_npm()

    _header("2 · Running setup")
    run_setup()

    _header("3 · Verifying packages")
    run_tests()

    _header("4 · Launching app")
    launch_app()


if __name__ == "__main__":
    main()
