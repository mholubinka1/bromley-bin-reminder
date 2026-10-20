# Warn before the Garden Waste subscription renews or lapses

## Problem Statement

A Garden Waste subscription runs for a year, and when it is not renewed the garden bins
silently stop being collected. The council tells the subscriber only through its own
channels, and the WasteWorks page shows nothing but a Renewal date, which this service
ignores. A resident who relies on the service's Reminders hears nothing about the
subscription until a collection simply does not happen. Households that pay by direct debit
renew automatically, but still get no reminder that a payment is coming.

## Solution

Read the Garden Waste subscription from the WasteWorks page and send a **Renewal notice**
over every Channel (email and ntfy) on the weekly Sunday run: when the Renewal date is within
the next 30 days, and while the subscription is overdue (the council keeps showing it for
about four weeks after the date). The notice is separate from the collection Reminders, is
sent even in a week with no bin collections, and, when the page says the subscription renews
automatically by direct debit, says so to reassure the resident. Nothing is sent while a
cancellation or a pending subscription is shown, for households without Garden Waste, or when
the page cannot be read.

Nothing about the nightly and weekly collection Reminders changes.

## User Stories

1. As a resident with a Garden Waste subscription, I want a notice in the 30 days before it
   is due for renewal, so that my garden bins keep being collected.
2. As a resident whose subscription is overdue, I want a weekly notice until it is renewed
   or the council stops showing it, so that I know collections will not happen.
3. As a resident who pays by direct debit, I want the notice to tell me the subscription
   renews automatically, so that I am not alarmed.
4. As a resident, I want the notice to include the price and bin count the page shows, so
   that I know what I am renewing or paying.
5. As a resident whose cancellation or new subscription is already in progress, I want no
   renewal notice, so that I am not nagged about something I have already acted on.
6. As a resident with no Garden Waste, I want nothing at all.
7. As a resident, I want the notice by email and by ntfy, the same Channels as my Reminders.
8. As the maintainer, I want a notice to be sent even when no bin is collected that week.
9. As the maintainer, I want a failure reading or sending the notice never to stop the
   collection Reminders, and the reverse.
10. As the maintainer, I want a Renewal row I cannot understand to be logged, so that a
    change on the council's page shows up in the log file instead of silently disabling the
    notice.

## Implementation Decisions

- A `GardenWasteSubscription` value (frozen) holds the renewal date, the Subscription row's
  text (price and bin count, verbatim), whether the page says it renews automatically, and
  whether a cancellation or a pending subscription is in progress. It decides whether a
  notice is due for a given today and whether it is overdue, so the rules live in one place.
- Due rule: the renewal date is 0 to 30 days away (the same day counts). Overdue rule: the
  renewal date has passed. A subscription with a cancellation or a pending subscription or
  direct debit in progress never produces a notice.
- The Scraper gains `get_garden_waste_subscription()`, returning the value or `None`, parsed
  from a fresh render of the same page. It returns `None` for a household with no Garden
  Waste section. If the section is present but the Renewal row is missing or its date cannot
  be read, it logs a warning and returns `None`. It never raises for page-shape problems.
- The Renewal row is parsed from its leading `DD Month YYYY`. The row can carry trailing
  notes (", soon due for renewal.", ", subscription overdue.", "Cancellation in progress"),
  which are not part of the date. In progress is recognised from "Cancellation in progress"
  and from the page's "pending" status sentences. Automatic renewal is recognised from "will
  renew automatically". These formats come from the council's published page templates; no
  live example of a non-direct-debit, due or overdue page was available to check against.
- `Channel` gains `send_renewal(subscription, now)`, which like `send` never raises.
  `EmailChannel` and `NtfyChannel` each build their own message from the subscription in the
  notification module beside the existing builders: due or overdue wording, the price text,
  the date, and for a due notice the automatic-renewal reassurance when it applies. The email
  has its own subject. The ntfy push has its own title, with higher priority when overdue.
- The Sunday (Week) run checks the subscription in its own failure boundary, after the
  collection Reminder part, using its own clock reading, and sends the notice through every
  Channel when due. The nightly run never does. `CollectionSource` gains the new method.
  `schedule_reminder_runs` and `main()` are unchanged.
- The wording is neutral about what the resident must do beyond checking the subscription is
  renewed and paid. It does not claim to know whether the council auto-renews, except when
  the page says it does.
- No settings, schema or dependency changes. No ADR.

## Testing Decisions

- Tests assert external behaviour only: what the Scraper returns for saved page HTML, what the
  run sends to recording Channels, and what lands at the mocked system boundaries
  (`notify.SMTP`, `notify.requests.post`). No tests of private parsing helpers.
- Test pages are built from the council's published page templates, one builder for the
  Garden Waste section with the states below, since no real page of every state exists.
- Scraper: active with direct debit; due and not direct debit; due with direct debit;
  overdue; cancellation in progress; pending subscription; no Garden Waste section; Renewal
  row missing; date unparseable; trailing notes do not affect the date.
- Subscription rules as a pure function: the day boundaries (same day, 30 days, 31 days,
  yesterday), overdue, in progress, with and without automatic renewal.
- Reminder run with recording Channels: notice sent on the Week run when due and when
  overdue; not on the Tomorrow run; not when not due or not subscribed; sent when no
  collections are selected; a failing subscription read does not stop the collection
  Reminder and a failing collection scrape does not stop the notice.
- Real Channels at the boundaries: the email subject and body and the ntfy push for due,
  overdue and automatic renewal; one failing Channel does not block the other.
- Prior art: `tests/test_scraper.py`, `tests/test_reminder_run.py`, `tests/test_reminder.py`,
  `tests/test_ntfy_delivery.py`, `tests/support.py`.

## Out of Scope

- Verifying the markup against a live non-direct-debit, due or overdue page (none was
  available; the notice logs any Renewal text it cannot read so a difference shows up).
- Warning on days other than the Sunday run, repeated reminders within a week, or storing
  what has been sent.
- Renewing, cancelling or changing the subscription, or following the council's links.
- Price-change detection, other paid services, and any change to Period or the collection
  Reminders.

## Further Notes

- Closes #303. The decisions behind this spec were made in a design session: neutral wording
  with an automatic-renewal reassurance, Sunday-run delivery within 30 days, overdue notices
  while the page still shows the subscription, and a separate `send_renewal` Channel method.
- The page rows, their trailing notes and the status sentences are taken from the council's
  open-source WasteWorks templates (mySociety FixMyStreet's Bromley waste cobrand). Their
  live behaviour was confirmed only for an active direct-debit subscription.
