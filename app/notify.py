import logging.config
from email.mime.multipart import MIMEMultipart
from logging import Logger, getLogger
from smtplib import SMTP

import requests
from common.decorators import retry
from common.logging import APP_LOGGER_NAME, config
from common.settings import is_null_or_empty
from notification import NtfyNotification, WasteCollectionNotification

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

NTFY_TIMEOUT_SECONDS = 10


class SMTPClient:
    _username: str
    _password: str | None
    _server: str
    _port: int

    def __init__(
        self, username: str, password: str | None, server: str, port: int
    ) -> None:
        self._username = username
        self._password = password
        self._server = server
        self._port = port

    def send_mail(
        self, sender: str, receivers: str | list[str], message: MIMEMultipart
    ) -> None:
        client = SMTP(self._server, self._port)
        client.starttls()
        if not is_null_or_empty(self._password):
            client.login(str(self._username), str(self._password))
        client.sendmail(sender, receivers, message.as_string())
        client.quit()


class NtfyClient:
    _server: str
    _topic: str

    def __init__(self, server: str, topic: str) -> None:
        self._server = server
        self._topic = topic

    def publish(self, notification: NtfyNotification) -> None:
        response = requests.post(
            self._server,
            json={
                "topic": self._topic,
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority,
                "tags": notification.tags,
            },
            timeout=NTFY_TIMEOUT_SECONDS,
        )
        response.raise_for_status()


class Notify:
    _client: SMTPClient
    _ntfy_client: NtfyClient | None

    def __init__(
        self, email_client: SMTPClient, ntfy_client: NtfyClient | None = None
    ) -> None:
        self._client = email_client
        self._ntfy_client = ntfy_client

    def send_ntfy(self, notifications: list[NtfyNotification]) -> None:
        if self._ntfy_client is None:
            return
        for notification in notifications:
            try:
                self._publish_ntfy(self._ntfy_client, notification)
            except requests.RequestException:
                logger.error(f"Failed to send ntfy notification [{notification.title}]")
            else:
                logger.info(f"Sent ntfy notification [{notification.title}]")

    @retry()
    def _publish_ntfy(self, client: NtfyClient, notification: NtfyNotification) -> None:
        client.publish(notification)

    @retry()
    def send_email(
        self,
        notification: WasteCollectionNotification,
        sender: str,
        email_addresses: list[str],
    ) -> None:
        msg = notification.email
        msg["From"] = sender
        recipients = ", ".join(email_addresses)
        msg["To"] = recipients
        self._client.send_mail(sender, email_addresses, message=msg)
        logger.info(f"Sent notification e-mail to [{recipients}]")
