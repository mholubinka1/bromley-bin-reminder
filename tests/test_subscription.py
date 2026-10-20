from datetime import datetime

import pytest
from subscription import GardenWasteSubscription
from support import FRIDAY_EVENING, LONDON

TODAY = FRIDAY_EVENING  # 2 October 2026


def renewing_on(
    day: int, month: int, in_progress: bool = False
) -> GardenWasteSubscription:
    return GardenWasteSubscription(
        renewal_date=datetime(2026, month, day, tzinfo=LONDON),
        subscription_text="£80.00 per year (1 bin)",
        in_progress=in_progress,
    )


@pytest.mark.parametrize(
    ("day", "month", "due"),
    [
        (2, 10, True),  # renews today
        (1, 11, True),  # exactly 30 days away
        (2, 11, False),  # 31 days away
        (1, 10, True),  # yesterday: overdue
    ],
)
def test_a_renewal_notice_is_due_from_30_days_before_the_renewal_date_onwards(
    day: int, month: int, due: bool
) -> None:
    # Given a subscription renewing on that date and today
    subscription = renewing_on(day, month)

    # When asked whether a notice is due
    # Then it is due from 30 days before the renewal date, including once overdue
    assert subscription.renewal_notice_due(TODAY) is due


def test_a_subscription_is_overdue_only_once_its_renewal_date_has_passed() -> None:
    # Given subscriptions renewing today and yesterday
    today_renewal, yesterday_renewal = renewing_on(2, 10), renewing_on(1, 10)

    # When asked whether they are overdue
    # Then only the one whose date has passed is
    assert not today_renewal.is_overdue(TODAY)
    assert yesterday_renewal.is_overdue(TODAY)


def test_no_renewal_notice_is_due_while_something_is_in_progress() -> None:
    # Given a due and an overdue subscription, each with a cancellation in progress
    due, overdue = renewing_on(10, 10, in_progress=True), renewing_on(1, 10, True)

    # When asked whether a notice is due
    # Then neither is
    assert not due.renewal_notice_due(TODAY)
    assert not overdue.renewal_notice_due(TODAY)
