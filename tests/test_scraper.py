from datetime import datetime

import pytest
from scraper import ScraperError, WasteworksScraper
from support import FRIDAY_EVENING, LONDON, FixturePageSource, a_wasteworks_page

WASTEWORKS_URL = "https://example.com/waste"


class UnrenderablePageSource:
    def render(self, url: str) -> str:
        raise ScraperError(f"Failed to render Wasteworks page: {url}")


def test_scraper_returns_each_service_with_its_next_collection_date() -> None:
    # Given a WasteWorks page listing food waste on Saturday and garden waste on Tuesday
    page = a_wasteworks_page(
        ("Food Waste", "Saturday, 3rd October"),
        ("Garden Waste", "Tuesday, 6th October"),
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read on Friday evening
    collections = scraper.get_upcoming_collections()

    # Then each service has its collection date, in London time
    assert [(c.service_name, c.next_collection_date) for c in collections] == [
        ("Food Waste", datetime(2026, 10, 3, tzinfo=LONDON)),
        ("Garden Waste", datetime(2026, 10, 6, tzinfo=LONDON)),
    ]


def test_scraper_ignores_in_progress_notes_and_ordinal_suffixes() -> None:
    # Given a page whose dates carry an in-progress note and st, nd, rd and th suffixes
    page = a_wasteworks_page(
        ("Food Waste", "Saturday, 3rd October (In Progress)"),
        ("Garden Waste", "Thursday, 1st October"),
        ("Paper", "Friday, 2nd October"),
        ("Glass", "Wednesday, 7th October"),
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then each date is read as the day it names
    assert [c.next_collection_date for c in collections] == [
        datetime(2026, 10, 3, tzinfo=LONDON),
        datetime(2026, 10, 1, tzinfo=LONDON),
        datetime(2026, 10, 2, tzinfo=LONDON),
        datetime(2026, 10, 7, tzinfo=LONDON),
    ]


def test_scraper_dates_a_january_collection_read_in_december_in_the_next_year() -> None:
    # Given a clock on Monday 29 December 2025 and a page listing Friday 2nd January
    monday_evening = datetime(2025, 12, 29, 18, 0, tzinfo=LONDON)
    page = a_wasteworks_page(("Food Waste", "Friday, 2nd January"))
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: monday_evening
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then the collection falls in the next year
    assert [c.next_collection_date for c in collections] == [
        datetime(2026, 1, 2, tzinfo=LONDON)
    ]


def test_scraper_skips_a_service_without_a_next_collection() -> None:
    # Given a page whose last service has no next collection
    page = a_wasteworks_page(
        ("Food Waste", "Saturday, 3rd October"),
        ("Garden Waste", None),
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then only the service with a collection is returned
    assert [c.service_name for c in collections] == ["Food Waste"]


def test_scraper_returns_no_collections_for_a_page_without_services() -> None:
    # Given a page listing no services
    scraper = WasteworksScraper(
        FixturePageSource(a_wasteworks_page()),
        WASTEWORKS_URL,
        clock=lambda: FRIDAY_EVENING,
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then there are none
    assert collections == []


def test_scraper_fails_when_the_page_cannot_be_rendered() -> None:
    # Given a page source that cannot render the page
    scraper = WasteworksScraper(
        UnrenderablePageSource(), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read
    # Then the render failure reaches the caller
    with pytest.raises(ScraperError):
        scraper.get_upcoming_collections()
