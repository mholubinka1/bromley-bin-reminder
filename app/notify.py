import logging.config
from email.mime.multipart import MIMEMultipart
from logging import Logger, getLogger
from smtplib import SMTP
from typing import List, Optional

from common.logging import APP_LOGGER_NAME, config
from decorator import retry
from notify_utils import WasteCollectionNotification

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


def is_null_or_empty(s: Optional[str]) -> bool:
    if not s:
        return False
    return s.strip() == ""


class SMTPClient:
    _username: str
    _password: Optional[str]
    _server: str
    _port: int

    def __init__(
        self, username: str, password: Optional[str], server: str, port: int
    ) -> None:
        self._username = username
        self._password = password
        self._server = server
        self._port = port

    def send_mail(
        self, sender: str, receivers: str | List[str], message: MIMEMultipart
    ) -> None:
        client = SMTP(self._server, self._port)
        client.starttls()
        if not is_null_or_empty(self._password):
            client.login(str(self._username), str(self._password))
        client.sendmail(sender, receivers, message.as_string())
        client.quit()


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
        msg = notification.email
        msg["From"] = sender
        recipients = ", ".join(email_addresses)
        msg["To"] = recipients
        self._client.send_mail(sender, email_addresses, message=msg)
        logger.info(f"Sent notification e-mail to [{recipients}]")
