# Give email and ntfy a shared Channel interface

## Problem Statement

The Reminder run knows about each delivery route separately. `send_reminders` builds the
email content, calls the email sender inside its own try/except, then builds the ntfy
notifications and calls the ntfy sender, which hides an "ntfy is not configured" check
inside the `Notify` class. The run therefore owns each route's content, its error handling
and its configuration, and the independence of the two routes is a consequence of call
order and an ad hoc try/except rather than of a shared contract. Adding a route, or
testing one route on its own, means editing the run.

## Solution

Make **Channel** (already in the glossary) a real interface. A Channel is given a
Reminder's collections, the run's single clock reading and the Period, and delivers the
Reminder over its route, building its own content and owning its own retries, failure
handling and log lines. A Channel's send never raises, so independence between Channels is
a property of the interface. The Reminder run holds a list of Channels (email always, ntfy
only when configured) and sends through each in turn.

Nothing a recipient sees changes: the same email and ntfy content, the same retries, the
same schedule and the same configuration.

## User Stories

1. As the maintainer, I want the Reminder run to send through a list of Channels, so that
   it knows nothing about email or ntfy.
2. As the maintainer, I want each Channel to own its content, retries, failure handling and
   log lines, so that everything about one route lives in one place.
3. As the maintainer, I want a Channel's send never to raise, so that one Channel failing
   cannot block another by construction.
4. As the maintainer, I want ntfy to be present in the list only when configured, so that
   the run has no "is this route configured?" check.
5. As the maintainer, I want to test one Channel without the run, and the run without a
   real Channel, so that a new route needs no change to the run.
6. As a resident, I want the email Reminder to have the same subject, content and
   recipients as today.
7. As a resident, I want one ntfy push per bin, at the same priority and with the same
   text, as today, and the topic never to appear in logs.
8. As a resident, I want a failing email not to stop the ntfy pushes (and the reverse), as
   today.

## Implementation Decisions

- A `Channel` Protocol with one operation, `send(collections, now, period)`, which never
  raises.
- `EmailChannel` is built with the SMTP client, the sender address and the target email
  addresses. It builds the email content, sends it with the existing retry, logs "Sent
  notification e-mail to [...]" on success, and catches and logs "Failed to send <period>
  email reminder." on failure, exactly as today.
- `NtfyChannel` is built with the ntfy client. It builds one push per bin, publishes each
  with the existing retry, and keeps today's per-notification success and failure log
  lines. Building the content is now inside its failure handling: a failure there is
  logged as "Failed to send <period> ntfy reminder." instead of escaping and failing the
  whole run. This is the only deliberate behaviour difference and is practically
  unreachable.
- `SMTPClient` and `NtfyClient` stay as the thin boundary adapters the Channels wrap.
  Channels live in the same module as today's `Notify`, so tests still patch
  `notify.SMTP` and `notify.requests.post`.
- `build_channels(settings)` returns the list: the email Channel first, then the ntfy
  Channel only when ntfy is configured. It replaces `build_notify`; `Notify` is removed.
- `send_reminders(channels, collections, now, period)` sends through each Channel in
  order. `run_reminder` takes the list of Channels and no longer takes settings;
  `schedule_reminder_runs` takes the Channels and keeps settings for the time and
  timezone. The run still reads its clock once per run and uses that reading for selection
  and sending.
- `main()` builds the Channels with `build_channels(settings)` and passes them on.
- No schema, config or content changes. No ADR.

## Testing Decisions

- Tests assert external behaviour through the mocked system boundaries (`notify.SMTP`,
  `notify.requests.post`), not private helpers.
- Main seam: `send_reminders` with `build_channels(settings)`, as the existing reminder,
  email-content, run and schedule tests already exercise it; those change only to the new
  signatures. They keep proving email content, one push per bin, and that a failing email
  does not stop the pushes.
- `NtfyChannel.send` is tested directly in place of `Notify.send_ntfy`: JSON body, retry,
  one failing notification not stopping the others, HTTP errors, and the topic never in
  logs. "Ntfy not configured" becomes `build_channels` returning only the email Channel.
- One new test with plain fake Channels shows the run sends through whatever Channels it
  is given, in order, without knowing their type.
- Not unit tested, as before: the `main()` wiring line.
- Prior art: `tests/test_ntfy_delivery.py`, `tests/test_reminder.py`,
  `tests/test_reminder_run.py`.

## Out of Scope

- New Channels, new configuration, changed content, priorities or retry policy.
- The SMTP or ntfy clients' internals, and the `retry` decorator.
- Logging configuration (separate candidate).

## Further Notes

- Origin: architecture review candidate #5, building on `Period` (PR #288), the Reminder
  run (PR #294), the Page source seam (PR #299) and validated settings (PR #307).
