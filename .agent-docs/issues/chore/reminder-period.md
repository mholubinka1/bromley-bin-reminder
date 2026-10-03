# Issues: chore/reminder-period

## Pin reminder output and inject the clock

**GitHub issue**: #285

**Blocked by**: None

**User stories**: 5, 6, 7, 8

### What to build

Make the clock injectable (`WasteCollectionNotification` takes `now`; `send_reminders` computes it) and add characterisation tests through `send_reminders` that pass on the current code.

### Acceptance criteria

- [ ] Nightly email: subject, `X-Priority: 1`, `Importance: high`, `<title>`/`<h1>` show tomorrow's date, single "Bin Type" column, a row per collection with its service colour
- [ ] Weekly email: subject, "Week Commencing" heading from `now`, "Bin Type" and "Collection Date" columns, a row per collection with its date
- [ ] ntfy nightly and weekly title, message, priority and tag asserted for both Periods
- [ ] Tests use a fixed `now`; no time patching
- [ ] All tests pass

---

## Add Period type with selection and ntfy wording

**GitHub issue**: #286

**Blocked by**: #285

**User stories**: 1, 2, 4, 7

### What to build

Introduce the `Period` enum with `select()` and the ntfy fields; `build_ntfy_notifications`, `send_reminders` and the `main.py` jobs use it.

### Acceptance criteria

- [ ] Tomorrow selects only `is_tomorrow` collections; Week selects only `is_this_week` ones, sorted by date; empty input returns empty
- [ ] ntfy output unchanged for both Periods
- [ ] `send_reminders` takes a `Period`; no `"tomorrow"`/`"week"` strings remain in the ntfy or job code
- [ ] Unknown-period test removed
- [ ] All tests pass

---

## Drive the email from Period with one shared template

**GitHub issue**: #287

**Blocked by**: #286

**User stories**: 2, 3, 5, 6

### What to build

One shared email template driven by Period data; close the stray unclosed `<td>`.

### Acceptance criteria

- [ ] One email template; no `match` on the Period in the email builder
- [ ] The characterisation tests from the first slice pass unchanged
- [ ] All tests pass

---
