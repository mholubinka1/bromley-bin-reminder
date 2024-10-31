import logging.config
from email.mime.multipart import MIMEMultipart
from logging import Logger, getLogger
from smtplib import SMTP
from typing import List

from common.logging import APP_LOGGER_NAME, config
from decorator import retry
from notify_utils import WasteCollectionNotification

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class SMTPClient:
    _username: str
    _password: str
    _client: SMTP

    def __init__(self, username: str, password: str, server: str, port: int) -> None:
        self._client = SMTP(server, port)
        self._client.starttls()
        self._username = username
        self._password = password

    def login(self) -> None:
        self._client.login(self._username, self._password)

    def send_mail(
        self, sender: str, receivers: str | List[str], message: MIMEMultipart
    ) -> None:
        self._client.sendmail(sender, receivers, message.as_string())


class Notify:
    _client: SMTPClient

    def __init__(self, email_client: SMTPClient):
        self._client = email_client

    @retry()
    def send_email(
        self,
        notification: WasteCollectionNotification,
        sender: str,
        email_addresses: List[str],
    ) -> None:
        self._client.login()
        msg = notification.email
        msg["From"] = sender
        recipients = ", ".join(email_addresses)
        msg["To"] = recipients
        self._client.send_mail(sender, email_addresses, message=msg)
        logger.info(f"Sent notification e-mail to [{recipients}]")
