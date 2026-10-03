import pytest
from notification import build_ntfy_notifications
from period import Period
from support import a_collection


def test_night_before_notification_prompts_putting_the_bin_out() -> None:
    # Given food waste is collected tomorrow
    collections = [a_collection("Food Waste")]

    # When the night-before notifications are built
    notifications = build_ntfy_notifications(collections, period=Period.TOMORROW)

    # Then there is one high priority notification tagged with the banana emoji
    assert len(notifications) == 1
    assert notifications[0].title == "Food Waste: tomorrow"
    assert notifications[0].message == "Put it out tonight."
    assert notifications[0].priority == 4
    assert notifications[0].tags == ["banana"]


def test_weekly_notifications_announce_each_service_with_its_collection_date() -> None:
    # Given paper is collected on Tuesday and mixed recycling on Wednesday
    collections = [
        a_collection("Paper & Cardboard", day=6),
        a_collection("Mixed Recycling (Cans, Plastics & Glass)", day=7),
    ]

    # When the weekly notifications are built
    notifications = build_ntfy_notifications(collections, period=Period.WEEK)

    # Then there is one default priority notification per service, in order
    assert [n.title for n in notifications] == [
        "Paper & Cardboard: this week",
        "Mixed Recycling (Cans, Plastics & Glass): this week",
    ]
    assert [n.message for n in notifications] == [
        "Collection is Tuesday 6th October.",
        "Collection is Wednesday 7th October.",
    ]
    assert [n.priority for n in notifications] == [3, 3]


@pytest.mark.parametrize(
    ("service_name", "emoji"),
    [
        ("Mixed Recycling (Cans, Plastics & Glass)", "recycle"),
        ("Paper & Cardboard", "newspaper"),
        ("Garden Waste", "fallen_leaf"),
        ("Non-Recyclable Refuse", "wastebasket"),
        ("Food Waste", "banana"),
    ],
)
def test_each_service_is_tagged_with_its_own_emoji(
    service_name: str, emoji: str
) -> None:
    # Given a collection of the service
    collections = [a_collection(service_name)]

    # When the notifications are built
    notifications = build_ntfy_notifications(collections, period=Period.WEEK)

    # Then the notification carries only that service's emoji
    assert notifications[0].tags == [emoji]


def test_unrecognised_service_gets_a_generic_litter_tag() -> None:
    # Given a collection of a service we have no emoji for
    collections = [a_collection("Bulky Waste")]

    # When the notifications are built
    notifications = build_ntfy_notifications(collections, period=Period.WEEK)

    # Then the notification is tagged with the generic litter emoji
    assert notifications[0].tags == ["put_litter_in_its_place"]


def test_no_collections_means_no_notifications() -> None:
    # Given nothing is being collected
    # When the notifications are built
    notifications = build_ntfy_notifications([], period=Period.WEEK)

    # Then there are none
    assert notifications == []
