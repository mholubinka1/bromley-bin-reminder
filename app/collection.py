import logging.config
from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


@dataclass
class WasteCollection:
    service_name: str
    next_collection_date: datetime
    is_tomorrow: bool
    is_this_week: bool


def print_date(date: datetime) -> str:
    day = date.day
    day_suffix = "th"
    if day in [1, 21, 31]:
        day_suffix = "st"
    elif day in [2, 22]:
        day_suffix = "nd"
    elif day in [3, 23]:
        day_suffix = "rd"
    return date.strftime(f"%A {day}{day_suffix} %B")


def is_collection_tomorrow(current_date: datetime, collection_date: datetime) -> bool:
    return collection_date.date() == (current_date + timedelta(days=1)).date()


def is_collection_this_week(current_date: datetime, collection_date: datetime) -> bool:
    # this week includes the following monday to avoid the situation where monday bins aren't notified a week in advance
    next_week = current_date + timedelta(days=8)
    return collection_date.date() < next_week.date()
