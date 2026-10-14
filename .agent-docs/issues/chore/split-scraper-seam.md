# Issues: chore/split-scraper-seam

## Make the Page source a real seam and test the Scraper's parsing

**GitHub issue**: #296

**Blocked by**: None

**User stories**: 1, 4, 6

### What to build

Introduce the `PageSource` Protocol and move every browser concern (driver creation driven by `ENV_FLAG`, the wait for the service headings, the retry, and `ScraperError`) into a Selenium adapter. `WasteworksScraper` takes a Page source, the URL and a clock, renders the page and parses it as a pure function of the HTML and the clock's current time, keeping every existing parsing rule. It still sets `is_tomorrow`/`is_this_week` for now, computed from the clock, so no other code changes. `main.py` is wired with the Selenium Page source and its existing current-time clock. The Scraper's parsing is covered by tests that use a fixture Page source.

### Acceptance criteria

- [ ] Given fixture HTML with several services and a fixed clock, the Scraper returns each service with its dated, timezone-aware collection
- [ ] A date with an ordinal suffix and an "(In Progress)" note parses to the right day
- [ ] Given a late-December clock and an early-January date, the collection resolves to January of the next year
- [ ] A service with no "Next collection" row is skipped; an empty page yields no collections
- [ ] A Page source that raises `ScraperError` propagates from `get_upcoming_collections()`
- [ ] `main.py` constructs the Scraper with a Selenium Page source, the URL and a clock, and no longer passes a timezone
- [ ] All tests pass

---

## Let the Period decide from dates and remove the flags

**GitHub issue**: #297

**Blocked by**: #296

**User stories**: 2, 3, 5, 7

### What to build

`Period.select(collections, today)` decides from each collection's date and an injected today: Tomorrow keeps collections dated the day after today; Week keeps collections dated before the day eight days after today, sorted by date (same rules as the removed predicates, including no lower bound). The Reminder run reads its clock once and uses that one reading for selecting and sending. `WasteCollection` keeps only the Service and date: the two flags and their predicates are removed from it and from the Scraper, and tests that built collections with flags now build them from dates.

### Acceptance criteria

- [ ] Tomorrow keeps only collections dated tomorrow
- [ ] Week keeps everything dated before today plus 8 days (including the following Monday), excludes today plus 8 days, and sorts by date
- [ ] Both Periods return an empty list for empty input
- [ ] `WasteCollection` has no `is_tomorrow`/`is_this_week` fields, and the predicates are gone
- [ ] The Reminder run reads its clock once per run
- [ ] The existing run, scheduling and reminder tests pass with collections defined by date
- [ ] All tests pass

---
