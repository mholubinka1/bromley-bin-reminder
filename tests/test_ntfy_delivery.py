import io
import logging
from typing import Any
from unittest.mock import MagicMock, patch

import requests
from common.logging import APP_LOGGER_NAME
from notification import NtfyNotification
from notify import Notify, NtfyClient

TOPIC = "bromley-bin-collections-ntfy-test"


def test_each_notification_is_posted_to_the_ntfy_server_as_json() -> None:
    # Given a notifier configured with an ntfy server and topic
    notify = Notify(
        email_client=MagicMock(),
        ntfy_client=NtfyClient(server="https://ntfy.example.com", topic=TOPIC),
    )
    notification = NtfyNotification(
        title="Food Waste: tomorrow",
        message="Put it out tonight.",
        priority=4,
        tags=["banana"],
    )

    # When the notification is sent
    with patch("notify.requests.post") as post:
        notify.send_ntfy([notification])

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
    notify = Notify(
        email_client=MagicMock(),
        ntfy_client=NtfyClient(server="https://ntfy.example.com", topic=TOPIC),
    )
    notification = NtfyNotification(
        title="Food Waste: tomorrow",
        message="Put it out tonight.",
        priority=4,
        tags=["banana"],
    )

    # When the notification is sent
    with (
        patch("notify.requests.post") as post,
        patch("common.decorators.time.sleep"),
    ):
        post.side_effect = [requests.ConnectionError("unreachable"), MagicMock()]
        notify.send_ntfy([notification])

    # Then it is posted a second time
    assert post.call_count == 2


def test_one_failing_notification_does_not_stop_the_others_being_delivered() -> None:
    # Given three notifications, the second of which the server always rejects
    notify = Notify(
        email_client=MagicMock(),
        ntfy_client=NtfyClient(server="https://ntfy.example.com", topic=TOPIC),
    )
    notifications = [
        NtfyNotification(title=title, message="m", priority=3, tags=[])
        for title in ("First", "Second", "Third")
    ]

    def post(url: str, json: dict[str, Any], timeout: int) -> MagicMock:
        if json["title"] == "Second":
            raise requests.ConnectionError("unreachable")
        return MagicMock()

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.addHandler(handler)

    # When the notifications are sent
    try:
        with (
            patch("notify.requests.post", side_effect=post) as mock_post,
            patch("common.decorators.time.sleep"),
        ):
            notify.send_ntfy(notifications)
    finally:
        app_logger.removeHandler(handler)

    # Then the first and third are still delivered and no exception propagates
    delivered = [
        call.kwargs["json"]["title"]
        for call in mock_post.call_args_list
        if call.kwargs["json"]["title"] != "Second"
    ]
    assert delivered == ["First", "Third"]

    # And the failure is logged by title without revealing the topic
    logs = log_stream.getvalue()
    assert "Second" in logs
    assert TOPIC not in logs


def test_nothing_is_posted_when_ntfy_is_not_configured() -> None:
    # Given a notifier with no ntfy client
    notify = Notify(email_client=MagicMock())
    notification = NtfyNotification(
        title="Food Waste: tomorrow",
        message="Put it out tonight.",
        priority=4,
        tags=["banana"],
    )

    # When a notification is sent
    with patch("notify.requests.post") as post:
        notify.send_ntfy([notification])

    # Then nothing is posted
    post.assert_not_called()
