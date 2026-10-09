import logging.config
import sys
import time
from argparse import ArgumentParser, Namespace
from datetime import datetime
from logging import Logger, getLogger
from threading import Thread
from zoneinfo import ZoneInfo

from common.logging import APP_LOGGER_NAME, config
from common.settings import ConfigLoader, validate_settings
from notify import build_notify
from reload import ConfigChangePoller
from reminder import schedule_reminder_runs
from schedule import default_scheduler, run_pending
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
        logger.info(f"ntfy notifications {'enabled' if settings.ntfy else 'disabled'}.")
        notify = build_notify(settings)
    except Exception:
        logger.exception("Could not load startup configuration.")
        sys.exit(1)

    # Re-exec the interpreter directly: re-running the `uv run` launcher would stack
    # another waiting uv parent process on every reload.
    command = [sys.executable, *sys.argv]
    poller = ConfigChangePoller(path=config_file, command=command)
    polling_thread = Thread(target=poller.poll, daemon=True)
    polling_thread.start()
    logger.info(f"Monitoring config file {config_file} for changes.")

    def current_time() -> datetime:
        return datetime.now(tz)

    schedule_reminder_runs(
        default_scheduler, web_scraper, notify, settings, current_time
    )

    try:
        while True:
            run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        poller.stop()
    polling_thread.join()


if __name__ == "__main__":
    main()
