@echo off
setlocal EnableDelayedExpansion

echo.
echo [1mQ-Print ^| Checking Python[0m
echo.

set SCRIPT_DIR=%~dp0
set PYTHON=

:: ── locate Python ─────────────────────────────────────────────────────────────
for %%C in (python python3 py) do (
    where %%C >nul 2>&1
    if not errorlevel 1 (
        set PYTHON=%%C
        goto :version_check
    )
)

:: Python not found — attempt winget install
:try_install
echo   [33m![0m  Python not found. Attempting install via winget ...
winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo   [31mx[0m  Could not install Python automatically.
    echo        Download: https://www.python.org/downloads/
    exit /b 1
)

:: Refresh search after install
:: Note: winget updates the registry PATH, not the current process PATH.
:: If Python is still not found here, the user must open a new terminal.
for %%C in (python python3 py) do (
    where %%C >nul 2>&1
    if not errorlevel 1 (
        set PYTHON=%%C
        goto :version_check
    )
)

echo   [33m![0m  Python was installed but requires a new terminal to appear in PATH.
echo        Close this window, open a new Command Prompt, and run launch.bat again.
exit /b 0

:: ── version check ─────────────────────────────────────────────────────────────
:version_check
for /f "tokens=*" %%V in ('!PYTHON! -c "import sys; print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))"') do set PY_VER=%%V
for /f "tokens=1 delims=." %%A in ("!PY_VER!") do set PY_MAJOR=%%A
for /f "tokens=2 delims=." %%B in ("!PY_VER!") do set PY_MINOR=%%B

if !PY_MAJOR! LSS 3 goto :too_old
if !PY_MAJOR! EQU 3 if !PY_MINOR! LSS 12 goto :too_old
goto :ok_python

:too_old
echo   [31mx[0m  Python 3.12+ required, found !PY_VER!.
echo        Download: https://www.python.org/downloads/
exit /b 1

:ok_python
echo   [32mv[0m  Python !PY_VER!

:: ── hand off to launcher.py ───────────────────────────────────────────────────
!PYTHON! "%SCRIPT_DIR%launcher.py"
exit /b %errorlevel%
