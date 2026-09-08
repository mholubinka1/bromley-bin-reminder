# Issues: chore/pi-media-container-bind-mounts

## Move `bin-reminder` config bind mount to the `pi-media` per-container layout

**Issue**: #270

**Blocked by**: None

**User stories**: 1

### What to build

Repoint `bromley-bin-reminder`'s single `/config` host bind mount from
`/home/pi/.config/bin-reminder` to `/mnt/media/pi-media/containers/bin-reminder/config`, in
this repo's reference `docker-compose.yml` and in the committed `pi-desktop` deploy compose
(`docker/docker-compose.yml`), then cut the running container over on the Pi and remove the
old SD-card directory.

Leave `image`, `pull_policy`, `labels`, `restart` and the container-internal path `/config`
untouched. Do not add a `/logs` or `/extensions` mount — logging is stdout-only. Do not touch
the README or config templates — no host paths appear in them.

### Acceptance criteria

- [ ] `docker-compose.yml` `/config` bind source is
      `/mnt/media/pi-media/containers/bin-reminder/config`
- [ ] `image`, `pull_policy`, `labels`, `restart`, and the container path `/config` are
      unchanged
- [ ] No `/logs` or `/extensions` mount is added
- [ ] No stale reference to `/home/pi/.config/bin-reminder` remains in the repo outside this
      spec/issue
- [ ] Rendered compose (`docker compose -f - config`) shows exactly one bind, pointing at the
      new path
- [ ] Pi: `/mnt/media/pi-media/containers/bin-reminder/config/config.yml` exists and its md5
      matches the old `/home/pi/.config/bin-reminder/config.yml`
- [ ] Pi: committed `pi-desktop` `docker/docker-compose.yml` updated and committed (only that
      file)
- [ ] Pi: `docker inspect bin-reminder` shows `/config` -> new path, `rw=true`,
      `state=running`, `restarts=0`
- [ ] Pi: old `/home/pi/.config/bin-reminder` removed after verification passes

---
