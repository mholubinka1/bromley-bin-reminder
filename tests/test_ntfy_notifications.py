import pytest
from notification import build_ntfy_notifications
from period import Period
from support import a_collection


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
