import pytest
from period import Period
from support import a_collection


def test_tomorrow_selects_only_the_bins_collected_tomorrow() -> None:
    # Given food waste is collected tomorrow and garden waste is collected later this week
    collections = [
        a_collection("Food Waste", day=3, is_tomorrow=True),
        a_collection("Garden Waste", day=6, is_tomorrow=False),
    ]

    # When the bins for the night-before reminder are selected
    selected = Period.TOMORROW.select(collections)

    # Then only the food waste is selected
    assert [c.service_name for c in selected] == ["Food Waste"]


def test_week_selects_this_weeks_bins_in_collection_date_order() -> None:
    # Given bins collected this week and later, listed out of date order
    collections = [
        a_collection("Garden Waste", day=6, is_this_week=True),
        a_collection("Paper & Cardboard", day=20, is_this_week=False),
        a_collection("Food Waste", day=3, is_this_week=True),
    ]

    # When the bins for the weekly reminder are selected
    selected = Period.WEEK.select(collections)

    # Then only this week's bins are selected, earliest collection first
    assert [c.service_name for c in selected] == ["Food Waste", "Garden Waste"]


@pytest.mark.parametrize("period", list(Period))
def test_no_bins_are_selected_when_there_are_no_collections(period: Period) -> None:
    # Given there are no collections
    # When the bins for a reminder are selected
    selected = period.select([])

    # Then nothing is selected
    assert selected == []
