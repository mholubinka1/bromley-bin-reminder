from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, unique

from collection import WasteCollection, print_date

NIGHT_BEFORE_PRIORITY = 4
WEEKLY_PRIORITY = 3
WEEK_COMMENCING_PREFIX = "Week Commencing: "


@dataclass(frozen=True)
class PeriodDetails:
    ntfy_title_suffix: str
    ntfy_priority: int
    email_subject: str
    shows_collection_dates: bool
    collections_label: str


@unique
class Period(Enum):
    TOMORROW = PeriodDetails(
        ntfy_title_suffix="tomorrow",
        ntfy_priority=NIGHT_BEFORE_PRIORITY,
        email_subject="REMINDER: Bins",
        shows_collection_dates=False,
        collections_label="Tomorrow's collections",
    )
    WEEK = PeriodDetails(
        ntfy_title_suffix="this week",
        ntfy_priority=WEEKLY_PRIORITY,
        email_subject="Weekly Collections",
        shows_collection_dates=True,
        collections_label="This week's collections",
    )

    @property
    def ntfy_title_suffix(self) -> str:
        return self.value.ntfy_title_suffix

    @property
    def ntfy_priority(self) -> int:
        return self.value.ntfy_priority

    @property
    def email_subject(self) -> str:
        return self.value.email_subject

    @property
    def shows_collection_dates(self) -> bool:
        return self.value.shows_collection_dates

    @property
    def collections_label(self) -> str:
        return self.value.collections_label

    def select(self, collections: list[WasteCollection]) -> list[WasteCollection]:
        match self:
            case Period.TOMORROW:
                return [c for c in collections if c.is_tomorrow]
            case Period.WEEK:
                return sorted(
                    (c for c in collections if c.is_this_week),
                    key=lambda c: c.next_collection_date,
                )

    def ntfy_message(self, collection: WasteCollection) -> str:
        match self:
            case Period.TOMORROW:
                return "Put it out tonight."
            case Period.WEEK:
                return f"Collection is {print_date(collection.next_collection_date)}."

    def email_heading(self, now: datetime) -> str:
        match self:
            case Period.TOMORROW:
                return print_date(now + timedelta(days=1))
            case Period.WEEK:
                return f"{WEEK_COMMENCING_PREFIX}{print_date(now)}"
