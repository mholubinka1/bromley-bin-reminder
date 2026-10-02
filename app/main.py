import logging.config
import sys
import time
from argparse import ArgumentParser, Namespace
from logging import Logger, getLogger
from threading import Thread
from zoneinfo import ZoneInfo

from common.logging import APP_LOGGER_NAME, config
from common.settings import ApplicationSettings, ConfigLoader, validate_settings
from notify import Notify, NtfyClient, SMTPClient
from reload import ConfigChangePoller
from reminder import send_reminders
from schedule import every, repeat, run_pending
from scraper import WasteworksScraper

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

logger.info("Starting bromley-bin-reminder.")


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--config-file", type=str, required=True)
    args = parser.parse_args()
    return args


def main() -> None:
    try:
        args = parse_args()
        config_file = args.config_file
        configLoader = ConfigLoader(config_file)
        settings = configLoader.get_config()
        validate_settings(settings)
        tz = ZoneInfo(settings.remind.tz)
        web_scraper = WasteworksScraper(settings.wasteworks_url, tz)
        smtp_client = SMTPClient(
            username=settings.smtp.username,
            password=settings.smtp.password,
            server=settings.smtp.server,
            port=settings.smtp.port,
        )
        ntfy_client = (
            NtfyClient(server=settings.ntfy.server, topic=settings.ntfy.topic)
            if settings.ntfy
            else None
        )
        logger.info(f"ntfy notifications {'enabled' if ntfy_client else 'disabled'}.")
        notify = Notify(email_client=smtp_client, ntfy_client=ntfy_client)
    except Exception:
        logger.exception("Could not load startup configuration.")
        sys.exit(1)

    # Keep in step with the Dockerfile CMD — both launch the app the same way.
    command = [
        "uv",
        "run",
        "--no-sync",
        "python",
        "./app/main.py",
        "--config-file",
        config_file,
    ]
    poller = ConfigChangePoller(path=config_file, command=command)
    polling_thread = Thread(target=poller.poll, daemon=True)
    polling_thread.start()
    logger.info(f"Monitoring config file {config_file} for changes.")

    # @repeat(every(60).seconds, settings, web_scraper, notify)
    @repeat(
        every().day.at(settings.remind.time, settings.remind.tz),
        settings,
        web_scraper,
        notify,
    )
    def daily_job(
        settings: ApplicationSettings, scraper: WasteworksScraper, notify: Notify
    ) -> None:
        try:
            logger.info("Daily scrape and alert job running.")
            collections = scraper.get_upcoming_collections()
            upcoming_collections = [c for c in collections if c.is_tomorrow]
            logger.info(
                f"{len(upcoming_collections)} collections scheduled for tomorrow."
            )
            if len(upcoming_collections) != 0:
                services = ", ".join([c.service_name for c in upcoming_collections])
                logger.info(f"Upcoming collections: [{services}]")
                logger.info("Sending notifications about tomorrow's collections.")
                send_reminders(
                    notify, settings, upcoming_collections, tz, period="tomorrow"
                )
        except Exception:
            logger.exception("Daily scrape and alert job failed.")

    # @repeat(every(5).seconds, settings, web_scraper, notify)
    @repeat(
        every().sunday.at(settings.remind.time, settings.remind.tz),
        settings,
        web_scraper,
        notify,
    )
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
                send_reminders(
                    notify, settings, this_week_collections, tz, period="week"
                )
        except Exception:
            logger.exception("Weekly scrape and alert job failed.")

    try:
        while True:
            run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        poller.stop()
    polling_thread.join()


if __name__ == "__main__":
    main()
