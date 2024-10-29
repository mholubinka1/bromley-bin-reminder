import logging.config
import sys
import time
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config
from common.settings import get_settings
from notify import Notify
from notify_utils import SMTPClient
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
smtp_client = SMTPClient(
    username=settings.smtp.username,
    password=settings.smtp.password,
    server=settings.smtp.server,
    port=settings.smtp.port,
)
notify = Notify(email_client=smtp_client)


@repeat(every(5).seconds, web_scraper, notify)
def job(scraper: WasteworksScraper, notify: Notify) -> None:
    try:
        logger.info("Scrape and alert job running.")
        collections = scraper.get_upcoming_collections()
        upcoming_collections = [c for c in collections if c.is_tomorrow]
        notify.send(upcoming_collections)
    except Exception as e:
        logger.exception(e)


while True:
    run_pending()
    time.sleep(1)
