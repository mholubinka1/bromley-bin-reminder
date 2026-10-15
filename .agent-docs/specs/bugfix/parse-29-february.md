# Parse a collection dated 29 February

## Problem Statement

When the WasteWorks page lists a Waste Collection on 29 February, the Scraper cannot read
it. The date parser first parses the page's date text without a year to learn its month, and
Python assumes the year 1900 for that parse. 1900 was not a leap year, so "Tuesday, 29
February" raises `ValueError: day is out of range for month`. The error escapes the scrape,
so the whole Reminder run fails (it is logged as "<Period> reminder run failed." and
nothing is sent) on every run while the page lists a 29 February collection. The next leap
day is 29 February 2028. Tracked as issue #298.

## Solution

Read the month directly from the month name in the date text, derive the target year from
it (the current year, or the next year for a January date read in December), and parse the
full date once with that year. A 29 February collection read in a leap year then parses to
that date. Every other parsing rule is unchanged.

## User Stories

1. As a resident, I want my Reminders to keep arriving when a collection falls on 29
   February, so that I do not miss a bin day because of the date.
2. As the maintainer, I want a date the page can legitimately list never to fail the whole
   Reminder run, so that one date cannot silence the service.
3. As the maintainer, I want a regression test for 29 February, so that the parser cannot
   regress on leap days.

## Implementation Decisions

- The date parser reads the month from the month name at the end of the cleaned date text
  (a month-name-only parse, which has no day to be out of range), instead of the year-less
  full parse that assumed 1900.
- The target year is computed exactly as today: the current year, except that a January date
  read in December belongs to the next year.
- The full date is then parsed once, with that year and the clock's timezone.
- A date that does not match the expected format still raises `ValueError`, as today.
- No other parsing rule changes: parenthesised notes and ordinal suffixes are still
  stripped, the selectors and the `find_next("dt")` behaviour are untouched.
- No schema, config, or interface changes. No ADR.

## Testing Decisions

- The regression test goes through the existing seam, `WasteworksScraper` with a fixture
  Page source and a fixed clock, asserting on the returned Waste Collections: a page listing
  "Tuesday, 29th February" read with a clock on Friday 25 February 2028 yields 29 February
  2028 in London time. It must fail before the fix.
- The existing Scraper tests (ordinal suffixes, "(In Progress)", the December-to-January
  rollover, a missing next collection, an empty page, a render failure) stay unchanged and
  prove the other rules are preserved.
- Prior art: `tests/test_scraper.py`, `tests/support.py` (`a_wasteworks_page`,
  `FixturePageSource`).

## Out of Scope

- The forward-scanning `find_next("dt")` quirk (a separate follow-up).
- Any other change to date handling, such as supporting a page that lists a date more than a
  few weeks away, or a different date format.

## Further Notes

- Origin: issue #298, found while planning the Scraper/Page source split (PR #299), which
  deliberately preserved the bug so the refactor stayed one concern.
