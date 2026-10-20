from datetime import datetime
from unittest.mock import MagicMock, patch

import requests
from common.settings import parse_settings
from notify import Channel, build_channels
from subscription import GardenWasteSubscription
from support import FRIDAY_EVENING, LONDON, sent_email, sent_email_html, yaml_settings

NTFY_SERVER = "https://ntfy.example.com"
SUBSCRIPTION = GardenWasteSubscription(
    renewal_date=datetime(2027, 6, 12, tzinfo=LONDON),
    subscription_text="£80.00 per year (1 bin)",
)


def email_and_ntfy_channels() -> list[Channel]:
    settings = parse_settings(
        yaml_settings(ntfy={"server": NTFY_SERVER, "topic": "a-topic"})
    )
    return build_channels(settings)


def test_renewal_notice_email_states_the_date_and_price() -> None:
    # Given the e-mail Channel
    channel = build_channels(parse_settings(yaml_settings()))[0]

    # When the renewal notice is sent
    with patch("notify.SMTP") as smtp:
        channel.send_renewal(SUBSCRIPTION, FRIDAY_EVENING)

    # Then the e-mail names the date and the price text
    assert sent_email(smtp).subject == "Garden Waste subscription due for renewal"
    body = sent_email_html(smtp)
    assert "12 June 2027" in body
    assert "£80.00 per year (1 bin)" in body


def test_renewal_notice_ntfy_push_states_the_date_and_price() -> None:
    # Given the ntfy Channel
    channel = email_and_ntfy_channels()[1]

    # When the renewal notice is sent
    with patch("notify.requests.post") as post:
        channel.send_renewal(SUBSCRIPTION, FRIDAY_EVENING)

    # Then one push is published with the date and the price text
    assert post.call_count == 1
    assert post.call_args.kwargs["json"] == {
        "topic": "a-topic",
        "title": "Garden Waste: due for renewal",
        "message": "Subscription is due for renewal on 12 June 2027 (£80.00 per year (1 bin)).",
        "priority": 3,
        "tags": ["fallen_leaf"],
    }


AUTOMATIC_SUBSCRIPTION = GardenWasteSubscription(
    renewal_date=datetime(2027, 6, 12, tzinfo=LONDON),
    subscription_text="£80.00 per year (1 bin)",
    renews_automatically=True,
)


def test_renewal_notice_email_reassures_when_the_subscription_renews_automatically() -> (
    None
):
    # Given the e-mail Channel and a subscription that renews automatically
    channel = build_channels(parse_settings(yaml_settings()))[0]

    # When the renewal notice is sent
    with patch("notify.SMTP") as smtp:
        channel.send_renewal(AUTOMATIC_SUBSCRIPTION, FRIDAY_EVENING)

    # Then the e-mail says it renews automatically by direct debit
    assert "renews automatically by direct debit" in sent_email_html(smtp)


def test_renewal_notice_email_has_no_reassurance_for_a_manual_subscription() -> None:
    # Given the e-mail Channel and a subscription that does not renew automatically
    channel = build_channels(parse_settings(yaml_settings()))[0]

    # When the renewal notice is sent
    with patch("notify.SMTP") as smtp:
        channel.send_renewal(SUBSCRIPTION, FRIDAY_EVENING)

    # Then the e-mail does not claim it renews automatically
    assert "automatically" not in sent_email_html(smtp)


def test_renewal_notice_ntfy_push_reassures_and_has_no_reassurance_when_manual() -> (
    None
):
    # Given the ntfy Channel
    channel = email_and_ntfy_channels()[1]

    # When the renewal notice is sent for an automatic and a manual subscription
    with patch("notify.requests.post") as post:
        channel.send_renewal(AUTOMATIC_SUBSCRIPTION, FRIDAY_EVENING)
        channel.send_renewal(SUBSCRIPTION, FRIDAY_EVENING)

    # Then only the automatic one says it renews automatically by direct debit
    automatic, manual = (call.kwargs["json"]["message"] for call in post.call_args_list)
    assert "renews automatically by direct debit" in automatic
    assert "automatically" not in manual


OVERDUE_AT = datetime(2027, 6, 20, 18, 0, tzinfo=LONDON)


def test_overdue_notice_email_says_the_subscription_is_overdue() -> None:
    # Given the e-mail Channel and a subscription whose renewal date has passed
    channel = build_channels(parse_settings(yaml_settings()))[0]

    # When the renewal notice is sent
    with patch("notify.SMTP") as smtp:
        channel.send_renewal(AUTOMATIC_SUBSCRIPTION, OVERDUE_AT)

    # Then the e-mail says it is overdue, with the date and price, and no reassurance
    assert sent_email(smtp).subject == "Garden Waste subscription overdue"
    body = sent_email_html(smtp)
    assert "overdue" in body
    assert "12 June 2027" in body
    assert "£80.00 per year (1 bin)" in body
    assert "automatically" not in body


def test_overdue_notice_ntfy_push_has_a_higher_priority_than_a_due_notice() -> None:
    # Given the ntfy Channel
    channel = email_and_ntfy_channels()[1]

    # When an overdue and a due notice are sent
    with patch("notify.requests.post") as post:
        channel.send_renewal(SUBSCRIPTION, OVERDUE_AT)
        channel.send_renewal(SUBSCRIPTION, FRIDAY_EVENING)

    # Then the overdue push says so and outranks the due one
    overdue, due = (call.kwargs["json"] for call in post.call_args_list)
    assert overdue["title"] == "Garden Waste: subscription overdue"
    assert "12 June 2027" in overdue["message"]
    assert overdue["priority"] > due["priority"]


def test_a_failing_email_channel_does_not_block_the_ntfy_renewal_notice() -> None:
    # Given an e-mail Channel whose SMTP server is down, and a working ntfy Channel
    channels = email_and_ntfy_channels()

    # When the renewal notice is sent through each Channel
    with (
        patch("notify.SMTP", side_effect=OSError("smtp down")),
        patch("notify.requests.post", return_value=MagicMock()) as post,
        patch("common.decorators.time.sleep"),
    ):
        for channel in channels:
            channel.send_renewal(SUBSCRIPTION, FRIDAY_EVENING)

    # Then the ntfy push is still published and nothing propagates
    assert post.call_count == 1


def test_a_failing_ntfy_channel_does_not_block_the_email_renewal_notice() -> None:
    # Given a working e-mail Channel and an ntfy server that is down
    channels = email_and_ntfy_channels()

    # When the renewal notice is sent through each Channel, ntfy first
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post", side_effect=requests.ConnectionError("down")),
        patch("common.decorators.time.sleep"),
    ):
        for channel in reversed(channels):
            channel.send_renewal(SUBSCRIPTION, FRIDAY_EVENING)

    # Then the e-mail is still sent
    assert smtp.return_value.sendmail.call_count == 1
