from dataclasses import dataclass
from datetime import datetime

RENEWAL_NOTICE_LEAD_DAYS = 30


@dataclass(frozen=True)
class GardenWasteSubscription:
    renewal_date: datetime
    subscription_text: str
    renews_automatically: bool = False
    in_progress: bool = False

    def _days_until_renewal(self, today: datetime) -> int:
        return (self.renewal_date.date() - today.date()).days

    def is_overdue(self, today: datetime) -> bool:
        return self._days_until_renewal(today) < 0

    def renewal_notice_due(self, today: datetime) -> bool:
        return self._days_until_renewal(today) <= RENEWAL_NOTICE_LEAD_DAYS
