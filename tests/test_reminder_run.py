import logging
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from common.logging import APP_LOGGER_NAME
from common.settings import ApplicationSettings
from notify import build_notify
from period import Period
from reminder import run_reminder
from support import (
    FRIDAY_EVENING,
    FailingScraper,
    FakeScraper,
    a_collection,
    sent_email,
    yaml_settings,
)

NTFY_SERVER = "https://ntfy.example.com"


@pytest.fixture
def app_log(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    app_logger.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger=APP_LOGGER_NAME)
    yield caplog
    app_logger.removeHandler(caplog.handler)


def test_tomorrow_run_reminds_only_about_the_bins_collected_tomorrow() -> None:
    # Given ntfy is configured, food waste is collected tomorrow and garden waste later
    settings = ApplicationSettings(
        yaml_settings(ntfy={"server": NTFY_SERVER, "topic": "a-topic"})
    )
    scraper = FakeScraper(
        [
            a_collection("Food Waste", day=3, is_tomorrow=True),
            a_collection("Garden Waste", day=6, is_tomorrow=False),
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
            build_notify(settings),
            settings,
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
    settings = ApplicationSettings(yaml_settings())
    scraper = FakeScraper(
        [
            a_collection("Food Waste", day=3, is_tomorrow=True),
            a_collection("Garden Waste", day=6, is_tomorrow=False),
        ]
    )

    # When the Tomorrow reminder run executes
    with patch("notify.SMTP"), patch("notify.requests.post"):
        run_reminder(
            Period.TOMORROW,
            scraper,
            build_notify(settings),
            settings,
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
    settings = ApplicationSettings(
        yaml_settings(ntfy={"server": NTFY_SERVER, "topic": "a-topic"})
    )
    scraper = FakeScraper([a_collection("Garden Waste", day=6, is_tomorrow=False)])

    # When the Tomorrow reminder run executes
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        run_reminder(
            Period.TOMORROW,
            scraper,
            build_notify(settings),
            settings,
            clock=lambda: FRIDAY_EVENING,
        )

    # Then no email and no push go out
    assert smtp.return_value.sendmail.call_count == 0
    assert post.call_count == 0


@pytest.mark.parametrize("period", list(Period))
def test_run_that_cannot_scrape_is_logged_and_sends_nothing(
    period: Period, app_log: pytest.LogCaptureFixture
) -> None:
    # Given the WasteWorks page cannot be scraped
    settings = ApplicationSettings(yaml_settings())

    # When the reminder run executes
    with (
        patch("notify.SMTP") as smtp,
        patch("notify.requests.post") as post,
    ):
        run_reminder(
            period,
            FailingScraper(),
            build_notify(settings),
            settings,
            clock=lambda: FRIDAY_EVENING,
        )

    # Then the failure is logged against the period, nothing is sent and nothing propagates
    failures = [r for r in app_log.records if r.levelno == logging.ERROR]
    assert [r.getMessage() for r in failures] == [
        f"{period.name.title()} reminder run failed."
    ]
    assert failures[0].exc_info is not None
    assert smtp.return_value.sendmail.call_count == 0
    assert post.call_count == 0


def test_week_run_reminds_about_this_weeks_bins_earliest_first(
    app_log: pytest.LogCaptureFixture,
) -> None:
    # Given ntfy is configured, and bins are collected this week (listed out of order) and later
    settings = ApplicationSettings(
        yaml_settings(ntfy={"server": NTFY_SERVER, "topic": "a-topic"})
    )
    scraper = FakeScraper(
        [
            a_collection("Garden Waste", day=8, is_this_week=True),
            a_collection("Paper & Cardboard", day=20, is_this_week=False),
            a_collection("Food Waste", day=6, is_this_week=True),
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
            build_notify(settings),
            settings,
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
