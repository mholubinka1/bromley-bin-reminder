# Give the application settings one validated entry point

## Problem Statement

Getting usable settings takes three calls whose order matters: `ConfigLoader` reads the
YAML and builds `ApplicationSettings` by raw dictionary indexing, `validate_settings` then
mutates those settings in place (applying the poll-time and timezone defaults, with
warnings), and `main()` finally parses the timezone string into a `ZoneInfo` a second time.
`ConfigLoader` also calls `sys.exit(1)` itself, so a load failure can only be tested by
catching `SystemExit`, and a half-built, not-yet-valid `ApplicationSettings` exists between
the calls. The timezone is validated against `pytz.all_timezones` in one place and resolved
with `zoneinfo` in another.

## Solution

One call returns settings that are already valid, or raises. The timezone is resolved once
and carried on the settings. Loading never decides what failure means:
`main()` catches, logs and exits, exactly as it does today for its other startup errors.

Nothing a resident sees changes. Defaults, warnings, validation errors, and the process
exiting with status 1 on bad configuration are preserved.

## User Stories

1. As the maintainer, I want one call to return settings that are already valid, so that no
   code can hold half-built settings or call the steps in the wrong order.
2. As the maintainer, I want settings loading to raise instead of exiting the process, so
   that failures are testable without catching `SystemExit`.
3. As the maintainer, I want `main()` alone to decide that a configuration failure means
   logging it and exiting with status 1, as today.
4. As the maintainer, I want the timezone validated and resolved once, so that the scheduler
   and the clock cannot disagree about which zone is in use.
5. As a resident, I want a blank poll time to fall back to 18:00 with a warning, as today.
6. As a resident, I want a blank timezone, or one that is not recognised, to fall back to
   Europe/London with a warning, as today.
7. As a resident, I want a blank WasteWorks URL, a blank SMTP username, or a missing SMTP
   server or port to stop startup with the same error messages, as today.
8. As a resident, I want ntfy to stay optional, with a blank topic disabling it and a blank
   server falling back to https://ntfy.sh, as today.
9. As the maintainer, I want the YAML path to appear in the error when the file cannot be
   loaded, so that the log still says which file was at fault.
10. As the maintainer, I want tests to build settings from a raw dictionary without writing
    a file, so that Reminder and Channel tests stay simple.

## Implementation Decisions

- `ApplicationSettings` becomes a plain data holder of already-valid values: the WasteWorks
  URL, the remind block (target emails, poll time, timezone name), the SMTP block, the
  optional ntfy block, and a resolved `timezone` (`ZoneInfo`).
- `parse_settings(raw)` builds and validates settings from the parsed YAML dictionary and
  returns them, or raises. It applies the existing defaults and emits the existing warning
  messages. It replaces the in-place mutation by `validate_settings`.
- `load_settings(path)` reads the YAML file and returns `parse_settings` of its contents.
  Any failure (missing or unreadable file, malformed YAML, a missing required key, a
  validation error) propagates as an exception whose message names the path. It never calls
  `sys.exit`. `ConfigLoader` and `validate_settings` are removed.
- Validation rules and messages are unchanged: blank URL, blank SMTP username, and missing
  SMTP server or port raise `RuntimeError` with the current texts; a missing required key
  still raises (a `KeyError`).
- The timezone is validated against `pytz.all_timezones_set` (the same set as before, and
  the one the scheduler's lookup uses) and then resolved once with `ZoneInfo(name)`; a name
  either rejects takes the unrecognised-timezone path. Names are taken exactly as written,
  so valid IANA names behave as before. `ZoneInfo` alone is not enough: it accepts names
  such as "Factory" and, on case-insensitive filesystems, wrong-case names, which the
  scheduler would then fail on.
- `remind.tz` stays the validated timezone name as a string, because `schedule`'s `.at()`
  takes a name and does its own lookup. `main()` builds its clock from the settings'
  `timezone` instead of parsing the name again. `schedule_reminder_runs` is unchanged.
- `main()` calls `load_settings` inside its existing startup `try`; its single handler logs
  "Could not load startup configuration." with the traceback and exits 1. The separate
  "Failed to load application settings from <path>" log and its own exit are removed; the
  path now travels in the exception message. The "Successfully loaded settings" info log is
  kept.
- `pytz` stays in `pyproject.toml`: `schedule` imports it itself for `.at(time, tz)`, and
  the settings keep using its zone list for validation so the two always agree.
- No schema, config-file, or Channel-contract changes. No ADR.

## Testing Decisions

- Tests assert on external behaviour: the settings returned, the exceptions raised, and
  the warnings logged (via `caplog`), never on private helpers.
- `parse_settings(raw)` is the main seam: ntfy rules (the existing eight tests, moved over),
  poll-time default and warning, blank timezone default and warning, unrecognised timezone
  default and warning, the resolved `timezone` matching the name, each validation error,
  and a missing required key.
- `load_settings(path)` is a thin second seam, tested with a temporary YAML file: a valid
  file loads; a missing file raises with the path in the message; malformed YAML raises.
- Tests elsewhere that construct `ApplicationSettings(yaml_settings(...))` switch to
  `parse_settings(yaml_settings(...))`.
- Not unit tested, as before: `main()`'s catch, log and `sys.exit(1)`.
- Prior art: `tests/test_settings.py`, `tests/support.py`.

## Out of Scope

- Logging configuration (separate candidate), the Channel interface (separate candidate).
- New settings, new validation rules, or changed defaults.
- Removing `pytz` from `pyproject.toml`.
- Hot-reload behaviour of `ConfigChangePoller`.

## Further Notes

- Origin: architecture review candidate #4, building on `Period` (PR #288), the Reminder
  run (PR #294) and the Page source seam (PR #299).
