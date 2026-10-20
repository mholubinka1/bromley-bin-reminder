# Issues: chore/configure-logging-once

## Logging is configured once, at startup

**Blocked by**: None

**User stories**: 1, 2, 3, 5, 6

### What to build

A single `configure_logging(log_dir=None)` in the logging module reads the log directory
(from `LOG_DIR`, defaulting as today), builds the configuration with the existing
`build_config` and applies it with one `dictConfig`. The module-level `config` and its
import-time construction are removed. `main()` calls `configure_logging()` first and logs
"Starting bromley-bin-reminder." right after; every other module drops its `dictConfig`
call and keeps only the logger fetch by name. The logging tests' restore fixture also
restores propagation and level, and the existing test helpers keep working without
double-recording.

### Acceptance criteria

- [ ] Given a writable log directory, when logging is configured, then the app logger has console and file handlers with propagation off, and messages reach the log file
- [ ] Given an unwritable log directory, when logging is configured, then only the console handler is used and the reason is printed once on stderr
- [ ] Given logging is configured twice, then the app logger has a single set of handlers
- [ ] Given a module is imported, then no handler is added to the app logger and no log file is opened
- [ ] Only `configure_logging` calls `dictConfig` in the application; format, handlers, rotation and log lines are unchanged

---

## Tests read logs with plain caplog

**Blocked by**: #312

**User stories**: 4

### What to build

With nothing configuring logging at import, the app logger propagates and plain `caplog`
sees it. The `app_log` fixture shrinks to setting the app logger's level and returning
`caplog` without attaching a handler, and the ntfy delivery tests' private
`captured_app_logs` helper is replaced by it.

### Acceptance criteria

- [ ] Given a test that triggers a logged failure, when it asserts on the log, then it reads it through `caplog` with no hand-attached handler, and each line is recorded once
- [ ] `captured_app_logs` is gone and `app_log` no longer attaches a handler

---
