from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import requests
from collection import WasteCollection
from common.settings import ApplicationSettings
from notify import Notify, NtfyClient, SMTPClient
from reminder import send_reminders

LONDON = ZoneInfo("Europe/London")
NTFY_SERVER = "https://ntfy.example.com"


def a_collection(service_name: str, day: int) -> WasteCollection:
    return WasteCollection(
        service_name=service_name,
        next_collection_date=datetime(2026, 10, day, tzinfo=LONDON),
        is_tomorrow=True,
        is_this_week=True,
    )


def settings_with_ntfy(ntfy: dict[str, str] | None) -> ApplicationSettings:
    yaml_settings = {
        "remind": {
            "url": "https://example.com/waste",
            "email_addresses": ["resident@example.com"],
            "time": "18:00",
        },
        "smtp": {
            "username": "bins@example.com",
            "password": "secret",
            "server": "smtp.example.com",
            "port": 587,
        },
    }
    if ntfy is not None:
        yaml_settings["ntfy"] = ntfy
    return ApplicationSettings(yaml_settings)


def a_notifier(settings: ApplicationSettings) -> Notify:
    smtp_client = SMTPClient(
        username=settings.smtp.username,
        password=settings.smtp.password,
        server=settings.smtp.server,
        port=settings.smtp.port,
    )
    ntfy_client = (
        NtfyClient(server=settings.ntfy.server, topic=settings.ntfy.topic)
        if settings.ntfy
        else None
    )
    return Notify(email_client=smtp_client, ntfy_client=ntfy_client)


def test_night_before_reminder_is_emailed_and_pushed_once_per_bin() -> None:
    # Given ntfy is configured and two bins are collected tomorrow
    settings = settings_with_ntfy({"server": NTFY_SERVER, "topic": "a-topic"})
    collections = [
        a_collection("Food Waste", day=3),
        a_collection("Garden Waste", day=3),
    ]

    # When the night-before reminder is sent
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        send_reminders(a_notifier(settings), settings, collections, LONDON, "tomorrow")

    # Then one email goes out and one high priority push per bin
    assert smtp.return_value.sendmail.call_count == 1
    assert [call.kwargs["json"]["title"] for call in post.call_args_list] == [
        "Food Waste: tomorrow",
        "Garden Waste: tomorrow",
    ]
    assert {call.kwargs["json"]["priority"] for call in post.call_args_list} == {4}


def test_weekly_reminder_is_emailed_and_pushed_once_per_bin_in_order() -> None:
    # Given ntfy is configured and two bins are collected this week
    settings = settings_with_ntfy({"server": NTFY_SERVER, "topic": "a-topic"})
    collections = [
        a_collection("Garden Waste", day=5),
        a_collection("Food Waste", day=7),
    ]

    # When the weekly reminder is sent
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        send_reminders(a_notifier(settings), settings, collections, LONDON, "week")

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
        send_reminders(a_notifier(settings), settings, collections, LONDON, "tomorrow")

    # Then only the email is sent and nothing is posted
    assert smtp.return_value.sendmail.call_count == 1
    post.assert_not_called()


def test_reminder_is_still_pushed_when_the_email_cannot_be_sent() -> None:
    # Given ntfy is configured but the SMTP server is failing
    settings = settings_with_ntfy({"server": NTFY_SERVER, "topic": "a-topic"})
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
        send_reminders(a_notifier(settings), settings, collections, LONDON, "tomorrow")

    # Then every bin is still pushed and no exception propagates
    assert [call.kwargs["json"]["title"] for call in post.call_args_list] == [
        "Food Waste: tomorrow",
        "Garden Waste: tomorrow",
    ]


def test_reminder_is_still_emailed_when_ntfy_cannot_be_reached() -> None:
    # Given ntfy is configured but the server is unreachable
    settings = settings_with_ntfy({"server": NTFY_SERVER, "topic": "a-topic"})
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
        send_reminders(a_notifier(settings), settings, collections, LONDON, "tomorrow")

    # Then the email is still sent and no exception propagates
    assert smtp.return_value.sendmail.call_count == 1
