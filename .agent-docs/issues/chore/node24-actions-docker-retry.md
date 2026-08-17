# Issues: chore/node24-actions-docker-retry

> Work complete — PR ready to merge.

## Harden ci-arm64.yml — Node 24 actions + Docker retry

**Issue**: #255

**Blocked by**: None

**User stories**: 1, 2

### What to build

Update `.github/workflows/ci-arm64.yml` so it only uses `node24`-runtime GitHub Actions, and
so the Docker Hub login/build/push step retries on transient failure instead of failing the
whole build outright.

Bump `actions/checkout` from `v2` to `v7`. Remove `docker/login-action` and
`docker/build-push-action` entirely, replacing both with a single step that runs
`docker login` (credentials via `env:`, piped via `--password-stdin`) and
`docker buildx build --push --tag "$TAG" .` against the local checkout, wrapped in
`nick-fields/retry@v4` (3 attempts, 15s wait, 5 minute timeout). Keep the existing
branch-based tag logic (`dev` for non-`main`, `latest` for `main`) and the
`DOCKER_IMAGE`/`DOCKER_REGISTRY` env vars unchanged.

### Acceptance criteria

- [x] `actions/checkout@v2` is bumped to `actions/checkout@v7`
- [x] `docker/login-action` and `docker/build-push-action` no longer appear in the workflow
- [x] Docker login and build/push run as shell commands wrapped in `nick-fields/retry@v4`
      (`max_attempts: 3`, `retry_wait_seconds: 15`, `timeout_minutes: 5`)
- [x] Docker Hub credentials are passed via the step's `env:` block, not as a CLI argument
- [x] The build uses the local checkout, not a remote `git#{sha}` context, with an inline
      YAML comment explaining why
- [x] A pushed run of the workflow succeeds (`gh run watch`)
- [x] The run's logs contain no "Node.js 20 is deprecated" warning

---
