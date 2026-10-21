# Journey record: FU-j1-demo-state — J-1 step 4 asserts the fresh-store demo clock, not a demo_state row

| Field | Value |
|---|---|
| Claim | J-1 step 4 (`test_j1_session_resume_and_owner_guard`) passes with `reply_composer` bound; it now asserts no `demo_state` row on a fresh store and `demo_clock.now == DEMO_START` |
| Decision | Fixed the **test**, not the product. The product promises `DEMO_START` on a fresh store **without writing** (stage7/cases.md §6 `DemoClock.now`; AEA-10 `DemoStateRepo.get` docstring); `seed_first_boot` never writes `demo_state`; only `DemoService.set_staffing`/`advance_clock` and `ResetService.reset` do. The old assertion required a row no spec asks for. Seeding the row at start-up would add an undesigned writer and change AEA-10's behaviour for no user-visible gain |
| Level | `integrated with a scripted model` on `e9d07f3` + this test file; on `main`: step reported blocked on AEA-51 |
| Tested revision | Branch `aea-fu-j1-demo-state-fu-j1-demo-state` commit `d3702c2` (from `main` `9d12b8f`); repro tree `e9d07f3` with that file checked out |
| Environment | Host `claude-vultr`; Python 3.12; uv; journey harness (real app via `launch_server` on a first-boot copy of the issued SQLite; scripted model adapter; socket guard on) |
| Command | `uv run pytest "tests/journeys/j1/test_aea_57.py::test_j1_session_resume_and_owner_guard" -rs -q` (on `e9d07f3`, before and after); `uv run pytest -m journey tests/journeys/j1 -rs -q` (on `main` branch and on `e9d07f3`); `uv run python -m tests.journeys.affected --base main` |
| Result | Before (`e9d07f3`, unmodified test): 1 failed, step "4 start session", `AssertionError: expected exactly one row, got 0`. After (`e9d07f3` + fixed file): node 1 passed; whole `tests/journeys/j1`: 7 passed, 3 skipped (blocked-on AEA-51: run_graph not bound; AEA-57 note in test_aea_59), 13 errors, all browser journeys needing `apps/web/dist` (BrowserPrerequisiteError, same before and after). On the fix branch (`main` base): 4 passed, 6 skipped, same 13 browser errors; affected-journeys command: 2 passed, 4 skipped (blocked-on AEA-51: reply_composer not bound) |
| Evidence location | This file plus the pytest output of the commands above |
| Remaining limitations | The browser leg of J-1 (AEA-58) not run here (no production build in the worktree). `test_aea_59` skip text says the harness is not on main; unchanged by this ticket |
| Blocked by | `main`: AEA-51 (`reply_composer`) for J-1 steps 4-7; none for the repro run |
