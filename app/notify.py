from typing import List

from waste_utils import WasteCollection


class WasteCollectionNotification:
    def create_email(self, upcoming_collections: List[WasteCollection]) -> None:
        pass

    def create_push(self, upcoming_collections: List[WasteCollection]) -> None:
        pass


class Notify:
    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def send(self, upcoming_collections: List[WasteCollection]) -> None:
        pass
