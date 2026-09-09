# Swap Poetry for uv

## Problem Statement

The project's dependency and virtual-environment management runs on Poetry. Poetry is
slow to resolve, needs its own bootstrap step in the Docker build (a dedicated venv plus
`pip install poetry`), and forces a second generated artefact — `requirements.txt`,
exported by a pre-commit hook — to be kept in sync even though nothing in the repository
consumes it. The maintainer wants the faster, single-binary `uv` toolchain instead, and
wants the dependency set refreshed to current versions while the manifest is being
rewritten anyway.

## Solution

Replace Poetry with `uv` everywhere it appears:

- `pyproject.toml` is rewritten from the legacy `[tool.poetry]` tables into standard
  PEP 621 `[project]` metadata with a `[dependency-groups]` `dev` group and a `[tool.uv]`
  section declaring the project non-packaged.
- `poetry.lock` is replaced by a freshly resolved `uv.lock`; `requirements.txt` is
  deleted.
- The Docker image installs `uv` by copying it from Astral's published, version-pinned
  image and provisions the environment with `uv sync --frozen --no-dev`. The container
  entrypoint and the in-app config-reload restart command run through `uv run --no-sync`.
- The pre-commit config drops the three Poetry hooks and gains the `uv-pre-commit`
  `uv-lock` hook. The mypy, isort, black and ruff hooks are untouched.
- Dependabot switches from the `pip` ecosystem to the `uv` ecosystem.
- Because the lock is regenerated from scratch, every dependency moves to the newest
  version its existing version constraint already permits. No constraint is loosened or
  bumped to a new major.

After the change a contributor clones the repo, runs `uv sync`, and has a working
environment; `uv run python ./app/main.py --config-file ...` starts the reminder service
exactly as `poetry run` did; and `docker build` produces a functionally identical image.

## User Stories

1. As the maintainer, I want `uv sync` to create the project environment from a committed
   `uv.lock`, so that I no longer need Poetry installed to work on the project.
2. As the maintainer, I want `pyproject.toml` in standard PEP 621 form, so that the
   manifest is portable to any PEP 621-aware tool and not tied to Poetry's dialect.
3. As the maintainer, I want the Docker image built with `uv`, so that image builds skip
   the Poetry bootstrap and resolve dependencies faster.
4. As the maintainer, I want the config-reload restart in `app/main.py` to invoke `uv`
   rather than `poetry`, so that live config reloads keep working inside the container.
5. As the maintainer, I want the pre-commit hooks to keep `uv.lock` consistent with
   `pyproject.toml`, so that a drifted lock is caught before commit — the role
   `poetry-check` / `poetry-lock` played before.
6. As the maintainer, I want Dependabot to read `uv.lock`, so that automated dependency
   PRs continue after Poetry is gone.
7. As the maintainer, I want `requirements.txt` and its export hook removed, so that
   there is no stale generated artefact to reason about.
8. As the maintainer, I want all dependencies refreshed to the latest versions their
   current constraints allow, so that the migration also clears accumulated minor/patch
   drift.
9. As a contributor, I want no reference to Poetry left anywhere in the repository, so
   that there is a single, unambiguous toolchain to learn.

## Implementation Decisions

### `pyproject.toml`

- Replace `[tool.poetry]`, `[tool.poetry.dependencies]` and
  `[tool.poetry.group.dev.dependencies]` with:
  - `[project]` — `name`, `version`, `description`, `readme`, `requires-python = ">=3.11"`,
    and `dependencies` as a PEP 508 list.
  - `[dependency-groups]` — `dev = [...]` holding isort, black, mypy, ruff, pre-commit.
- Caret constraints (`^x.y.z`) become `>=x.y.z` lower bounds. `pytz = "^2026.1"` and the
  other exact-looking pins follow the same rule. The `lxml` extra becomes
  `lxml[html-clean]>=6.0.4`.
- Remove the `[build-system]` table. Add `[tool.uv]` with `package = false` so `uv`
  treats the repo as a non-packaged project (the Poetry equivalent of
  `package-mode = false`).
- Keep the existing `[tool.ruff.lint]` section verbatim.
- `authors` is carried across in PEP 621 form (`[{name = "...", email = "..."}]`).

### Lockfile

- Generate `uv.lock` with `uv lock`. Commit it. Delete `poetry.lock`.
- Delete `requirements.txt`.
- Leave the commented Poetry/uv boilerplate in `.gitignore` as-is — it is upstream
  GitHub `Python.gitignore` template text and does not ignore `uv.lock`.

### `.python-version`

- Add `.python-version` containing `3.11`, so `uv` and the `python:3.11-slim` Docker base
  agree on the interpreter and `uv` provisions a matching one when absent.

### `Dockerfile`

- Drop `POETRY_HOME`, `POETRY_VENV`, `POETRY_CACHE_DIR`, the `python -m venv` +
  `pip install poetry` block, and the `PATH` append for the Poetry venv.
- Add `COPY --from=ghcr.io/astral-sh/uv:<pinned> /uv /uvx /bin/` near the top
  (`<pinned>` = a fixed `uv` version, not a floating tag).
- `COPY pyproject.toml uv.lock ./` (was `pyproject.toml poetry.lock`).
- `RUN uv sync --frozen --no-dev` in place of `poetry install --no-root --only main`.
- `ENV UV_PROJECT_ENVIRONMENT=/app/.venv`, `ENV UV_FROZEN=1`, and a writable
  `ENV UV_CACHE_DIR=/opt/uv-cache` (created and `chown`ed to `sel_user`, or made
  world-writable) so the runtime `uv run` as `sel_user` never attempts a re-resolve or
  fails on an unwritable cache.
- `CMD ["uv", "run", "--no-sync", "python", "./app/main.py", "--config-file",
  "/config/config.yml"]`.
- The geckodriver / firefox-esr / xvfb / `useradd` / `VOLUME /config` lines are
  unchanged.

### `app/main.py`

- The config-reload restart command list changes from
  `["poetry", "run", "python", "./app/main.py", "--config-file", config_file]` to
  `["uv", "run", "--no-sync", "python", "./app/main.py", "--config-file", config_file]`.
- No other logic changes.

### `.pre-commit-config.yaml`

- Remove the `python-poetry/poetry` repo (`poetry-check`, `poetry-lock`) and the
  `python-poetry/poetry-plugin-export` repo (`poetry-export`).
- Add:
  ```yaml
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: <pinned>
    hooks:
      - id: uv-lock
  ```
- mypy, isort, black, ruff hooks are left exactly as they are.

### `.github/dependabot.yml`

- `package-ecosystem: pip` becomes `package-ecosystem: uv`. `directory`, `schedule`
  (`interval: daily`) and the `python-packages` group (`patterns: ["*"]`) are unchanged.

### Dependency refresh

- Whatever `uv lock` resolves from the translated constraints is the accepted set — this
  is the "latest within existing ranges" outcome by construction. No manual version
  picking.

## Testing Decisions

This is a build-tooling migration in a repository that currently has no automated test
suite, so "tests" here means the verification gates the change must pass, exercised at the
highest seam that is runnable.

- **Primary seam — the Docker image build.** `docker build .` exercises the entire `uv`
  path: image-copy of `uv`, `uv sync --frozen --no-dev` against the committed lock, and
  the `uv run` entrypoint. This machine has no Docker daemon, so this seam runs in CI
  (`.github/workflows/ci-arm64.yml`, which builds and pushes on every branch push) rather
  than locally. A green CI build on the branch is the acceptance signal for stories 1, 3
  and 8.
- **Local seam — environment resolution and import smoke.** `uv sync` must succeed, and
  `uv run python -c "import app.main, app.scraper, app.notify, app.notification,
  app.collection, app.reload, app.common.settings, app.common.decorators,
  app.common.logging"` must import every module cleanly under the resolved environment.
  This catches a dropped dependency or a bad constraint translation without needing
  Docker.
- **Hook seam.** `uvx pre-commit run --all-files` must pass, proving the new `uv-lock`
  hook and the retained mypy/isort/black/ruff hooks all work against the rewritten
  manifest and that `uv.lock` is in sync (story 5).
- **Grep gate.** A repository-wide search for `poetry` / `POETRY` (excluding
  `.gitignore`'s upstream template comment) returns nothing (story 9).
- No prior art for tests exists in the codebase; none is added here (out of scope).

## Out of Scope

- Loosening or raising any dependency version constraint, or any deliberate major-version
  upgrade. Only the lock moves, within current ranges.
- Adding a test suite, a CI lint/test job, or any change to
  `.github/workflows/ci-arm64.yml`.
- Changes to the mypy (`setup.cfg`), ruff, isort or black configuration.
- README content (the setup sections are currently empty and stay that way).
- `.vscode/launch.json` (uses `debugpy` directly, no Poetry reference).
- Publishing the project as an installable package.

## Further Notes

- The single hardcoded `"poetry"` string in `app/main.py` is easy to miss in review — it
  is inside the `ConfigChangePoller` command list, not near any other tooling reference.
- `requirements.txt` is 53 KB and has no in-repo consumer; it existed only as the
  `poetry-export` target. Dependabot's `pip` ecosystem could read `pyproject.toml`
  directly, so its removal does not lose coverage once the ecosystem is switched to `uv`.
- `uv` (0.12.x) and the `uv-pre-commit` / `ghcr.io/astral-sh/uv` versions should all be
  pinned to the same released version at implementation time.
