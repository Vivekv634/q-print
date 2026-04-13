"""Cross-platform printer management for Q-Print.

On Windows: uses win32print / PyMuPDF / Pillow (existing behaviour).
On Linux / macOS: uses CUPS via the `lp` / `lpstat` / `lpinfo` CLI tools
                  and sends the PDF file directly (CUPS handles rendering).
"""

import logging
import os
import platform
import shutil
import subprocess
from typing import Any, Optional

logger = logging.getLogger(__name__)

_SYSTEM = platform.system()

# ── Windows imports ────────────────────────────────────────────────────────────
_WIN_AVAILABLE = False
if _SYSTEM == "Windows":
    try:
        import win32print
        import win32ui
        import win32con
        from PIL import Image, ImageWin
        import fitz
        _WIN_AVAILABLE = True
    except ImportError:
        logger.warning(
            "Windows printing libraries unavailable (win32print / PyMuPDF / Pillow). "
            "Printing disabled on this Windows install."
        )

# ── CUPS availability check (shutil.which — no subprocess at import time) ──────
_CUPS_AVAILABLE = False
if _SYSTEM in ("Linux", "Darwin"):
    _CUPS_AVAILABLE = shutil.which("lp") is not None and shutil.which("lpstat") is not None
    if not _CUPS_AVAILABLE:
        logger.warning(
            "CUPS tools (lp / lpstat) not found. Install CUPS:\n"
            "  Linux:  sudo apt install cups  (or dnf/pacman equivalent)\n"
            "  macOS:  pre-installed — check System Settings → Printers"
        )

# Windows status flag descriptions
PRINTER_STATUS_FLAGS: dict[int, str] = {
    0x00000001: "Paused",           0x00000002: "Error",
    0x00000008: "Pending Deletion", 0x00000010: "Paper Jam",
    0x00000020: "Paper Out",        0x00000040: "Manual Feed",
    0x00000080: "Paper Problem",    0x00000100: "Offline",
    0x00000200: "IO Active",        0x00000400: "Busy",
    0x00000800: "Printing",         0x00001000: "Output Bin Full",
    0x00002000: "Not Available",    0x00004000: "Waiting",
    0x00008000: "Processing",       0x00010000: "Initializing",
    0x00020000: "Warming Up",       0x00040000: "Toner/Ink Low",
    0x00080000: "No Toner/Ink",     0x00200000: "Page Punt",
    0x00400000: "User Intervention Required",
    0x00800000: "Out of Memory",    0x01000000: "Door Open",
}

# lp paper size option values
PAPER_SIZE_MAP: dict[str, str] = {
    "a0": "ISOA0", "a1": "ISOA1", "a2": "ISOA2",
    "a3": "ISOA3", "a4": "ISOA4", "a5": "ISOA5",
    "letter": "Letter", "legal": "Legal", "tabloid": "Tabloid",
}


# ── Windows implementation ─────────────────────────────────────────────────────

class _WindowsPrinterManager:
    def get_printers(self) -> list[str]:
        printers: list[Any] = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        return [p[2] for p in printers]

    def get_printer_status(self, printer_name: str) -> dict[str, Any]:
        try:
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                info: dict[str, Any] = win32print.GetPrinter(hprinter, 2)
                flags: list[str] = [
                    label
                    for flag, label in PRINTER_STATUS_FLAGS.items()
                    if info["Status"] & flag
                ]
                status_str: str = ", ".join(flags) if flags else "Ready"
                return {"name": printer_name, "status": status_str, "jobs": info["cJobs"]}
            finally:
                win32print.ClosePrinter(hprinter)
        except Exception as e:
            logger.error(f"Printer status error for '{printer_name}': {e}")
            return {"name": printer_name, "status": "Error", "jobs": 0}

    def print_job(
        self,
        job: dict[str, Any],
        printer_name: str,
        file_storage_path: str,
    ) -> bool:
        all_ok = True
        for filedata in job.get("filedataArray", []):
            if not isinstance(filedata, dict):
                all_ok = False
                continue
            stored = _find_stored_file(
                file_storage_path,
                filedata.get("_file_id", ""),
                filedata.get("file_name", ""),
            )
            if not stored:
                logger.error(
                    f"File not found: {filedata.get('_file_id')}_{filedata.get('file_name')}"
                )
                all_ok = False
                continue
            try:
                self._print_pdf(
                    file_path=stored,
                    printer_name=printer_name,
                    copies=int(filedata.get("no_of_copies", 1)),
                    color=filedata.get("color_mode") == "color",
                    landscape=filedata.get("layout") == "landscape",
                    paper_size=str(filedata.get("paper_size", "a4")),
                )
                logger.info(f"Printed: {stored} → {printer_name}")
            except Exception as e:
                logger.error(f"Print failed for {stored}: {e}")
                all_ok = False
        return all_ok

    def _print_pdf(
        self,
        file_path: str,
        printer_name: str,
        copies: int,
        color: bool,
        landscape: bool,
        paper_size: str,
    ) -> None:
        doc = fitz.open(file_path)
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        try:
            dpi_x: int = hdc.GetDeviceCaps(win32con.LOGPIXELSX)
            printable_w: int = hdc.GetDeviceCaps(win32con.HORZRES)
            printable_h: int = hdc.GetDeviceCaps(win32con.VERTRES)
            hdc.StartDoc(os.path.basename(file_path))
            for _ in range(copies):
                for page in doc:
                    zoom: float = dpi_x / 72.0
                    mat = fitz.Matrix(zoom, zoom)
                    colorspace = fitz.csRGB if color else fitz.csGRAY
                    pix = page.get_pixmap(matrix=mat, colorspace=colorspace, alpha=False)
                    img = Image.frombytes(
                        "RGB" if color else "L",
                        (pix.width, pix.height),
                        pix.samples,
                    ).convert("RGB")
                    if landscape:
                        img = img.rotate(90, expand=True)
                    scale: float = min(printable_w / img.width, printable_h / img.height)
                    if scale != 1.0:
                        img = img.resize(
                            (int(img.width * scale), int(img.height * scale)),
                            Image.LANCZOS,
                        )
                    hdc.StartPage()
                    dib = ImageWin.Dib(img)
                    dib.draw(hdc.GetHandleAttrib(), (0, 0, img.width, img.height))
                    hdc.EndPage()
            hdc.EndDoc()
        finally:
            hdc.DeleteDC()
            doc.close()


# ── CUPS implementation (Linux / macOS) ────────────────────────────────────────

class _CupsPrinterManager:
    def get_printers(self) -> list[str]:
        """Return names of all CUPS-configured printers."""
        try:
            result = subprocess.run(
                ["lpstat", "-a"],
                capture_output=True, text=True, timeout=5,
            )
            printers: list[str] = []
            for line in result.stdout.splitlines():
                # "HP_LaserJet accepting requests since …"
                name = line.split()[0] if line.strip() else ""
                if name:
                    printers.append(name)
            return printers
        except Exception as e:
            logger.error(f"lpstat -a failed: {e}")
            return []

    def get_printer_status(self, printer_name: str) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["lpstat", "-p", printer_name],
                capture_output=True, text=True, timeout=5,
            )
            output = result.stdout.strip()
            # Count pending jobs
            jobs_result = subprocess.run(
                ["lpstat", "-o", printer_name],
                capture_output=True, text=True, timeout=5,
            )
            job_count = len([l for l in jobs_result.stdout.splitlines() if l.strip()])

            if "disabled" in output.lower():
                status = "Disabled"
            elif "idle" in output.lower():
                status = "Ready"
            elif "processing" in output.lower():
                status = "Printing"
            elif result.returncode != 0:
                status = "Unavailable"
            else:
                status = "Ready"

            return {"name": printer_name, "status": status, "jobs": job_count}
        except Exception as e:
            logger.error(f"Printer status error for '{printer_name}': {e}")
            return {"name": printer_name, "status": "Error", "jobs": 0}

    def print_job(
        self,
        job: dict[str, Any],
        printer_name: str,
        file_storage_path: str,
    ) -> bool:
        all_ok = True
        for filedata in job.get("filedataArray", []):
            if not isinstance(filedata, dict):
                all_ok = False
                continue
            stored = _find_stored_file(
                file_storage_path,
                filedata.get("_file_id", ""),
                filedata.get("file_name", ""),
            )
            if not stored:
                logger.error(
                    f"File not found: {filedata.get('_file_id')}_{filedata.get('file_name')}"
                )
                all_ok = False
                continue
            try:
                self._lp_print(
                    file_path=stored,
                    printer_name=printer_name,
                    copies=int(filedata.get("no_of_copies", 1)),
                    color=filedata.get("color_mode") == "color",
                    landscape=filedata.get("layout") == "landscape",
                    paper_size=str(filedata.get("paper_size", "a4")),
                )
                logger.info(f"Sent to CUPS: {stored} → {printer_name}")
            except Exception as e:
                logger.error(f"CUPS print failed for {stored}: {e}")
                all_ok = False
        return all_ok

    def _lp_print(
        self,
        file_path: str,
        printer_name: str,
        copies: int,
        color: bool,
        landscape: bool,
        paper_size: str,
    ) -> None:
        cmd = ["lp", "-d", printer_name, "-n", str(copies)]

        # Color mode
        if not color:
            cmd += ["-o", "print-color-mode=monochrome"]

        # Orientation
        if landscape:
            cmd += ["-o", "landscape"]

        # Paper size
        cups_paper = PAPER_SIZE_MAP.get(paper_size.lower(), "ISOA4")
        cmd += ["-o", f"media={cups_paper}"]

        cmd.append(file_path)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"lp returned {result.returncode}: {result.stderr.strip()}")


# ── Null implementation (printing unavailable) ─────────────────────────────────

class _NullPrinterManager:
    def get_printers(self) -> list[str]:
        return []

    def get_printer_status(self, printer_name: str) -> dict[str, Any]:
        return {"name": printer_name, "status": "Unavailable", "jobs": 0}

    def print_job(self, job: dict[str, Any], printer_name: str, file_storage_path: str) -> bool:
        logger.error("Printing unavailable on this system.")
        return False


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _find_stored_file(storage_path: str, file_id: str, file_name: str) -> Optional[str]:
    if not os.path.exists(storage_path) or not file_id or not file_name:
        return None
    for fname in os.listdir(storage_path):
        if file_id in fname and file_name in fname:
            return os.path.join(storage_path, fname)
    return None


# ── Public facade ──────────────────────────────────────────────────────────────

class PrinterManager:
    """Platform-transparent printer manager.

    Delegates to the appropriate backend:
      Windows          → win32print / PyMuPDF / Pillow
      Linux / macOS   → CUPS (lp / lpstat CLI)
      anything else   → no-op (logs errors)

    The status cache (`_status_cache`) is populated by PrinterPanel's background
    worker after every successful poll so that QuickPrintMenu can build its menu
    without making any subprocess calls on the Qt main thread.
    """

    def __init__(self) -> None:
        # Last-known printer statuses — populated by PrinterPanel's background thread.
        # Access is safe from the Qt main thread only (written and read on the same thread).
        self._status_cache: list[dict[str, Any]] = []

        if _SYSTEM == "Windows" and _WIN_AVAILABLE:
            self._impl: Any = _WindowsPrinterManager()
            logger.info("PrinterManager: using Windows (win32print) backend")
        elif _SYSTEM in ("Linux", "Darwin") and _CUPS_AVAILABLE:
            self._impl = _CupsPrinterManager()
            logger.info("PrinterManager: using CUPS backend")
        else:
            self._impl = _NullPrinterManager()
            logger.warning(
                f"PrinterManager: no printing backend available on {_SYSTEM}. "
                "Install CUPS (Linux/macOS) or win32print (Windows)."
            )

    # ── Cache helpers (main-thread only) ────────────────────────────────────────

    def update_status_cache(self, results: list[dict[str, Any]]) -> None:
        """Store the latest printer status snapshot.  Called from PrinterPanel's
        signal handler (Qt main thread) after every background poll."""
        self._status_cache = list(results)

    def get_cached_status(self) -> list[dict[str, Any]]:
        """Return the last-known printer status list without any I/O."""
        return list(self._status_cache)

    # ── Backend delegation (may block — call from background threads only) ───────

    def get_printers(self) -> list[str]:
        return self._impl.get_printers()

    def get_printer_status(self, printer_name: str) -> dict[str, Any]:
        return self._impl.get_printer_status(printer_name)

    def print_job(
        self,
        job: dict[str, Any],
        printer_name: str,
        file_storage_path: str,
    ) -> bool:
        return self._impl.print_job(job, printer_name, file_storage_path)
