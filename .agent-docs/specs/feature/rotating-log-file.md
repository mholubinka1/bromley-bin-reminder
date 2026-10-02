# Spec: feature/rotating-log-file

## Problem
Logging is stdout-only, so logs vanish with the container. They should persist on pi-media,
mirroring the `/config` bind mount.

## Decisions
- Add a `RotatingFileHandler` (5 MB, 5 backups) writing `bin-reminder.log` in the log directory.
- Console (stdout) handler is kept alongside it.
- Log directory comes from `LOG_DIR` (default `/logs`). If it is not writable (local dev),
  file logging is skipped and the app logs to console only.
- Dockerfile creates `/logs`, owned by `sel_user`, and declares `VOLUME /logs`.
- docker-compose binds `/mnt/media/pi-media/containers/bin-reminder/logs:/logs`.

## Out of scope
Log format/level changes; log shipping.
