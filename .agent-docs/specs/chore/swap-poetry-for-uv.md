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
  image and provisions the environment with `uv sync --frozen --no-dev --no-cache`. The
  container entrypoint and the in-app config-reload restart command run through
  `uv run --no-sync`.
- The pre-commit config drops the three Poetry hooks and gains the `uv-pre-commit`
  `uv-lock` hook. The mypy, isort, black and ruff hook *definitions* (ids, args,
  `additional_dependencies`) are untouched; their pinned `rev`s are realigned to the
  versions the refreshed lock resolved, as part of the dependency refresh below.
- Dependabot switches from the `pip` ecosystem to the `uv` ecosystem.
- Because the lock is regenerated from scratch, every dependency moves to the newest
  version its existing version constraint already permits. No constraint is loosened or
  bumped to a new major. The pre-commit hook `rev`s for the linters follow the same
  rule — each moves to the newest release its dev-dependency constraint already allows
  (e.g. isort's `>=8.0.1,<10.0.0` admits 9.x), so the hook and the locked library stay
  on the same version.

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
- Each caret constraint (`^x.y.z`) on a *package* is translated to the range it actually
  means — `>=x.y.z,<{next major}.0.0` — so the upper bound Poetry implied is preserved
  rather than dropped (dropping it would loosen the constraint). `pytz = "^2026.1"`
  becomes `pytz>=2026.1,<2027.0`; the `lxml` extra becomes
  `lxml[html-clean]>=6.0.4,<7.0.0`. Constraints already written as explicit ranges
  (`isort`, `mypy`, `ruff`) are copied across unchanged.
- The one exception is the interpreter constraint: `python = "^3.11"` becomes
  `requires-python = ">=3.11"`, left unbounded. A `<4.0` cap on `requires-python` is not
  idiomatic PEP 621 and needlessly narrows the resolver; there is no Python 4 to guard
  against. The `.python-version` file and the `python:3.11-slim` base still pin the
  actual runtime to 3.11.
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
- `RUN uv sync --frozen --no-dev --no-cache` in place of
  `poetry install --no-root --only main`. `--no-cache` keeps the build (run as root) from
  leaving a populated cache in the image; the runtime `uv run --no-sync` never touches it.
- `ENV UV_PROJECT_ENVIRONMENT=/app/.venv` (a fixed venv path both build and runtime
  agree on) and `ENV UV_FROZEN=1` (runtime `uv run` never attempts a re-resolve).
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
- The mypy, isort, black and ruff hook definitions (ids, args,
  `additional_dependencies`) are left exactly as they are. Their pinned `rev`s are
  bumped to match the versions the refreshed lock resolved (`mirrors-mypy` → the tag
  for the locked mypy, `pycqa/isort` → the locked isort, `ruff-pre-commit` → the locked
  ruff), so hook and library never drift apart. `black`'s pin already matched and is
  left alone.

### `.github/dependabot.yml`

- `package-ecosystem: pip` becomes `package-ecosystem: uv`. `directory`, `schedule`
  (`interval: daily`) and the `python-packages` group (`patterns: ["*"]`) are unchanged.

### Dependency refresh

- Whatever `uv lock` resolves from the translated constraints is the accepted set — this
  is the "latest within existing ranges" outcome by construction. No manual version
  picking.
- The linter pre-commit hook `rev`s (`mirrors-mypy`, `pycqa/isort`, `ruff-pre-commit`)
  are bumped to the tags matching those resolved versions, so a hook never runs a
  different version of a tool than the one the lock pins. This is the same
  latest-within-range rule applied to the hook pins; it is not a constraint change.

## Testing Decisions

This is a build-tooling migration in a repository that currently has no automated test
suite, so "tests" here means the verification gates the change must pass, exercised at the
highest seam that is runnable.

- **Primary seam — the Docker image build.** `docker build .` exercises the entire `uv`
  path: image-copy of `uv`, `uv sync --frozen --no-dev --no-cache` against the committed
  lock, and the `uv run` entrypoint. This machine has no Docker daemon, so this seam runs in CI
  (`.github/workflows/ci-arm64.yml`, which builds and pushes on every branch push) rather
  than locally. A green CI build on the branch is the acceptance signal for stories 1, 3
  and 8.
- **Local seam — environment resolution and import smoke.** `uv sync` must succeed, and
  every `app/` module must import cleanly under the resolved environment with `app/` on
  `sys.path` (the app runs as `python ./app/main.py`, so its modules import as bare
  `main`, `scraper`, `common.logging`, … — not `app.main`). This catches a dropped
  dependency or a bad constraint translation without needing Docker.
- **Hook seam.** `uvx pre-commit run --all-files` must pass, proving the new `uv-lock`
  hook and the retained mypy/isort/black/ruff hooks all work against the rewritten
  manifest and that `uv.lock` is in sync (story 5).
- **Grep gate.** A repository-wide search for `poetry` / `POETRY` (excluding
  `.gitignore`'s upstream template comment) returns nothing (story 9).
- No prior art for tests exists in the codebase; none is added here (out of scope).

## Out of Scope

- Loosening or raising any dependency version constraint. Resolved versions (and the
  linter hook `rev`s that track them) may move to the newest release each existing
  constraint already allows — including across a major boundary the constraint already
  spans, as `isort`'s `<10.0.0` spans 9.x — but no constraint's bounds are edited.
- Adding a test suite, a CI lint/test job, or any change to
  `.github/workflows/ci-arm64.yml`.
- Changes to the mypy (`setup.cfg`), ruff, isort or black *configuration* — hook ids,
  args, `additional_dependencies`, or the tool config files. Only the pinned `rev`s move.
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
