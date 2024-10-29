import logging.config
import sys
import time
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config
from common.settings import ApplicationSettings, get_settings
from notify import Notify, SMTPClient
from notify_utils import WasteCollectionNotification
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


# @repeat(every(5).seconds, settings, web_scraper, notify)
@repeat(every().day.at(settings.remind.time).seconds, settings, web_scraper, notify)
def job(
    settings: ApplicationSettings, scraper: WasteworksScraper, notify: Notify
) -> None:
    try:
        logger.info("Scrape and alert job running.")
        collections = scraper.get_upcoming_collections()
        upcoming_collections = [c for c in collections if c.is_tomorrow]
        logger.info(f"{len(upcoming_collections)} collections scheduled for tomorrow.")
        if len(upcoming_collections) != 0:
            services = ", ".join([c.service_name for c in upcoming_collections])
            logger.info(f"Upcoming collections: [{services}]")
            logger.info("Sending notifications about tomorrow's collections.")
            notification = WasteCollectionNotification(upcoming_collections)
            notify.send_email(
                notification, settings.smtp.username, settings.remind.target_emails
            )
    except Exception as e:
        logger.exception(e)


while True:
    run_pending()
    time.sleep(1)
