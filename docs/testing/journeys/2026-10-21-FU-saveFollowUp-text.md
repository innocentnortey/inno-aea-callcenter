# Journey record — FU-saveFollowUp-text (email follow-up to a general destination)

Wording, **provisional pending the UX session** (Innocent 2026-10-21: "just do whatever you recommend"):

- `followup.saved_email_general`: "Follow-up saved: email, any time." (template `Follow-up saved: email, {window}.`; window words mornings, afternoons, any time)
- Destination label for an email to a general destination: "a general contact".
- Basis: SCREEN_SPECS SCR-1's saved line ("Follow-up saved: phone call, the number ending in 02, mornings.", R-27) with the destination left out, because a general destination holds no address. These are the same words AEA-42's CaseService double already returns. Plain, no promise, and nothing says a message was sent (R-34). Email on record and phone to a general destination are still unbuilt (they raise); their wording is a separate follow-up.

| Field | Value |
|---|---|
| Claim | FU-saveFollowUp-text: `saveFollowUp` with EMAIL_GENERAL (`email`, `general`, `any`) returns 200 with `saved_line` "Follow-up saved: email, any time." and stores the `followups` row and one `followup_saved` event. Journey: **J-7** follow-up leg (CON-5) |
| Level | <fill in: see Step 7> |
| Tested revision | <branch SHA> |
| Environment | worktree; `uv run`; service tests: temp SQLite copy of the issued DB, no server, no model |
| Command | `uv run pytest tests/unit/policy/test_texts.py tests/services/test_followup_text.py -q`; `uv run pytest "tests/contract/test_openapi_server.py::test_success_matches_contract[saveFollowUp/email_general]" "tests/contract/test_openapi_server.py::test_success_matches_contract[saveFollowUp/phone_mornings]" -q -rs`; `uv run python -m tests.journeys.affected --base main` |
| Result | <real counts> |
| Evidence location | this record; the implementer's report |
| Remaining limitations | Wording provisional (UX session). Email on record and phone general still raise `NotImplementedError` (500). No browser leg |
| Blocked by | AEA-51 (binds `reply_composer`; on main the contract drive skips with `not bound: reply_composer`) |
