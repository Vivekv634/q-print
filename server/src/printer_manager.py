import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    import win32print
    import win32ui
    import win32con
    from PIL import Image, ImageWin
    import fitz
    PRINTING_AVAILABLE = True
except ImportError:
    PRINTING_AVAILABLE = False
    logger.warning(
        "Windows printing libraries unavailable (win32print / PyMuPDF / Pillow). "
        "PrinterManager disabled."
    )

PAPER_SIZE_MAP: dict[str, int] = {
    "a0": 24, "a1": 25, "a2": 26,
    "a3": 8,  "a4": 9,  "a5": 11,
    "letter": 1, "legal": 5, "tabloid": 3,
}

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


class PrinterManager:
    def get_printers(self) -> list[str]:
        if not PRINTING_AVAILABLE:
            return []
        printers: list[Any] = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )
        return [p[2] for p in printers]

    def get_printer_status(self, printer_name: str) -> dict[str, Any]:
        if not PRINTING_AVAILABLE:
            return {"name": printer_name, "status": "Unavailable", "jobs": 0}
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
        if not PRINTING_AVAILABLE:
            logger.error("Printing unavailable.")
            return False

        all_ok: bool = True
        for filedata in job.get("filedataArray", []):
            if not isinstance(filedata, dict):
                all_ok = False
                continue
            stored: Optional[str] = self._find_stored_file(
                file_storage_path,
                filedata.get("_file_id", ""),
                filedata.get("file_name", ""),
            )
            if not stored:
                logger.error(
                    f"File not found in storage: "
                    f"{filedata.get('_file_id')}_{filedata.get('file_name')}"
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

    def _find_stored_file(
        self,
        storage_path: str,
        file_id: str,
        file_name: str,
    ) -> Optional[str]:
        if not os.path.exists(storage_path) or not file_id or not file_name:
            return None
        for fname in os.listdir(storage_path):
            if file_id in fname and file_name in fname:
                return os.path.join(storage_path, fname)
        return None

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
