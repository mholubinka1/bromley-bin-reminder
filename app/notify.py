import logging.config
from email.mime.multipart import MIMEMultipart
from logging import Logger, getLogger
from smtplib import SMTP
from typing import List

from common.logging import APP_LOGGER_NAME, config
from notify_utils import WasteCollectionNotification

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class SMTPClient:
    _client: SMTP

    def __init__(self, username: str, password: str, server: str, port: int) -> None:
        self._client = SMTP(server, port)
        self._client.starttls()
        self._login(username, password)

    def _login(self, username: str, password: str) -> None:
        self._client.login(username, password)

    def send_mail(self, sender: str, receiver: str, message: MIMEMultipart) -> None:
        self._client.sendmail(sender, receiver, message.as_string())


class Notify:
    _client: SMTPClient

    def __init__(self, email_client: SMTPClient):
        self._client = email_client

    def send_email(
        self,
        notification: WasteCollectionNotification,
        sender: str,
        email_addresses: List[str],
    ) -> None:
        msg = notification.email
        msg["From"] = sender
        for address in email_addresses:
            msg["To"] = address
            self._client.send_mail(sender, msg["To"], message=msg)
            logger.info(f"Sent notification e-mail to {address}")