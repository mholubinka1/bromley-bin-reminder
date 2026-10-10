from datetime import time
from unittest.mock import patch

from common.settings import ApplicationSettings
from notify import build_notify
from reminder import schedule_reminder_runs
from schedule import Scheduler
from support import FRIDAY_EVENING, FakeScraper, a_collection, sent_email, yaml_settings

LONDON_NAME = "Europe/London"


def settings_reminding_at_six_pm_in_london() -> ApplicationSettings:
    settings = ApplicationSettings(yaml_settings())
    settings.remind.time = "18:00"
    settings.remind.tz = LONDON_NAME
    return settings


def test_reminder_runs_are_scheduled_daily_and_on_sundays_at_the_reminder_time() -> (
    None
):
    # Given reminders are configured for 18:00 London time
    settings = settings_reminding_at_six_pm_in_london()
    scheduler = Scheduler()

    # When the reminder runs are scheduled
    schedule_reminder_runs(
        scheduler,
        FakeScraper([]),
        build_notify(settings),
        settings,
        clock=lambda: FRIDAY_EVENING,
    )

    # Then there is one run every day and one every Sunday, both at 18:00 London time
    daily, weekly = scheduler.get_jobs()
    assert (daily.unit, daily.interval, daily.start_day) == ("days", 1, None)
    assert (weekly.unit, weekly.interval, weekly.start_day) == (
        "weeks",
        1,
        "sunday",
    )
    for job in (daily, weekly):
        assert job.at_time == time(18, 0)
        assert str(job.at_time_zone) == LONDON_NAME


def test_scheduled_runs_remind_about_their_own_period_using_the_clock() -> None:
    # Given food waste is collected tomorrow and garden waste later this week
    settings = settings_reminding_at_six_pm_in_london()
    scraper = FakeScraper(
        [
            a_collection("Food Waste", day=3, is_tomorrow=True),
            a_collection("Garden Waste", day=6, is_tomorrow=False),
        ]
    )
    scheduler = Scheduler()
    schedule_reminder_runs(
        scheduler,
        scraper,
        build_notify(settings),
        settings,
        clock=lambda: FRIDAY_EVENING,
    )
    daily, weekly = scheduler.get_jobs()

    # When the scheduler fires the daily run, then the weekly run
    with patch("notify.SMTP") as daily_smtp:
        daily.run()
    with patch("notify.SMTP") as weekly_smtp:
        weekly.run()

    # Then the daily run reminds about tomorrow's bins and the weekly run about the week's
    daily_email = sent_email(daily_smtp)
    assert daily_email.heading == "Saturday 3rd October"
    assert [row[0] for row in daily_email.rows] == ["Food Waste"]
    weekly_email = sent_email(weekly_smtp)
    assert weekly_email.heading == "Week Commencing: Friday 2nd October"
    assert [row[0] for row in weekly_email.rows] == ["Food Waste", "Garden Waste"]
