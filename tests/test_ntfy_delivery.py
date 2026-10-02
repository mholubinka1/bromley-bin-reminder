import io
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch

import requests
from common.logging import APP_LOGGER_NAME
from notify import Notify, NtfyClient
from support import a_notification

TOPIC = "bromley-bin-collections-ntfy-test"


def an_ntfy_notifier() -> Notify:
    return Notify(
        email_client=MagicMock(),
        ntfy_client=NtfyClient(server="https://ntfy.example.com", topic=TOPIC),
    )


@contextmanager
def captured_app_logs() -> Iterator[io.StringIO]:
    # caplog cannot see the app logger because it does not propagate
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.addHandler(handler)
    try:
        yield log_stream
    finally:
        app_logger.removeHandler(handler)


def test_each_notification_is_posted_to_the_ntfy_server_as_json() -> None:
    # Given a notifier configured with an ntfy server and topic
    notify = an_ntfy_notifier()

    # When the notification is sent
    with patch("notify.requests.post") as post:
        notify.send_ntfy([a_notification()])

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
    notify = an_ntfy_notifier()

    # When the notification is sent
    with (
        patch("notify.requests.post") as post,
        patch("common.decorators.time.sleep"),
    ):
        post.side_effect = [requests.ConnectionError("unreachable"), MagicMock()]
        notify.send_ntfy([a_notification()])

    # Then it is posted a second time
    assert post.call_count == 2


def test_one_failing_notification_does_not_stop_the_others_being_delivered() -> None:
    # Given three notifications, the second of which the server always rejects
    notify = an_ntfy_notifier()
    notifications = [
        a_notification(title=title) for title in ("First", "Second", "Third")
    ]

    def post(url: str, json: dict[str, Any], timeout: int) -> MagicMock:
        if json["title"] == "Second":
            raise requests.ConnectionError("unreachable")
        return MagicMock()

    # When the notifications are sent
    with (
        captured_app_logs() as log_stream,
        patch("notify.requests.post", side_effect=post) as mock_post,
        patch("common.decorators.time.sleep"),
    ):
        notify.send_ntfy(notifications)

    # Then the first and third are still delivered and no exception propagates
    attempted = [call.kwargs["json"]["title"] for call in mock_post.call_args_list]
    assert attempted == ["First", "Second", "Second", "Second", "Third"]

    # And the failure is logged by title without revealing the topic
    logs = log_stream.getvalue()
    assert "Second" in logs
    assert TOPIC not in logs


def test_notifications_are_still_delivered_when_the_server_answers_with_an_error() -> (
    None
):
    # Given an ntfy server that answers every request with HTTP 500
    notify = an_ntfy_notifier()
    notifications = [a_notification(title=title) for title in ("First", "Second")]
    error_response = MagicMock()
    error_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

    # When the notifications are sent
    with (
        captured_app_logs() as log_stream,
        patch("notify.requests.post", return_value=error_response) as post,
        patch("common.decorators.time.sleep"),
    ):
        notify.send_ntfy(notifications)

    # Then every notification is still attempted, no exception propagates
    # and the failures are logged without revealing the topic
    attempted = {call.kwargs["json"]["title"] for call in post.call_args_list}
    assert attempted == {"First", "Second"}
    logs = log_stream.getvalue()
    assert "Failed to send ntfy notification [First]" in logs
    assert "Failed to send ntfy notification [Second]" in logs
    assert TOPIC not in logs


def test_nothing_is_posted_when_ntfy_is_not_configured() -> None:
    # Given a notifier with no ntfy client
    notify = Notify(email_client=MagicMock())

    # When a notification is sent
    with patch("notify.requests.post") as post:
        notify.send_ntfy([a_notification()])

    # Then nothing is posted
    post.assert_not_called()
