# Move `bin-reminder` Config Bind Mount to the `pi-media` Per-Container Layout

## Problem Statement

The `bromley-bin-reminder` service bind-mounts its config directory from the Pi's SD card:

```yaml
volumes:
  - /home/pi/.config/bin-reminder:/config
```

The Pi's other Docker stacks are being moved off the SD card onto the media drive under a
single per-container root (`/mnt/media/pi-media/containers/<container-name>/…`). The sibling
`hypervolt-agile-scheduler` service in the same `pi-desktop` compose has already migrated;
`bin-reminder` is the remaining SD-card holdout in that file. Keeping container state on the
SD card adds avoidable write wear and leaves the layout inconsistent across the stack.

## Solution

Repoint the single `/config` host bind from `/home/pi/.config/bin-reminder` to
`/mnt/media/pi-media/containers/bin-reminder/config`, in both this repo's reference
`docker-compose.yml` and the committed `pi-desktop` deploy compose, then cut the running
container over on the Pi and remove the old SD-card directory.

## User Stories

1. As the Pi maintainer, I want `bin-reminder`'s config to live under
   `/mnt/media/pi-media/containers/bin-reminder/`, so that all containers in the `pi-desktop`
   stack follow one per-container layout and the SD card takes fewer writes.

## Implementation Decisions

- **One bind mount only.** `bin-reminder` mounts `/config` and nothing else. Logging is
  stdout-only (`app/common/logging.py` configures a single `StreamHandler` to
  `ext://sys.stdout`), captured by Docker's log driver, so there is no `/logs` or
  `/extensions` mount to move and no host `log/` directory is created. The runbook's "name
  the log subdir `log` not `logs`" guidance does not apply here.
- **New host path:** `/mnt/media/pi-media/containers/bin-reminder/config` → `/config`.
- **Container-internal path is unchanged.** Only the host side of the bind moves. The image's
  `CMD … --config-file /config/config.yml` and `VOLUME /config` in the `Dockerfile` need no
  edit.
- **`image`, `pull_policy`, `labels`, `restart` are untouched.**
- **The service is already present in the committed `pi-desktop` compose**
  (`docker/docker-compose.yml`), so the deploy-side change is a one-line edit to its
  `volumes:` entry, not a new service block.
- **No `depends_on`, no healthcheck.** `bin-reminder` depends on nothing and defines no
  healthcheck, so the cutover has no dependency to reconcile and the post-cutover pass
  criterion is `state=running` with `restarts` unchanged rather than `health=healthy`.
- **README and config templates are not touched.** The README sections are empty stubs and
  neither `config/config.yml.template` nor `.env.template` names a host path.
- **No ADR.** Consistent with the precedent set by the previous chore in this repo
  (`node24-actions-docker-retry`), a small, low-risk change that is a translation of an
  already-executed cross-repo pattern (`hypervolt-agile`, 2026-09-08) is recorded here in the
  spec/issue rather than in a new ADR. This repo has no ADR directory.

## Testing Decisions

No application code or test logic changes — this is deployment configuration only.
Verification is direct:

- Render the edited `docker-compose.yml` (`docker compose -f - config`) and confirm the sole
  bind source is `/mnt/media/pi-media/containers/bin-reminder/config`.
- `grep` the repo for the old host path and confirm no references remain outside this
  spec/issue.
- On the Pi after cutover: `docker inspect bin-reminder` shows the `/config` mount resolving
  to the new path with `rw=true`, `state=running`, `restarts=0`, and `docker logs` shows the
  scheduler running normally against `/config/config.yml`.

## Out of Scope

- Any change to application behaviour, dependencies, or the test suite.
- Migrating other/older stacks on the Pi — only `bin-reminder` in the `pi-desktop`
  `docker/docker-compose.yml` is in scope.
- Reconciling the uncommitted Windows-workstation copy of the `pi-desktop` compose
  (`c:\Users\mehol\git\pi-desktop\docker\docker-compose.yml`) with the committed file. The
  cutover commits the committed file; the workstation copy is reconciled by hand afterwards.

## Further Notes

The running container's compose labels point at a workstation path that was committed to
`pi-desktop` anyway, so the committed `docker/docker-compose.yml` is the file edited during
cutover. After cutover the Pi's `pi-desktop` checkout carries a local commit ahead of the
workstation copy until reconciled.
