import logging.config
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from collection import WasteCollection
from common.logging import APP_LOGGER_NAME, config
from common.settings import ApplicationSettings
from notification import WasteCollectionNotification, build_ntfy_notifications
from notify import Notify

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


def send_reminders(
    notify: Notify,
    settings: ApplicationSettings,
    collections: list[WasteCollection],
    tz: ZoneInfo,
    period: str,
) -> None:
    try:
        notification = WasteCollectionNotification(collections, tz, period=period)
        notify.send_email(
            notification, settings.smtp.username, settings.remind.target_emails
        )
    except Exception:
        logger.exception(f"Failed to send {period} email reminder.")
    notify.send_ntfy(build_ntfy_notifications(collections, period))
