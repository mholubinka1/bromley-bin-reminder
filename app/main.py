import logging.config
import os
import pathlib
import sys
import time
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config
from common.settings import Settings, get_settings
from schedule import every, repeat, run_pending
from scraper import DynamicHTMLScraper

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

logger.info("Starting bromley-bin-reminder.")

CONFIG_PATH = os.path.join(pathlib.Path(__file__).parent.resolve(), "config.yml")
RETRIES = 5

try:
    settings = get_settings()
    print(settings.wasteworks_url)
    print(settings.remind.target_emails)
except Exception as e:
    logger.critical(f"Error loading startup configurations: {e}.")
    sys.exit(1)

web_scraper = DynamicHTMLScraper(settings.wasteworks_url)


@repeat(every(30).seconds, settings, web_scraper)
def job(settings: Settings, scraper: DynamicHTMLScraper) -> None:
    logger.info(
        f"Job running: [url: {settings.wasteworks_url}, email_addresses: {settings.remind.target_emails}, time: {settings.remind.time}]"
    )
    scraper.render_web_page()


while True:
    run_pending()
    time.sleep(1)

"""
attempt = 1
while attempt < RETRIES:
    try:
        content = download_webpage(url=settings.wasteworks_url)
        soup = BeautifulSoup(content, "html.parser")
        logger.info(
            f"Web content from {settings.wasteworks_url} downloaded successfully."
        )
        break
    except Exception as e:
        logger.error(f"Failed to download webpage: {e}.")
        if attempt == RETRIES:
            logger.critical("Retries exhausted. Aborting.")
            sys.exit(1)
        retries_remaining = RETRIES - attempt
        logger.info(f"Retrying. Retries remaining: {retries_remaining}")
        attempt += 1


today = datetime.today().date()
print(soup.prettify)
"""
