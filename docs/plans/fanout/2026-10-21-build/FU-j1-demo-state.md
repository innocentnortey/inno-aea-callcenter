# Plan — [FU-j1-demo-state] J-1 step 4 reads a `demo_state` row the product never writes on a fresh store

**Status:** planned (READY) · **Lane:** `lane::build-loop` (test code + a journey record; not `risk::security`: no auth,
secret, PII, network or deployment surface; nothing under `src/` is edited)
**Issue:** wave-fix item from the AEA-51 pass-1 run (no GitLab issue) · **Base revision:** `main` `9d12b8f`
**Planner model:** claude-opus-5-5 · **Implementer:** `fanout-implementer` (Sonnet)

## Goal

Finding (AEA-51 pass 1, journeys with `reply_composer` bound):
`tests/journeys/j1/test_aea_57.py::test_j1_session_resume_and_owner_guard` fails at step **"4 start session"** because it
runs `journey.db.scalar("SELECT demo_now FROM demo_state WHERE id = 1")`, and on a fresh journey DB there is no `id = 1`
row, so `DbReader.one` raises `AssertionError("expected exactly one row, got 0")`.

**Decision made here: fix the test, not the product.** The test asserted something the product never promised. Step 4
will instead assert what the product actually does on a fresh store: **no `demo_state` row exists**, and the CON-1
response's `demo_clock.now` equals `DEMO_START`, the value `DemoClock` reads when the row is absent.

## Context

AEA-57 wrote J-1 while `reply_composer` was unbound, so step 4 always reported `blocked-on AEA-51` and the `demo_state`
read never ran. The AEA-51 branch (`aea-51-aea-51-customer-path`, head `e9d07f3`) binds `reply_composer`, the step now
runs, and the read fails. `tests/journeys/j1/`, `services/demo.py` and `adapters/sqlite/repos_cases_state.py` are
byte-identical between `e9d07f3` and `main` `9d12b8f` (checked with `git diff e9d07f3 main --stat -- …`: empty).

### Why the test is wrong and the product is right (the evidence for the decision)

| Source | What it says |
|---|---|
| `docs/design/contracts/stage7/cases.md` §6 (wins over DO-4) | `class DemoClock: … def now(self) -> datetime: ...  # demo_state.demo_now; DEMO_START on a fresh store (§1.1)` |
| `docs/design/contracts/stage7/cases.md` §1.1 / §1.3 | `demo_state` is one row; the **reset** "Updated" list is where `demo_state.reset()` writes it. Nothing lists a start-up write |
| `src/meridian/adapters/sqlite/repos_cases_state.py` `DemoStateRepo.get` (AEA-10) | Docstring: *"A fresh store reads DEMO_START and nobody_online without writing."* Returns `DemoStateRow(demo_now=DEMO_START, staffing="nobody_online")` when the row is missing |
| AEA-10 plan, `test_demo_state_defaults_and_reset` | "fresh → `DEMO_START`, `nobody_online`" |
| AEA-30 plan AC-1 | "`DemoClock.now()` … read from `demo_state`, `DEMO_START` on a fresh store" |
| AEA-31 `seed_first_boot` (`src/meridian/services/reset.py`, the only start-up writer, called from `register_reset`'s `first_boot`) | Writes the four seed cases and a `seed_events` row; never touches `demo_state`. AEA-10 plan: "`demo_state.reset()` is AEA-31's separate call", made only inside `ResetService.reset` |
| Writers of `demo_state` in `src/` (grep) | Only `DemoService.set_staffing`, `DemoService.advance_clock`, `ResetService.reset`. None runs at start-up or on CON-1 |
| Sibling journey `tests/journeys/j6/test_aea_30.py::_demo_now` | Already reads the row tolerantly: `parse_wall(found[0]["demo_now"]) if found else DEMO_START` |

Making start-up write the row would change AEA-10's documented "without writing" behaviour and add a writer the design does
not list, to satisfy a test assertion that no spec asks for. The granted exception (one AEA-30/31 function) does not
cover `DemoStateRepo` (AEA-10) or `migrate`, and nothing user-visible changes either way: `GET /api/demo/clock` and CON-1
already answer `DEMO_START` on a fresh store. So the AEA-57 test changes.

## Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Requirements | n/a: no product behaviour changes | — |
| Component contracts | `docs/design/contracts/stage7/cases.md` §1.1 (`DEMO_START`, CAS-23), §1.3 (reset "Updated" row), §6 (`DemoClock.now`: "DEMO_START on a fresh store") | Step 4's expectation: no row on a fresh store; `demo_clock.now == DEMO_START` |
| DO-4 | `docs/design/contracts/internal-components.md` §13 (`cases: CaseRepos … demo_state`) | No conflict; stage7 wins |
| Journey rules | `.claude/rules/integrated-journeys.md` §3 rule 5 (reproduce first, then protect), §4 (levels, record fields) | Reproduce on `e9d07f3` first; record at `docs/testing/journeys/2026-10-21-FU-j1-demo-state.md` with the decision and why |
| Test scope | `.claude/rules/build-loop-test-scope.md` incl. *AEA addition* | Affected tests + fast gates + affected journeys; no full suite (no shared fixture, settings, lockfile or cross-package module changes) |
| Harness | `tests/journeys/support/db.py` (`DbReader.rows`, `.one`, `.scalar`), `run.py` (`JourneyRun.step`), `steps.py` (`NEED_OWNERS["reply_composer"] = "AEA-51"`), `plugin.py` (`journey` fixture is function-scoped: one fresh DB copy per test) | Use `journey.db.rows(...)`, which returns `[]` instead of raising; no harness edit |
| Evaluation plan / Observability / Metrics | DO-5, DO-6, DO-7 | n/a: no entry point, workflow, eval case or metric changes |
| Signed decisions | `docs/plans/stage7-signoff.md` D-4…D-15 | None touched |
| Signed contracts | `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md` | Not touched; CON-1's `demo_clock` shape unchanged |

## Source-contract reconciliation

| Obligation | Governing source | In finding | Disposition | Plan step or owner |
|---|---|---|---|---|
| Step 4 passes with `reply_composer` bound | finding | yes | in-ticket | Steps 2, 4 |
| Decide product-vs-test owner and record why | finding | yes | in-ticket: **test** (evidence table above) | Step 5 |
| Fresh store keeps no `demo_state` row; clock reads `DEMO_START` | cases.md §6; AEA-10 `DemoStateRepo.get` | no | added: step 4 asserts both, so a future start-up writer shows up as a deliberate design change | Step 2 |
| CON-1's `demo_clock.now` equals the demo clock, not the server clock (R-3) | cases.md §6; AEA-30 AC-1 | partly (the old assertion) | in-ticket: compared to `DEMO_START` | Step 2 |
| Other J-1 steps and tests unchanged | finding | yes | in-ticket: edit only the two lines of step 4 plus one import | Step 2 |
| AEA-30 / AEA-31 / AEA-57 tests stay green | finding | yes | in-ticket (no `src/` change; run them) | Step 6 |
| Test file ≤ 500 lines | workspace `code-structure.md` §1 | no | n/a: file is 336 lines; the edit adds about 1 line | — |

## Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

## Acceptance criteria

1. **[journey] AC-1** — `tests/journeys/j1/test_aea_57.py::test_j1_session_resume_and_owner_guard` step "4 start
   session" passes with `reply_composer` bound. **Level: `integrated with a scripted model`** (real app, first-boot DB
   copy, scripted adapter), run on a throwaway worktree at the AEA-51 head `e9d07f3` with this fix's test file applied.
   On `main` the same step still reports `blocked-on AEA-51: reply_composer not bound` (skipped, not failed).
   Evidence: `docs/testing/journeys/2026-10-21-FU-j1-demo-state.md`.
2. **AC-2** — Reproduction first: on `e9d07f3` with the **unmodified** test, the same node fails at step 4 with
   `expected exactly one row, got 0`. Quoted in the record.
3. **AC-3** — All other J-1 tests and steps keep their current result on both trees (on `e9d07f3`: every J-1 test that
   reaches its steps passes or reports blocked on an owner other than AEA-51; on `main`: identical pass/skip set to before
   the change).
4. **AC-4** — `tests/services/test_demo.py`, `tests/services/test_reset.py`, `tests/integration/test_demo_reset.py`
   (AEA-30/31) and every J-1 test (AEA-57) green or skipped-as-before on the branch.
5. **AC-5** — `ruff check`, `ruff format --check` and `mypy` clean on the changed file.
6. **AC-6 (plan-added)** — The record states the decision (test, not product) and the reason, citing cases.md §6 and
   `DemoStateRepo.get`.

**Worked pair:** n/a. J-1 step 4 is the login → greeting path; no WP-N exercises it (no model call happens on CON-1).

## File map (owned files — the only files you may create or edit)

| File | Current or planned | Change |
|---|---|---|
| `tests/journeys/j1/test_aea_57.py` | current (AEA-57, merged; exception granted) | Step 4 of `test_j1_session_resume_and_owner_guard`: replace the two `demo_state` lines; add one import |
| `docs/testing/journeys/2026-10-21-FU-j1-demo-state.md` | planned | Create: the §4 evidence record with a *Decision* row |

Read only (never edit): `src/meridian/**` (in particular `services/demo.py`, `services/reset.py`,
`adapters/sqlite/repos_cases_state.py`, `adapters/sqlite/migrate.py`, `web/container.py`), `tests/journeys/support/**`,
every other journey file, the AEA-51 worktree `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-51` (another agent's;
never edit, commit in, or run tests from it), `docs/design/**`, the plan files of other tickets.

## Shared code to use (copied from `main` `9d12b8f`)

```python
# src/meridian/adapters/sqlite/repos_cases_state.py (re-exported by repos_cases, the import J-6 uses)
DEMO_START = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))  # CAS-23, verbatim

class DemoStateRepo:
    def get(self) -> DemoStateRow:
        """A fresh store reads DEMO_START and nobody_online without writing."""
```

```python
# tests/journeys/support/db.py — DbReader
def rows(self, sql: str, params: Sequence[object] = ()) -> list[dict[str, Any]]: ...   # [] when no row
def one(self, sql: str, params: Sequence[object] = ()) -> dict[str, Any]: ...          # raises unless exactly 1
def scalar(self, sql: str, params: Sequence[object] = ()) -> Any: ...                  # = one(...) first value
```

Import line to add (same form as `tests/journeys/j6/test_aea_30.py` line 17):

```python
from meridian.adapters.sqlite.repos_cases import DEMO_START
```

## Steps

0. **Worktree.** If the orchestrator gave you a worktree, use it. Otherwise:
   `git -C /home/linuxuser/workspaces/inno-aea-callcenter worktree add /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-j1-demo-state -b fu-j1-demo-state main`,
   then in it `export UV_LINK_MODE=hardlink && uv sync` (never copy a venv; no `node_modules`). Import check:
   `uv run python -c "import meridian.web.app"`.

1. **Reproduce first (AC-2).** Create a throwaway detached worktree at the AEA-51 head (yours to delete; do not touch the
   AEA-51 worktree itself):
   ```bash
   git -C /home/linuxuser/workspaces/inno-aea-callcenter worktree add --detach /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-j1-repro e9d07f3
   cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-j1-repro && export UV_LINK_MODE=hardlink && uv sync
   uv run pytest "tests/journeys/j1/test_aea_57.py::test_j1_session_resume_and_owner_guard" -rs -q
   ```
   Expected: **1 failed**, with `expected exactly one row, got 0` from step "4 start session". Copy the failing line into
   your notes for the record. If it fails for a different reason, stop and report (the finding no longer matches).

2. **Edit step 4** in `tests/journeys/j1/test_aea_57.py` (your worktree). Inside
   `test_j1_session_resume_and_owner_guard`, in the `with journey.step(J1, "4 start session", ...)` block, replace
   exactly these two lines:
   ```python
           demo_now = journey.db.scalar("SELECT demo_now FROM demo_state WHERE id = 1")
           assert datetime.fromisoformat(demo_now) == datetime.fromisoformat(start["demo_clock"]["now"])
   ```
   with:
   ```python
           # A fresh store keeps no demo_state row; the demo clock reads DEMO_START (stage7/cases.md §6, DemoStateRepo.get)
           assert journey.db.rows("SELECT demo_now FROM demo_state WHERE id = 1") == []
           assert datetime.fromisoformat(start["demo_clock"]["now"]) == DEMO_START
   ```
   Add `from meridian.adapters.sqlite.repos_cases import DEMO_START` to the first-party imports; let
   `uv run ruff check --fix tests/journeys/j1/test_aea_57.py` place it (isort: it sorts before
   `from meridian.domain.common import Role`). `datetime` stays imported (still used). Change nothing else in the file:
   no other step, no `needs=`, no helper, no print line.
   - Invariant protected: the step still proves the CON-1 clock is the demo clock (not the server clock), and now also
     proves a session start writes no clock row.
   - Aware datetimes compare by instant, so `2026-10-16T10:00:00-05:00` from the route equals `DEMO_START`.

3. **Iterate on `main` (your worktree):** `uv run pytest -m journey tests/journeys/j1 -rs -q`. Expected: the same
   pass/skip set as before your edit; `test_j1_session_resume_and_owner_guard` is **skipped** `blocked-on AEA-51:
   reply_composer not bound` (step 4 never runs on `main`). Confirm the "before" set by running the same command once
   before step 2 (or with `git stash`).

4. **Prove the fix on the AEA-51 head (AC-1, AC-3).** Commit first (step 7), then in the repro worktree:
   ```bash
   cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-j1-repro
   git checkout fu-j1-demo-state -- tests/journeys/j1/test_aea_57.py
   uv run pytest "tests/journeys/j1/test_aea_57.py::test_j1_session_resume_and_owner_guard" -rs -q
   uv run pytest -m journey tests/journeys/j1 -rs -q
   ```
   Expected: the node **passes** (steps 4, 6 and 7). For the whole of `j1`: no failures. If steps 6 or 7, or another J-1
   test, fail on `e9d07f3` for a reason **other than** the `demo_state` read, do not fix it here: quote the failing
   assertion in the record under *Remaining limitations*, mark AC-3 not met, and report it to the orchestrator as a new
   finding for AEA-51. Then delete the throwaway:
   `git -C /home/linuxuser/workspaces/inno-aea-callcenter worktree remove --force /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-j1-repro`.

5. **Write the record** `docs/testing/journeys/2026-10-21-FU-j1-demo-state.md` (date from
   `TZ=America/Chicago date +%F`; if it is not 2026-10-21, use that date in the filename and tell the orchestrator). Title:
   `# Journey record: FU-j1-demo-state — J-1 step 4 asserts the fresh-store demo clock, not a demo_state row`. One table
   with the integrated-journeys §4 fields, plus a **Decision** row placed right after *Claim*:

   | Field | Value to write |
   |---|---|
   | Claim | J-1 step 4 (`test_j1_session_resume_and_owner_guard`) passes with `reply_composer` bound; it now asserts no `demo_state` row on a fresh store and `demo_clock.now == DEMO_START` |
   | Decision | Fixed the **test**, not the product. The product promises `DEMO_START` on a fresh store **without writing** (stage7/cases.md §6 `DemoClock.now`; AEA-10 `DemoStateRepo.get` docstring); `seed_first_boot` never writes `demo_state`; only `DemoService.set_staffing`/`advance_clock` and `ResetService.reset` do. The old assertion required a row no spec asks for. Seeding the row at start-up would add an undesigned writer and change AEA-10's behaviour for no user-visible gain |
   | Level | `integrated with a scripted model` on `e9d07f3` + this test file; on `main`: step reported blocked on AEA-51 |
   | Tested revision | Your commit SHA on `fu-j1-demo-state` (from `main` `9d12b8f`), and the repro tree `e9d07f3` with that file checked out |
   | Environment | Host `claude-vultr`; Python 3.12; uv; journey harness (real app via `launch_server` on a first-boot copy of the issued SQLite; scripted model adapter; socket guard on) |
   | Command | The commands of steps 1, 3, 4 and 6, verbatim |
   | Result | Before (step 1): the quoted `expected exactly one row, got 0` failure. After: per-command pass/fail/skip counts |
   | Evidence location | This file plus the pytest output of the commands above |
   | Remaining limitations | The browser leg of J-1 (AEA-58) not run here; anything found in step 4's "other reason" branch |
   | Blocked by | `main`: AEA-51 (`reply_composer`) for J-1 steps 4–7; none for the repro run |

   No secrets, demo password, cookie values, codes or phone numbers in the record.

6. **Final gates (cheapest first, stop at the first red), in your worktree:**
   ```bash
   uv run ruff check tests/journeys/j1/test_aea_57.py
   uv run ruff format --check tests/journeys/j1/test_aea_57.py
   uv run mypy tests/journeys/j1/test_aea_57.py
   uv run --with pytest-xdist pytest tests/services/test_demo.py tests/services/test_reset.py tests/integration/test_demo_reset.py -n 2 -q
   uv run python -m tests.journeys.affected --base main
   ```
   The last command selects every journey (any change under `tests/journeys/` is an always-input); it is the project's
   merge-gate command and runs serially. Passing = 0 failed; skips only with `blocked-on …` reasons, the same set as on
   `main` before your change. No full `pytest` run (nothing here reaches everything).

7. **Commit** on `fu-j1-demo-state` (explicit paths, never `git add -A`; do not push; never force-push):
   ```bash
   git add tests/journeys/j1/test_aea_57.py docs/testing/journeys/2026-10-21-FU-j1-demo-state.md
   git commit -m "test(FU-j1-demo-state): J-1 step 4 asserts the fresh-store demo clock, not a demo_state row

   The product reads DEMO_START on a fresh store without writing (stage7/cases.md 6; AEA-10 DemoStateRepo.get);
   nothing writes demo_state at start-up or on CON-1, so the old scalar read failed once reply_composer was bound.

   Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
   ```
   Commit the test edit before step 4 (the repro checks the file out from the branch), then amend nothing: add the record
   in a second commit with the same trailer if that is easier.

## Data and fixtures

None new. The journey harness builds a disposable first-boot copy of the issued SQLite per test (`journey_environment`);
no seed, fixture or synthetic value is added.

## Risks and edge cases

- **Something writes `demo_state` before step 4 later** (e.g. AEA-51 or a later ticket adds a start-up write). The new
  `== []` assertion then fails loudly. That is intended: it would be an undesigned writer per cases.md §6. Do not relax
  the assertion to the tolerant J-6 form; report it instead.
- **Collision:** AEA-51 (in flight) does not touch `tests/journeys/j1/` (its diff stat vs `main` lists no J-1 file), so the
  two branches merge cleanly. No other open plan owns `test_aea_57.py`.
- **Disk:** about 14 GB free on `/`. The repro worktree's `uv sync` uses hardlinks; remove the worktree at the end of step 4.
- **Ports:** the harness binds an ephemeral localhost port; never pass 4019 or 5184.

## What you must not do

- Edit anything under `src/`, `tests/journeys/support/`, other journey files, `apps/web/**`, `docs/ux/**`,
  `docs/design/**`, the OpenAPI or `UI_CONTRACTS.md`, the briefing, issued data, `docs/archive/`, `docs/parked/`.
- Edit, commit in, or run tests from `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-51`.
- Add a `demo_state` write anywhere, or change `DemoStateRepo`, `migrate`, `seed_first_boot` or the container.
- Weaken any other assertion in J-1, or change `needs=` / `operations=` on any step.
- Run the full suite, use `-n` above 2, push, or force-push. Read or print `.env`.

## Checks and evidence

| Check | Command | Evidence |
|---|---|---|
| Reproduction (AC-2) | step 1 command on `e9d07f3` | Record *Result* "before" line |
| Fix on AEA-51 head (AC-1, AC-3) | step 4 commands | Record *Result* |
| J-1 on `main` unchanged (AC-3) | `uv run pytest -m journey tests/journeys/j1 -rs -q` | Report: same pass/skip set before and after |
| AEA-30/31 tests (AC-4) | `uv run --with pytest-xdist pytest tests/services/test_demo.py tests/services/test_reset.py tests/integration/test_demo_reset.py -n 2 -q` | Report |
| Lint, format, types (AC-5) | step 6 first three commands | Report |
| Affected journeys | `uv run python -m tests.journeys.affected --base main` | Report + record *Command* |
| Capture verification | n/a: no workflow touched | — |
| Evaluation check | n/a | — |

## Gates

None (no human, external, paid or live gate).
