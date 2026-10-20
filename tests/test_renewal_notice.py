from datetime import timedelta

from period import Period
from reminder import run_reminder
from subscription import GardenWasteSubscription
from support import FRIDAY_EVENING, FakeScraper, RecordingChannel

SUBSCRIPTION_TEXT = "£80.00 per year (1 bin)"


def a_subscription(days_until_renewal: int) -> GardenWasteSubscription:
    return GardenWasteSubscription(
        renewal_date=FRIDAY_EVENING + timedelta(days=days_until_renewal),
        subscription_text=SUBSCRIPTION_TEXT,
    )


def test_sunday_run_sends_a_renewal_notice_when_the_subscription_is_due_soon() -> None:
    # Given a subscription renewing in 20 days and no bin collected this week
    subscription = a_subscription(days_until_renewal=20)
    channel = RecordingChannel("only", [])

    # When the Sunday (Week) run happens
    run_reminder(
        Period.WEEK,
        FakeScraper([], subscription=subscription),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then the Channel is sent the renewal notice
    assert channel.renewals == [(subscription, FRIDAY_EVENING)]


def test_sunday_run_sends_nothing_when_the_renewal_is_31_days_away() -> None:
    # Given a subscription renewing in 31 days
    channel = RecordingChannel("only", [])

    # When the Sunday (Week) run happens
    run_reminder(
        Period.WEEK,
        FakeScraper([], subscription=a_subscription(days_until_renewal=31)),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then no renewal notice is sent
    assert channel.renewals == []


def test_sunday_run_sends_a_renewal_notice_when_the_renewal_is_exactly_30_days_away() -> (
    None
):
    # Given a subscription renewing in exactly 30 days
    subscription = a_subscription(days_until_renewal=30)
    channel = RecordingChannel("only", [])

    # When the Sunday (Week) run happens
    run_reminder(
        Period.WEEK,
        FakeScraper([], subscription=subscription),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then the renewal notice is sent
    assert channel.renewals == [(subscription, FRIDAY_EVENING)]


def test_tomorrow_run_sends_no_renewal_notice() -> None:
    # Given a subscription renewing in 20 days
    channel = RecordingChannel("only", [])

    # When the Tomorrow run happens
    run_reminder(
        Period.TOMORROW,
        FakeScraper([], subscription=a_subscription(days_until_renewal=20)),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then no renewal notice is sent
    assert channel.renewals == []


def test_sunday_run_sends_no_renewal_notice_without_a_garden_waste_section() -> None:
    # Given a page with no Garden Waste section
    channel = RecordingChannel("only", [])

    # When the Sunday (Week) run happens
    run_reminder(
        Period.WEEK,
        FakeScraper([], subscription=None),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then no renewal notice is sent
    assert channel.renewals == []


def test_sunday_run_sends_the_renewal_notice_even_when_no_bin_is_collected() -> None:
    # Given a due subscription and no collections that week
    subscription = a_subscription(days_until_renewal=5)
    channel = RecordingChannel("only", [])

    # When the Sunday (Week) run happens
    run_reminder(
        Period.WEEK,
        FakeScraper([], subscription=subscription),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then no collection reminder is sent but the renewal notice is
    assert channel.reminders == []
    assert channel.renewals == [(subscription, FRIDAY_EVENING)]
