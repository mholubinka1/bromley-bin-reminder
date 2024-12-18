import logging.config
import sys
from dataclasses import dataclass
from logging import Logger, getLogger
from typing import Dict, List

import yaml
from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


@dataclass
class RemindSettings:
    target_emails: List[str]
    time: str


@dataclass
class SMTPSettings:
    username: str
    password: str
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
