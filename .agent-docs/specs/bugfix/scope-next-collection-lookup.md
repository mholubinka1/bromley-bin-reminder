# Scope each service's "Next collection" lookup to its own section

## Problem Statement

The Scraper finds a service's date with `find_next("dt", string="Next collection")` from the
service's heading. That scans forward through the rest of the whole document, not just the
service's own section. So a service with no "Next collection" row takes the next service's
row and is reported with that service's date. The resident would get a Reminder (email and
ntfy) for a collection that is not theirs, on the wrong date. Tracked as issue #302.

The live WasteWorks page does list services without that row: "Bulky waste" (cost only) and
"Batteries, small electrical items and textiles" (no rows), alongside five services that
have one. They are currently the last two on the page, so no later row exists for them to
take and they are skipped correctly. The bug is latent: if WasteWorks ever lists one of them
before a service that has a row, that service's date is misattributed.

## Solution

Bound each service's search to its own section: look forward from its heading only until the
next service heading (or the end of the page). A service with no "Next collection" row in
its section is skipped. Nothing else about reading the page changes.

Nothing a recipient sees changes for today's page; the fix removes the risk of a wrong-date
Reminder if the page's service order changes.

## User Stories

1. As a resident, I want a service to be reminded about only on its own collection date, so
   that I never put a bin out on another service's day.
2. As the maintainer, I want a service without a "Next collection" row to be skipped
   wherever it appears on the page, so that the page's service order cannot cause a wrong
   date.
3. As the maintainer, I want test fixtures that mirror the real page's structure and service
   order, so that tests reflect what the Scraper actually reads.

## Implementation Decisions

- The lookup walks the elements after a service's heading in document order and stops at the
  next service heading (or the end of the document), taking the first `dt` whose text is
  "Next collection" within that range. This relies on document order only, not on how the
  page nests its sections, so it adds no new markup dependency and fails safe.
- The date is still the `dd` immediately following that `dt`, parsed exactly as today.
- A service with no such `dt` in its range is skipped, as the last-service case is today.
- The service heading selector (`h3.govuk-heading-m.waste-service-name`) and all date
  parsing are unchanged.
- No new logging: a skipped service stays silent, as today.
- No interface, schema or config changes. No ADR.

## Testing Decisions

- Tests go through the existing seam: `WasteworksScraper` with a fixture Page source and a
  fixed clock, asserting on the returned Waste Collections. Scenarios: a service in the
  middle without the row is skipped and its neighbours keep their own dates (fails before the
  fix); a service first on the page without the row is skipped (fails before the fix); the
  real page's order (five services with rows, then two without) returns exactly the five with
  their own dates; the existing scenarios are unchanged.
- The test page builder mirrors the real page's structure: each service in a
  `div.waste-service-grid`, its heading inside `div.waste-service-grid--service-name`, and
  its rows as `dt`/`dd` pairs (Frequency, Next collection, Last collection). A service can be
  built with or without the "Next collection" row. Fixture dates are invented; no household
  data goes into the repository.
- Prior art: `tests/test_scraper.py`, `tests/support.py` (`a_wasteworks_page`).

## Out of Scope

- Using the Garden Waste Subscription and Renewal rows (a separate stub, issue #303).
- Logging when a service is skipped, or any other change to how the page is read.
- Locating a service's section by a container class name.

## Further Notes

- Origin: issue #302, found while planning the Scraper/Page source split (PR #299).
- The live page was inspected with the app's own Selenium Page source to ground the fixtures;
  nothing from it is recorded here beyond the public service names and structure.
