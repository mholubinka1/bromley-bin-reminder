import argparse
import logging.config
import os
import subprocess
import sys
import time
from logging import Logger, getLogger
from typing import List

from common.logging import APP_LOGGER_NAME, config
from common.settings import ApplicationSettings, ConfigLoader, validate_settings
from notification import WasteCollectionNotification
from notify import Notify, SMTPClient
from schedule import every, repeat, run_pending
from scraper import WasteworksScraper
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)

logger.info("Starting bromley-bin-reminder.")


class RestartOnConfigChangeHandler(FileSystemEventHandler):  # type: ignore
    _path: str
    _command: List[str]

    def __init__(self, path: str, command: List) -> None:
        self._path = path
        self._command = command

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        path = (
            event.src_path.decode("utf-8")
            if isinstance(event.src_path, bytes)
            else event.src_path
        )
        if os.path.normpath(path) == os.path.normpath(self._path):
            logger.info(f"Change detected: {path}. Restarting application.")
            subprocess.Popen(self._command)
            exit(0)


def main() -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--config-file")
        args = parser.parse_args()
        config_file = args.config_file
        configLoader = ConfigLoader(config_file)
        settings = configLoader.get_config()
        validate_settings(settings)
        web_scraper = WasteworksScraper(settings.wasteworks_url)
        smtp_client = SMTPClient(
            username=settings.smtp.username,
            password=settings.smtp.password,
            server=settings.smtp.server,
            port=settings.smtp.port,
        )
        notify = Notify(email_client=smtp_client)
    except Exception as e:
        logger.critical(f"Error loading startup configuration: {e}.")
        sys.exit(1)

    command = [
        "poetry",
        "run",
        "python",
        "./app/main.py",
        "--config-file",
        config_file,
    ]  # ./app/main.py
    event_handler = RestartOnConfigChangeHandler(path=config_file, command=command)
    observer = Observer()
    observer.schedule(event_handler, path="./config", recursive=False)
    observer.start()

    logger.info(f"Monitoring config file {config_file} for changes.")

    # @repeat(every(60).seconds, settings, web_scraper, notify)
    @repeat(every().day.at(settings.remind.time), settings, web_scraper, notify)
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
                notification = WasteCollectionNotification(
                    upcoming_collections, period="tomorrow"
                )
                notify.send_email(
                    notification, settings.smtp.username, settings.remind.target_emails
                )
        except Exception as e:
            logger.exception(e)

    # @repeat(every(5).seconds, settings, web_scraper, notify)
    @repeat(every().sunday.at("18:00"), settings, web_scraper, notify)
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

    try:
        while True:
            run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
