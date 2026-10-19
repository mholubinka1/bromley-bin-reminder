# Issues: chore/validated-settings

## Settings are built and validated by one call

**Blocked by**: None

**User stories**: 1, 4, 5, 6, 7, 8, 10

### What to build

`ApplicationSettings` becomes a plain holder of already-valid values, including a resolved
timezone. One call, `parse_settings(raw)`, builds it from the parsed YAML dictionary and
returns valid settings or raises. It applies the existing poll-time and timezone defaults
with the existing warnings, keeps the existing validation errors and ntfy rules, and
resolves the timezone once with `zoneinfo`. `validate_settings` is removed; the config
loader calls `parse_settings`, and `main()` builds its clock from the settings' resolved
timezone instead of parsing the name again. Tests that built settings directly use
`parse_settings`.

### Acceptance criteria

- [ ] Given a blank poll time, when parsed, then the time is 18:00 and a warning is logged
- [ ] Given a blank timezone, when parsed, then the timezone is Europe/London and a warning is logged
- [ ] Given an unrecognised timezone, when parsed, then the timezone is Europe/London and a warning is logged
- [ ] Given a valid timezone, when parsed, then `timezone` is that zone and `remind.tz` is its name
- [ ] Given a blank URL, blank SMTP username, or missing SMTP server or port, when parsed, then it raises `RuntimeError` with the current message
- [ ] Given a missing required key, when parsed, then it raises
- [ ] The existing ntfy rules behave as before
- [ ] `validate_settings` is gone; `pytz` stays (the scheduler uses it, and the timezone check uses its zone list so the two agree)

---

## Loading raises instead of exiting

**Blocked by**: #305

**User stories**: 2, 3, 9

### What to build

`load_settings(path)` reads the YAML file and returns `parse_settings` of its contents. Any
failure raises an exception whose message names the path, and nothing in settings loading
calls `sys.exit`. `ConfigLoader` is removed. `main()` calls `load_settings` inside its
startup handler, which logs "Could not load startup configuration." and exits 1.

### Acceptance criteria

- [ ] Given a valid file, when loaded, then valid settings are returned
- [ ] Given a missing file, when loaded, then it raises and the message names the path
- [ ] Given malformed YAML, when loaded, then it raises and the message names the path
- [ ] `ConfigLoader` and its `sys.exit` are gone; `main()` still logs and exits 1 on any startup failure

---
