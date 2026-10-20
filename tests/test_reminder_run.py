import logging
from datetime import datetime
from unittest.mock import patch

import pytest
from collection import WasteCollection
from common.settings import parse_settings
from notify import build_channels
from period import Period
from reminder import run_reminder
from support import (
    FRIDAY_EVENING,
    LONDON,
    FailingScraper,
    FakeScraper,
    a_collection,
    sent_email,
    yaml_settings,
)

NTFY_SERVER = "https://ntfy.example.com"


def test_tomorrow_run_reminds_only_about_the_bins_collected_tomorrow() -> None:
    # Given ntfy is configured, food waste is collected tomorrow and garden waste later
    settings = parse_settings(
        yaml_settings(ntfy={"server": NTFY_SERVER, "topic": "a-topic"})
    )
    scraper = FakeScraper(
        [
            a_collection("Food Waste", day=3),
            a_collection("Garden Waste", day=6),
        ]
    )

    # When the Tomorrow reminder run executes on Friday evening
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        run_reminder(
            Period.TOMORROW,
            scraper,
            build_channels(settings),
            clock=lambda: FRIDAY_EVENING,
        )

    # Then one email and one push go out, for food waste only, dated tomorrow
    assert smtp.return_value.sendmail.call_count == 1
    email = sent_email(smtp)
    assert email.heading == "Saturday 3rd October"
    assert [row[0] for row in email.rows] == ["Food Waste"]
    assert [call.kwargs["json"]["title"] for call in post.call_args_list] == [
        "Food Waste: tomorrow"
    ]


def test_tomorrow_run_logs_its_progress_and_the_services_it_reminds_about(
    app_log: pytest.LogCaptureFixture,
) -> None:
    # Given food waste is collected tomorrow and garden waste later
    settings = parse_settings(yaml_settings())
    scraper = FakeScraper(
        [
            a_collection("Food Waste", day=3),
            a_collection("Garden Waste", day=6),
        ]
    )

    # When the Tomorrow reminder run executes
    with patch("notify.SMTP"), patch("notify.requests.post"):
        run_reminder(
            Period.TOMORROW,
            scraper,
            build_channels(settings),
            clock=lambda: FRIDAY_EVENING,
        )

    # Then the run logs its progress, including which collections it reminds about
    run_log = [r.getMessage() for r in app_log.records if r.filename == "reminder.py"]
    assert run_log == [
        "Tomorrow reminder run started.",
        "Tomorrow's collections: 1",
        "Tomorrow's collections: [Food Waste]",
        "Sending reminders for tomorrow's collections.",
    ]


def test_tomorrow_run_sends_nothing_when_no_bins_are_collected_tomorrow() -> None:
    # Given ntfy is configured and nothing is collected tomorrow
    settings = parse_settings(
        yaml_settings(ntfy={"server": NTFY_SERVER, "topic": "a-topic"})
    )
    scraper = FakeScraper([a_collection("Garden Waste", day=6)])

    # When the Tomorrow reminder run executes
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        run_reminder(
            Period.TOMORROW,
            scraper,
            build_channels(settings),
            clock=lambda: FRIDAY_EVENING,
        )

    # Then no email and no push go out
    assert smtp.return_value.sendmail.call_count == 0
    assert post.call_count == 0


def test_run_reads_the_clock_once() -> None:
    # Given a clock that counts how often it is read and a bin collected tomorrow
    settings = parse_settings(yaml_settings())
    scraper = FakeScraper([a_collection("Food Waste", day=3)])
    clock_reads = 0

    def counting_clock() -> datetime:
        nonlocal clock_reads
        clock_reads += 1
        return FRIDAY_EVENING

    # When the Tomorrow reminder run selects and sends
    with patch("notify.SMTP") as smtp, patch("notify.requests.post"):
        run_reminder(
            Period.TOMORROW,
            scraper,
            build_channels(settings),
            clock=counting_clock,
        )

    # Then the reminder went out and the clock was read exactly once
    assert smtp.return_value.sendmail.call_count == 1
    assert clock_reads == 1


@pytest.mark.parametrize(
    ("period", "expected_failure_logs"),
    [
        (Period.TOMORROW, ["Tomorrow reminder run failed."]),
        # the Week run also reads the subscription, which fails the same way
        (Period.WEEK, ["Week reminder run failed.", "Week renewal check failed."]),
    ],
)
def test_run_that_cannot_scrape_is_logged_and_sends_nothing(
    period: Period, expected_failure_logs: list[str], app_log: pytest.LogCaptureFixture
) -> None:
    # Given the WasteWorks page cannot be scraped
    settings = parse_settings(yaml_settings())

    # When the reminder run executes
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        run_reminder(
            period,
            FailingScraper(),
            build_channels(settings),
            clock=lambda: FRIDAY_EVENING,
        )

    # Then the failure is logged against the period, nothing is sent and nothing propagates
    failures = [r for r in app_log.records if r.levelno == logging.ERROR]
    assert [r.getMessage() for r in failures] == expected_failure_logs
    assert all(r.exc_info is not None for r in failures)
    assert smtp.return_value.sendmail.call_count == 0
    assert post.call_count == 0


def test_week_run_reminds_about_this_weeks_bins_earliest_first(
    app_log: pytest.LogCaptureFixture,
) -> None:
    # Given ntfy is configured, and bins are collected this week (listed out of order) and later
    settings = parse_settings(
        yaml_settings(ntfy={"server": NTFY_SERVER, "topic": "a-topic"})
    )
    scraper = FakeScraper(
        [
            a_collection("Garden Waste", day=8),
            a_collection("Paper & Cardboard", day=20),
            a_collection("Food Waste", day=6),
        ]
    )

    # When the Week reminder run executes on Friday evening
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        run_reminder(
            Period.WEEK,
            scraper,
            build_channels(settings),
            clock=lambda: FRIDAY_EVENING,
        )

    # Then this week's bins are emailed and pushed earliest first, and the run logs them
    email = sent_email(smtp)
    assert email.subject == "Weekly Collections"
    assert [row[0] for row in email.rows] == ["Food Waste", "Garden Waste"]
    assert [call.kwargs["json"]["title"] for call in post.call_args_list] == [
        "Food Waste: this week",
        "Garden Waste: this week",
    ]
    assert "This week's collections: [Food Waste, Garden Waste]" in [
        r.getMessage() for r in app_log.records
    ]


def test_run_whose_scrape_crosses_midnight_selects_for_the_day_after_the_scrape() -> (
    None
):
    # Given the run starts on Friday night and the scrape finishes after midnight,
    # with food waste dated Sunday 4th October
    settings = parse_settings(yaml_settings())
    time_now = {"now": datetime(2026, 10, 2, 23, 58, tzinfo=LONDON)}

    class MidnightCrossingScraper:
        def get_upcoming_collections(self) -> list[WasteCollection]:
            time_now["now"] = datetime(2026, 10, 3, 0, 3, tzinfo=LONDON)
            return [a_collection("Food Waste", day=4)]

        def get_garden_waste_subscription(self) -> None:
            return None

    # When the Tomorrow reminder run executes
    with patch("notify.SMTP") as smtp:
        run_reminder(
            Period.TOMORROW,
            MidnightCrossingScraper(),
            build_channels(settings),
            clock=lambda: time_now["now"],
        )

    # Then the run reminds about Sunday's bins, as the day after the scrape finished
    email = sent_email(smtp)
    assert email.heading == "Sunday 4th October"
    assert [row[0] for row in email.rows] == ["Food Waste"]
