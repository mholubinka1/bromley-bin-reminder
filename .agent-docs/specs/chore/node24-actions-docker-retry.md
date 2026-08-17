# CI: Node 24 Action Runtimes + Docker Login/Push Retry

## Problem Statement

The ARMv7 Docker Build/Publish workflow (`.github/workflows/ci-arm64.yml`) pins action
versions (`actions/checkout@v2`, `docker/login-action@v2`, `docker/build-push-action@v4`)
whose `action.yml` declares `using: node20`. GitHub removes Node 20 support from Actions
runners entirely on 2026-09-16 — after that date these actions stop working outright, not
just warn. Separately, the Docker Hub login/build/push steps have no retry: a transient DNS
blip or momentary Docker Hub auth hiccup fails the whole build with no automatic recovery,
requiring a manual re-push to notice and fix.

## Solution

Bump the pinned actions to versions confirmed `node24`, and replace the two Docker actions
with plain shell commands wrapped in a retry action, so transient failures self-heal instead
of failing the whole build.

## User Stories

1. As the repo maintainer, I want the CI workflow to use only Node 24-runtime actions, so
   that builds keep working after GitHub removes Node 20 support on 2026-09-16.
2. As the repo maintainer, I want the Docker Hub login/build/push step to retry on transient
   failure, so that a momentary DNS or auth blip doesn't require me to notice a failed build
   and manually re-push.

## Implementation Decisions

- `.github/workflows/ci-arm64.yml` is the only file in scope — this repo has no separate
  `ci-checks.yml`/quality-check workflow to touch.
- Action pin bumps (all confirmed `node24` via each tag's `action.yml`):
  - `actions/checkout@v2` → `actions/checkout@v7`
  - `docker/login-action@v2` and `docker/build-push-action@v4` are removed entirely (see below)
- The job runs on the self-hosted `[ARM64]` runner. Confirmed via a recent run's log
  (`Current runner version: '2.336.0'`) that this exceeds the `v2.327.1` minimum required for
  Node 24 actions — no runner upgrade needed.
- Replace the "Docker Login" and "Docker Build and Push" steps with a single retry-wrapped
  shell step using `nick-fields/retry@v4` (confirmed `node24`): `max_attempts: 3`,
  `retry_wait_seconds: 15`, `timeout_minutes: 5`.
  - `docker login` reads `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN` from the step's `env:` block
    (not passed as a `--password` CLI arg) via `--password-stdin`.
  - `docker buildx build --push --tag "$TAG" .` builds from the local checkout rather than a
    remote `git#{sha}` context (the previous `docker/build-push-action` default). This is a
    deliberate improvement — building from the already-checked-out working tree avoids a
    second, separate fetch of the same commit, which was the confirmed root cause of a
    transient CI failure in an earlier repo in this hardening series. Document this inline
    with a YAML comment so it isn't "fixed" back to a remote-context build later.
  - The existing branch-based tag logic (`dev` for non-`main`, `latest` for `main`) and the
    `DOCKER_IMAGE`/`DOCKER_REGISTRY` env vars are unchanged.
- `nick-fields/retry` only wraps raw shell `command:`, not other `uses:` actions — this is why
  the two Docker actions are replaced with shell commands rather than wrapped directly.

## Testing Decisions

No application code or test suite is touched by this change — it is CI configuration only.
Verification is direct execution, consistent with the rest of this hardening series:

- Push the working branch and confirm via `gh run watch` that the Docker Build/Publish
  workflow succeeds.
- Confirm via `gh run view <run-id> --log | grep -i deprecat` that no "Node.js 20 is
  deprecated" warning remains in the run's logs.
- Two-axis code review (Standards + Spec) to a clean pass, plus a manually-requested Copilot
  PR review (`gh pr edit <n> --add-reviewer '@copilot'`) since automatic Copilot review was
  disabled repo-wide during this repo's earlier security-hardening pass.

## Out of Scope

- Any change to application behaviour, dependencies, or the app's own test suite.
- The self-hosted runner's version/config — confirmed sufficient, not touched.
- Consolidating this pattern into a shared composite action across other repos — this fix
  stays local to `bromley-bin-reminder`.

## Further Notes

This is a small, well-scoped, low-risk change, part of a proven cross-repo pattern (first
applied in `hypervolt-agile`, PR #68, merged 2026-08-11). No architectural decision is being
made here that warrants an ADR — the design is already validated elsewhere.
