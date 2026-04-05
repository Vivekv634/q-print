#!/usr/bin/env bash
# Q-Print launcher for macOS and Linux.
# Single job: ensure Python >= 3.12 is available, then hand off to launcher.py.

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
RED="\033[31m"
CYAN="\033[36m"
YELLOW="\033[33m"
RESET="\033[0m"

ok()     { echo -e "  ${GREEN}✓${RESET}  $*"; }
fail()   { echo -e "  ${RED}✗${RESET}  $*" >&2; exit 1; }
info()   { echo -e "  ${CYAN}→${RESET}  $*"; }
warn()   { echo -e "  ${YELLOW}!${RESET}  $*"; }
header() { echo -e "\n${BOLD}$*${RESET}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── locate Python ──────────────────────────────────────────────────────────────
PYTHON=""
for candidate in python3 python python3.13 python3.12; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

try_install_python() {
    warn "Python 3.12+ not found. Attempting auto-install …"
    if [[ "$(uname)" == "Darwin" ]]; then
        if command -v brew &>/dev/null; then
            brew install python@3.12 || return 1
        else
            return 1
        fi
    else
        # Linux: probe for package managers in priority order
        if command -v apt-get &>/dev/null; then
            sudo apt-get install -y python3 python3-venv python3-pip || return 1
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y python3 python3-pip || return 1
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm python || return 1
        else
            return 1
        fi
    fi
    # Refresh PYTHON after install
    for candidate in python3 python python3.13 python3.12; do
        if command -v "$candidate" &>/dev/null; then
            PYTHON="$candidate"
            return 0
        fi
    done
    return 1
}

header "Q-Print · Checking Python"

if [[ -z "$PYTHON" ]]; then
    if ! try_install_python; then
        fail "Could not install Python automatically.\n     Download: https://www.python.org/downloads/"
    fi
    # Guard: install succeeded but PATH not yet updated in this shell session
    if [[ -z "$PYTHON" ]]; then
        fail "Python was installed but is not yet in PATH.\n     Please open a new terminal and run launch.sh again."
    fi
fi

# ── version check ──────────────────────────────────────────────────────────────
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 12 ]]; }; then
    fail "Python 3.12+ required, found $PY_VER.\n     Download: https://www.python.org/downloads/"
fi

ok "Python $PY_VER"

# ── hand off ───────────────────────────────────────────────────────────────────
exec "$PYTHON" "$SCRIPT_DIR/launcher.py"
