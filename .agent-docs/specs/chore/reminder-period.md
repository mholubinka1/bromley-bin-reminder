# Make the Reminder Period a real concept

## Problem Statement

A Reminder covers either tomorrow's collections (nightly) or this week's (Sundays). That
distinction is a bare string, `"tomorrow"` or `"week"`, and it is matched in five places:
the collection filter and sort in the scheduled jobs, the email subject and priority
headers, the email body, the ntfy title and priority, and the ntfy message. Changing or
adding a Period edits all of them. A mistyped string only fails at send time, with a
`NotImplementedError`. The email body is built from two near-identical ~60-line HTML
templates with copy-pasted CSS.

## Solution

Introduce **Period** (now in the glossary) as a type with exactly two members, Tomorrow
and Week. A Period owns everything that varies between Reminders: which Waste Collections
it selects, and the wording of the email and the ntfy notifications. The Channel code
(email builder, ntfy builder) no longer branches on the Period; it reads data from it.
The two email templates collapse into one.

Nothing a recipient sees changes. Subjects, headers, titles, headings, table contents,
ntfy titles, messages, priorities and tags are identical to today.

## User Stories

1. As the maintainer, I want the Period to be a closed type, so that an invalid Period is a
   type error rather than a runtime `NotImplementedError` at send time.
2. As the maintainer, I want to add or change a Period in one place, so that email, ntfy
   and selection cannot drift apart.
3. As the maintainer, I want a single email template, so that a styling fix is made once.
4. As the maintainer, I want the choice of which collections a Period includes to live
   with the Period, so that the scheduled jobs stop duplicating filtering and sorting.
5. As a resident, I want the nightly email to look exactly as it does today (subject,
   high-priority headers, tomorrow's date heading, Bin Type table with colours), so that
   the refactor is invisible to me.
6. As a resident, I want the weekly email to look exactly as it does today (subject, "Week
   Commencing" heading, Bin Type and Collection Date columns), so that the refactor is
   invisible to me.
7. As a resident subscribed to ntfy, I want each notification's title, message, priority
   and emoji tag unchanged for both Periods.
8. As the maintainer, I want the email heading dates computed from an injected clock, so
   that tests are deterministic without patching time.

## Implementation Decisions

- New module holding a `Period` enum with members `TOMORROW` and `WEEK`. Each member
  carries plain data only (no HTML, no email headers): email subject, ntfy title suffix,
  ntfy priority, and whether the email table shows the Collection Date column. Period does
  not import any Channel code.
- `Period.select(collections)` returns the Waste Collections for that Period. Tomorrow
  keeps those with `is_tomorrow`; Week keeps those with `is_this_week`, sorted by
  `next_collection_date`. It reads the existing `is_tomorrow` and `is_this_week` flags
  (removing those flags is a separate change).
- `Period` supplies `ntfy_message(collection)` (Tomorrow: "Put it out tonight."; Week:
  "Collection is <date>.") and an email heading derived from `now` (Tomorrow: the date of
  `now` plus one day; Week: "Week Commencing: <date of now>").
- The email builder and the ntfy builder take a `Period` and read these fields; neither
  contains a `match` on the Period.
- One shared email HTML template. Table columns follow `shows_collection_dates`. The stray
  unclosed `<td>` in today's weekly rows is closed; browsers already auto-close it.
  Whitespace and indentation of the generated HTML may differ.
- The clock is injected: the email builder takes `now: datetime` in place of `tz`.
  `send_reminders` computes `datetime.now(tz)` once and passes it down. Its signature
  otherwise changes only in that `period` is a `Period` rather than a `str`.
- The scheduled jobs in `main.py` replace their inline filtering and sorting with
  `Period.select(...)` and pass `Period.TOMORROW` / `Period.WEEK` to `send_reminders`. The
  job bodies are otherwise left as they are.
- No schema, config, or Channel-contract changes. No ADR.

## Testing Decisions

- Tests assert external behaviour through the highest existing seam, `send_reminders`,
  with `notify.SMTP` and `notify.requests.post` patched (system boundaries), as in
  `tests/test_reminder.py`. The clock is a fixed `now`, never patched.
- Characterisation tests are written first against today's behaviour, then must keep
  passing through the refactor. Email: parse the message handed to SMTP and assert on
  subject, `X-Priority`, `Importance`, `<title>`, `<h1>`, table header cells, and one row
  per collection (service name, colour, and the date when shown). ntfy: assert on the JSON
  posted. Both Periods, plus an empty collection list.
- A second, pure seam: `Period.select`. Tomorrow keeps only `is_tomorrow` collections;
  Week keeps only `is_this_week` collections, sorted by date; empty input returns empty.
- Existing `build_ntfy_notifications` tests are updated to pass a `Period`. The
  unknown-period test is removed, because the type no longer permits it.
- Prior art: `tests/test_reminder.py`, `tests/test_ntfy_notifications.py`,
  `tests/support.py` (`a_collection`).

## Out of Scope

- Extracting the daily and weekly jobs from `main.py` (architecture review candidate #1).
- Removing the `is_tomorrow` / `is_this_week` flags from `WasteCollection` or moving date
  rules out of the scraper (candidate #3).
- Any visible change to the emails or ntfy notifications, including CSS tidy-ups.
- Channel changes, settings changes, logging changes.

## Further Notes

- Origin: architecture review candidate #2, "Make the reminder period a real concept".
- Mention the closed stray `<td>` and the possible whitespace differences in the PR
  description.
