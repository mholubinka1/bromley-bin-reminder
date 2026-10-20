from dataclasses import dataclass
from datetime import datetime

RENEWAL_NOTICE_LEAD_DAYS = 30


@dataclass(frozen=True)
class GardenWasteSubscription:
    renewal_date: datetime
    subscription_text: str
    renews_automatically: bool = False
    in_progress: bool = False

    def renewal_notice_due(self, today: datetime) -> bool:
        days_until_renewal = (self.renewal_date.date() - today.date()).days
        return 0 <= days_until_renewal <= RENEWAL_NOTICE_LEAD_DAYS
