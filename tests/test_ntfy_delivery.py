from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests
from collection import WasteCollection
from common.settings import parse_settings
from notify import EmailChannel, NtfyChannel, NtfyClient, build_channels
from period import Period
from support import FRIDAY_EVENING, a_collection, yaml_settings

TOPIC = "bromley-bin-collections-ntfy-test"


def an_ntfy_channel() -> NtfyChannel:
    return NtfyChannel(NtfyClient(server="https://ntfy.example.com", topic=TOPIC))


def collections_named(*service_names: str) -> list[WasteCollection]:
    return [a_collection(name) for name in service_names]


def test_each_notification_is_posted_to_the_ntfy_server_as_json() -> None:
    # Given a notifier configured with an ntfy server and topic
    channel = an_ntfy_channel()

    # When the notification is sent
    with patch("notify.requests.post") as post:
        channel.send(collections_named("Food Waste"), FRIDAY_EVENING, Period.TOMORROW)

    # Then it is published as JSON to the server, naming the topic
    assert post.call_count == 1
    assert post.call_args.args[0] == "https://ntfy.example.com"
    assert post.call_args.kwargs["json"] == {
        "topic": TOPIC,
        "title": "Food Waste: tomorrow",
        "message": "Put it out tonight.",
        "priority": 4,
        "tags": ["banana"],
    }
    assert post.call_args.kwargs["timeout"] > 0


def test_a_notification_is_retried_when_the_ntfy_server_fails_once() -> None:
    # Given an ntfy server that fails once and then accepts the notification
    channel = an_ntfy_channel()

    # When the notification is sent
    with (
        patch("notify.requests.post") as post,
        patch("common.decorators.time.sleep"),
    ):
        post.side_effect = [requests.ConnectionError("unreachable"), MagicMock()]
        channel.send(collections_named("Food Waste"), FRIDAY_EVENING, Period.TOMORROW)

    # Then it is posted a second time
    assert post.call_count == 2


def test_one_failing_notification_does_not_stop_the_others_being_delivered(
    app_log: pytest.LogCaptureFixture,
) -> None:
    # Given three notifications, the second of which the server always rejects
    channel = an_ntfy_channel()
    collections = collections_named("First", "Second", "Third")

    def post(url: str, json: dict[str, Any], timeout: int) -> MagicMock:
        if json["title"] == "Second: tomorrow":
            raise requests.ConnectionError("unreachable")
        return MagicMock()

    # When the notifications are sent
    with (
        patch("notify.requests.post", side_effect=post) as mock_post,
        patch("common.decorators.time.sleep"),
    ):
        channel.send(collections, FRIDAY_EVENING, Period.TOMORROW)

    # Then the first and third are still delivered and no exception propagates
    attempted = [call.kwargs["json"]["title"] for call in mock_post.call_args_list]
    assert attempted[0] == "First: tomorrow"
    assert attempted[-1] == "Third: tomorrow"
    assert attempted.count("Second: tomorrow") > 1

    # And the failure is logged by title without revealing the topic
    assert "Second: tomorrow" in app_log.text
    assert TOPIC not in app_log.text


def test_notifications_are_still_delivered_when_the_server_answers_with_an_error(
    app_log: pytest.LogCaptureFixture,
) -> None:
    # Given an ntfy server that answers every request with HTTP 500
    channel = an_ntfy_channel()
    collections = collections_named("First", "Second")
    error_response = MagicMock()
    error_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

    # When the notifications are sent
    with (
        patch("notify.requests.post", return_value=error_response) as post,
        patch("common.decorators.time.sleep"),
    ):
        channel.send(collections, FRIDAY_EVENING, Period.TOMORROW)

    # Then every notification is still attempted, no exception propagates
    # and the failures are logged without revealing the topic
    attempted = {call.kwargs["json"]["title"] for call in post.call_args_list}
    assert attempted == {"First: tomorrow", "Second: tomorrow"}
    assert app_log.text.count("Failed to send ntfy notification [First: tomorrow]") == 1
    assert "Failed to send ntfy notification [Second: tomorrow]" in app_log.text
    assert TOPIC not in app_log.text


def test_nothing_is_posted_when_ntfy_is_not_configured() -> None:
    # Given application settings with no ntfy section
    settings = parse_settings(yaml_settings())

    # When the Channels are built and a reminder is sent through them
    channels = build_channels(settings)
    with patch("notify.SMTP"), patch("notify.requests.post") as post:
        for channel in channels:
            channel.send(
                collections_named("Food Waste"), FRIDAY_EVENING, Period.TOMORROW
            )

    # Then email is the only Channel and nothing is posted
    assert len(channels) == 1
    assert isinstance(channels[0], EmailChannel)
    post.assert_not_called()
