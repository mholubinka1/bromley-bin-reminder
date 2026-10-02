# Issues: feature/ntfy-notifications

## Build per-bin ntfy notifications

**GitHub issue**: #277

**Blocked by**: None

**User stories**: 1, 2, 3, 4

### What to build

Add the test runner (pytest, pytest-cov) and a pure builder that turns a list of Waste
Collections and a period into one ntfy notification per Service in the locked format.
Remove the unused `_create_push` stub.

### Acceptance criteria

- [ ] Given collections for several Services and period `tomorrow`, one notification per
      Service is produced, each titled `<Service>: tomorrow`, body `Put it out tonight.`,
      priority high (4), tagged with only that Service's emoji.
- [ ] Given period `week`, one notification per Service titled `<Service>: this week`,
      body `Collection is <Weekday> <ordinal> <Month>.`, default priority (3), in the order
      supplied.
- [ ] Each of the five Services maps to its confirmed emoji; no colour tags are used.
- [ ] An unknown Service yields a notification with a generic tag instead of an error.
- [ ] An empty list yields no notifications; an unknown period raises.
- [ ] `uv run pytest` passes.

---

## Deliver ntfy notifications from optional config

**GitHub issue**: #278

**Blocked by**: #277

**User stories**: 5, 6, 8, 9

### What to build

Optional `ntfy:` config block (server defaulting to `https://ntfy.sh`, topic), an ntfy
client that posts each notification as JSON with retry and timeout, and a `Notify` send
that attempts every notification even if one fails.

### Acceptance criteria

- [ ] Config without an `ntfy:` block, or with a blank topic, loads and disables ntfy.
- [ ] With a topic, each notification is posted as JSON to the server containing topic,
      title, message, priority and tags.
- [ ] A failing notification is retried; once retries are exhausted the remaining
      notifications are still sent and the failure is logged without the topic.
- [ ] Server defaults to `https://ntfy.sh` when omitted.

---

## Send Reminders over every Channel from the daily and weekly jobs

**GitHub issue**: #279

**Blocked by**: #278

**User stories**: 1, 2, 4, 7

### What to build

A reminder module that sends a Reminder over email and, when configured, ntfy, with
per-channel error isolation. Daily and weekly jobs use it. Update the config template,
README and context glossary.

### Acceptance criteria

- [ ] Weekly job with ntfy configured sends the email plus one ntfy notification per bin
      due this week; daily job sends the email plus one per bin due tomorrow.
- [ ] With ntfy not configured, only email is sent, as before.
- [ ] If email sending fails, ntfy notifications are still sent, and vice versa.
- [ ] `config/config.yml.template` and README document the ntfy block, including the
      64-character topic limit.
- [ ] A real notification sent from the finished code to the test topic matches the
      locked format.
