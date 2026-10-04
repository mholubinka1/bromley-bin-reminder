from unittest.mock import patch

import requests
from common.settings import ApplicationSettings
from notify import build_notify
from period import Period
from reminder import send_reminders
from support import FRIDAY_EVENING, a_collection, yaml_settings

NTFY_SERVER = "https://ntfy.example.com"


def settings_with_ntfy(ntfy: dict[str, str] | None) -> ApplicationSettings:
    if ntfy is None:
        return ApplicationSettings(yaml_settings())
    return ApplicationSettings(yaml_settings(ntfy=ntfy))


def an_ntfy_configured_application() -> ApplicationSettings:
    return settings_with_ntfy({"server": NTFY_SERVER, "topic": "a-topic"})


def test_night_before_reminder_is_emailed_and_pushed_once_per_bin() -> None:
    # Given ntfy is configured and two bins are collected tomorrow
    settings = an_ntfy_configured_application()
    collections = [
        a_collection("Food Waste", day=3),
        a_collection("Garden Waste", day=3),
    ]

    # When the night-before reminder is sent
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        send_reminders(
            build_notify(settings),
            settings,
            collections,
            FRIDAY_EVENING,
            Period.TOMORROW,
        )

    # Then one email goes out and one high priority push per bin
    assert smtp.return_value.sendmail.call_count == 1
    assert [call.kwargs["json"]["title"] for call in post.call_args_list] == [
        "Food Waste: tomorrow",
        "Garden Waste: tomorrow",
    ]
    assert {call.kwargs["json"]["priority"] for call in post.call_args_list} == {4}


def test_weekly_reminder_is_emailed_and_pushed_once_per_bin_in_order() -> None:
    # Given ntfy is configured and two bins are collected this week
    settings = an_ntfy_configured_application()
    collections = [
        a_collection("Garden Waste", day=5),
        a_collection("Food Waste", day=7),
    ]

    # When the weekly reminder is sent
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        send_reminders(
            build_notify(settings), settings, collections, FRIDAY_EVENING, Period.WEEK
        )

    # Then one email goes out and one default priority push per bin, in order
    assert smtp.return_value.sendmail.call_count == 1
    assert [call.kwargs["json"]["title"] for call in post.call_args_list] == [
        "Garden Waste: this week",
        "Food Waste: this week",
    ]
    assert {call.kwargs["json"]["priority"] for call in post.call_args_list} == {3}


def test_reminder_without_ntfy_configured_only_sends_the_email() -> None:
    # Given ntfy is not configured
    settings = settings_with_ntfy(None)
    collections = [a_collection("Food Waste", day=3)]

    # When the night-before reminder is sent
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        send_reminders(
            build_notify(settings),
            settings,
            collections,
            FRIDAY_EVENING,
            Period.TOMORROW,
        )

    # Then only the email is sent and nothing is posted
    assert smtp.return_value.sendmail.call_count == 1
    post.assert_not_called()


def test_reminder_is_still_pushed_when_the_email_cannot_be_sent() -> None:
    # Given ntfy is configured but the SMTP server is failing
    settings = an_ntfy_configured_application()
    collections = [
        a_collection("Food Waste", day=3),
        a_collection("Garden Waste", day=3),
    ]

    # When the night-before reminder is sent
    with (
        patch("notify.SMTP", side_effect=OSError("smtp down")),
        patch("notify.requests.post") as post,
        patch("common.decorators.time.sleep"),
    ):
        send_reminders(
            build_notify(settings),
            settings,
            collections,
            FRIDAY_EVENING,
            Period.TOMORROW,
        )

    # Then every bin is still pushed and no exception propagates
    assert [call.kwargs["json"]["title"] for call in post.call_args_list] == [
        "Food Waste: tomorrow",
        "Garden Waste: tomorrow",
    ]


def test_reminder_is_still_emailed_when_ntfy_cannot_be_reached() -> None:
    # Given ntfy is configured but the server is unreachable
    settings = an_ntfy_configured_application()
    collections = [
        a_collection("Food Waste", day=3),
        a_collection("Garden Waste", day=3),
    ]

    # When the night-before reminder is sent
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post", side_effect=requests.ConnectionError),
        patch("common.decorators.time.sleep"),
    ):
        send_reminders(
            build_notify(settings),
            settings,
            collections,
            FRIDAY_EVENING,
            Period.TOMORROW,
        )

    # Then the email is still sent and no exception propagates
    assert smtp.return_value.sendmail.call_count == 1


def test_night_before_push_tells_the_resident_to_put_the_bin_out_tonight() -> None:
    # Given ntfy is configured and food waste is collected tomorrow
    settings = an_ntfy_configured_application()
    collections = [a_collection("Food Waste", day=3)]

    # When the night-before reminder is sent
    with patch("notify.SMTP"), patch("notify.requests.post") as post:
        send_reminders(
            build_notify(settings),
            settings,
            collections,
            FRIDAY_EVENING,
            Period.TOMORROW,
        )

    # Then the push is a high priority prompt tagged with the bin's emoji
    assert post.call_args.kwargs["json"] == {
        "topic": "a-topic",
        "title": "Food Waste: tomorrow",
        "message": "Put it out tonight.",
        "priority": 4,
        "tags": ["banana"],
    }


def test_weekly_push_announces_the_collection_date() -> None:
    # Given ntfy is configured and garden waste is collected on Tuesday 6th October
    settings = an_ntfy_configured_application()
    collections = [a_collection("Garden Waste", day=6)]

    # When the weekly reminder is sent
    with patch("notify.SMTP"), patch("notify.requests.post") as post:
        send_reminders(
            build_notify(settings), settings, collections, FRIDAY_EVENING, Period.WEEK
        )

    # Then the push is a default priority announcement tagged with the bin's emoji
    assert post.call_args.kwargs["json"] == {
        "topic": "a-topic",
        "title": "Garden Waste: this week",
        "message": "Collection is Tuesday 6th October.",
        "priority": 3,
        "tags": ["fallen_leaf"],
    }
