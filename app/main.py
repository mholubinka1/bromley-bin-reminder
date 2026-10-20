import sys
import time
from argparse import ArgumentParser, Namespace
from datetime import datetime
from logging import Logger, getLogger
from threading import Thread

from common.logging import APP_LOGGER_NAME, configure_logging
from common.settings import load_settings
from notify import build_channels
from reload import ConfigChangePoller
from reminder import schedule_reminder_runs
from schedule import default_scheduler, run_pending
from scraper import SeleniumPageSource, WasteworksScraper

logger: Logger = getLogger(APP_LOGGER_NAME)


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--config-file", type=str, required=True)
    args = parser.parse_args()
    return args


def main() -> None:
    configure_logging()
    logger.info("Starting bromley-bin-reminder.")
    try:
        args = parse_args()
        config_file = args.config_file
        settings = load_settings(config_file)

        def current_time() -> datetime:
            return datetime.now(settings.timezone)

        web_scraper = WasteworksScraper(
            SeleniumPageSource(), settings.wasteworks_url, current_time
        )
        logger.info(f"ntfy notifications {'enabled' if settings.ntfy else 'disabled'}.")
        channels = build_channels(settings)
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

    schedule_reminder_runs(
        default_scheduler, web_scraper, channels, settings, current_time
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
