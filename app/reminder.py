import logging.config
from collections.abc import Callable
from datetime import datetime
from logging import Logger, getLogger
from typing import Protocol

from collection import WasteCollection
from common.logging import APP_LOGGER_NAME, config
from common.settings import ApplicationSettings
from notification import WasteCollectionNotification, build_ntfy_notifications
from notify import Notify
from period import Period

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


class CollectionSource(Protocol):
    def get_upcoming_collections(self) -> list[WasteCollection]: ...


def run_reminder(
    period: Period,
    scraper: CollectionSource,
    notify: Notify,
    settings: ApplicationSettings,
    clock: Callable[[], datetime],
) -> None:
    logger.info(f"{period.name.title()} reminder run started.")
    selected = period.select(scraper.get_upcoming_collections())
    logger.info(f"{period.collections_label}: {len(selected)}")
    if selected:
        services = ", ".join(c.service_name for c in selected)
        logger.info(f"{period.collections_label}: [{services}]")
        logger.info(f"Sending {period.collections_label} reminders.")
        send_reminders(notify, settings, selected, clock(), period)


def send_reminders(
    notify: Notify,
    settings: ApplicationSettings,
    collections: list[WasteCollection],
    now: datetime,
    period: Period,
) -> None:
    try:
        notification = WasteCollectionNotification(collections, now, period)
        notify.send_email(
            notification, settings.smtp.username, settings.remind.target_emails
        )
    except Exception:
        logger.exception(f"Failed to send {period.name.lower()} email reminder.")
    notify.send_ntfy(build_ntfy_notifications(collections, period))
