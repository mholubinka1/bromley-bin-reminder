# Issues: chore/swap-poetry-for-uv

## Replace Poetry with uv across the repository

**GitHub issue**: #272

**Blocked by**: None

**User stories**: 1, 2, 3, 4, 5, 6, 7, 8, 9

### What to build

Migrate the project's dependency and environment management from Poetry to `uv` in a
single change, leaving no Poetry reference anywhere in the repository.

- Rewrite `pyproject.toml` from the legacy `[tool.poetry]` tables into PEP 621
  `[project]` metadata plus a `[dependency-groups]` `dev` group and a `[tool.uv]` section
  with `package = false`. Caret constraints become `>=` lower bounds; the `lxml` extra is
  preserved; `requires-python = ">=3.11"`; `authors` carried across in PEP 621 form; the
  `[tool.ruff.lint]` section kept verbatim; `[build-system]` removed.
- Generate and commit `uv.lock`. Delete `poetry.lock` and `requirements.txt`.
- Add `.python-version` containing `3.11`.
- Dockerfile: install `uv` by copying from a version-pinned `ghcr.io/astral-sh/uv` image;
  `uv sync --frozen --no-dev` in place of the Poetry bootstrap and install; set
  `UV_PROJECT_ENVIRONMENT`, `UV_FROZEN`, and a writable `UV_CACHE_DIR` for the
  `sel_user` runtime; entrypoint `uv run --no-sync python ./app/main.py ...`. Geckodriver,
  firefox-esr, xvfb, `useradd`, and `VOLUME /config` lines unchanged.
- `app/main.py`: the config-reload restart command list uses `uv run --no-sync` instead
  of `poetry run`. No other logic changes.
- `.pre-commit-config.yaml`: drop the `poetry` and `poetry-plugin-export` repos; add the
  `astral-sh/uv-pre-commit` `uv-lock` hook. mypy, isort, black, ruff hooks untouched.
- `.github/dependabot.yml`: `package-ecosystem: pip` -> `uv`; directory, schedule, and
  group unchanged.
- Dependency refresh happens by construction: `uv lock` resolves each translated
  constraint to its newest permitted version. No constraint loosened or bumped to a new
  major.
- `uv`, `uv-pre-commit`, and the `ghcr.io/astral-sh/uv` image are all pinned to the same
  released `uv` version.

### Acceptance criteria

- [ ] `pyproject.toml` has no `[tool.poetry*]` or `[build-system]` table; it declares
      `[project]` with `requires-python = ">=3.11"`, a `[dependency-groups]` `dev` group,
      and `[tool.uv]` with `package = false`. The `[tool.ruff.lint]` section is byte-for-byte
      unchanged.
- [ ] `uv.lock` is committed and `uv lock --check` (or `uv sync --frozen`) reports it in
      sync with `pyproject.toml`.
- [ ] `poetry.lock` and `requirements.txt` no longer exist in the repository.
- [ ] `.python-version` exists and contains `3.11`.
- [ ] `uv sync` succeeds on a clean checkout and `uv run python -c "import app.main,
      app.scraper, app.notify, app.notification, app.collection, app.reload,
      app.common.settings, app.common.decorators, app.common.logging"` exits 0.
- [ ] `Dockerfile` contains no `poetry`/`POETRY` token, obtains `uv` via
      `COPY --from=ghcr.io/astral-sh/uv:<pinned>`, runs `uv sync --frozen --no-dev`, and
      its `CMD` invokes `uv run --no-sync`.
- [ ] `app/main.py`'s `ConfigChangePoller` command list starts with
      `["uv", "run", "--no-sync", "python", ...]` and contains no `"poetry"`.
- [ ] `.pre-commit-config.yaml` references neither `python-poetry/poetry` nor
      `poetry-plugin-export`, and includes the `astral-sh/uv-pre-commit` `uv-lock` hook;
      the mypy/isort/black/ruff hooks are unchanged.
- [ ] `.github/dependabot.yml` uses `package-ecosystem: uv` with directory, schedule, and
      group unchanged.
- [ ] `uvx pre-commit run --all-files` passes.
- [ ] A repository-wide search for `poetry`/`POETRY`, excluding the upstream template
      comment block in `.gitignore`, returns no matches.
- [ ] CI (`ci-arm64.yml`) builds and pushes the Docker image successfully on the branch.

---
