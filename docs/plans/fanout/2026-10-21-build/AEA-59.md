
## Deviations

Recorded by the implementer, 2026-10-21 (base `main` `0dedd59`, not `4a76850`).

- **Vocabulary extended for `staff_live.py` and `staff_session.py`, which merged after the plan.** `reference` is an allowed
  drive key; `last_event_id` may be an int (a literal header value); the words `live_case_claimed`, `live_case_joined`,
  `live_case_unclaimed`, `case_claimed_by_supervisor` and `case_events` are local-driver-only (the real app cannot seed
  them without a double), so those drives are listed and not run. Fixed in `openapi_cases.py`, never in a route file (plan R-5).
- **`CASES` on `main` now covers 11 operations in 6 files** (auth, events, handoff, staff_clock, staff_live, staff_session);
  19 operations are missing a case and are named with their file.
- **Every drive that passes the gate's clock lookup skips with `not bound: demo_clock`** (48 drives on this base), so the
  default run's real-app passes are the 401/400/login cases that fail before it. Reported in the record's *Blocked by*.
- **AC-14 is `xfail(strict=True)`** per R-1: `grep -n "error.message" tests/api/openapi_check.py` still matches (two lines).
  Run with `--runxfail` it fails on `assert secret not in text`, the intended reason.
- **AC-16 is a named skip** per R-2 (AEA-57 is not on `main`).
- **Context rows cite the branch name instead of a short sha** (the sha does not exist until the commit that contains the row).
- **Unrequested in the plan:** `index_mismatches()` lives in `openapi_variants.py` as step 12 says; `openapi_driver.py` imports
  `render_unhandled_error` from `meridian.web.errors` (the middleware re-imports it, mypy does not treat it as exported) and
  patches the name in `meridian.web.middleware`.
