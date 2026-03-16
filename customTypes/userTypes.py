from typing import List
from time import time


class User:
    """
    `User` data structure holds the data of the user such as name, unique_id, token_no
    """

    def __init__(self, name: str, unique_id: str):
        self.name = name
        self.token_no: int | None = None
        self.timestamp: int = time() * 1000000
        self.unique_id: str = unique_id
        self.etp: int = 0
        self.fileDetails: str[List] = []

    def printUser(self):
        print(
            self.name,
            self.token_no,
            self.unique_id,
            self.fileDetails,
        )
