# Issues: feature/rotating-log-file

## Write logs to a rotating file on a mounted volume

**Blocked by**: None

### Acceptance criteria

- [x] Given a writable log directory, config includes a rotating file handler writing `bin-reminder.log` there, alongside stdout.
- [x] The file handler rotates at a bounded size and keeps a bounded number of backups.
- [x] Given an unwritable or missing log directory, config has the console handler only and no error is raised.
- [x] Dockerfile creates a `sel_user`-owned `/logs` volume; compose bind-mounts the pi-media logs dir.
- [x] `uv run pytest` passes.
