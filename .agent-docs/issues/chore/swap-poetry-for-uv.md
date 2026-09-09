# Issues: chore/swap-poetry-for-uv

> Work complete — PR ready to merge.

## Replace Poetry with uv across the repository

**GitHub issue**: #272

**Blocked by**: None

**User stories**: 1, 2, 3, 4, 5, 6, 7, 8, 9

### What to build

Migrate the project's dependency and environment management from Poetry to `uv` in a
single change, leaving no Poetry reference anywhere in the repository.

- Rewrite `pyproject.toml` from the legacy `[tool.poetry]` tables into PEP 621
  `[project]` metadata plus a `[dependency-groups]` `dev` group and a `[tool.uv]` section
  with `package = false`. Each caret constraint is translated to the range it means
  (`^x.y.z` -> `>=x.y.z,<{next major}.0.0`), preserving the upper bound Poetry implied;
  the `lxml` extra is preserved; `requires-python = ">=3.11"`; `authors` carried across
  in PEP 621 form; the `[tool.ruff.lint]` section kept verbatim; `[build-system]` removed.
- Generate and commit `uv.lock`. Delete `poetry.lock` and `requirements.txt`.
- Add `.python-version` containing `3.11`.
- Dockerfile: install `uv` by copying from a version-pinned `ghcr.io/astral-sh/uv` image;
  `uv sync --frozen --no-dev` in place of the Poetry bootstrap and install; set
  `UV_PROJECT_ENVIRONMENT`, `UV_FROZEN`, and `UV_NO_CACHE=1` (so neither the root-run
  build sync nor the `sel_user`-run `uv run` touches a cache); entrypoint
  `uv run --no-sync python ./app/main.py ...`. Geckodriver, firefox-esr, xvfb, `useradd`,
  and `VOLUME /config` lines unchanged.
- `app/main.py`: the config-reload restart command list uses `uv run --no-sync` instead
  of `poetry run`. No other logic changes.
- `.pre-commit-config.yaml`: drop the `poetry` and `poetry-plugin-export` repos; add the
  `astral-sh/uv-pre-commit` `uv-lock` hook. The mypy/isort/black/ruff hook definitions
  (ids, args, `additional_dependencies`) are untouched; their pinned `rev`s are bumped to
  the tags matching the versions the refreshed lock resolved (`black` already matched).
- `.github/dependabot.yml`: `package-ecosystem: pip` -> `uv`; directory, schedule, and
  group unchanged.
- Dependency refresh happens by construction: `uv lock` resolves each constraint to its
  newest permitted version, and the linter hook `rev`s are realigned to those versions.
  No constraint's bounds are edited.
- `uv`, `uv-pre-commit`, and the `ghcr.io/astral-sh/uv` image are all pinned to the same
  released `uv` version.

### Acceptance criteria

- [x] `pyproject.toml` has no `[tool.poetry*]` or `[build-system]` table; it declares
      `[project]` with `requires-python = ">=3.11"`, a `[dependency-groups]` `dev` group,
      and `[tool.uv]` with `package = false`. The `[tool.ruff.lint]` section is byte-for-byte
      unchanged.
- [x] `uv.lock` is committed and `uv lock --check` (or `uv sync --frozen`) reports it in
      sync with `pyproject.toml`.
- [x] `poetry.lock` and `requirements.txt` no longer exist in the repository.
- [x] `.python-version` exists and contains `3.11`.
- [x] `uv sync` succeeds on a clean checkout and, with `app/` on `sys.path` (how the app
      is actually run), importing every `app/` module —  `main`, `scraper`, `notify`,
      `notification`, `collection`, `reload`, `common.settings`, `common.decorators`,
      `common.logging` — exits 0.
- [x] `Dockerfile` contains no `poetry`/`POETRY` token, obtains `uv` via
      `COPY --from=ghcr.io/astral-sh/uv:<pinned>`, runs `uv sync --frozen --no-dev`, sets
      `UV_PROJECT_ENVIRONMENT`, `UV_FROZEN` and `UV_NO_CACHE`, and its `CMD` invokes
      `uv run --no-sync`.
- [x] `app/main.py`'s `ConfigChangePoller` command list starts with
      `["uv", "run", "--no-sync", "python", ...]` and contains no `"poetry"`.
- [x] `.pre-commit-config.yaml` references neither `python-poetry/poetry` nor
      `poetry-plugin-export`, and includes the `astral-sh/uv-pre-commit` `uv-lock` hook;
      the mypy/isort/black/ruff hook definitions (ids, args, `additional_dependencies`)
      are unchanged, with only their pinned `rev`s realigned to the refreshed versions.
- [x] `.github/dependabot.yml` uses `package-ecosystem: uv` with directory, schedule, and
      group unchanged.
- [x] `uvx pre-commit run --all-files` passes.
- [x] No operational file (code, `Dockerfile`, `pyproject.toml`, pre-commit / CI /
      Dependabot config) references `poetry`/`POETRY`. The upstream template comment
      block in `.gitignore` and this change's own `.agent-docs/` spec and issue — which
      necessarily name Poetry to describe the migration — are not matches.
- [x] CI (`ci-arm64.yml`) builds and pushes the Docker image successfully on the branch.
      (Green on `b890524`, `d13fef7`, and `e4d8ee4`.)

---
