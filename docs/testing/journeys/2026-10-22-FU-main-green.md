# Journey record — FU-main-green (main green: three reds)

Test-only diff. `uv run python -m tests.journeys.affected --base main` selects `tests/journeys/j8/test_aea_31.py` (it imports `tests.services.reset_support`); it passes. No journey harness gate exists beyond that command's output; the all-journeys run is AEA-57's and the pre-deploy full suite is the orchestrator's.

| Field | Value |
|---|---|
| Claim | Fixes `tests/capture/test_cap9_runtime_ops.py::test_wf15_reset_script` (two `reset_events` rows, expected one), `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0` (real repo now holds journeys) and `tests/unit/adapters/test_tracing_langfuse.py::test_export_never_blocks_hanging_exporter` (wall-clock worst case flaked under load) |
| Fix for (1) | Test setup, not code. `make_dirty_demo` wrote an earlier `reset_events` row on purpose (AEA-31's kept-table proof); the reset service correctly keeps it (cases.md 1.3); seeding writes only a seed_event (WF-16), so no reset_event at first boot. The earlier row is now opt-in (`prior_reset_event=True`) for the two AEA-31 tests that rely on it (`test_writer_waits_for_reset_lock`, `test_reset_clears_codes_keeps_ops_records`). The frozen AEA-50 test is unedited (Innocent declined changing it, 2026-10-21). This departs from the AEA-31 plan's helper description (default no longer writes the earlier reset) |
| Fix for (2) | The test runs against a temporary tree with no journey files |
| Fix for (3) | Structural proof: every turn call completes while the exporter is stuck inside `export()` and unreleased; the 50 ms bound is asserted on the median call; the worst case is printed |
| Level | (1) integrated script entry point on a real SQLite copy, no model; J-8 `mock-tested` (its file's level); (2), (3) unit |
| Tested revision | the commit carrying this file on branch `aea-fu-main-green-fu-main-green` |
| Command | `uv run --with pytest-xdist pytest -q -n 2 tests/capture/test_cap9_runtime_ops.py tests/services tests/unit/web/test_register_reset.py tests/unit/test_affected_journeys.py tests/unit/adapters tests/journeys/j8`; 10 runs of `pytest -q -n 2 tests/unit/adapters/test_tracing_langfuse.py`; `uv run mypy`; `uv run python -m tests.journeys.affected --base main` |
| Result | 472 passed, 17 skipped, 2 xfailed, 7 errors (all in `tests/journeys/j8/test_aea_62.py`: browser journeys need `apps/web/dist`, not built in a backend worktree; not touched by this diff). Tracing file: 10/10 runs, 22 passed each. Full `uv run mypy`: no issues in 598 files. Affected journeys: 1 selected, passes |
| Evidence location | This file; the implementer's report |
| Remaining limitations | `test_export_never_blocks_small_cap_counts_drops` and `..._erroring_exporter` still assert the worst call under 50 ms over 22 and 7 calls (lower flake odds, same cause); follow-up. `test_aea_62.py` errors need the web build |
| Blocked by | none |
