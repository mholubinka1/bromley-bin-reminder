# ntfy Notifications

## Problem Statement

Reminders only arrive by email. The maintainer wants them as push notifications on their
phone too, via ntfy, without losing the existing email. Email groups every Service into
one message; on a phone, one glanceable notification per bin is more useful.

## Solution

Add ntfy as a second Channel alongside email, sent on the same schedule as the email
Reminders: the Sunday weekly job and the daily night-before job.

- Each Reminder produces **one ntfy notification per Service** (not one per run).
- Night-before notifications: title `<Service>: tomorrow`, body `Put it out tonight.`,
  high priority.
- Weekly notifications: title `<Service>: this week`, body
  `Collection is <Weekday> <ordinal> <Month>.`, default priority. Ordered by collection
  date, as the weekly email is.
- Every notification carries a single emoji tag identifying the Service, and no colour
  tags: Mixed Recycling `recycle`, Paper & Cardboard `newspaper`, Garden Waste
  `fallen_leaf`, Non-Recyclable Refuse `wastebasket`, Food Waste `banana`.
- ntfy is optional. An `ntfy:` config block with `server` (default `https://ntfy.sh`) and
  `topic` enables it; a missing block or blank topic leaves behaviour exactly as today.
- Channels are independent: an email failure does not stop ntfy and vice versa.

This format was prototyped against a real ntfy.sh topic and confirmed on the
maintainer's phone before implementation.

## User Stories

1. As the maintainer, I want one ntfy notification per bin on the weekly Reminder, so that
   I can see each bin and its date at a glance on my phone.
2. As the maintainer, I want one high-priority ntfy notification per bin the night
   before, so that I am prompted to put each bin out.
3. As the maintainer, I want an emoji per Service in each notification, so that I can tell
   the bins apart without reading.
4. As the maintainer, I want ntfy on the same schedule as email, so that nothing about
   when Reminders arrive changes.
5. As the maintainer, I want ntfy to be optional in config, so that existing deployments
   keep working with no config change.
6. As the maintainer, I want the topic and server in the bind-mounted config, so that the
   topic (effectively a secret on public ntfy.sh) never enters the repository.
7. As the maintainer, I want a failing channel not to block the other, so that an SMTP
   outage still lets the phone notification through and vice versa.
8. As the maintainer, I want transient ntfy failures retried like email, so that a brief
   network blip does not lose a Reminder.
9. As the maintainer, I want one failed bin notification not to prevent the remaining
   bins being sent, so that a partial failure still delivers as much as possible.

## Implementation Decisions

- A new ntfy notification model (title, message, priority, tags) built from a list of
  Waste Collections and a period (`tomorrow` / `week`). The Service-to-ntfy-tag mapping is
  a module-level constant; an unknown Service gets a generic
  fallback tag rather than raising, since the council can add Services.
- A new ntfy client in the notify module that publishes a notification as JSON to the
  configured server (JSON publishing is used so non-ASCII titles are safe), wrapped in the
  existing `retry` decorator, with a request timeout. Uses the existing `requests`
  dependency — no new runtime dependency. A `build_notify` factory in the same module
  builds the `Notify` (SMTP client plus optional ntfy client) from settings.
- `Notify` accepts an optional ntfy client and exposes a send for a list of
  notifications; one notification failing is logged and the rest are still attempted.
- `ApplicationSettings` gains an optional ntfy block (server, topic). A blank topic means
  ntfy is disabled, `main` logs at startup whether ntfy is enabled, and the topic is
  never logged.
- A new reminder module owns "send this Reminder over every configured Channel", with
  per-channel error isolation. The daily and weekly jobs in `main` call it instead of
  calling `send_email` directly. Job scheduling and scraping logic are unchanged.
- Config template, README and `context.md` document the new block and terms.
- Topic length: ntfy.sh caps topics at 64 characters; documented in the template.

## Testing Decisions

- Test external behaviour at two seams: the pure notification builder (collections in,
  notifications out) and the reminder module (collections in; asserts on what is handed
  to the mocked system boundaries — SMTP and `requests.post`).
- Mock only system boundaries: SMTP client and HTTP post. Time that matters is passed in
  (a fixed `now`) so tests are deterministic. The `retry` delay is patched to zero.
- There is no existing test suite or runner. pytest and pytest-cov are added as dev
  dependencies; pipeline-level coverage enforcement is outside this change.

## Out of Scope

- ntfy authentication (access tokens / basic auth) for self-hosted servers.
- Icons, click URLs, action buttons, attachments, delayed delivery.
- Changing email content, schedule, or making email optional.
- A CI test job.

## Further Notes

- ntfy.sh message cache is ~12h; Reminders are sent at the configured time daily.
- The existing unused `_create_push` stub on the notification class is removed.
