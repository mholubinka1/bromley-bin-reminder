import logging
from datetime import datetime

import pytest
from scraper import ScraperError, WasteworksScraper
from support import (
    DIRECT_DEBIT_STATUS,
    FRIDAY_EVENING,
    LONDON,
    FixturePageSource,
    a_garden_waste_page,
    a_wasteworks_page,
)

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


@pytest.mark.parametrize(
    "separator", [" ", "\t", "\n"], ids=["non-breaking space", "tab", "newline"]
)
def test_scraper_reads_a_date_whose_month_follows_any_whitespace(
    separator: str,
) -> None:
    # Given a page whose date has a non-space whitespace character before the month
    page = a_wasteworks_page(("Food Waste", f"Saturday, 3rd{separator}October"))
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then the date is read as normal
    assert [c.next_collection_date for c in collections] == [
        datetime(2026, 10, 3, tzinfo=LONDON)
    ]


def test_scraper_reads_a_collection_dated_on_a_leap_day() -> None:
    # Given a clock on Friday 25 February 2028 and a page listing Tuesday 29th February
    friday_evening_in_a_leap_year = datetime(2028, 2, 25, 18, 0, tzinfo=LONDON)
    page = a_wasteworks_page(("Food Waste", "Tuesday, 29th February"))
    scraper = WasteworksScraper(
        FixturePageSource(page),
        WASTEWORKS_URL,
        clock=lambda: friday_evening_in_a_leap_year,
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then the collection is dated the leap day
    assert [c.next_collection_date for c in collections] == [
        datetime(2028, 2, 29, tzinfo=LONDON)
    ]


@pytest.mark.parametrize("unreadable_date", ["", "Soon", "Tuesday, 3rd Octobre"])
def test_scraper_fails_on_a_collection_date_it_cannot_read(
    unreadable_date: str,
) -> None:
    # Given a page whose collection date is not in the expected format
    page = a_wasteworks_page(("Food Waste", unreadable_date))
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read
    # Then the date is rejected as an invalid value
    with pytest.raises(ValueError):
        scraper.get_upcoming_collections()


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


def test_scraper_skips_a_service_without_a_next_collection_in_the_middle_of_the_page() -> (
    None
):
    # Given garden waste has no next collection, between food waste and paper
    page = a_wasteworks_page(
        ("Food Waste", "Saturday, 3rd October"),
        ("Garden Waste", None),
        ("Paper", "Tuesday, 6th October"),
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then garden waste is skipped and the others keep their own dates
    assert [(c.service_name, c.next_collection_date) for c in collections] == [
        ("Food Waste", datetime(2026, 10, 3, tzinfo=LONDON)),
        ("Paper", datetime(2026, 10, 6, tzinfo=LONDON)),
    ]


def test_scraper_skips_a_service_without_a_next_collection_at_the_start_of_the_page() -> (
    None
):
    # Given garden waste has no next collection and is listed before paper
    page = a_wasteworks_page(
        ("Garden Waste", None),
        ("Paper", "Tuesday, 6th October"),
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then only paper is returned, with its own date
    assert [(c.service_name, c.next_collection_date) for c in collections] == [
        ("Paper", datetime(2026, 10, 6, tzinfo=LONDON)),
    ]


def test_scraper_reads_the_services_in_the_order_the_real_page_lists_them() -> None:
    # Given the services as WasteWorks lists them: five scheduled, then two without dates
    page = a_wasteworks_page(
        ("Mixed Recycling (Cans, Plastics & Glass)", "Friday, 9th October"),
        ("Paper & Cardboard", "Friday, 16th October"),
        ("Garden Waste", "Tuesday, 13th October"),
        ("Non-Recyclable Refuse", "Friday, 16th October"),
        ("Food Waste", "Friday, 9th October"),
        ("Bulky waste", None),
        ("Batteries, small electrical items and textiles", None),
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the upcoming collections are read
    collections = scraper.get_upcoming_collections()

    # Then the five scheduled services are returned, each with its own date
    assert [(c.service_name, c.next_collection_date.day) for c in collections] == [
        ("Mixed Recycling (Cans, Plastics & Glass)", 9),
        ("Paper & Cardboard", 16),
        ("Garden Waste", 13),
        ("Non-Recyclable Refuse", 16),
        ("Food Waste", 9),
    ]


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


def test_scraper_reads_the_garden_waste_subscription_with_a_trailing_renewal_note() -> (
    None
):
    # Given a Garden Waste section whose Renewal row carries a trailing note
    page = a_garden_waste_page(renewal="12 June 2027, soon due for renewal.")
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    subscription = scraper.get_garden_waste_subscription()

    # Then the date is the leading date and the price text is read as shown
    assert subscription is not None
    assert subscription.renewal_date == datetime(2027, 6, 12, tzinfo=LONDON)
    assert subscription.subscription_text == "£80.00 per year (1 bin)"


def test_scraper_reads_the_garden_waste_subscription_without_a_trailing_note() -> None:
    # Given a Garden Waste section whose Renewal row is only a date
    page = a_garden_waste_page(renewal="12 June 2027")
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    subscription = scraper.get_garden_waste_subscription()

    # Then the date is read
    assert subscription is not None
    assert subscription.renewal_date == datetime(2027, 6, 12, tzinfo=LONDON)


def test_scraper_reads_that_the_subscription_renews_automatically_by_direct_debit() -> (
    None
):
    # Given a Garden Waste section saying the subscription renews automatically
    page = a_garden_waste_page(
        renewal="12 June 2027, soon due for renewal.", status=DIRECT_DEBIT_STATUS
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    subscription = scraper.get_garden_waste_subscription()

    # Then it renews automatically
    assert subscription is not None
    assert subscription.renews_automatically


def test_scraper_reads_automatic_renewal_whatever_the_capitalisation() -> None:
    # Given a Garden Waste section whose automatic renewal sentence is capitalised differently
    page = a_garden_waste_page(
        renewal="12 June 2027, soon due for renewal.",
        status=DIRECT_DEBIT_STATUS.upper(),
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    subscription = scraper.get_garden_waste_subscription()

    # Then it still renews automatically
    assert subscription is not None
    assert subscription.renews_automatically


def test_scraper_reads_that_the_subscription_does_not_renew_automatically() -> None:
    # Given a Garden Waste section with no automatic renewal sentence
    page = a_garden_waste_page(renewal="12 June 2027, soon due for renewal.")
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    subscription = scraper.get_garden_waste_subscription()

    # Then it does not renew automatically
    assert subscription is not None
    assert not subscription.renews_automatically


@pytest.mark.parametrize(
    ("renewal", "status"),
    [
        ("12 June 2027 Cancellation in progress", ""),
        (
            "12 June 2027, soon due for renewal.",
            "This property has a pending garden subscription.",
        ),
        (
            "12 June 2027, soon due for renewal.",
            "This property has a pending direct debit subscription.",
        ),
        ("12 June 2027, soon due for renewal.", "PENDING GARDEN SUBSCRIPTION."),
    ],
)
def test_scraper_reads_that_a_cancellation_or_new_subscription_is_in_progress(
    renewal: str, status: str
) -> None:
    # Given a Garden Waste section showing a cancellation or pending subscription
    page = a_garden_waste_page(renewal=renewal, status=status)
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    subscription = scraper.get_garden_waste_subscription()

    # Then it is in progress, and the date is still read
    assert subscription is not None
    assert subscription.in_progress
    assert subscription.renewal_date == datetime(2027, 6, 12, tzinfo=LONDON)


def test_scraper_reads_a_plain_subscription_as_not_in_progress() -> None:
    # Given a Garden Waste section with nothing in progress
    page = a_garden_waste_page(
        renewal="12 June 2027, soon due for renewal.", status=DIRECT_DEBIT_STATUS
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    subscription = scraper.get_garden_waste_subscription()

    # Then nothing is in progress
    assert subscription is not None
    assert not subscription.in_progress


@pytest.mark.parametrize("renewal", [None, "not a date", ""])
def test_scraper_logs_a_warning_and_finds_nothing_when_the_renewal_cannot_be_read(
    renewal: str | None, caplog: pytest.LogCaptureFixture
) -> None:
    # Given a Garden Waste section whose Renewal row is missing or not a date
    page = a_garden_waste_page(renewal=renewal)
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    with caplog.at_level(logging.WARNING):
        subscription = scraper.get_garden_waste_subscription()

    # Then there is none and the problem is logged
    assert subscription is None
    assert "Could not read the Garden Waste renewal" in caplog.text


def test_scraper_logs_a_warning_when_only_the_subscription_row_is_missing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given a Garden Waste section with a Renewal row but no Subscription row
    page = a_garden_waste_page(renewal="12 June 2027", subscription=None)
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    with caplog.at_level(logging.WARNING):
        subscription = scraper.get_garden_waste_subscription()

    # Then there is none and the problem is logged
    assert subscription is None
    assert "Could not read the Garden Waste renewal" in caplog.text


def test_scraper_reads_the_date_of_an_overdue_subscription() -> None:
    # Given a Garden Waste section whose Renewal row says the subscription is overdue
    page = a_garden_waste_page(renewal="12 June 2027, subscription overdue.")
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    subscription = scraper.get_garden_waste_subscription()

    # Then the date is the leading date, whatever the note after it
    assert subscription is not None
    assert subscription.renewal_date == datetime(2027, 6, 12, tzinfo=LONDON)


def test_scraper_warns_and_misses_an_in_progress_note_when_the_section_container_is_missing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given a Garden Waste heading outside any section container, with a pending note
    page = (
        '<html><body><h3 class="govuk-heading-m waste-service-name">Garden Waste</h3>'
        '<dl class="govuk-summary-list">'
        "<div><dt>Subscription</dt><dd>£80.00 per year (1 bin)</dd></div>"
        "<div><dt>Renewal</dt><dd>12 June 2027</dd></div></dl>"
        "<p>This property has a pending garden subscription.</p></body></html>"
    )
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    with caplog.at_level(logging.WARNING):
        subscription = scraper.get_garden_waste_subscription()

    # Then the date is read, the note is missed, and the warning says so
    assert subscription is not None
    assert not subscription.in_progress
    assert "will not be detected" in caplog.text


def test_scraper_quietly_finds_no_subscription_in_a_garden_waste_section_with_only_a_cost(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given a Garden Waste section that shows only a cost, like an unsubscribed service
    page = a_wasteworks_page(("Garden Waste", None))
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    with caplog.at_level(logging.WARNING):
        subscription = scraper.get_garden_waste_subscription()

    # Then there is none and nothing is logged as a problem
    assert subscription is None
    assert caplog.text == ""


def test_scraper_finds_no_subscription_without_a_garden_waste_section() -> None:
    # Given a page listing only food waste
    page = a_wasteworks_page(("Food Waste", "Saturday, 3rd October"))
    scraper = WasteworksScraper(
        FixturePageSource(page), WASTEWORKS_URL, clock=lambda: FRIDAY_EVENING
    )

    # When the Garden Waste subscription is read
    # Then there is none
    assert scraper.get_garden_waste_subscription() is None
