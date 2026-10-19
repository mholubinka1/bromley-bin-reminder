# Issues: chore/shared-channel-interface

## The Reminder run sends through a list of Channels

**Blocked by**: None

**User stories**: 1, 2, 4, 5, 6, 7, 8

### What to build

A `Channel` interface with one operation, `send(collections, now, period)`. An email
Channel and an ntfy Channel implement it, each building its own content and owning its
retries and log lines; they wrap the existing SMTP and ntfy boundary clients. A single
`build_channels(settings)` call returns the list (email always, ntfy only when configured)
and replaces `build_notify`; `Notify` is removed. The Reminder run and `send_reminders`
send through the list and no longer take settings for sending; the schedule keeps settings
for the time and timezone. `main()` builds the Channels. Existing tests move to the new
signatures, and the ntfy delivery tests exercise the ntfy Channel directly.

### Acceptance criteria

- [ ] Given ntfy is configured, when a night-before Reminder is sent, then one email goes out and one high priority push per bin
- [ ] Given ntfy is not configured, when a Reminder is sent, then only the email is sent and `build_channels` returns only the email Channel
- [ ] Given the email fails, when a Reminder is sent, then the failure is logged as before and the pushes still go out
- [ ] Given one ntfy notification fails, when the Reminder is sent, then the others are still delivered and the topic is never logged
- [ ] Given plain fake Channels, when the run sends, then each receives the same collections, clock reading and Period, in order
- [ ] `Notify` and `build_notify` are gone; email and ntfy content, retries and log lines are unchanged

---

## A Channel's send never raises

**Blocked by**: #309

**User stories**: 3

### What to build

The ntfy Channel catches and logs a failure while building its content, as "Failed to send
<period> ntfy reminder.", instead of letting it escape and fail the whole run. This is the
one deliberate behaviour difference of the refactor.

### Acceptance criteria

- [ ] Given ntfy content cannot be built, when a Reminder is sent, then the failure is logged, no exception propagates, and the email still goes out

---
