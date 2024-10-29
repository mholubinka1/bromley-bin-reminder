import logging.config
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Tuple

from common.logging import APP_LOGGER_NAME, config

logging.config.dictConfig(config)
logger: Logger = getLogger(APP_LOGGER_NAME)


@dataclass
class WasteCollection:
    service_name: str
    next_collection_date: datetime
    is_tomorrow: bool


def is_collection_tomorrow(current_date: datetime, collection_date: datetime) -> bool:
    return collection_date.date() == (current_date + timedelta(days=1)).date()


def parse_date(date: str) -> Tuple[bool, datetime]:
    date = re.sub(r"\s*\(In Progress\)", "", date)
    date = re.sub(r"\b(\d+)(th|rd|nd|st)\b", r"\1", date)
    date = date.strip()
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    parsed_date = datetime.strptime(date, "%A, %d %B")
    collection_month = parsed_date.month
    if current_month == 12 and collection_month == 1:
        target_year = current_year + 1
    else:
        target_year = current_year
    collection_date = datetime.strptime(f"{date} {target_year}", "%A, %d %B %Y")
    is_tomorrow = is_collection_tomorrow(
        current_date=current_date, collection_date=collection_date
    )
    return (is_tomorrow, collection_date)