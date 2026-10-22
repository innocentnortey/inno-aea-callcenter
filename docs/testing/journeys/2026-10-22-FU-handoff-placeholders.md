# Journey record — FU-handoff-placeholders (handoff, settled and change-request cards send the UXR-19 split; AEA-55 F5)

| Field | Value |
|---|---|
| Claim | AC-8: J-6 card text. WP-7's handoff card and settled request, and a nobody-online CON-4 card and its settled request, each join (UXR-19: `promise_text, due_label. extra_lines`) to the fixed sentence word for word, with no `{`/`}` and no `.,`. Fixes AEA-55 finding F5 |
| Level | integrated with a scripted model (API level, real app, real graph, temp DB copy, scripted model at the provider boundary, no browser) |
| Tested revision | aea-fu-handoff-placeholders-fu-handoff-placeholders (the commit that carries this record) |
| Environment | worktree; `uv run`; `open_customer_run` real app over a temp SQLite copy of the issued DB; scripted model; no paid call |
| Command | `uv run pytest -m journey tests/journeys/j6/test_aea_42_f5.py -q -s`; `uv run python -m tests.journeys.affected --base main` |
| Result | New journey: 1 passed (step 1 refund card joins clean; step 2 person-request card joins clean). Affected journeys (48 selected because the diff edits `tests/journeys/`): 86 passed, 12 skipped, 33 errors, every error `BrowserPrerequisiteError` (no `apps/web/dist` in a backend worktree: j1/j9 `test_aea_58`, j2/j3/j6/j8 `test_aea_62`); no assertion failure. `j4/test_aea_39`, `j4/test_aea_51`, `j7/test_aea_42`, `j7/test_aea_30` passed |
| Evidence location | this record; the pytest output lines `step 1: ... refund card joins clean`, `step 2: ... person-request card joins clean` |
| Remaining limitations | Browser render of the card not re-checked here: the J-6 browser leg `test_aea_62.py` is blocked on the UX selector contract (AEA-55 F8) and the missing web build. Conversations stored before this fix keep their old blocks until a demo reset |
| Blocked by | none for the API level |
