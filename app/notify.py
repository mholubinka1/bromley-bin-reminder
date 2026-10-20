from datetime import datetime
from email.mime.multipart import MIMEMultipart
from logging import Logger, getLogger
from smtplib import SMTP
from typing import Protocol

import requests
from collection import WasteCollection
from common.decorators import retry
from common.logging import APP_LOGGER_NAME
from common.settings import ApplicationSettings, is_null_or_empty
from notification import (
    NtfyNotification,
    WasteCollectionNotification,
    build_ntfy_notifications,
)
from period import Period

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


class Channel(Protocol):
    """A delivery route for a Reminder.

    send must not raise: a Channel catches and logs its own failures, so one failing
    Channel can never stop the next from delivering.
    """

    def send(
        self, collections: list[WasteCollection], now: datetime, period: Period
    ) -> None: ...


class EmailChannel:
    _client: SMTPClient
    _sender: str
    _email_addresses: list[str]

    def __init__(
        self, client: SMTPClient, sender: str, email_addresses: list[str]
    ) -> None:
        self._client = client
        self._sender = sender
        self._email_addresses = email_addresses

    def send(
        self, collections: list[WasteCollection], now: datetime, period: Period
    ) -> None:
        try:
            self._send_email(WasteCollectionNotification(collections, now, period))
        except Exception:
            logger.exception(f"Failed to send {period.name.lower()} email reminder.")

    @retry()
    def _send_email(self, notification: WasteCollectionNotification) -> None:
        msg = notification.email
        msg["From"] = self._sender
        recipients = ", ".join(self._email_addresses)
        msg["To"] = recipients
        self._client.send_mail(self._sender, self._email_addresses, message=msg)
        logger.info(f"Sent notification e-mail to [{recipients}]")


class NtfyChannel:
    _client: NtfyClient

    def __init__(self, client: NtfyClient) -> None:
        self._client = client

    def send(
        self, collections: list[WasteCollection], now: datetime, period: Period
    ) -> None:
        try:
            notifications = build_ntfy_notifications(collections, period)
        except Exception:
            logger.exception(f"Failed to send {period.name.lower()} ntfy reminder.")
            return
        for notification in notifications:
            try:
                self._publish(notification)
            except Exception:
                logger.exception(
                    f"Failed to send ntfy notification [{notification.title}]"
                )
            else:
                logger.info(f"Sent ntfy notification [{notification.title}]")

    @retry()
    def _publish(self, notification: NtfyNotification) -> None:
        self._client.publish(notification)


def build_channels(settings: ApplicationSettings) -> list[Channel]:
    smtp_client = SMTPClient(
        username=settings.smtp.username,
        password=settings.smtp.password,
        server=settings.smtp.server,
        port=settings.smtp.port,
    )
    channels: list[Channel] = [
        EmailChannel(smtp_client, settings.smtp.username, settings.remind.target_emails)
    ]
    if settings.ntfy:
        channels.append(
            NtfyChannel(
                NtfyClient(server=settings.ntfy.server, topic=settings.ntfy.topic)
            )
        )
    return channels
