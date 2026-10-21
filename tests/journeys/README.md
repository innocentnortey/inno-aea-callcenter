# Journey tests

Integrated journeys (`.claude/rules/integrated-journeys.md`). Evidence levels and record format: §4 of that rule.

## Layout

- `j1/` … `j10/` map to journeys J-1 … J-10 in `docs/plans/slice-plan.md` §0a.
- `support/` is AEA-57's (harness and the pytest plugin). `browser/` is AEA-58's.
- Each ticket adds only `j<N>/test_aea_<NN>.py` and marks its tests `@pytest.mark.journey`.
  Basenames repeat across folders, which is why every `j<N>/` is a package.

## Commands

- Collect: `uv run pytest -m journey --collect-only -q` (exit 0 even before any journey exists).
- Affected journeys on a branch: `uv run python -m tests.journeys.affected --base main`
  (add `--list-only` to print without running; pytest arguments go after `--`).
- Merge gate: `uv run python -m tests.journeys.affected --base <main SHA before the merge>`,
  for example `--base HEAD^1` on a merge commit.
- Changes to `pyproject.toml`, `uv.lock`, `tests/conftest.py`, the harness, the OpenAPI file, issued data or
  `apps/web/` select every journey.

## Plugin

AEA-57's plugin goes in `tests/journeys/support/plugin.py`; `tests/conftest.py` loads it once it exists.

## Records

Write `docs/testing/journeys/YYYY-MM-DD-<scope>.md` at level `mock-tested`, `integrated with a scripted model` or `verified with live models`
(`integrated-journeys.md` §4).
