#!/usr/bin/env python3
"""
Q-Print setup script.

Run once after cloning the repository:
    python setup.py

Safe to re-run — all steps are idempotent.
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT   = Path(__file__).resolve().parent
CLIENT = ROOT / "client"
SERVER = ROOT / "server"
VENV   = SERVER / ".venv"
IS_WIN = platform.system() == "Windows"

# Files created from their .example counterparts.
# Tuple: (source_example, destination)
EXAMPLE_FILES = [
    (CLIENT / "shop_config.example.json",  CLIENT / "shop_config.json"),
    (CLIENT / "cost.example.json",         CLIENT / "public" / "cost.json"),
]

REQUIRED_DIRS = [
    CLIENT / "data",
    CLIENT / "data" / "print_job_file_storage",
]

# ── Terminal output helpers ────────────────────────────────────────────────
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


# ── Requirement checks ─────────────────────────────────────────────────────

def check_python() -> None:
    v = sys.version_info
    if v < (3, 12):
        _fail(
            f"Python 3.12+ is required. Found {v.major}.{v.minor}.\n"
            f"     Download: https://www.python.org/downloads/"
        )
    _ok(f"Python {v.major}.{v.minor}.{v.micro}")


def check_node() -> None:
    try:
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        )
        ver = result.stdout.strip()
        major = int(ver.lstrip("v").split(".")[0])
        if major < 18:
            _fail(
                f"Node.js 18+ is required. Found {ver}.\n"
                f"     Download: https://nodejs.org/"
            )
        _ok(f"Node.js {ver}")
    except FileNotFoundError:
        _fail(
            "Node.js was not found in PATH.\n"
            "     Download: https://nodejs.org/"
        )


def check_npm() -> None:
    try:
        result = subprocess.run(
            ["npm", "--version"], capture_output=True, text=True, check=True
        )
        _ok(f"npm {result.stdout.strip()}")
    except FileNotFoundError:
        _fail("npm was not found. It is bundled with Node.js — reinstall Node.js.")


# ── Python virtual environment ─────────────────────────────────────────────

def setup_venv() -> None:
    if VENV.exists():
        _ok("Python venv already exists (server/.venv)")
        return
    _info("Creating virtual environment at server/.venv …")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV)], check=True
        )
        _ok("Virtual environment created")
    except subprocess.CalledProcessError as e:
        _fail(f"Failed to create venv: {e}")


def _pip() -> Path:
    return VENV / ("Scripts/pip.exe" if IS_WIN else "bin/pip")


def install_python_deps() -> None:
    req = SERVER / "requirements.txt"
    if not req.exists():
        _warn("server/requirements.txt not found — skipping Python deps")
        return
    _info("Installing Python dependencies …")
    try:
        subprocess.run(
            [str(_pip()), "install", "-r", str(req), "-q"],
            check=True,
        )
        _ok("Python dependencies installed")
    except subprocess.CalledProcessError as e:
        _fail(f"pip install failed: {e}")


def install_pywin32() -> None:
    """Install pywin32 on Windows — required for physical printing via win32print."""
    if not IS_WIN:
        return
    _info("Installing pywin32 (Windows printing support) …")
    try:
        subprocess.run(
            [str(_pip()), "install", "pywin32", "-q"],
            check=True,
        )
        _ok("pywin32 installed")
    except subprocess.CalledProcessError as e:
        _warn(f"pywin32 install failed: {e}\n     Printing will be unavailable until it is installed manually.")


# ── Node.js dependencies ───────────────────────────────────────────────────

def install_node_deps() -> None:
    if not (CLIENT / "package.json").exists():
        _warn("client/package.json not found — skipping npm install")
        return
    if (CLIENT / "node_modules").exists():
        _ok("node_modules already exists — skipping npm install")
        return
    _info("Running npm install in client/ …")
    try:
        subprocess.run(
            ["npm", "install", "--silent"],
            cwd=str(CLIENT),
            check=True,
        )
        _ok("Node.js dependencies installed")
    except subprocess.CalledProcessError as e:
        _fail(f"npm install failed: {e}")


# ── Config files ───────────────────────────────────────────────────────────

def copy_example_files() -> None:
    for src, dst in EXAMPLE_FILES:
        if not src.exists():
            _warn(f"Example file not found: {src.relative_to(ROOT)}")
            continue
        if dst.exists():
            _ok(f"{dst.relative_to(ROOT)} already exists — skipped")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            _ok(f"Created {dst.relative_to(ROOT)}")


# ── Runtime directories ────────────────────────────────────────────────────

def create_dirs() -> None:
    for d in REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)
    _ok(f"Runtime directories ready (client/data/)")


# ── Entry point ────────────────────────────────────────────────────────────

def main() -> None:
    print(f"\n{_BOLD}╔══════════════════════════════╗")
    print(f"║      Q-Print  Setup          ║")
    print(f"╚══════════════════════════════╝{_RESET}")

    _header("1 · Checking requirements")
    check_python()
    check_node()
    check_npm()

    _header("2 · Python environment")
    setup_venv()
    install_python_deps()
    install_pywin32()

    _header("3 · Node.js environment")
    install_node_deps()

    _header("4 · Configuration files")
    copy_example_files()

    _header("5 · Runtime directories")
    create_dirs()

    activate = (
        r"server\.venv\Scripts\activate"
        if IS_WIN
        else "source server/.venv/bin/activate"
    )

    print(f"\n{_BOLD}{_GREEN}✓  Setup complete!{_RESET}\n")
    print("Next steps:")
    print(f"  1. Activate the venv:  {activate}")
    print( "  2. Start the app:      python main.py")
    print( "  3. A dialog will prompt you to name this shop on first launch.")
    print(f"  4. Edit {_BOLD}client/shop_config.json{_RESET} to change identity at any time.\n")


if __name__ == "__main__":
    main()
