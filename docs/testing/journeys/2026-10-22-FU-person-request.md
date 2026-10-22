# Journey record — FU-person-request (held write lock gives 503 HANDOFF_FAILED; CON-4 timed child span)

| Field | Value |
|---|---|
| Claim | FU-person-request: AEA-51 findings F-4 and F-5 fixed in `PersonRequestService.request()`. A write lock held past the busy timeout answers 503 `HANDOFF_FAILED` (body matches the OpenAPI `requestPerson`, no raw error text, no `cases` or `turns` row); the CON-4 turn span has one timed `handoff` child. CAP-3 AC-46 and AC-48 un-xfailed. Journey: **J-7** CON-4 step |
| Level | integrated with a scripted model (API level, real app, real DB copy, no browser) for the un-xfailed CAP-3 tests; mock-tested for J-7 (`test_aea_42`, `test_aea_30`) and the new route test |
| Tested revision | aea-fu-person-request-fu-person-request 0ae5dc6 (record committed after it) |
| Environment | worktree; `uv run`; temp SQLite copies of the issued DB; scripted model; no paid call |
| Command | `uv run pytest tests/services/test_person_request_lock_span.py tests/api/test_handoff_lock.py tests/services/test_person_request.py -q`; `uv run --with pytest-xdist pytest -n 2 -q <affected list in the plan>`; `uv run pytest -q -rA tests/capture/test_cap3_handoff.py tests/capture/test_cap1_customer_chat.py::test_status_values_within_lists tests/integration/test_customer_failures.py`; `uv run python -m tests.journeys.affected --base main` |
| Result | New + AEA-42 tests: 15 passed. Affected list: 849 passed, 1 skipped, 1 xfailed (pre-existing AEA-23 follow-up). CAP-3 / CAP-1 / customer failures: 13 passed; `test_wf2_turn_has_timed_children` and `test_con4_held_write_lock_gives_503` PASSED. ruff and mypy clean. Affected journeys: 64 passed, 11 skipped, 15 errors, all browser journeys (j1/j9 `test_aea_58`) that need `apps/web/dist`, absent in a backend worktree; no assertion failures |
| Evidence location | this record; the implementer's report |
| Remaining limitations | No browser leg. A lock arriving after the case is written leaves the turn row `running` (customer gets 503 and a new press answers already_open); a stale-running reclaim is out of scope |
| Blocked by | none (integrated browser harness AEA-57 not needed for this claim) |
