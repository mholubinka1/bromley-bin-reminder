import argparse
import logging.config
import sys
import time
from logging import Logger, getLogger
from typing import Tuple

from common.logging import APP_LOGGER_NAME, config
from common.settings import ApplicationSettings, ConfigLoader
from notify import Notify, SMTPClient
from notify_utils import WasteCollectionNotification
from schedule import every, repeat, run_pending
from scraper import WasteworksScraper

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

logger.info("Starting bromley-bin-reminder.")


def on_config_update(settings: ApplicationSettings) -> Tuple[WasteworksScraper, Notify]:
    web_scraper = WasteworksScraper(settings.wasteworks_url)
    smtp_client = SMTPClient(
        username=settings.smtp.username,
        password=settings.smtp.password,
        server=settings.smtp.server,
        port=settings.smtp.port,
    )
    notify = Notify(email_client=smtp_client)
    return web_scraper, notify


try:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file")
    args = parser.parse_args()
    configLoader = ConfigLoader(args.config_file)
    settings = configLoader.get_config()
    web_scraper, notify = on_config_update(settings)
except Exception as e:
    logger.critical(f"Error loading startup configurations: {e}.")
    sys.exit(1)


# @repeat(every(5).seconds, settings, web_scraper, notify)
@repeat(every().day.at(settings.remind.time), settings, web_scraper, notify)
def daily_job(
    settings: ApplicationSettings, scraper: WasteworksScraper, notify: Notify
) -> None:
    try:
        logger.info("Daily scrape and alert job running.")
        collections = scraper.get_upcoming_collections()
        upcoming_collections = [c for c in collections if c.is_tomorrow]
        logger.info(f"{len(upcoming_collections)} collections scheduled for tomorrow.")
        if len(upcoming_collections) != 0:
            services = ", ".join([c.service_name for c in upcoming_collections])
            logger.info(f"Upcoming collections: [{services}]")
            logger.info("Sending notifications about tomorrow's collections.")
            notification = WasteCollectionNotification(
                upcoming_collections, period="tomorrow"
            )
            notify.send_email(
                notification, settings.smtp.username, settings.remind.target_emails
            )
    except Exception as e:
        logger.exception(e)


# @repeat(every(5).seconds, settings, web_scraper, notify)
@repeat(every().monday.at("09:00"), settings, web_scraper, notify)
def weekly_job(
    settings: ApplicationSettings, scraper: WasteworksScraper, notify: Notify
) -> None:
    try:
        logger.info("Weekly scrape and alert job running.")
        collections = scraper.get_upcoming_collections()
        this_week_collections = [c for c in collections if c.is_this_week]
        this_week_collections = sorted(
            this_week_collections, key=lambda x: x.next_collection_date
        )
        logger.info(
            f"{len(this_week_collections)} collections scheduled for this upcoming week."
        )
        if len(this_week_collections) != 0:
            services = ", ".join([c.service_name for c in this_week_collections])
            logger.info(f"Collections this week: [{services}]")
            logger.info("Sending notifications about this week's collections.")
            notification = WasteCollectionNotification(
                this_week_collections, period="week"
            )
            notify.send_email(
                notification, settings.smtp.username, settings.remind.target_emails
            )
    except Exception as e:
        logger.exception(e)


while True:
    run_pending()
    time.sleep(1)
