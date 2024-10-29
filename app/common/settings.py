import json
import logging.config
import os
import sys
from dataclasses import dataclass
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


@dataclass
class RemindSettings:
    target_emails: str
    time: str


@dataclass
class SMTPSettings:
    username: str
    password: str
    server: str
    port: int


class ApplicationSettings:
    def __init__(
        self, url: str, remind_settings: RemindSettings, smtp_settings: SMTPSettings
    ) -> None:
        self.wasteworks_url = url
        self.remind = remind_settings
        self.smtp = smtp_settings


def get_settings() -> ApplicationSettings:
    try:
        email_addresses = json.loads(os.environ["EMAIL_ADDRESSES"])
        reminder_time = os.environ["REMINDER_TIME"]
        remind_settings = RemindSettings(
            target_emails=email_addresses, time=reminder_time
        )

        smtp_username = os.environ["SMTP_USERNAME"]
        smtp_password = os.environ["SMTP_PASSWORD"]
        smtp_server = os.environ["SMTP_SERVER"]
        smtp_port = int(os.environ["SMTP_PORT"])
        smtp_settings = SMTPSettings(
            username=smtp_username,
            password=smtp_password,
            server=smtp_server,
            port=smtp_port,
        )

        url = os.environ["URL"]
        return ApplicationSettings(url, remind_settings, smtp_settings)
    except Exception:
        logger.critical("Failed to load application settings.")
        sys.exit(1)
