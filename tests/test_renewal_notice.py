from datetime import timedelta

from collection import WasteCollection
from period import Period
from reminder import run_reminder
from subscription import GardenWasteSubscription
from support import FRIDAY_EVENING, FakeScraper, RecordingChannel, a_collection

SUBSCRIPTION_TEXT = "£80.00 per year (1 bin)"


def a_subscription(
    days_until_renewal: int, in_progress: bool = False
) -> GardenWasteSubscription:
    return GardenWasteSubscription(
        renewal_date=FRIDAY_EVENING + timedelta(days=days_until_renewal),
        subscription_text=SUBSCRIPTION_TEXT,
        in_progress=in_progress,
    )


class SubscriptionFailingScraper(FakeScraper):
    def get_garden_waste_subscription(self) -> GardenWasteSubscription | None:
        raise RuntimeError("WasteWorks page could not be rendered")


class CollectionsFailingScraper(FakeScraper):
    def get_upcoming_collections(self) -> list[WasteCollection]:
        raise RuntimeError("WasteWorks page could not be rendered")


def test_sunday_run_sends_no_renewal_notice_while_a_cancellation_or_pending_subscription_is_in_progress() -> (
    None
):
    # Given a due subscription that has a cancellation or new subscription in progress
    subscription = a_subscription(days_until_renewal=5, in_progress=True)
    channel = RecordingChannel("only", [])

    # When the Sunday (Week) run happens
    run_reminder(
        Period.WEEK,
        FakeScraper([], subscription=subscription),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then no renewal notice is sent
    assert channel.renewals == []


def test_a_failing_subscription_read_does_not_stop_the_collection_reminder() -> None:
    # Given a bin collected this week and a subscription read that fails
    collections = [a_collection("Food Waste", day=3)]
    channel = RecordingChannel("only", [])

    # When the Sunday (Week) run happens
    run_reminder(
        Period.WEEK,
        SubscriptionFailingScraper(collections),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then the collection reminder is still sent and there is no renewal notice
    assert [reminder[0] for reminder in channel.reminders] == [collections]
    assert channel.renewals == []


def test_a_failing_collection_scrape_does_not_stop_the_renewal_notice() -> None:
    # Given a collection scrape that fails and a due subscription
    subscription = a_subscription(days_until_renewal=5)
    channel = RecordingChannel("only", [])

    # When the Sunday (Week) run happens
    run_reminder(
        Period.WEEK,
        CollectionsFailingScraper([], subscription=subscription),
        [channel],
        clock=lambda: FRIDAY_EVENING,
    )

    # Then the renewal notice is still sent and no collection reminder is
    assert channel.renewals == [(subscription, FRIDAY_EVENING)]
    assert channel.reminders == []


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


def test_sunday_run_sends_a_renewal_notice_when_the_subscription_is_overdue() -> None:
    # Given a subscription whose renewal date passed 3 days ago
    subscription = a_subscription(days_until_renewal=-3)
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
