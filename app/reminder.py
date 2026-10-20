from collections.abc import Callable
from datetime import datetime
from logging import Logger, getLogger
from typing import Protocol

from collection import WasteCollection
from common.logging import APP_LOGGER_NAME
from common.settings import ApplicationSettings
from notify import Channel
from period import Period
from schedule import Scheduler
from subscription import GardenWasteSubscription

logger: Logger = getLogger(APP_LOGGER_NAME)


class CollectionSource(Protocol):
    def get_upcoming_collections(self) -> list[WasteCollection]: ...

    def get_garden_waste_subscription(self) -> GardenWasteSubscription | None: ...


def run_reminder(
    period: Period,
    scraper: CollectionSource,
    channels: list[Channel],
    clock: Callable[[], datetime],
) -> None:
    period_name = period.name.title()
    logger.info(f"{period_name} reminder run started.")
    try:
        collections = scraper.get_upcoming_collections()
        now = clock()
        selected = period.select(collections, now)
        logger.info(f"{period.collections_label}: {len(selected)}")
        if selected:
            services = ", ".join(c.service_name for c in selected)
            logger.info(f"{period.collections_label}: [{services}]")
            logger.info(f"Sending reminders for {period.collections_label.lower()}.")
            send_reminders(channels, selected, now, period)
    except Exception:
        logger.exception(f"{period_name} reminder run failed.")
    if period is Period.WEEK:
        try:
            send_renewal_notice_if_due(scraper, channels, clock)
        except Exception:
            logger.exception(f"{period_name} renewal check failed.")


def send_renewal_notice_if_due(
    scraper: CollectionSource,
    channels: list[Channel],
    clock: Callable[[], datetime],
) -> None:
    subscription = scraper.get_garden_waste_subscription()
    now = clock()  # after the read, as for collections: it may have crossed midnight
    if subscription is not None and subscription.renewal_notice_due(now):
        logger.info("Sending Garden Waste renewal notice.")
        for channel in channels:
            channel.send_renewal(subscription, now)


def schedule_reminder_runs(
    scheduler: Scheduler,
    scraper: CollectionSource,
    channels: list[Channel],
    settings: ApplicationSettings,
    clock: Callable[[], datetime],
) -> None:
    remind = settings.remind
    run_args = (scraper, channels, clock)
    scheduler.every().day.at(remind.time, remind.tz).do(
        run_reminder, Period.TOMORROW, *run_args
    )
    scheduler.every().sunday.at(remind.time, remind.tz).do(
        run_reminder, Period.WEEK, *run_args
    )


def send_reminders(
    channels: list[Channel],
    collections: list[WasteCollection],
    now: datetime,
    period: Period,
) -> None:
    for channel in channels:
        channel.send(collections, now, period)
