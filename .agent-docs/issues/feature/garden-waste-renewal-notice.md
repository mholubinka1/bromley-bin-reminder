# Issues: feature/garden-waste-renewal-notice

> Work complete — PR ready to merge.

## A due renewal reaches the resident on Sunday

**Blocked by**: None

**User stories**: 1, 4, 6, 7, 8

### What to build

The Scraper reads the Garden Waste subscription from the WasteWorks page (the leading date
of the Renewal row, ignoring any trailing note, and the Subscription row's text) and returns
it, or nothing for a household without Garden Waste. A `GardenWasteSubscription` value
decides that a notice is due when the renewal date is 0 to 30 days away. `Channel` gains
`send_renewal`, implemented by the email and ntfy Channels, each building its own message
(date and price). The Sunday (Week) run checks the subscription after the collection
Reminder part, in its own failure boundary, and sends the notice through every Channel when
due, even in a week with no collections. The nightly run does nothing new.

### Acceptance criteria

- [x] Given a subscription renewing in 20 days, when the Sunday run happens, then the email and the ntfy push go out with the date and price
- [x] Given a renewal 31 days away, when the Sunday run happens, then nothing is sent
- [x] Given a renewal exactly 30 days away, when the Sunday run happens, then a notice is sent
- [x] Given a page with no Garden Waste section, when the Sunday run happens, then nothing is sent
- [x] Given the Tomorrow run, then no notice is sent
- [x] Given no bin is collected that week, when the Sunday run happens, then the notice is still sent
- [x] Given a Renewal row with a trailing note such as ", soon due for renewal.", then the date is still read

---

## Automatic renewal reassurance

**Blocked by**: #316

**User stories**: 3

### What to build

The Scraper records whether the page says the subscription renews automatically by direct
debit, and the due notice on both Channels says so to reassure the resident.

### Acceptance criteria

- [x] Given the page says the subscription renews automatically, when a due notice is sent, then the email and the ntfy push say so
- [x] Given a due subscription that does not renew automatically, when a notice is sent, then it has no such line

---

## Overdue notice

**Blocked by**: #316

**User stories**: 2

### What to build

A renewal date that has passed makes the subscription overdue, and the Sunday run sends an
overdue notice on both Channels (the council keeps showing the subscription for about four
weeks). The ntfy push for an overdue subscription has a higher priority.

### Acceptance criteria

- [x] Given a Renewal date that has passed, when the Sunday run happens, then an overdue notice goes out on both Channels
- [x] Given an overdue notice on ntfy, then its priority is higher than a due notice's

---

## Stay quiet, and log what cannot be read

**Blocked by**: #316

**User stories**: 5, 9, 10

### What to build

No notice while a cancellation or a pending subscription or direct debit is shown. A Garden
Waste section whose Renewal row is missing or whose date cannot be read produces no notice
and a logged warning, and never an error. The subscription read and the collection part of
the Sunday run fail independently.

### Acceptance criteria

- [x] Given "Cancellation in progress", or a pending subscription or direct debit, when the Sunday run happens, then no notice is sent
- [x] Given a Garden Waste section whose Renewal row is missing or unparseable, when the Sunday run happens, then nothing is sent and a warning is logged
- [x] Given the subscription read fails, when the Sunday run happens, then the collection Reminder is still sent
- [x] Given the collection scrape fails, when the Sunday run happens, then the notice is still sent

---
