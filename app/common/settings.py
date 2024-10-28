import json
import logging.config
import os
import sys
from logging import Logger, getLogger
from typing import List

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class RemindSettings:
    def __init__(self, email_addresses: List[str], reminder_time: str) -> None:
        self.target_emails = email_addresses
        self.time = reminder_time


class Settings:
    def __init__(
        self, url: str, email_addresses: List[str], reminder_time: str
    ) -> None:
        self.wasteworks_url = url
        self.remind = RemindSettings(email_addresses, reminder_time)


def get_settings() -> Settings:
    try:
        url = os.environ["URL"]
        email_addresses = json.loads(os.environ["EMAIL_ADDRESSES"])
        reminder_time = os.environ["REMINDER_TIME"]
        return Settings(url, email_addresses, reminder_time)
    except Exception:
        logger.critical("Failed to load application settings.")
        sys.exit(1)
