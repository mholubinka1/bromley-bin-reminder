# Extract the Reminder run from main.py

## Problem Statement

The two scheduled jobs that send Reminders, the nightly and the weekly one, are
defined as nested closures inside `main()`. They are near-duplicates: each scrapes the
WasteWorks page, selects the Waste Collections for its Period, logs a handful of
period-specific lines, sends the Reminder, and catches and logs any failure. The
behaviour that matters most (what a run does, and what happens when it fails) can only
be exercised by running the whole application, and every change to it means editing two
copies.

## Solution

Introduce the **Reminder run** (now in the glossary) as a single operation parameterised
by Period. One function owns "scrape, select that Period's Waste Collections, send the
Reminder when there are any, and survive failure". `main.py` is left with wiring: loading
configuration, starting the config poller, and registering one Reminder run per Period on
the scheduler.

Nothing a recipient sees changes, and the schedule is unchanged. Only the maintainer's
info-level log wording changes, and it becomes consistent across Periods.

## User Stories

1. As the maintainer, I want one Reminder run shared by both Periods, so that a change to
   how a run behaves is made once.
2. As the maintainer, I want `main.py` to only wire dependencies and register the
   schedule, so that I can read the application's startup without reading Reminder logic.
3. As the maintainer, I want the Reminder run testable without Selenium, a real clock, or
   starting the scheduler, so that its behaviour is covered by fast, deterministic tests.
4. As a resident, I want the nightly Reminder to cover exactly tomorrow's collections and
   the weekly Reminder exactly this week's, sent at the same times as today.
5. As a resident, I want nothing to be sent on a day with no collections due.
6. As the maintainer, I want a scrape failure, or any other error in a run, to be logged
   with the Period and never to stop later runs, so that one bad night does not silence
   the service.
7. As the maintainer, I want the run's info logs worded consistently for both Periods
   (for example "Tomorrow's collections: [Food Waste]"), so that logs are easy to read
   and search.

## Implementation Decisions

- A Reminder run function in the existing reminder module takes the Period, a scraper,
  the notifier, the settings, and a clock (a callable returning the current time, read at
  run time because the run fires long after startup).
- The scraper is described by a small Protocol exposing `get_upcoming_collections()`;
  production supplies the Selenium scraper, tests supply a fake.
- A run: logs that it started; scrapes; selects with `Period.select`; logs the count and,
  if non-zero, the services; sends via `send_reminders` with `now` from the clock;
  catches any exception and logs "<Period> reminder run failed." with the traceback.
- `send_reminders` is unchanged, including its email-vs-ntfy failure isolation and its
  "Failed to send ... email reminder." log.
- `Period` gains one plain-data field, `collections_label` ("Tomorrow's collections" /
  "This week's collections"), exposed as a property like the existing fields.
- Log lines of a run: "<Period name> reminder run started."; "<collections_label>: <N>"
  style count line; "<collections_label>: [<services>]" when N is non-zero;
  "Sending <collections_label> reminders."; and on failure "<Period name> reminder run
  failed.". The old four distinct info lines per job are replaced by these.
- `main.py` registers one run per Period on the scheduler (the scheduling library's
  `.do(...)` form in place of the `@repeat` decorator on nested functions), passing a
  clock of `datetime.now(tz)`. The daily run keeps `every().day.at(time, tz)` and the
  weekly run `every().sunday.at(time, tz)`. The commented-out interval helper lines are
  left as they are.
- No schema, config, or Channel-contract changes. No ADR.

## Testing Decisions

- Tests exercise the Reminder run through its function with a fake scraper, a fixed
  clock, and the existing system-boundary patches (`notify.SMTP`,
  `notify.requests.post`), asserting on what is sent and logged, not on internals.
- Scenarios: a Tomorrow run sends only tomorrow's collections and the email heading uses
  the clock's date; a Week run sends only this week's collections in date order; nothing
  is sent when nothing is due; a scraper that raises is logged as "<Period> reminder run
  failed." and does not propagate and sends nothing; the unified log lines, including
  "Tomorrow's collections: [...]".
- Prior art: `tests/test_reminder.py` and `tests/test_email_content.py` (patching and the
  fixed `FRIDAY_EVENING` clock), `tests/support.py` (`a_collection`).
- The scheduler wiring in `main.py` stays untested, as today.

## Out of Scope

- Removing the `is_tomorrow` / `is_this_week` flags from `WasteCollection` or moving date
  rules out of the scraper (architecture review candidate #3).
- Changes to `send_reminders`, the email or ntfy content, Channels, settings, or the
  scraper itself.
- Changing the schedule times or switching scheduler libraries.

## Further Notes

- Origin: architecture review candidate #1, built on the `Period` type merged in PR #288.
- The PR description should list the new log wording, since it is the one observable
  change.
