import logging.config
import sys
import time
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config
from common.settings import get_settings
from schedule import every, repeat, run_pending
from scraper import WasteworksScraper

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

logger.info("Starting bromley-bin-reminder.")

try:
    settings = get_settings()
except Exception as e:
    logger.critical(f"Error loading startup configurations: {e}.")
    sys.exit(1)

web_scraper = WasteworksScraper(settings.wasteworks_url)


@repeat(every(5).seconds, web_scraper)
def job(scraper: WasteworksScraper) -> None:
    try:
        logger.info("Scrape and alert job running.")
        collections = scraper.get_upcoming_collections()
        print(collections)
    except Exception as e:
        logger.exception(e)


while True:
    run_pending()
    time.sleep(1)

RETRIES = 5

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
