# Split the Scraper at the Page source seam

## Problem Statement

The Scraper does four jobs in one class: it launches headless Firefox, waits for the
WasteWorks page, parses its HTML, and stamps each Waste Collection with `is_tomorrow` and
`is_this_week` flags computed from `datetime.now()`. Only the first two need a browser, but
the parsing, and the date logic that is most likely to go wrong (the December-to-January
rollover, the "(In Progress)" and ordinal suffixes, services with no next collection) is
only reachable through Selenium, so none of it has a test. The flags also bake the moment
of scraping into the data, so the question "is this collection tomorrow?" is decided in the
Scraper rather than by the Period that asks it.

## Solution

Make the **Page source** (now in the glossary) a real seam. The Scraper obtains the page
HTML from a Page source and parses it as a pure function of that HTML and the current time;
production supplies a Selenium Page source, tests supply saved HTML. A Waste Collection
holds only its Service and date, and the Period decides, from the date and an injected
"today", whether a collection belongs to its Reminder.

Nothing a recipient sees changes, the schedule is unchanged, and the Scraper's parsing
rules are preserved exactly, quirks included.

## User Stories

1. As the maintainer, I want the WasteWorks page parsing testable without a browser, so
   that date handling is covered by fast, deterministic tests.
2. As the maintainer, I want a Waste Collection to be only a Service and a date, so that it
   is not tied to the moment it was scraped.
3. As the maintainer, I want the Period to decide which collections it includes from their
   dates and an injected today, so that all of that Period's rules live in one place.
4. As the maintainer, I want the Selenium browser code isolated behind one small adapter,
   so that changing how the page is fetched cannot affect parsing.
5. As a resident, I want the nightly Reminder to cover exactly tomorrow's collections and
   the weekly Reminder exactly this week's (including the following Monday), as today.
6. As the maintainer, I want a collection dated early January to resolve to the next year
   when the page is read in late December, as today.
7. As the maintainer, I want a single reading of the clock per Reminder run used for both
   selecting and sending, so that a run is internally consistent.

## Implementation Decisions

- A `PageSource` Protocol with one operation that renders a URL and returns its HTML.
  Production has a Selenium adapter holding everything browser-related that is in the
  Scraper today: driver creation driven by `ENV_FLAG`, the wait for the service headings,
  the retry, and the `ScraperError` raised when rendering fails. Tests use a fixture adapter
  returning saved HTML.
- The Scraper takes a Page source, the WasteWorks URL, and a clock (a callable returning
  the current time). `get_upcoming_collections()` renders the page and parses it using the
  clock's current time. It no longer takes a timezone: the clock's time already carries
  one. Its interface as the Reminder run's `CollectionSource` is unchanged.
- Parsing is a pure function of the HTML and the current time and keeps every existing
  rule: services are the `h3.govuk-heading-m.waste-service-name` headings; the date is the
  `dd` following the service's "Next collection" `dt`; parenthesised notes and ordinal
  suffixes are stripped; the year is the current year, except that a January date read in
  December belongs to the next year; a service without a "Next collection" row is skipped.
  The collection date carries the current time's timezone.
- `WasteCollection` keeps only `service_name` and `next_collection_date`. The
  `is_tomorrow`/`is_this_week` fields and the `is_collection_tomorrow` and
  `is_collection_this_week` predicates are removed.
- `Period.select(collections, today)` takes the current time. Tomorrow keeps collections
  dated the day after `today`. Week keeps collections dated before the day eight days after
  `today` (so the following Monday is included, and, as today, there is no lower bound),
  sorted by date. These are exactly the rules of the removed predicates.
- The Reminder run reads its clock once per run, after the scrape completes (as the old
  flags were decided at scrape time, so a scrape that crosses midnight selects for the day
  after it finished), and uses that single reading for both `Period.select` and
  `send_reminders`.
- `main.py` constructs the Scraper with a Selenium Page source, the URL and its existing
  current-time clock, replacing the timezone argument.
- The latent leap-day crash in date parsing (a collection dated 29 February fails to parse
  because the format is parsed without a year) is deliberately preserved; it is tracked as a
  separate follow-up issue.
- No schema, config, or Channel-contract changes. No ADR.

## Testing Decisions

- Tests exercise the Scraper through `get_upcoming_collections()` with a fixture Page
  source and a fixed clock, asserting on the returned Waste Collections, not on private
  parsing helpers. Scenarios: a normal page; ordinal and "(In Progress)" suffixes; a
  late-December clock with a January date; a service with no next collection; an empty
  page; a Page source that raises `ScraperError`.
- `Period.select(collections, today)` is tested directly as a pure function: Tomorrow's
  boundary, Week's boundary at the following Monday and the day after, date ordering, and
  empty input. These replace the flag-based tests.
- The Reminder run, scheduling and reminder tests are updated, not extended: collections
  are built from dates and the injected clock instead of flags, and they keep proving each
  run reminds about the right collections end to end.
- The fixture HTML is written to match the selectors the parser relies on; the real
  WasteWorks markup could not be inspected here, so fixtures cover those selectors only.
- Not unit tested, as before: the Selenium adapter (it needs a real browser) and the
  `main()` construction line.
- Prior art: `tests/test_period.py`, `tests/test_reminder_run.py`, `tests/support.py`.

## Out of Scope

- Fixing the leap-day crash or any other parsing quirk (tracked separately).
- Changing the selectors, the timeout, the retry policy or `ENV_FLAG` behaviour.
- Email or ntfy content, Channels, settings, logging, the Reminder run's log lines.

## Further Notes

- Origin: architecture review candidate #3, building on `Period` (PR #288) and the
  Reminder run (PR #294).
