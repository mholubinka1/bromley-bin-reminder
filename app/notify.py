from typing import List

from notify_utils import SMTPClient
from waste_utils import WasteCollection


class WasteCollectionNotification:
    def create_email(self, upcoming_collections: List[WasteCollection]) -> None:
        pass

    def create_push(self, upcoming_collections: List[WasteCollection]) -> None:
        pass


class Notify:
    _client: SMTPClient

    def __init__(self, email_client: SMTPClient):
        self._client = email_client

    def send(self, upcoming_collections: List[WasteCollection]) -> None:
        pass
