import logging.config
import sys
from dataclasses import dataclass
from logging import Logger, getLogger
from typing import Dict, List, Optional

import yaml
from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

DEFAULT_DAILY_POLL_TIME = "18:00"


def is_null_or_empty(s: Optional[str]) -> bool:
    if not s:
        return True
    return s.strip() == ""


@dataclass
class RemindSettings:
    target_emails: List[str]
    time: str


@dataclass
class SMTPSettings:
    username: str
    password: Optional[str]
    server: str
    port: int


class ApplicationSettings:
    def __init__(self, yaml_settings: Dict) -> None:
        self.wasteworks_url = yaml_settings["remind"]["url"]
        self.remind = RemindSettings(
            target_emails=yaml_settings["remind"]["email_addresses"],
            time=yaml_settings["remind"]["time"],
        )
        self.smtp = SMTPSettings(
            username=yaml_settings["smtp"]["username"],
            password=yaml_settings["smtp"]["password"],
            server=yaml_settings["smtp"]["server"],
            port=yaml_settings["smtp"]["port"],
        )


class ConfigLoader:
    _config: ApplicationSettings
    _path: str

    def __init__(self, config_path: str) -> None:
        self._path = config_path
        self._load_config()

    def get_config(self) -> ApplicationSettings:
        return self._config

    def _load_config(self) -> None:
        try:
            with open(self._path, "r") as file:
                settings = yaml.safe_load(file)
            logger.info(f"Successfully loaded settings from {self._path}")
            self._config = ApplicationSettings(settings)
        except Exception as e:
            logger.critical(
                f"Failed to load application settings from {self._path}: {e}"
            )
            sys.exit(1)


def validate_settings(settings: ApplicationSettings) -> None:
    if is_null_or_empty(settings.wasteworks_url):
        raise RuntimeError("A valid wasteworks URL must be provided.")
    if is_null_or_empty(settings.remind.time):
        logger.warning(
            f"Custom daily poll time not provided, using default: {DEFAULT_DAILY_POLL_TIME}"
        )
        settings.remind.time = DEFAULT_DAILY_POLL_TIME
    if is_null_or_empty(settings.smtp.username):
        raise RuntimeError("A valid sender e-mail address must be provided.")
    if is_null_or_empty(settings.smtp.server) or settings.smtp.port is None:
        raise RuntimeError("SMTP server and port configurations must be provided.")
    return
