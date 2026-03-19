from typing import Literal


class FilePrintingInstruction:
    def __init__(self, file_path: str = "", no_of_copies: int = 1):
        self.file_path: str = file_path
        self.no_of_copies: int = no_of_copies
        self.color: bool = False
        self.layout: Literal["portrait", "landscape"] = "portrait"
        self.paper_size: Literal[
            "letter", "legal", "tabloid", "a0", "a1", "a2", "a3", "a4", "a5"
        ] = "a4"
        self.background_graphics: bool = False
        self.headers_footers: bool = False
        self.margins: Literal["none", "default", "minimal"] = "default"

    def printDetails(self):
        print(
            self.file_path,
            self.background_graphics,
            self.color,
            self.no_of_copies,
            self.layout,
            self.paper_size,
            self.margins,
            self.headers_footers,
        )
