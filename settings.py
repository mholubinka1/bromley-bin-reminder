import logging.config
import sys
from logging import Logger, getLogger
from typing import Dict

import yaml

from logging_config import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class RemindSettings:
    def __init__(self, yaml_settings: Dict) -> None:
        self.target_emails = yaml_settings["remind"]["email_addresses"]


class Settings:
    def __init__(self, yaml_settings: Dict) -> None:
        self.wasteworks_url = yaml_settings["wasteWorks"]["url"]
        self.remind = RemindSettings(yaml_settings)


def get_settings(
    config_file_path: str,
) -> Settings:
    try:
        with open(config_file_path, "r") as file:
            settings = yaml.safe_load(file)
        logger.info(f"Successfully loaded settings from {config_file_path}")
        return Settings(settings)
    except Exception as e:
        logger.critical(
            f"Failed to load application settings from {config_file_path}: {e}"
        )
        sys.exit(1)
