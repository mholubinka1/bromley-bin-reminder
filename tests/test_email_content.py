from unittest.mock import patch

from common.settings import ApplicationSettings
from notify import build_notify
from period import Period
from reminder import send_reminders
from support import (
    FRIDAY_EVENING,
    a_collection,
    sent_email,
    sent_email_html,
    yaml_settings,
)


def test_night_before_email_lists_each_bin_with_its_colour_under_tomorrows_date() -> (
    None
):
    # Given food waste is collected tomorrow, Saturday 3rd October
    settings = ApplicationSettings(yaml_settings())
    collections = [a_collection("Food Waste", day=3)]

    # When the night-before reminder is sent on Friday evening
    with patch("notify.SMTP") as smtp:
        send_reminders(
            build_notify(settings),
            settings,
            collections,
            now=FRIDAY_EVENING,
            period=Period.TOMORROW,
        )

    # Then the email is high priority and lists the bin and its colour under tomorrow's date
    email = sent_email(smtp)
    assert email.subject == "REMINDER: Bins"
    assert email.x_priority == "1"
    assert email.importance == "high"
    assert email.title == "Saturday 3rd October - Bin Collections"
    assert email.heading == "Saturday 3rd October"
    assert email.header_cells == ["Bin Type"]
    assert email.rows == [["Food Waste", "#d0a500"]]


def test_weekly_email_lists_each_bin_with_its_colour_and_collection_date() -> None:
    # Given food waste and garden waste are collected this week
    settings = ApplicationSettings(yaml_settings())
    collections = [
        a_collection("Food Waste", day=6),
        a_collection("Garden Waste", day=8),
    ]

    # When the weekly reminder is sent on Friday evening
    with patch("notify.SMTP") as smtp:
        send_reminders(
            build_notify(settings),
            settings,
            collections,
            now=FRIDAY_EVENING,
            period=Period.WEEK,
        )

    # Then the email is headed with the week commencing date and lists each bin, colour and date
    email = sent_email(smtp)
    assert email.subject == "Weekly Collections"
    assert email.title == "Week Commencing: Friday 2nd October - Bin Collections"
    assert email.heading == "Week Commencing: Friday 2nd October"
    assert email.header_cells == ["Bin Type", "Collection Date"]
    assert email.rows == [
        ["Food Waste", "#d0a500", "Tuesday 6th October"],
        ["Garden Waste", "#8B4513", "Thursday 8th October"],
    ]


def test_weekly_email_closes_every_table_cell_it_opens() -> None:
    # Given food waste is collected this week
    settings = ApplicationSettings(yaml_settings())
    collections = [a_collection("Food Waste", day=6)]

    # When the weekly reminder is sent
    with patch("notify.SMTP") as smtp:
        send_reminders(
            build_notify(settings),
            settings,
            collections,
            now=FRIDAY_EVENING,
            period=Period.WEEK,
        )

    # Then every table cell in the email is closed
    html = sent_email_html(smtp)
    assert html.count("<td") == html.count("</td>")
