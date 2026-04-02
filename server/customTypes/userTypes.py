from typing import List
from time import time


class User:
    """
    `User` data structure holds user metadata such as name, unique_id, and file details.
    NOTE: This class is a legacy data structure. The active app uses the JSON-based
    UserType defined in the Next.js client (client/types/user.types.ts).
    """

    def __init__(self, name: str, unique_id: str) -> None:
        self.name: str = name
        self.token_no: int | None = None
        self.timestamp: int = int(time() * 1000)  # milliseconds, consistent with JS Date.getTime()
        self.unique_id: str = unique_id
        self.etp: int = 0
        self.fileDetails: List[str] = []

    def printUser(self) -> None:
        print(
            self.name,
            self.token_no,
            self.unique_id,
            self.fileDetails,
        )
