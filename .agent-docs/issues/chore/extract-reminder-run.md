# Issues: chore/extract-reminder-run

> Work complete — PR ready to merge.

## Run the Tomorrow Reminder through one Reminder run

**GitHub issue**: #291

**Blocked by**: None

**User stories**: 1, 3, 4, 5, 7

### What to build

Add the Reminder run to the reminder module: it takes a Period, a scraper (described by a small Protocol), the notifier, the settings and a clock, scrapes, selects with `Period.select`, logs, and sends via `send_reminders`. `Period` gains a `collections_label` so the run's log lines name the Period. Covered end to end for the Tomorrow Period, including the nothing-due case.

### Acceptance criteria

- [x] Given a fake scraper returning food waste due tomorrow and garden waste due later, and a fixed clock, a Tomorrow run sends one email and one ntfy notification for food waste only
- [x] The email heading shows the clock's date plus one day
- [x] The run logs "Tomorrow's collections: [Food Waste]"
- [x] Given nothing due tomorrow, nothing is sent
- [x] Tests use the existing system-boundary patches and a fixed clock; no time patching
- [x] All tests pass

---

## Run the Week Reminder and survive failure

**GitHub issue**: #292

**Blocked by**: #291

**User stories**: 1, 4, 6, 7

### What to build

The same Reminder run for the Week Period, and failure survival: any error in a run, including a scraper that raises, is logged with the Period and never propagates.

### Acceptance criteria

- [x] Given collections across the week out of date order, a Week run sends only this week's collections, earliest first, with the weekly email and ntfy wording
- [x] The run logs "This week's collections: [..]"
- [x] Given a scraper that raises, either run logs "<Period> reminder run failed." with the traceback, sends nothing, and does not propagate the exception
- [x] All tests pass

---

## Wire the scheduler to the Reminder run in main.py

**GitHub issue**: #293

**Blocked by**: #292

**User stories**: 2, 4

### What to build

Replace the two nested job functions in `main()` with one scheduler registration per Period using the Reminder run: the daily run at the configured time and the weekly run on Sundays at the same time, with a clock of `datetime.now(tz)`. `main.py` no longer selects collections, calls `send_reminders`, or imports what only the nested functions needed.

### Acceptance criteria

- [x] The daily and weekly runs are registered on the same schedule as before, through a scheduling function in the reminder module that is covered by tests (registrations, and each registered job reminds about its own Period using the injected clock)
- [x] `main.py` contains no collection selection and no `send_reminders` call
- [x] The existing tests pass unchanged
- [x] All tests pass

---
