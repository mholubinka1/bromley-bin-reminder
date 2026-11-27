# Firefox is always shut down when a page render fails

## Problem Statement

`SeleniumPageSource.render` (app/scraper.py) calls `driver.get(url)` before its `try`
block. If `driver.get` raises (seen live 2026-11-27 18:00: a short `dnsNotFound` for
recyclingservices.bromley.gov.uk), neither `driver.quit()` runs. The `@retry()` decorator
then starts a new Firefox, and the first one keeps running until the container restarts:
about 10 processes and ~325 MB RSS on the Pi (≈8% of its RAM). Each failed attempt leaks
one more Firefox, so one bad run can leak up to three (3 attempts).

## Solution

Create the driver, then put everything after it, `driver.get(url)` included, inside `try`,
and shut the driver down once in `finally`. A failure to shut it down is logged and never
hides the original error.

## User Stories

1. As the maintainer, I want every Firefox a render starts to be shut down, so that a
   failed render cannot slowly exhaust the Pi's memory.
2. As the maintainer, I want a failed render to still raise `ScraperError`, so that the
   retry and the Reminder run behave as before.
3. As the maintainer, I want a failed shutdown logged without masking the render error, so
   that the real cause of a failure stays visible.

## Implementation Decisions

- Every Firefox that `render` starts is shut down before `render` returns or raises,
  whichever step fails: `driver.get`, the wait, or reading `page_source`.
- A failed render still raises `ScraperError`; the success path returns the page source
  exactly as now.
- If `driver.quit()` raises during cleanup, it is logged as a WARNING and swallowed, so the
  original error (or the page source) is what the caller sees.
- The 300-second wait becomes a named constant. `_create_firefox_web_driver` and the
  retry decorator are unchanged. No ADR.

## Testing Decisions

- Seam: a `SeleniumPageSource` subclass overriding `_create_firefox_web_driver` to return a
  fake driver that records `quit()` calls. `time.sleep` is patched so the retry and the
  wait's polling run instantly; the wait timeout constant is patched to 0 for the wait
  failure.
- Scenarios: `get` fails on every attempt (ScraperError, every created driver quit); the wait
  never matches (ScraperError, quit); success (page source returned, quit once); `quit()`
  raises after a failed `get` (ScraperError still raised, the shutdown failure logged).
- Prior art: `tests/test_scraper.py`.

## Out of Scope

- Retry policy, DNS resilience, the Selenium/geckodriver versions.

## Further Notes

- Deploy check: after merge and the Watchtower update on the Pi, no `firefox-esr` processes
  in `docker top bin-reminder` between daily 18:00 runs, including after a run whose log
  shows a render WARNING.
