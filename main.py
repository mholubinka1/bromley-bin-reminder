import logging.config
import os
import pathlib
import sys
from datetime import datetime
from logging import Logger, getLogger

from bs4 import BeautifulSoup

from common.logging import APP_LOGGER_NAME, config
from common.settings import get_settings
from common.utils import download_webpage

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

logger.info("Starting bromley-bin-reminder.")

CONFIG_PATH = os.path.join(pathlib.Path(__file__).parent.resolve(), "config.yml")
RETRIEs = 5

try:
    settings = get_settings(config_file_path=CONFIG_PATH)
    print(settings.wasteworks_url)
    print(settings.remind.target_emails)
except Exception as e:
    logger.critical(f"Error loading startup configurations: {e}.")
    sys.exit(1)

attempt = 1
while attempt < RETRIEs:
    try:
        content = download_webpage(url=settings.wasteworks_url)
        soup = BeautifulSoup(content, "html.parser")
        logger.info(
            f"Web content from {settings.wasteworks_url} downloaded successfully."
        )
        break
    except Exception as e:
        logger.error(f"Failed to download webpage: {e}.")
        if attempt == RETRIEs:
            logger.critical("Retries exhausted. Aborting.")
            sys.exit(1)
        retries_remaining = RETRIEs - attempt
        logger.info(f"Retrying. Retries remaining: {retries_remaining}")
        attempt += 1


today = datetime.today().date()
print(soup.prettify)
