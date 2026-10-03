from dataclasses import dataclass
from enum import Enum

from collection import WasteCollection, print_date

NIGHT_BEFORE_PRIORITY = 4
WEEKLY_PRIORITY = 3


@dataclass(frozen=True)
class PeriodDetails:
    ntfy_title_suffix: str
    ntfy_priority: int


class Period(Enum):
    TOMORROW = PeriodDetails(
        ntfy_title_suffix="tomorrow", ntfy_priority=NIGHT_BEFORE_PRIORITY
    )
    WEEK = PeriodDetails(ntfy_title_suffix="this week", ntfy_priority=WEEKLY_PRIORITY)

    @property
    def ntfy_title_suffix(self) -> str:
        return self.value.ntfy_title_suffix

    @property
    def ntfy_priority(self) -> int:
        return self.value.ntfy_priority

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
