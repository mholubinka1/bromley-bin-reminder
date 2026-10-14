import logging.config
from dataclasses import dataclass
from datetime import datetime
from logging import Logger, getLogger

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


@dataclass
class WasteCollection:
    service_name: str
    next_collection_date: datetime


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
