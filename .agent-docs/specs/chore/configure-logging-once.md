# Configure logging once

## Problem Statement

Logging is configured as an import side effect, many times over. Eight modules (the entry
point, the Reminder run, notify, the Scraper, the reload poller, the collection model, the
settings and the retry decorator) each call `dictConfig` at import and then fetch the
shared app logger. Every call rebuilds the handlers, so a working rotating log file is
re-opened eight times. Logging is configured by whichever module happens to import first.
The logging module itself builds its configuration at import, which probes and opens the log
file (and prints the console-only fallback) just by being imported, so tests and tools get
that side effect too. Because the app logger does not propagate, tests need two hand-rolled
workarounds to see its records, and the tests that do configure logging restore only the
handlers, leaving propagation and level changed for later tests.

## Solution

Configure logging exactly once, explicitly, at the start of `main()`. Every other module
only fetches the logger by name and never configures anything. Importing a module has no
logging side effects, so tests see an unconfigured app logger that propagates and can be
read with plain `caplog`.

Nothing changes in production: the same format, handlers, rotation, console-only fallback
with its message, and log lines.

## User Stories

1. As the maintainer, I want logging configured in one place at startup, so that import
   order cannot change how logging behaves.
2. As the maintainer, I want importing a module to have no logging or file side effects, so
   that tests and tools can import freely.
3. As the maintainer, I want the log file opened once, not once per importing module.
4. As the maintainer, I want tests to read log lines with plain `caplog`, so that no
   hand-attached handlers are needed.
5. As a resident running the service, I want the same log format, file rotation and
   console-only fallback (with its warning) as today.
6. As a resident running the service, I want the same "Starting bromley-bin-reminder." line
   and every other log line unchanged.

## Implementation Decisions

- The logging module exposes `configure_logging(log_dir=None)`: it takes the log directory
  (default from the existing `LOG_DIR` environment variable, falling back to `/logs`),
  builds the configuration with the existing `build_config`, and applies it with a single
  `dictConfig`. `build_config` is unchanged, including the writability probe, the
  console-only fallback and the stderr message.
- The module-level `config` and its import-time construction are removed.
- `main()` calls `configure_logging()` first, before parsing arguments. The "Starting
  bromley-bin-reminder." line moves from the entry module's top level into `main()`,
  right after configuring.
- Every other module drops its `dictConfig` call and its `config` import and keeps only
  `logger = getLogger(APP_LOGGER_NAME)`. Fetching a logger by name before it is configured
  is safe: it is the same object once configured.
- The app logger keeps `propagate=False` once configured, as today.
- No new configuration, no changed log content, no ADR.

## Testing Decisions

- Tests assert observable behaviour: the handlers on the app logger after
  `configure_logging`, what reaches the log file, and what the stderr fallback says.
- New tests in the existing logging tests: configuring with a writable directory leaves the
  app logger with console and file handlers, propagation off, and messages reach the log
  file; configuring with an unwritable directory leaves only the console handler and
  reports the reason once; configuring twice leaves one set of handlers.
- The existing `build_config` tests stay. The logger-restore fixture in the logging tests
  also restores propagation and level, so configuring in one test cannot leak into others.
- Other tests read logs with `caplog`. The `app_log` fixture shrinks to setting the app
  logger's level and returning `caplog` (no handler attach), and the ntfy delivery tests'
  private `captured_app_logs` context manager is replaced by it.
- Not unit tested, as before: `main()` calling `configure_logging()` first.
- Prior art: `tests/test_logging.py`, `tests/conftest.py`.

## Out of Scope

- Changing the log format, levels, rotation limits, destinations or the `LOG_DIR` variable.
- Structured logging, per-module loggers, or changing what is logged.
- The `propagate=False` setting itself.

## Further Notes

- Origin: architecture review candidate #6, the last of the list, building on the earlier
  refactors (Period #288, Reminder run #294, Page source #299, validated settings #307,
  Channels #311).
- The brief said the fallback message printed repeatedly; it prints once per process
  because the configuration is built once at import. The real cost of the current design is
  the repeated `dictConfig` (re-opening the log file) and the import-time side effects.
