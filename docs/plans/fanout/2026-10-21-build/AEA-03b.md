# Plan — [AEA-03b] history texts (Code entered, Details sent)

**Status:** planned (READY). Re-plan of a built branch: the code exists; this plan states the ticket, closes the review
items still open and makes the branch mergeable on today's main.
**Issue:** none. The ledger row (`.claude/state/build-ledger.md`, `AEA-03b | #201 | B | built`) names GitLab #201, but
`env -u GITLAB_TOKEN glab issue view 201` returns `404 Not Found` (checked 2026-10-21), and
`docs/plans/tickets/AEA-03b.md` does not exist on main, in the worktree or in git history. Until the orchestrator files
them, **this plan's *Acceptance criteria* section is the ticket spec** (derived word for word from the request that
created the ticket, AEA-40 plan §8 R-4).
**Base revision:** main `900a1d8` (Merge AEA-18). Branch `aea-03b-history-texts` at `f3bbfac`, merge-base `35aefdd`.
Worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-03b`.
**Lane / risk:** `lane::build-loop`, no `risk::security` (two fixed display strings; no data, access or secret surface),
so no frozen tests and no security review. Planner model: `claude-opus-5-5`. Implementer: Sonnet.

## Goal

Add exactly two fixed customer texts to `policy/texts.py` so AEA-40's thread-history rebuild (AC-19) can show a code turn
as "Code entered" and a form turn as "Details sent", the same words the live chat row uses, instead of the stored
redacted markers "[code entered]" / "[details submitted]":

- `TextId.HISTORY_CODE_ENTERED = "history.code_entered"` → `"Code entered"`
- `TextId.HISTORY_DETAILS_SENT = "history.details_sent"` → `"Details sent"`

Source of the request: `docs/plans/fanout/2026-10-21-build/AEA-40.md` §8 R-4 ("Request: AEA-03 follow-up adding exactly
`TextId.HISTORY_CODE_ENTERED = "history.code_entered"` → "Code entered" and `TextId.HISTORY_DETAILS_SENT =
"history.details_sent"` → "Details sent" (the UX build's live-row wording, `docs/plans/fanout/2026-10-21-ux4/g1-chat-core.md`
line 487). The frozen tests use these names.").

## Context

AEA-03 (merged) wrote `policy/texts.py`, 75 texts in 10 groups. AEA-40's planner found its AC-19 needs two display texts
that do not exist and, because AEA-40's plan forbids adding `TextId` members itself (AEA-40 plan line 175), requested this
follow-up. A previous implementer built it (`8db744f` code, `f3bbfac` docs, area map, render test, journey record).
Review then left two problems this plan fixes: (1) the journey record says "Blocked by AEA-57", but AEA-57 merged
(ledger row: `bd79a29`) and `tests/journeys/affected.py` selects 11 journeys for this diff, which nobody has run; (2) the
branch no longer merges cleanly into main: `.claude/reference/area-map.md` row A0 conflicts with main's AEA-02b edit.

## Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Requirements | AEA-40 ticket `docs/plans/tickets/AEA-40.md` AC-19 (line 157); customer audit `docs/plans/ux-join/audit-customer.md` A-7 | History rows read like the live rows; "the texts come from `policy/texts.py`". This ticket supplies the two fixed texts; AEA-40 does the mapping |
| Wording source | `docs/plans/fanout/2026-10-21-ux4/g1-chat-core.md` line 487 (Step 6 `customerRowText`) and line 220 | `code` → `"Code entered"`, `form` → `"Details sent"`, "never digits". Exact strings, no placeholders |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` (DAT row, line 1060, points `policy/texts.py` to stage7 data.md); addendum `docs/design/contracts/stage7/data.md` §2 "`policy/texts.py` (AEA-03)" (wins over DO-4) | `class TextId(StrEnum)` valued `"<group>.<name>"`; `render(text_id: TextId, /, **values: str) -> str`; new texts are recorded in §2 (precedent: residual pass R-W-6 added `PERSON_REQUEST_LABEL` there) |
| Cross-topic dependencies | `docs/design/contracts/stage7/web.md` dependency table (end of file) | AEA-40 records `blocked-on` rows here; a row for these two ids lets AEA-40 lift its block |
| Evaluation plan | DO-5 `docs/design/evaluation-plan.md` | n/a: display strings, no model behaviour, no eval case changes |
| Observability contract | DO-6 | n/a: no entry point, no log or trace field. The texts never contain a code or form value, so CAP-n are untouched |
| Key-metrics registry | DO-7 | n/a: no metric reads these texts |
| Test scope | `.claude/rules/build-loop-test-scope.md` + its *AEA addition* | Affected tests + fast gates before the commit; affected journeys before the commit (AEA-57 is merged, so the journey gate exists) |
| Journeys | `.claude/rules/integrated-journeys.md` §3–§4; `docs/plans/tickets/_conventions.md` | Exactly one `[journey]` criterion with its level and *Blocked by*; record in `docs/testing/journeys/2026-10-21-AEA-03b.md` in the §4 field format |
| Context upkeep | `.claude/rules/context-maintenance.md` | Area-map row A0 names AEA-03b and its status in the same change |

## Source-contract reconciliation

| Obligation | Governing source | In ticket | Disposition | Plan step or owner |
|---|---|---|---|---|
| Two `TextId` members with exactly these names and values | AEA-40 plan §8 R-4 | AC-1 | in-ticket (built, `8db744f`) | Step 2 verifies |
| Template strings exactly "Code entered", "Details sent", no placeholders | g1-chat-core.md line 487 | AC-1, AC-3 | in-ticket | Step 2, Step 3 |
| Every text matches its source fixture entry and the source file quotes it | AEA-03 test `test_every_sentence_matches_its_source_fixture`, `test_fixture_quotes_its_source_files` | AC-2 | in-ticket (built) | Step 2 verifies |
| New group `history` counted (2), total 77 | `test_text_id_shape_and_named_ids` (`GROUPS`, `EXPECTED_COUNTS`) | AC-2 | in-ticket (built) | Step 2 verifies |
| The row text can never carry the code or the details (render refuses any value) | g1-chat-core "never digits"; data.md §2 addition "the row never holds the code or the details" | AC-3 | added (no test yet) | Step 3 |
| data.md §2 records the two ids; web.md dependency table has the AEA-03b row | context-maintenance rule 1; data.md residual-pass precedent | AC-4 | in-ticket (built, `f3bbfac`) | Step 2 verifies |
| Area-map A0 row names AEA-03b and its status; conflict with main resolved keeping AEA-02b's text | context-maintenance rule 1; area map | AC-4 | added (conflict is new) | Step 1 |
| The history mapping itself (`_customer_text`, code → HISTORY_CODE_ENTERED, form → HISTORY_DETAILS_SENT) | AEA-40 AC-19, AEA-40 plan Step B2 | — | other-ticket: AEA-40 | AEA-40 |
| UX agreement of the wording (AEA-40-4) | AEA-40 ticket line 240; AEA-03 plan U-12 | — | n/a: the wording is the UX build's own live-row text (g1-chat-core Step 6, already in `apps/web`), so history and live rows agree by construction; nothing in `docs/ux/**` or the OpenAPI changes | — |
| Affected journeys run before the commit; record states the real result | build-loop-test-scope *AEA addition*; integrated-journeys §4 | AC-5 | added (record is stale) | Step 4, Step 5 |
| Ticket file and GitLab issue exist | `_conventions.md` | — | other-ticket: orchestrator | §Risks R-1 |

## Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

## Acceptance criteria

These stand in for the missing ticket file (see Status). AC-1, AC-2 and AC-4 are already met on the branch; the
implementer re-verifies them. AC-3 and AC-5 are the open work.

- [ ] **AC-1 [unit] (example pair, from AEA-40 AC-19)** Input `render(TextId.HISTORY_CODE_ENTERED)` → output
  `"Code entered"`; input `render(TextId.HISTORY_DETAILS_SENT)` → output `"Details sent"`; the enum values are
  `"history.code_entered"` and `"history.details_sent"`. — verify:
  `uv run pytest tests/unit/policy/test_texts.py::test_history_row_texts -q` — evidence: 1 passed. (No PRD worked pair
  WP-1…WP-8 covers history rows; this AC-19 pair is the ticket's worked pair.)
- [ ] **AC-2 [invariant]** The text table stays whole: the fixture and `TextId` hold the same 77 ids, every template
  equals its fixture entry, the fixture's source file (`g1-chat-core.md`) quotes both strings, and the group counts
  include `"history": 2`. — verify: `uv run pytest tests/unit/policy/test_texts.py -q` — evidence: all pass; the
  `-s` print of `test_text_id_shape_and_named_ids` shows `'history': 2` and `total 77`.
- [ ] **AC-3 [invariant] (plan-added)** The two history texts take no values, so a code or form value can never reach
  them: `render(TextId.HISTORY_CODE_ENTERED, digits="x")` and `render(TextId.HISTORY_DETAILS_SENT, digits="x")` each
  raise `TextRenderError` with `.placeholder == "digits"`. — verify:
  `uv run pytest tests/unit/policy/test_texts.py::test_history_row_texts_take_no_values -q` — evidence: 1 passed.
- [ ] **AC-4 [docs]** `docs/design/contracts/stage7/data.md` §2 and its header list the two ids; `stage7/web.md`'s
  dependency table has the `data (DAT), AEA-03b (AEA-40 R-4)` row; `.claude/reference/area-map.md` row A0 lists
  `03b` in *Tickets* and the AEA-03b clause in *Status*, **and still contains main's AEA-02b text** (`views.py` in
  *Owns*, the "AEA-02b: `domain/views.py` actual" clause). — verify:
  `grep -c "HISTORY_CODE_ENTERED" docs/design/contracts/stage7/data.md docs/design/contracts/stage7/web.md` (each ≥ 1);
  `grep -n "AEA-02b: \`domain/views.py\` actual" .claude/reference/area-map.md` and
  `grep -n "AEA-03b adds the \`history\` group" .claude/reference/area-map.md` both print the A0 line;
  `git diff main --stat` lists only the seven owned files.
- [ ] **AC-5 [journey]** Runs no journey of its own: the two texts have no server path until AEA-40's history rebuild
  lands (J-1's refresh/resume step, slice plan §0a). The affected-journey gate runs on the branch and is green: every
  selected journey passes or is skipped as blocked, none fails. The record
  `docs/testing/journeys/2026-10-21-AEA-03b.md` states level **`mock-tested`**, *Blocked by* **AEA-40** (no longer
  AEA-57), names **J-1** (refresh/resume of the thread) as the journey that will exercise these texts, and quotes the
  real command and its result. — verify: `uv run python -m tests.journeys.affected --base main` — evidence: the
  command's summary line (`N journeys affected`, pytest `X passed, Y skipped`, 0 failed) copied into the record.

## File map

All paths relative to the worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-03b`.

| File | Current or planned | Change |
|---|---|---|
| `src/meridian/policy/texts.py` | actual (branch) | Already has the two members (after `PERSON_REQUEST_LABEL`, under comment `# --- history ... ---`) and the two `_TEXTS` entries. **No change** unless Step 2 finds a mismatch |
| `tests/unit/policy/texts_source_fixture.json` | actual (branch) | Already has the two entries (`kind: "proposal"`, `file: docs/plans/fanout/2026-10-21-ux4/g1-chat-core.md`, `line: 487`). No change |
| `tests/unit/policy/test_texts.py` | actual (branch) | Already has `"history"` in `GROUPS`, `"history": 2` in `EXPECTED_COUNTS`, `test_history_row_texts`. **Add** `test_history_row_texts_take_no_values` (Step 3) |
| `docs/design/contracts/stage7/data.md` | actual (branch) | Already has the header line and the §2 paragraph. No change |
| `docs/design/contracts/stage7/web.md` | actual (branch) | Already has the dependency row. No change |
| `.claude/reference/area-map.md` | actual (branch), **conflicts with main** | Resolve the A0 row in the merge (Step 1). Touch no other row |
| `docs/testing/journeys/2026-10-21-AEA-03b.md` | actual (branch), stale | **Rewrite** with the real journey result (Step 5) |

Shared surfaces read only: `tests/journeys/**` (AEA-57's; never edit), `docs/plans/fanout/2026-10-21-ux4/g1-chat-core.md`
(source the fixture quotes), every other file. Not owned and **not to be touched**: `docs/plans/tickets/**`,
`docs/plans/fanout/2026-10-21-build/AEA-40.md`, `.claude/state/build-ledger.md` (the orchestrator's), `apps/web/**`,
`docs/ux/**`, the OpenAPI, any other area-map row.

## Shared code to use

From `src/meridian/policy/texts.py` (main, unchanged by this ticket):

```python
PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {"case_ref", "due_label", "window", "digits", "rep_name", "n", "amount"}
)
class TextId(StrEnum): ...            # values "<group>.<name>"
TEXTS: Final[Mapping[TextId, str]]    # read-only view of _TEXTS
class TextRenderError(KeyError):
    text_id: str
    placeholder: str | None
def render(text_id: TextId, /, **values: str) -> str
```

`render` raises `TextRenderError(text_id.value, min(supplied - required), "unexpected placeholder")` when a value is
supplied that the template does not use. For the two history texts `required` is empty, so `digits="x"` raises with
`placeholder == "digits"`. The test file already imports `TextId`, `TextRenderError` and `render` from
`meridian.policy.texts` (top of `tests/unit/policy/test_texts.py`), and `pytest`.

## Steps

**Step 0 — preconditions (no code).**
`cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-03b`; `export UV_LINK_MODE=hardlink`;
`git status --short` is empty; `git log --oneline -2` shows `f3bbfac` then `8db744f`. Never rebase, never force-push.

**Step 1 — bring the branch up to main and resolve the area-map conflict.**
1. `git merge --no-ff main` (merge, not rebase: the branch history stays as built).
2. Git stops on `.claude/reference/area-map.md`. Resolve the **A0 Foundation** row (the line starting `| 0 | **A0
   Foundation** |`) by taking **main's** version of the whole line and making exactly two edits to it:
   - *Tickets* cell: `AEA-01, 02, 03, 04, 10, 11` → `AEA-01, 02, 03, 03b, 04, 10, 11`.
   - *Status* cell: replace `` `policy/texts.py` actual (AEA-03, `2689582`); `` with
     `` `policy/texts.py` actual (AEA-03, `2689582`; AEA-03b adds the `history` group, 2 texts, total 77); ``
     (drop the branch's "on branch `aea-03b-history-texts`" wording: after the merge the text is on main).
   Keep main's `views.py` in *Owns* and main's `AEA-02b: domain/views.py actual (...)` clause unchanged. If any other
   row conflicts, take main's version of it unchanged.
3. If any other file conflicts, stop and report (none is expected: main did not touch the other six files since
   `35aefdd`).
4. `git add .claude/reference/area-map.md`, then `git commit` with the message
   `Merge main into aea-03b-history-texts (area map A0 row: keep AEA-02b, add AEA-03b)` and, as its last line,
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
   Invariant protected: main's AEA-02b area-map record is not lost; this ticket's area-map edit stays on one row.

**Step 2 — verify the built code (no edits expected).**
`grep -n "HISTORY_CODE_ENTERED\|HISTORY_DETAILS_SENT" src/meridian/policy/texts.py` prints 4 lines (two members, two
`_TEXTS` entries) with exactly the values and strings in *Goal*. `grep -n '"history' tests/unit/policy/texts_source_fixture.json`
prints the two ids. Run `uv run pytest tests/unit/policy/test_texts.py -q` → all pass. If a value differs from *Goal*,
fix it to *Goal* (the names and strings are fixed by AEA-40 R-4 and AEA-40's frozen tests).

**Step 3 — add the no-values test (AC-3).** Append to `tests/unit/policy/test_texts.py`, after `test_history_row_texts`:

```python
@pytest.mark.parametrize("text_id", [TextId.HISTORY_CODE_ENTERED, TextId.HISTORY_DETAILS_SENT])
def test_history_row_texts_take_no_values(text_id: TextId) -> None:
    with pytest.raises(TextRenderError) as err:
        render(text_id, digits="x")
    assert err.value.placeholder == "digits"
    assert err.value.text_id == text_id.value
```

Use the literal `"x"`: never a digit string, code-like or card-like value (project rule). Run
`uv run pytest tests/unit/policy/test_texts.py -q` → green.

**Step 4 — run the affected journeys (AC-5).**
`uv run python -m tests.journeys.affected --base main` (no `--journey-record`: this ticket's record is hand-written,
because the selected journeys do not exercise these texts and an auto-record would claim the wrong scope). Expect
about 11 journeys selected (the list before the merge: `j1/test_aea_49.py`, `j1/test_aea_57.py`, `j10/test_aea_32.py`,
`j10/test_aea_48.py`, `j6/test_aea_47.py`, `j7/test_aea_41.py`, `j7/test_aea_42.py`, `j7/test_aea_46.py`,
`j8/test_aea_31.py`, `j8/test_aea_44.py`, `j9/test_aea_41.py`; they are selected because they import modules that
import `meridian.policy.texts`). Pass = 0 failed; skips reported as `blocked-on …` are expected. Servers bind
`127.0.0.1` on ephemeral ports (never 4019 or 5184). If a journey fails, check whether it also fails on main
(`git stash` is not needed: run the same command in `/home/linuxuser/workspaces/inno-aea-callcenter` with
`--files src/meridian/policy/texts.py`); a failure that reproduces on main is pre-existing: record it, do not fix it
here, and report it.

**Step 5 — rewrite the journey record (AC-5).** Replace `docs/testing/journeys/2026-10-21-AEA-03b.md` with the
integrated-journeys §4 fields:

| Field | Value to write |
|---|---|
| Claim | AEA-03b: `history.code_entered` ("Code entered") and `history.details_sent` ("Details sent") exist in `policy/texts.py`, match their source fixture, render, and refuse any value. No journey of its own: no server path reads them until AEA-40's history rebuild. Journey that will exercise them: **J-1** (refresh/resume of the thread, AEA-40 AC-19) |
| Level | `mock-tested` |
| Tested revision | the SHA of the Step 1 merge commit, followed by "+ the AEA-03b test/record commit" (the record cannot hold its own SHA; never amend to add it) |
| Environment | worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-03b`; Python via `uv run`; unit tests: no server, DB or model; journeys: AEA-57 harness (real app in-thread on 127.0.0.1, disposable DB copy, scripted model) |
| Command | `uv run pytest tests/unit/policy tests/unit/test_import_direction.py -q`; `uv run python -m tests.journeys.affected --base main` |
| Result | the real counts from Steps 4 and 6, e.g. "unit: N passed; journeys: 11 affected, X passed, Y skipped (blocked-on …), 0 failed; none exercises the history texts" |
| Evidence location | this record; the implementer's report |
| Remaining limitations | No integrated path renders these texts yet; AEA-40 is not built |
| Blocked by | AEA-40 (history rebuild) |

Do not write "-n 2" in the command: this project's pytest run is serial.

**Step 6 — fast gates and affected tests, cheapest first, stop at the first red.**
1. `uv run ruff check src tests` and `uv run ruff format --check src tests`
2. `uv run mypy` (uses `[tool.mypy] files = ["src/meridian", "tests", "eval"]`, strict; do not narrow it to `src`)
3. Affected tests (direct importers of `meridian.policy.texts`, per `grep -rl "policy.texts" tests`):
   `uv run pytest tests/unit/policy tests/unit/test_import_direction.py tests/unit/agent/nodes/test_compose.py tests/unit/agent/nodes/test_compose_blocks.py tests/services/test_reset.py tests/services/test_person_request.py -q`
4. Step 4's journey command, if anything changed since it ran.

**Step 7 — commit.** `git add tests/unit/policy/test_texts.py docs/testing/journeys/2026-10-21-AEA-03b.md` (plus
`src/meridian/policy/texts.py` / the fixture only if Step 2 changed them). Message:
`test+docs(AEA-03b): history texts refuse values; journey record with the affected-journey run` and the last line
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push (only the merge step pushes main).

## Data and fixtures

Synthetic only. The two fixture entries already exist in `tests/unit/policy/texts_source_fixture.json`, sourced from
`docs/plans/fanout/2026-10-21-ux4/g1-chat-core.md` line 487 (our UX build plan, kind `proposal`). The AC-3 test value is
the literal `"x"`. No issued data, no codes, no phone or card-like numbers.

## Risks and edge cases

- **R-1 (orchestrator) — the ticket has no spec file and no GitLab issue.** #201 is a 404 and
  `docs/plans/tickets/AEA-03b.md` was never written (AEA-02b / #200 is the same: also a 404, merged without a file).
  The implementer must not create either (not owned). Request: the orchestrator copies this plan's *Acceptance criteria*
  into `docs/plans/tickets/AEA-03b.md` and files the issue, or records in the ledger that this plan is the spec. Not a
  product decision; it does not block the build.
- **R-2 — area-map collisions.** Open branches `aea-24`, `aea-28`, `aea-34`, `aea-36`, `aea-40`, `aea-50` also edit
  `.claude/reference/area-map.md`. This ticket edits the A0 row only; any later merge conflict on another row is that
  ticket's. If one of them also edits A0 before this merges, the merge step applies the same rule as Step 1.
- **R-3 — AEA-40 dependency.** AEA-40's plan Step 0 gate greps `HISTORY_CODE_ENTERED\|HISTORY_DETAILS_SENT` in
  `src/meridian/policy/texts.py` on main; it lifts AEA-40's Part B block only after this merges. The names must not
  change.
- **R-4 — previous report was wrong about the journey gate.** "AEA-57 has not landed" is false (ledger: merged
  `bd79a29`); the gate exists and must run (Step 4).
- **R-5 — pre-existing red elsewhere.** `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0`
  is stale on main (ledger AEA-06, AEA-57). It is not in this ticket's affected set; do not run or fix it here.
- Edge: `render(TextId.HISTORY_*)` with no values returns the string; `TEXTS` is read-only; adding members after
  `PERSON_REQUEST_LABEL` keeps the module's import-time check (`set(_TEXTS) != set(TextId)`) satisfied.

## Checks and evidence

| Check | Command | Evidence |
|---|---|---|
| Lint, format | `uv run ruff check src tests`; `uv run ruff format --check src tests` | clean |
| Type check | `uv run mypy` | `Success: no issues found` |
| Affected tests | Step 6.3 command | all pass, count in the report |
| AC-1 | `uv run pytest tests/unit/policy/test_texts.py::test_history_row_texts -q` | 1 passed |
| AC-2 | `uv run pytest tests/unit/policy/test_texts.py -q -s` | pass; print shows `'history': 2`, `total 77` |
| AC-3 | `uv run pytest tests/unit/policy/test_texts.py::test_history_row_texts_take_no_values -q` | 2 passed (parametrized) |
| AC-4 | greps in AC-4; `git diff main --stat` | the seven owned files only |
| AC-5 (journeys) | `uv run python -m tests.journeys.affected --base main` | 0 failed; counts copied into the record |
| Capture verification | n/a: no workflow, log or trace touched | — |
| Evaluation check | n/a: no model behaviour changed | — |

Full suite: not required (no shared fixture, settings, lockfile or cross-codebase module change; `policy/texts.py` gains
two additive members).

## Gates

None (no human, paid or live gate).

## Must not

- Do not rename the ids or change the strings; do not add other `TextId` members (AEA-29's email/general follow-up texts,
  AEA-29 plan RF-22, are not this ticket).
- Do not edit `tests/journeys/**`, `apps/web/**`, `docs/ux/**`, the OpenAPI, `UI_CONTRACTS.md`, ticket files, the ledger,
  AEA-40's plan, or any area-map row other than A0.
- No rebase, no force-push, no `git add -A`, no push. No `-n` flag to pytest. No `.env` reads.
