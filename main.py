import logging.config
import os
import pathlib
import sys
from datetime import datetime
from logging import Logger, getLogger

from logging_config import APP_LOGGER_NAME, config
from settings import get_settings

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

logger.info("Starting bromley-bin-reminder.")

CONFIG_PATH = os.path.join(pathlib.Path(__file__).parent.resolve(), "config.yml")

try:
    settings = get_settings(config_file_path=CONFIG_PATH)
    print(settings.wasteworks_url)
    print(settings.remind.target_emails)
except Exception as e:
    logger.critical(f"Error loading startup configurations: {e}.")
    sys.exit(1)


today = datetime.today().date()
