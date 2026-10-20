from datetime import datetime

import pytest
from period import Period
from support import FRIDAY_EVENING, LONDON, a_collection


def test_tomorrow_selects_only_the_bins_dated_the_day_after_today() -> None:
    # Given food waste is dated Saturday 3rd October and garden waste Tuesday 6th
    collections = [
        a_collection("Food Waste", day=3),
        a_collection("Garden Waste", day=6),
    ]

    # When the bins for the night-before reminder are selected on Friday 2nd October
    selected = Period.TOMORROW.select(collections, FRIDAY_EVENING)

    # Then only the food waste is selected
    assert [c.service_name for c in selected] == ["Food Waste"]


def test_week_selects_the_bins_dated_before_eight_days_from_today_earliest_first() -> (
    None
):
    # Given bins dated tomorrow, on the following Friday (7 days on) and the Saturday
    # after (8 days on), listed out of date order
    collections = [
        a_collection("Garden Waste", day=9),
        a_collection("Paper & Cardboard", day=10),
        a_collection("Food Waste", day=3),
    ]

    # When the bins for the weekly reminder are selected on Friday 2nd October
    selected = Period.WEEK.select(collections, FRIDAY_EVENING)

    # Then the bin dated 7 days on is included, the one 8 days on is not, earliest first
    assert [c.service_name for c in selected] == ["Food Waste", "Garden Waste"]


@pytest.mark.parametrize("period", list(Period))
def test_no_bins_are_selected_when_there_are_no_collections(period: Period) -> None:
    # Given there are no collections
    # When the bins for a reminder are selected
    selected = period.select([], FRIDAY_EVENING)

    # Then nothing is selected
    assert selected == []


def test_tomorrow_compares_calendar_dates_not_elapsed_time() -> None:
    # Given bins dated today, tomorrow and the day after
    collections = [
        a_collection("Today", day=2),
        a_collection("Tomorrow", day=3),
        a_collection("Day After", day=4),
    ]

    # When the night-before bins are selected at 23:59 on Friday 2nd October
    late_friday = datetime(2026, 10, 2, 23, 59, tzinfo=LONDON)
    selected = Period.TOMORROW.select(collections, late_friday)

    # Then only the bin dated the next calendar day is selected
    assert [c.service_name for c in selected] == ["Tomorrow"]


def test_week_run_on_a_sunday_covers_the_coming_monday_through_the_next_sunday() -> (
    None
):
    # Given bins dated the coming Monday, the Sunday after it, and the Monday after that
    collections = [
        a_collection("Coming Monday", day=5),
        a_collection("Next Sunday", day=11),
        a_collection("Monday After", day=12),
    ]

    # When the weekly bins are selected on Sunday 4th October
    sunday_evening = datetime(2026, 10, 4, 18, 0, tzinfo=LONDON)
    selected = Period.WEEK.select(collections, sunday_evening)

    # Then the Monday a week on is left for next week's reminder
    assert [c.service_name for c in selected] == ["Coming Monday", "Next Sunday"]
