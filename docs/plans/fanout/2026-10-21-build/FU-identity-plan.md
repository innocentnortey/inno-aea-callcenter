# Plan — [FU-identity-plan] Identity-resume plan: an unverified customer's burning "no", three wrong codes, and the burning case's due time (AEA-51 findings F-1, F-2)

**Status:** planned (READY).
**Issue:** none. This is a wave-fix item, not a ticket. It comes from the strict xfails AEA-51 merged. This plan is its spec and its item note.
**Base revision:** main `8785135` (ledger: AEA-51 merged).
**Lane / risk:** `lane::build-loop`, no `risk::security`. The fix routes an existing plan field through one more turn and moves one case timestamp. It adds no auth, secret, PII store or network surface. So there are no frozen tests and no security review (rule `build-loop-test-scope`). The identity path is touched, but only to carry a plan that already exists; what a locked customer is told is unchanged (R-16 "reveals nothing" stays green, R-6 below).
**Models:** planner `claude-opus-5-5`; implementer Sonnet.
**Slug:** `fu-identity-plan`.

---

## 1. Goal and sources

### What this item delivers, concretely

Three customer chats behave as the PRD worked pairs say. Today they do not.

1. **WP-6 "no", customer not yet verified.**
   - **The chat:** "I smell something burning from the vents" → the burning check card → "No" → the locate form → the code → the earliest repair windows → a pick.
   - **Today:** the window pick books the visit, but **no case ever opens**.
   - **After this item:** the P2 `burning_ruled_out` case opens on the code turn, when the windows are shown. That is the same moment it opens for a verified customer today.
2. **WF-1 (AC-34), three wrong codes.**
   - **The chat:** an invoice question → the locate form → three wrong codes.
   - **Today:** the code locks and **no case opens**.
   - **After this item:** the locking turn opens an `identity_unverified` P3 case (escalation rule 5, R-16).
3. **WP-6 "no", any customer (CAS-16 option A).**
   - **The chat:** the customer books the urgent visit the "no" branch offers.
   - **Today:** the P2 case keeps the standard due time ("1 business day", Mon 7:00 pm).
   - **After this item:** the booking moves the case's internal due time to the **start of the booked window**. If no visit is booked, the due time stays the standard promise due.

### Why they fail today (what was found reading `main`)

- **F-1 (both chats 1 and 2).** `Plan` is a turn-scoped state key (`agent/graph.py` `TURN_SCOPED_KEYS`), so every turn resets it.
  - On the "no" turn, the gates node writes `_burning_ruled_out_plan()` (`front.py` lines 65–75): one `BOOK_NEW` task with `needs_identity=True`, and `handoff_request=BURNING_RULED_OUT`.
  - `route_act_plan` sends the turn to `identity`. With no form or code, `identity` returns `{}`, and `route_after_identity` sends it to `facts`. **`escalation` never runs on that turn.**
  - `facts._next_open_tasks` (`reply.py` lines 127–163) saves the task as an `OpenTask` with `status="waiting_identity"`, but `OpenTask` has no place for the plan's `handoff_request`. The request is lost.
  - On the code turn the gate is `CODE_ENTRY`, so the planner does not run and `state.plan is None`.
    - `route_after_identity` resumes the open tasks from `open_tasks` alone. `escalation` sees `plan=None`, so there is no rule-4 request.
    - For a locked code, `policy/escalation.py::_private_task_open` (lines 56–61) looks only at `inputs.plan` and the results. Both are empty, so rule 5 (`identity_unverified`) never fires.
- **F-2 (chat 3).**
  - The P2 case opens on the windows turn with no window known. `CaseService.open_case` takes `window_start` only from `change_request` (`cases.py` line 133), so the due is `promise.due_at`.
  - On the pick turn (`CARD_CHOICE`), the booking is written and escalation decides `none`. Nothing writes to the case again.
  - `policy/handoff.py::case_due_at` (lines 249–255) already returns `window_start` for `BURNING_RULED_OUT`. Nothing ever calls it with a booked window.

### Sources (each was read for this plan)

| Source | Location | What it obliges here |
|---|---|---|
| The three strict xfails | `tests/graph/test_worked_pairs_api.py` lines 310–326 (`test_wp6_no_due_is_booked_window_start`), 328–337 (`test_wp6_no_unverified_still_opens_p2`), 471–480 (`test_wf1_three_wrong_codes_open_identity_unverified`) | Their xfail reasons name F-1 and F-2. Remove exactly these three decorators. The tests' bodies are the acceptance |
| AEA-51 plan | `docs/plans/fanout/2026-10-21-build/AEA-51.md` AC-12 (line 276), AC-34 (line 298), §8 R-16, *Deviations* item 3 (lines 1724–1727) | AC-12: `no` → urgent booking offer + P2 `burning_ruled_out`, due = booked window start (CAS-16 A). AC-34: three wrong codes → `identity_unverified` P3 |
| CAS-16 (decided A by D-14) | `docs/plans/7b-decisions/cases.md` §"CAS-16" (lines 22–58); `docs/plans/stage7-signoff.md` D-14 (line 50) | P2, reason `burning_ruled_out`. "Its internal due time is the urgent booking's window start … If no slot could be booked, the due time is the standard promise due." The customer still sees the standard promise |
| Graph-nodes addendum | `docs/design/contracts/stage7/graph-nodes.md` §6 (GRN-6) | The code-built plan for `burning_answer == "no"`: one scheduling `BOOK_NEW` task, `handoff_request` = CAS-16's reason, `source="rules_only"`, routed through `route_act_plan` (identity first) |
| DO-4 escalation table | `docs/design/contracts/internal-components.md` §6 rule table (lines 459–470); `stage7/cases.md` §3.4 | Rule 4: a plan `handoff_request` escalates. Rule 5: identity `not_verified` or `locked` **with a private task open** → `identity_unverified` P3, the reply reveals nothing (R-16) |
| PRD | `docs/prd/inno-aea-callcenter-prd.md` R-16 (line 212), R-7 | R-16: "No match, an ambiguous match, no usable contact or a failed code → hand off without revealing whether an account exists" |
| Policy | `src/meridian/policy/handoff.py` `case_due_at`, `_PRIORITY` (`BURNING_RULED_OUT: P2`, "CAS-16 option A (D-14)"), `_ISSUED_WINDOW_END` | Priority and the due rule are already code. This item only feeds them the booked window |
| Test scope | `.claude/rules/build-loop-test-scope.md` with its *AEA addition* | Affected tests while iterating. Fast gates, affected tests and affected journeys before the commit. The full suite once, because `domain/state.py` is imported across the codebase (see §7) |
| Journeys | `.claude/rules/integrated-journeys.md` §3–§4 | One `[journey]` criterion with its level and *Blocked by*. Record in `docs/testing/journeys/` |
| Design rules | workspace `code-design-solid-modularity.md`, `code-structure.md` | Stay inside the existing modules. Size caps: see the file map |

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Change | Lines now → after (cap) |
|---|---|---|
| `src/meridian/domain/state.py` | modify: `OpenTask.handoff_request`, `IdentityNodeUpdate.plan`, new pure `identity_resume_plan` | 226 → ~285 (700) |
| `src/meridian/agent/nodes/front.py` | modify: the `identity` node writes the resume plan | 245 → ~255 (600) |
| `src/meridian/agent/nodes/reply.py` | modify: `_next_open_tasks` only | 385 → ~390 (600) |
| `src/meridian/agent/nodes/act.py` | modify: the `escalation` node asks the case service to move the burning due after a booking | 278 → ~330 (600) |
| `src/meridian/policy/handoff.py` | modify: add pure `window_start_of` | 363 → ~375 (600) |
| `src/meridian/services/_case_actions.py` | modify: add `align_burning_due_in`; widen the module docstring's first line | 304 → ~350 (600) |
| `src/meridian/services/cases.py` | modify: add the thin `CaseService.align_burning_due` | 564 → ~578 (600; **do not exceed 600**) |
| `tests/graph/test_worked_pairs_api.py` | modify **only** to delete the three `@pytest.mark.xfail(...)` decorators named in §1 | 823 → 808 |
| `tests/unit/domain/test_identity_resume_plan.py` | create | ~120 (500) |
| `tests/unit/agent/nodes/test_open_task_carry.py` | create | ~90 (500) |
| `tests/unit/agent/nodes/test_burning_due_align.py` | create | ~120 (500) |
| `tests/unit/policy/test_window_start_of.py` | create | ~30 (500) |
| `tests/services/test_cases_burning_due.py` | create | ~90 (500) |
| `docs/testing/journeys/2026-10-22-FU-identity-plan.md` | create (written by the journey recorder; fix the Claim and Level fields by hand if needed) | — |
| `docs/design/code-design.md` | append **one** line after the last `**Built:**` line of the list at lines 181–201 (append-style shared file) | +1 |

### Shared surfaces: read, never edit

- `src/meridian/agent/routers.py`: `route_after_identity` already routes an act plan with tasks through `route_act_plan`, and an identity failure to `escalation`. No change is needed.
- `src/meridian/policy/escalation.py`: rules 4 and 5 already do the right thing once `inputs.plan` is set.
- `src/meridian/agent/nodes/compose.py`, `compose_cards.py`, `plan.py`, `gates/*`, `services/handoff.py`, `services/identity.py`, `services/scheduling.py`, `adapters/**`, `web/**`.
- `tests/graph/worked_pair_scenarios.py`: the scenario drivers, including their F-1 docstrings. Do not edit.
- Every other test file: do not edit, skip, deselect or weaken any test or assertion.
- **Never edit:** `docs/ux/**`, `apps/web/**`, `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `docs/archive/`, `docs/parked/`, the briefing, issued data, `docs/design/contracts/**`.

### Other slices in flight (checked 2026-10-22)

- **FU-person-request**: branch `aea-fu-person-request-fu-person-request`. Owns `services/person_request.py`, `tests/capture/test_cap3_handoff.py` (decorators), `tests/services/test_person_request_lock_span.py` and `tests/api/test_handoff_lock.py`. No overlap.
- **AEA-58-F1**: only `tests/journeys/browser/*`.
- **AEA-61**: only `tests/live/*`.
- **AEA-40**: its worktree is stale against main; it touches none of these files.
- **Shared file:** both FU items append to `docs/design/code-design.md`. It is append-style, so a merge keeps both lines.

---

## 3. Requirements table

| # | Requirement (source) | How it is implemented | How it is verified |
|---|---|---|---|
| R-1 | F-1, AC-12, GRN-6, CAS-16 A: an **unverified** customer who answers "no" gets the P2 `burning_ruled_out` case (one case, that reason, P2) | Step 1: `OpenTask.handoff_request`. Step 3: `facts` keeps the plan's request on a `waiting_identity` task. Steps 1 and 2: on a `Verified` code turn, the `identity` node writes `identity_resume_plan(...)`, which carries the request. `route_after_identity` then sends the plan to the specialists, and escalation rule 4 opens the case | `tests/graph/test_worked_pairs_api.py::test_wp6_no_unverified_still_opens_p2` (un-xfailed); `tests/unit/domain/test_identity_resume_plan.py::test_verified_resumes_a_carried_request`; `tests/unit/agent/nodes/test_open_task_carry.py::test_waiting_task_carries_the_plan_request` |
| R-2 | F-1, AC-34, R-16, DO-4 §6 rule 5: **three wrong codes** → one `identity_unverified` P3 case | Steps 1 and 2: on a `CodeLocked` turn with a `waiting_identity` task, the `identity` node writes the resume plan. Its tasks have `needs_identity=True`, so `_private_task_open` is true and rule 5 escalates (`R16.identity_unverified`) | `::test_wf1_three_wrong_codes_open_identity_unverified` (un-xfailed); `test_identity_resume_plan.py::test_code_locked_resumes_waiting_tasks` |
| R-3 | F-2, AC-12, CAS-16 A: the P2 case's **due = the booked window start** | Steps 4–6: `window_start_of` (policy). `align_burning_due_in` uses `case_due_at`, writes `due_at` with a version bump, a `due_moved` case event and a `case_changed` stream event. `CaseService.align_burning_due` wraps it. The `escalation` node calls it when this turn wrote a `BOOKED` action and the thread's open case is `burning_ruled_out` | `::test_wp6_no_due_is_booked_window_start` (un-xfailed); `tests/services/test_cases_burning_due.py::test_align_moves_due_once_to_the_window_start`; `tests/unit/agent/nodes/test_burning_due_align.py::test_booking_moves_the_burning_case_due` |
| R-4 | CAS-16 A: "If no slot could be booked, the due time is the standard promise due" | Nothing moves the due without a `BOOKED` write. The case opens with `promise.due_at` as today | `test_burning_due_align.py::test_no_move_without_a_burning_case_or_a_booking` (windows-only leg); `test_cases_burning_due.py::test_align_moves_due_once_to_the_window_start` (due before the move == promise due) |
| R-5 | CAS-16 A "the urgent booking": the due follows **the first booking** only, and only for `burning_ruled_out` | `align_burning_due_in` returns `False` and writes nothing when the case's due already differs from its promise due (an earlier booking moved it), when the reason is anything else, or when there is no open case | `test_cases_burning_due.py::test_align_moves_due_once_to_the_window_start` (second call is a no-op); `::test_align_ignores_other_cases` |
| R-6 | R-16: a locked customer's reply and case **reveal nothing** | Unchanged compose path (`CODE_LOCKED` error block + the handoff card). The case is opened with the locked `IdentityState`, so `customer_id` is stored only when verified (`cases.py` line 139) | `::test_wf1_identity_failure_reveals_nothing` stays green; the `seen` scan there now also covers the handoff card on the locked turn |
| R-7 | A failed due move never fails the customer's turn (the booking is already committed) | The `escalation` node catches the exception, emits one `case_write_failed` signal (`node="escalation"`, `cause="write_error"`, `attempt=1`, `recovered=False`) and returns its decision | `test_burning_due_align.py::test_failed_move_signals_and_keeps_the_turn` |
| R-8 | No other flow changes (minimal fix) | The resume plan is written **only** for (a) `Verified` when a waiting task carries a request, and (b) `CodeLocked` when a task waits on identity. It is never written for `Located`, `NotVerified`, `CodeSent`, `CodeWrong`, `CodeExpired` or `CodeCapReached`, and never when `state.plan` is already set | `test_identity_resume_plan.py::test_other_steps_never_resume` and `::test_verified_without_a_carried_request_returns_none`; all of `tests/graph/test_worked_pairs_api.py` (WP-1…WP-8, WP-4F, DANGER, NODANGER), `tests/unit/agent/nodes/test_front.py` (key and import invariants) and `tests/unit/agent/test_routers.py` stay green |
| R-9 | Checkpoints written before this change still load | `OpenTask.handoff_request` defaults to `None` | `test_identity_resume_plan.py::test_open_task_request_defaults_to_none` |
| R-10 | `[journey]` (level `integrated with a scripted model`, API level) | The affected journeys run through the real server with the change bound | `uv run python -m tests.journeys.affected --base main -- --journey-record=FU-identity-plan` green. Record `docs/testing/journeys/2026-10-22-FU-identity-plan.md`, Level `integrated with a scripted model`, *Blocked by*: "browser legs of WP-6 / WF-1 wait on AEA-62". The WP-6 and WF-1 legs themselves are proven at the same level by the three un-xfailed tests (real app, disposable DB copy, scripted model, no browser) |
| R-11 | Fast gates | — | `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy` all clean |
| R-12 (residual, **not built**) | R-16 first half / AC-34 first half: a **locate no-match** should also hand off (`identity_unverified` P3) | **Out of scope.** Building it would open a case on both locate-failure threads in `test_wf1_identity_failure_reveals_nothing`. Their handoff cards would then carry different `reference` values and break that test's byte-identical comparison, which may not be edited | Reported as residual F-1c (§8 Risk 1). Locate failures behave exactly as today |

**The worked pairs for this item:** WP-6 (`test_wp6_burning_three_branches` stays green, plus the two un-xfailed WP-6 tests) and WF-1 / AC-34 (`test_wf1_identity_failure_reveals_nothing` stays green, plus the un-xfailed three-wrong-codes test).

---

## 4. Shared code to use (copied from `main` `8785135`)

```python
# src/meridian/domain/state.py (current)
class OpenTask(MeridianModel):
    task_id: str
    specialist: SpecialistKind
    intent: TaskIntent
    opened_turn: TurnId
    details: TaskDetails
    status: Literal["open", "waiting_identity", "done"]

class IdentityNodeUpdate(TypedDict, total=False):
    identity: IdentityState
    identity_step: IdentityStep
    halt: Halt

# src/meridian/domain/turn.py
Topic = Literal["booking", "membership", "billing", "warranty", "other"]
class PlannedTask(MeridianModel):
    order: int = Field(ge=1, le=3)
    specialist: SpecialistKind
    intent: TaskIntent
    needs_identity: bool
    resumes_task_id: str | None = None
class Plan(MeridianModel):
    mode: Literal["talk", "act"]
    tasks: tuple[PlannedTask, ...] = Field(max_length=3)
    handoff_request: HandoffReason | None
    topic: Topic
    source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"]
    planner_failed: bool = False
# TaskIntent members: ANSWER_QUESTION, READ_INVOICE, READ_MEMBERSHIP, READ_APPOINTMENTS, READ_WARRANTY,
#                     BOOK_NEW, RESCHEDULE, CANCEL, CONFIRM
class SignalRecord(MeridianModel):  # name, turn_id, thread_id, request_id, run_tag, node: str, cause: str | None,
                                    # role, specialist, attempt: int | None, recovered: bool | None
# SignalName.CASE_WRITE_FAILED = "case_write_failed"

# src/meridian/domain/identity.py — step kinds (the `kind` Literal of each step model)
# Located "located", NotVerified "not_verified", CodeSent "code_sent", CodeCapReached "code_cap_reached",
# Verified "verified", CodeWrong "code_wrong", CodeExpired "code_expired", CodeLocked "code_locked"

# src/meridian/domain/actions.py
class OpenCase(MeridianModel):
    case_ref: CaseRef; reason: HandoffReason; priority: Priority; state: CaseState
    promise: Promise; followup: FollowUp | None; live_queued: bool
class Settled(MeridianModel):
    actions: tuple[CompletedAction, ...]; open_case: OpenCase | None; read_at: dt.datetime
# CompletedAction.kind: ActionKind (BOOKED = "booked"); CompletedAction.after: dict[str, str] | None
# A BOOKED action's `after` holds "date" (ISO date) and "window" (e.g. "12:00-16:00") — services/scheduling.py _visit_dict

# src/meridian/domain/specialists.py
class SchedulingResult(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
    status: Literal["windows_shown", "written", "staff_change_request", "slot_taken", "out_of_area", "no_fit",
                    "not_verified", "booking_cap", "failed"]
    windows: tuple[ShownSlot, ...] = ()
    write: WriteResult | None = None          # WriteResult.action: CompletedAction
    ...; tools: tuple[ToolCallRecord, ...]; calls: tuple[CallRecord, ...]

# src/meridian/policy/handoff.py
_CHICAGO: Final = ZoneInfo("America/Chicago")
_ISSUED_WINDOW_END: Final[Mapping[time, time]]  # starts 08:00, 12:00, 13:00, 16:00
def case_due_at(reason: HandoffReason, promise: Promise, window_start: datetime | None) -> datetime | None:
    # returns window_start for FEE_BEARING_CHANGE and BURNING_RULED_OUT when given, else promise.due_at

# src/meridian/policy/escalation.py (unchanged; shown so the routing is clear)
def _private_task_open(inputs):  # True if any plan task needs_identity, or an account/scheduling result is not_verified
# rule 4: plan.handoff_request -> _plan_request(...) ; BURNING_RULED_OUT -> _escalate(reason, "R7.burning_ruled_out")
# rule 5: identity.status in ("not_verified", "locked") and _private_task_open -> IDENTITY_UNVERIFIED, "R16.identity_unverified"

# src/meridian/agent/routers.py (unchanged)
def route_after_identity(state):
    # halt -> halt route; identity_step.kind in {"not_verified","code_locked","code_cap_reached"} -> "escalation";
    # verified and plan.mode == "act" and plan.tasks -> route_act_plan(state); verified and open tasks -> resumed Sends;
    # else "facts"

# Case storage used by the new write body (all exist; cases.py and _case_actions.py already use them)
tx.cases.cases.get_for_thread_open(thread_id: ThreadId) -> CaseRow | None   # CaseRow.case_ref, .reason: HandoffReason,
                                                                             # .lifecycle, .due_at: datetime | None, .version
tx.cases.promises.current(case_ref) -> PromiseRow | None                    # PromiseRow.promise: Promise
tx.cases.cases.update_versioned(case_ref, expected_version, **changes) -> int | None   # "due_at" and "updated_at" allowed
tx.cases.case_events.append(CaseEventRow(case_ref=..., kind=str, actor_role="ai", detail={...}, at=now))
tx.core.events.append(case_stream(case_ref), StreamEvent(type="case_changed", payload={"version": v, "lifecycle": l}, at=now))
# from meridian.adapters.sqlite.rows import CaseEventRow, StreamEvent, case_stream   (already imported in _case_actions.py)

# GraphDeps (agent/context.py): deps.cases is the real CaseService in the app (web/container.py line 1231)
```

---

## 5. Steps (build in this order; each step is checkable on its own)

Base the work on `main` at `8785135` or later. If the orchestrator gives you no worktree, create one:

```bash
git -C /home/linuxuser/workspaces/inno-aea-callcenter worktree add \
  /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-identity-plan -b aea-fu-identity-plan-fu-identity-plan main
cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-identity-plan
export UV_LINK_MODE=hardlink
uv sync
```

- Never copy a venv. No `node_modules`.
- Do not bind ports 4019 or 5184.
- An import check is enough at setup: `uv run python -c "import meridian.agent.graph"`.

### Step 1 — `domain/state.py`: carry the request, allow the identity node to write a plan, build the resume plan

1. Add the imports:
   - `from collections.abc import Mapping, Sequence`
   - `from types import MappingProxyType`
   - `Final` added to the `typing` import
   - `HandoffReason` added to the `meridian.domain.common` import
   - `Topic` added to the `meridian.domain.turn` import

   `Plan`, `PlannedTask` and `TaskIntent` are already imported.
2. Add one field to `OpenTask`, after `status`:
   ```python
   handoff_request: HandoffReason | None = None  # FU-identity-plan (F-1): the plan's request, kept while the task waits on identity
   ```
   Invariant: the default `None` keeps every checkpoint written before this change loadable (`extra="forbid"` only rejects unknown keys).
   Update the class docstring to read `"""DO-4 section 1 WITHOUT `missing` (MissingInfo blocked, plan 8.2); plus `handoff_request` (FU-identity-plan)."""`.
3. Add `plan: Plan` to `IdentityNodeUpdate` (after `identity_step`).
4. Add the pure builder at the end of the module:
   ```python
   _RESUME_TOPIC: Final[Mapping[TaskIntent, Topic]] = MappingProxyType(
       {  # mirrors agent/nodes/plan.py _TOPIC_BY_INTENT (front.py may not import agent.nodes); ANSWER_QUESTION -> "other"
           TaskIntent.READ_INVOICE: "billing",
           TaskIntent.READ_MEMBERSHIP: "membership",
           TaskIntent.READ_WARRANTY: "warranty",
           TaskIntent.READ_APPOINTMENTS: "booking",
           TaskIntent.BOOK_NEW: "booking",
           TaskIntent.RESCHEDULE: "booking",
           TaskIntent.CANCEL: "booking",
           TaskIntent.CONFIRM: "booking",
       }
   )


   def identity_resume_plan(open_tasks: Sequence[OpenTask], step_kind: str) -> Plan | None:
       """The plan a code turn resumes when the identity detour ends (FU-identity-plan, AEA-51 finding F-1).

       `verified`: only when a task waiting on identity carries a handoff request, so the request reaches escalation
       (WP-6 "no" for an unverified customer). `code_locked`: when any task waits on identity, so escalation rule 5 sees
       a private task open (three wrong codes -> identity_unverified, R-16). Every other step kind: None. The tasks are
       the first three open tasks in stored order, as `routers._resumed` resumes them.
       """
       live = [t for t in open_tasks if t.status != "done"][:3]
       waiting = [t for t in live if t.status == "waiting_identity"]
       carried = next((t.handoff_request for t in waiting if t.handoff_request is not None), None)
       if step_kind == "verified":
           if carried is None:
               return None
       elif step_kind == "code_locked":
           if not waiting:
               return None
       else:
           return None
       return Plan(
           mode="act",
           tasks=tuple(
               PlannedTask(
                   order=i + 1,
                   specialist=t.specialist,
                   intent=t.intent,
                   needs_identity=t.status == "waiting_identity",
                   resumes_task_id=t.task_id,
               )
               for i, t in enumerate(live)
           ),
           handoff_request=carried,
           topic=_RESUME_TOPIC.get(live[0].intent, "other"),
           source="open_task",
       )
   ```
   Invariants:
   - `waiting` is non-empty whenever a plan is returned, so `live` is non-empty and `live[0]` is safe.
   - At most 3 tasks, so `Plan.tasks` `max_length=3` holds.
   - `needs_identity` mirrors `routers._resumed`.

**Check:** `uv run python -c "from meridian.domain.state import identity_resume_plan, OpenTask"`, then write and run `tests/unit/domain/test_identity_resume_plan.py` (§7).

### Step 2 — `agent/nodes/front.py`: the identity node writes the resume plan

1. Change the import line to:
   ```python
   from meridian.domain.state import (
       ConversationState,
       GatesUpdate,
       IdentityNodeUpdate,
       SafetyUpdate,
       identity_resume_plan,
   )
   ```
   No other import may be added. `test_front_module_imports` allows only the listed modules plus `meridian.domain.*`, and forbids `meridian.agent.nodes`.
2. In `identity(...)`, replace the block inside `if called:` (lines 237–242 today) with:
   ```python
   if called:
       with deps.uow() as tx:
           fresh = tx.core.reads.identity_state(thread_id)
       if step is None:
           return {"identity": fresh}
       update: IdentityNodeUpdate = {"identity_step": step, "identity": fresh}
       resumed = identity_resume_plan(state.open_tasks, step.kind) if state.plan is None else None
       if resumed is not None:
           update["plan"] = resumed  # F-1: the detour's plan, rebuilt for the turn that ends it
       return update
   ```
   Invariants:
   - `state.plan is None` guards against overwriting a plan written earlier in the same turn (the gates node's burning plan).
   - The `if step is not None: return {"identity_step": step}` branch after `if called:` is unchanged. It covers the no-call `NotVerified` from an incomplete form and never resumes.
3. Add one sentence to the module docstring: "On a verified or locked code it also writes the identity-resume plan (FU-identity-plan, finding F-1)."

**Check:** `uv run pytest tests/unit/agent/nodes/test_front.py tests/unit/agent/test_routers.py -q`. All must pass unchanged. In particular, `test_front_nodes_write_only_own_keys` (its identity cases have no open tasks), `test_identity_without_form_or_code_calls_nothing` and `test_front_module_imports`.

### Step 3 — `agent/nodes/reply.py`: keep the request on a waiting task

In `_next_open_tasks` (lines 127–163), inside the `for planned in state.plan.tasks:` loop:

1. Right after `status = _task_status(...)`, add:
   ```python
   carried = state.plan.handoff_request if status == "waiting_identity" else None  # F-1
   ```
2. In the resumed branch, change the `model_copy` update to:
   ```python
   {"status": status, "details": old.details.model_copy(update=update), "handoff_request": carried}
   ```
3. In the new-task branch, add `handoff_request=carried,` to the `OpenTask(...)` call.

Invariants:
- A request survives only while its task waits on identity.
- Once the task runs (status `open` or `done`), the request is cleared. Escalation saw it on that turn, so a later resume can never escalate it twice.
- Tasks not in this turn's plan are untouched (no change).

**Check:** write and run `tests/unit/agent/nodes/test_open_task_carry.py`; then `uv run pytest tests/unit/agent/nodes/test_reply_facts.py tests/unit/agent/nodes/test_reply_keys.py -q`.

### Step 4 — `policy/handoff.py`: the start of a booked window

1. Add, directly after `_window_text` (around line 185):
   ```python
   def window_start_of(slot_date: date, window: str) -> datetime:
       """The Chicago start of an issued appointment window on `slot_date` ("12:00-16:00" -> 12:00).

       Raises ValueError for a window the issued schema does not have. CAS-16 option A: a burning_ruled_out case is due
       at this time once its urgent visit is booked.
       """
       start = time.fromisoformat(window[:5])
       if start not in _ISSUED_WINDOW_END:
           raise ValueError("window is not an issued appointment window")
       return datetime.combine(slot_date, start, tzinfo=_CHICAGO)
   ```
2. Append `"window_start_of"` as the last entry of `__all__` (it sorts last).
3. Do not construct a `Promise` anywhere. `test_promise_construction_and_no_staff_text` counts exactly one `Promise(` call in this file.

**Check:** write and run `tests/unit/policy/test_window_start_of.py`; then `uv run pytest tests/unit/policy -q`.

### Step 5 — `services/_case_actions.py` and `services/cases.py`: move the due once

1. In `_case_actions.py`:
   - **Docstring:** change the module docstring's first line to: `"""Write bodies of the case service (A6): the staff actions `apply`, `set_followup`, `record_activity`, and the burning due move.`. Keep the rest of the docstring.
   - **Imports:** add `TurnId` to the `meridian.domain.common` import, `from meridian.domain.handoff import FollowUp, HandoffReason` (extend the existing line), `from meridian.policy.handoff import case_due_at`, and `from typing import Final`.
   - **`__all__`:** add `"align_burning_due_in"` and keep the list sorted.
   - **New function:** add it at the end of the module:
   ```python
   DUE_MOVED_RULE: Final = "CAS16.booked_window"  # CAS-16 option A (D-14)


   def align_burning_due_in(
       tx: UnitOfWork, thread_id: ThreadId, window_start: dt.datetime, turn_id: TurnId, now: dt.datetime
   ) -> bool:
       """Moves the thread's open burning_ruled_out case due to the booked window start, once (CAS-16 option A).

       False, with nothing written, when the thread has no open case, the case has another reason, its promise row is
       missing, or its due already differs from the promise due (an earlier booking moved it). Never commits.
       """
       row = tx.cases.cases.get_for_thread_open(thread_id)
       if row is None or row.reason is not HandoffReason.BURNING_RULED_OUT:
           return False
       prow = tx.cases.promises.current(row.case_ref)
       if prow is None or row.due_at != prow.promise.due_at:
           return False
       due = case_due_at(row.reason, prow.promise, window_start)
       if due == row.due_at:
           return False
       version = tx.cases.cases.update_versioned(row.case_ref, row.version, due_at=due, updated_at=now)
       if version is None:
           raise RuntimeError("case changed during the due move")
       tx.cases.case_events.append(
           CaseEventRow(
               case_ref=row.case_ref,
               kind="due_moved",
               actor_role="ai",
               detail={
                   "reason": row.reason.value,
                   "rule_id": DUE_MOVED_RULE,
                   "turn_id": str(turn_id),
                   "version": version,
               },
               at=now,
           )
       )
       tx.core.events.append(
           case_stream(row.case_ref),
           StreamEvent(type="case_changed", payload={"version": version, "lifecycle": row.lifecycle}, at=now),
       )
       return True
   ```
   Invariants:
   - "Once": the first booking moves the due off the promise due, so every later call returns `False`. That keeps the due at the urgent visit.
   - `"version"` in `detail` keeps `version_conflict` truthful: it reports this event's actor ("AI" side) for a stale staff action.
   - No customer text, phone or name is written: ids and codes only.
2. In `cases.py`:
   - **Import:** add `align_burning_due_in` to the `from meridian.services._case_actions import ...` line.
   - **Method:** add this method at the end of the class, after `record_activity`:
   ```python
   def align_burning_due(
       self, thread_id: ThreadId, window_start: dt.datetime, turn_id: TurnId, now: dt.datetime
   ) -> bool:
       """CAS-16 option A: the burning_ruled_out case is due at its booked window start; True when it moved."""
       with self._uow(write=True) as tx:
           moved = align_burning_due_in(tx, thread_id, window_start, turn_id, now)
           if moved:
               tx.commit()
           return moved
   ```
   `ThreadId` and `TurnId` are already imported in `cases.py`. Keep `cases.py` **≤ 600 lines** (`wc -l`).

**Check:** write and run `tests/services/test_cases_burning_due.py`; then `uv run pytest tests/services/test_cases.py tests/services/test_handoff.py -q`.

### Step 6 — `agent/nodes/act.py`: the escalation node moves the due after a booking

1. **Imports:**
   - `from datetime import date, datetime`. Note that the name `time` is the `time` module in this file; do not import `datetime.time`.
   - `from meridian.domain.actions import ActionKind`.
   - Extend `from meridian.policy.handoff import priority_for` to `import priority_for, window_start_of`.
   - `HandoffReason`, `SchedulingResult`, `SignalName`, `SignalRecord`, `emit_signal`, `Sequence`, `KnowledgeResult` and `AccountResult` are already imported.
2. Add two private helpers above `escalation`:
   ```python
   _ESCALATION_NODE: Final = "escalation"


   def _booked_window_start(
       results: Sequence[KnowledgeResult | AccountResult | SchedulingResult],
   ) -> datetime | None:
       """The start of the window this turn booked, from the BOOKED action's stored `after` (date, window)."""
       for result in results:
           if not isinstance(result, SchedulingResult) or result.status != "written" or result.write is None:
               continue
           action = result.write.action
           after = action.after or {}
           if action.kind is ActionKind.BOOKED and "date" in after and "window" in after:
               return window_start_of(date.fromisoformat(after["date"]), after["window"])
       return None


   def _align_burning_due(state: ConversationState, ctx: TurnContext, deps: GraphDeps) -> None:
       """CAS-16 option A (FU-identity-plan, finding F-2): a burning_ruled_out case opened on an earlier turn is due at the
       start of the visit booked for it. The booking is already written, so a failed move is signalled, never raised."""
       case = state.settled.open_case if state.settled is not None else None
       if case is None or case.reason is not HandoffReason.BURNING_RULED_OUT:
           return
       try:
           start = _booked_window_start(state.specialist_results)
           if start is not None:
               deps.cases.align_burning_due(ctx.ids.thread_id, start, ctx.ids.turn_id, ctx.now)
       except Exception:
           emit_signal(
               ctx.ids,
               SignalRecord(
                   name=SignalName.CASE_WRITE_FAILED,
                   turn_id=ctx.ids.turn_id,
                   thread_id=ctx.ids.thread_id,
                   request_id=ctx.ids.request_id,
                   run_tag=ctx.ids.run_tag,
                   node=_ESCALATION_NODE,
                   cause="write_error",
                   attempt=1,
                   recovered=False,
               ),
           )
   ```
3. In `escalation(...)`, keep the `EscalationInputs` construction exactly. Replace the return with:
   ```python
   decision = decide_escalation(inputs)
   _align_burning_due(state, runtime.context, deps)
   return {"escalation": decision}
   ```
   Invariants:
   - The node still writes only the `escalation` key (`test_act_nodes_write_only_own_keys`).
   - It never opens a unit of work itself: the strings `uow(` and `deps.uow` must not appear in `act.py` (`test_no_uow_during_specialists`). `CaseService` owns its transaction.
   - Why here: escalation is the one node every act turn passes after the specialists (`route_after_specialists`), and it already reads `state.settled`.
4. Update the module docstring to: `"""The act nodes: specialist fan-out, escalation decision (plus the CAS-16 due move after a booking) and handoff (A7b; graph-nodes section 9.5)."""`.

**Check:** write and run `tests/unit/agent/nodes/test_burning_due_align.py`; then `uv run pytest tests/unit/agent/nodes/test_act.py -q`.

### Step 7 — un-xfail the three integration tests

In `tests/graph/test_worked_pairs_api.py`, delete exactly these three decorator blocks (5 lines each), and nothing else:
- lines 310–314 (`reason="blocked-on a burning-ruled-out follow-up (finding F-2) …"`), above `test_wp6_no_due_is_booked_window_start`;
- lines 328–332 (`reason="blocked-on identity-resume plan follow-up (finding F-1): an unverified customer's burning 'no' plan …"`), above `test_wp6_no_unverified_still_opens_p2`;
- lines 471–475 (`reason="blocked-on identity-resume plan follow-up (finding F-1): on the turn that locks the code …"`), above `test_wf1_three_wrong_codes_open_identity_unverified`.

`pytest` stays imported (other tests use it).

**Check:** `uv run pytest tests/graph/test_worked_pairs_api.py -q -k "wp6 or wf1"`. All must pass, with no `xfail` and no `XPASS`. Then run the whole file: `uv run pytest tests/graph/test_worked_pairs_api.py -q`.

### Step 8 — context upkeep (one appended line)

In `docs/design/code-design.md`, insert this line directly after line 201 (`**Built:** services/demo.py, services/scheduler.py (AEA-30, …)`):

```
**Built (FU-identity-plan, wave fix):** `OpenTask.handoff_request` and `identity_resume_plan` in `domain/state.py`; the identity node writes the resume plan on a verified or locked code (AEA-51 F-1); `policy/handoff.window_start_of`, `CaseService.align_burning_due` (body `_case_actions.align_burning_due_in`) and its call from the escalation node move a `burning_ruled_out` case's due to the booked window start (CAS-16 A, F-2). Plan: `docs/plans/fanout/2026-10-21-build/FU-identity-plan.md`.
```

### Step 9 — gates, journeys, commit

1. Run §7's *before the final commit* list.
2. Commit on your branch with explicit paths (never `git add -A`):
   ```bash
   git add src/meridian/domain/state.py src/meridian/agent/nodes/front.py src/meridian/agent/nodes/reply.py \
     src/meridian/agent/nodes/act.py src/meridian/policy/handoff.py src/meridian/services/_case_actions.py \
     src/meridian/services/cases.py tests/graph/test_worked_pairs_api.py \
     tests/unit/domain/test_identity_resume_plan.py tests/unit/agent/nodes/test_open_task_carry.py \
     tests/unit/agent/nodes/test_burning_due_align.py tests/unit/policy/test_window_start_of.py \
     tests/services/test_cases_burning_due.py docs/testing/journeys/2026-10-22-FU-identity-plan.md \
     docs/design/code-design.md
   ```
   - Message subject: `fix(FU-identity-plan): carry the identity-detour plan; move the burning case due to the booked window (AEA-51 F-1, F-2)`.
   - Body: list R-1…R-12 briefly, plus the gate results.
   - Last line: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
3. Do not push; only the merge step pushes main. Never force-push.

### What the implementer must NOT do

- Do not change `routers.py`, `policy/escalation.py`, `compose.py`, `compose_cards.py`, `plan.py`, `gates/*`, `services/handoff.py`, `services/identity.py` or `services/scheduling.py`.
- Do not resume or escalate on `NotVerified` (locate failures), `CodeCapReached`, `CodeExpired`, `CodeWrong`, `CodeSent` or `Located` (R-8, R-12).
- Do not move a due for any reason other than `burning_ruled_out`, nor on `MOVED`, `CANCELLED` or change-request writes.
- Do not move a due that is already off its promise due.
- Do not open a new case on the booking turn, and do not change what the customer sees on that turn.
- Do not edit `worked_pair_scenarios.py`, any existing test (beyond the three decorator deletions) or any contract document.
- Do not put a phone number, code, name or card-like number in code, tests, logs or the journey record. Read customer values from the DB at run time, as the existing fixtures do.
- No paid model call: every test here uses the scripted adapter or doubles.

---

## 6. Data and fixtures

All data is synthetic or issued, read at run time from a disposable copy:

- **Service tests:** `tests/services/_case_fixtures.py`.
  - `store()` is a `temp_sqlite()` copy of the issued DB with migrations applied.
  - `services(s.uow)` returns `(CaseService, HandoffService, BriefAssembler, StaffingDemo)` built on `FixedClock(NOW)`. `NOW = WORKED_PAIRS_NOW`, Fri 2026-10-16 in Chicago.
  - `new_thread(tx, customer_text=...)`, `request(thread, reason, ...)`, `ctx(thread, turn)`, `new_turn()`, `wp4(tx)` and `CHI` are also there.
- **Node tests:** `tests/unit/agent/nodes/reply_fixtures.py`.
  - Helpers: `state(**overrides)` (gate FREE_TEXT, empty `settled`), `settled(*actions, open_case=...)`, `booked(turn)`, `write_result(action)`, `deps(uow=..., gw=..., cases=...)`, `gateway()`, `run(ctx)`, `turn_ctx(turn=...)`, `no_uow`, `signals(caplog)`, `watch_signals(caplog)`.
  - Constants: `THREAD`, `TURN_3`, `TURN_4`, `NOW`.
  - **`booked(turn)` is the BOOKED action on 2026-10-20, window `"12:00-16:00"`, so its window start is 2026-10-20 12:00 Chicago.**
- **Integration:**
  - `tests/integration/customer_support.open_customer_run` runs the real app on a disposable DB copy with the scripted adapter.
  - `tests/graph/worked_pair_scenarios.py` holds the drivers `wp6_no(run, verified_first=...)` and `identity_failures(run)`.
  - Customer MHC-10001's name and phone are read from the copy.

---

## 7. Checks

### The tests the implementer writes with the code (exact names)

**`tests/unit/domain/test_identity_resume_plan.py`**
- Module docstring: `"""FU-identity-plan (AEA-51 finding F-1): the identity-resume plan is a pure function of the open tasks."""`
- Imports: `meridian.domain.common` (`HandoffReason`, `TurnId`), `meridian.domain.state` (`OpenTask`, `TaskDetails`, `identity_resume_plan`) and `meridian.domain.turn` (`TaskIntent`).
- Helper: `_task(task_id, specialist, intent, status, request=None) -> OpenTask` with `opened_turn=TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")` and `details=TaskDetails()`.

The tests:
- `test_verified_resumes_a_carried_request`:
  - Input: one waiting `scheduling`/`BOOK_NEW` task `"t-1"` carrying `BURNING_RULED_OUT`, step kind `"verified"`.
  - Expect: `mode == "act"`, `handoff_request is HandoffReason.BURNING_RULED_OUT`, `source == "open_task"`, `topic == "booking"`, `planner_failed is False`.
  - Expect the tasks as `(order, specialist, intent, needs_identity, resumes_task_id)` to equal `[(1, "scheduling", TaskIntent.BOOK_NEW, True, "t-1")]`.
- `test_verified_without_a_carried_request_returns_none`: a waiting task with no request, kind `"verified"` → `None`.
- `test_code_locked_resumes_waiting_tasks`:
  - A waiting `account`/`READ_INVOICE` task, kind `"code_locked"` → a plan with `handoff_request is None`, `topic == "billing"` and `tasks[0].needs_identity is True`.
  - Only `status="open"` tasks → `None`.
  - `[]` → `None`.
- `test_other_steps_never_resume`: `@pytest.mark.parametrize("kind", ["located", "not_verified", "code_sent", "code_cap_reached", "code_wrong", "code_expired"])`. A waiting task carrying a request → `None`.
- `test_resume_plan_skips_done_and_caps_at_three`:
  - Input tasks, in order:
    - `t-0`: done
    - `t-1`: waiting, `account`/`READ_MEMBERSHIP`, carrying `MEMBERSHIP_CANCEL`
    - `t-2`: open, `knowledge`/`ANSWER_QUESTION`
    - `t-3`: waiting, `scheduling`/`BOOK_NEW`
    - `t-4`: open, `account`/`READ_WARRANTY`
  - Step kind `"verified"`.
  - Expect `resumes_task_id`s `["t-1", "t-2", "t-3"]`, orders `[1, 2, 3]`, `needs_identity` `[True, False, True]`, `handoff_request is MEMBERSHIP_CANCEL` and `topic == "membership"`.
- `test_open_task_request_defaults_to_none`: `OpenTask.model_validate({...})` without the key → `.handoff_request is None` (R-9).

**`tests/unit/agent/nodes/test_open_task_carry.py`**
- Module docstring: `"""FU-identity-plan (AEA-51 finding F-1): facts keeps a waiting task's handoff request across the identity detour."""`
- Use the same `_facts` helper as `test_reply_facts.py`:
  ```python
  def _facts(st, store): gw, _ = gateway(); return reply.facts(st, run(turn_ctx(turn=TURN_4)), deps=deps(uow=store.uow, gw=gw))
  ```
  Run it inside `with temp_sqlite() as store:` (`from tests.fixtures.sqlite import temp_sqlite`).

The tests:
- `test_waiting_task_carries_the_plan_request`:
  - Input: `state(plan=Plan(mode="act", tasks=(PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=True),), handoff_request=HandoffReason.BURNING_RULED_OUT, topic="booking", source="rules_only"))`, with no results and the identity not checked.
  - Expect `[task] = update["open_tasks"]`, `task.status == "waiting_identity"`, `task.handoff_request is HandoffReason.BURNING_RULED_OUT` and `task.task_id == f"task-{str(TURN_4)[:8]}-1"`.
- `test_task_that_runs_drops_the_request`:
  - Existing task: `OpenTask(task_id="t-1", specialist="scheduling", intent=TaskIntent.BOOK_NEW, opened_turn=TURN_3, details=TaskDetails(), status="waiting_identity", handoff_request=HandoffReason.BURNING_RULED_OUT)`.
  - The plan resumes `"t-1"` (`needs_identity=True`, `resumes_task_id="t-1"`, `source="open_task"`, same request).
  - Results: `[SchedulingResult(status="windows_shown", tools=(), calls=())]`.
  - Expect `[task]` with `task_id == "t-1"`, `status == "open"` and `handoff_request is None`.
- `test_no_request_stays_none`: the same as the first test but with `handoff_request=None` → the waiting task has `handoff_request is None`.

**`tests/unit/agent/nodes/test_burning_due_align.py`**
- Module docstring: `"""FU-identity-plan (AEA-51 finding F-2, CAS-16 option A): the escalation node moves a burning_ruled_out case's due to the booked window start; a failed move never fails the turn."""`
- Define:
  - `CHI = ZoneInfo("America/Chicago")`
  - `START = dt.datetime(2026, 10, 20, 12, 0, tzinfo=CHI)`
  - a local `AlignSpy` with `calls: list[tuple]` and an optional `error`. Its method `align_burning_due(self, thread_id, window_start, turn_id, now) -> bool` records the call, raises `error` if set, and returns `True`.
  - `_case(reason)`: `OpenCase(case_ref=CaseRef("MHC-C-0042"), reason=reason, priority=priority_for(reason), state="unassigned", promise=promise_for(reason, "nobody_online", NOW), followup=None, live_queued=False)`.
  - `_written()`: `SchedulingResult(status="written", write=write_result(booked(TURN_4)), tools=(), calls=())`. Add `# type: ignore[arg-type]` only if mypy asks, as `test_reply_facts.py` does.
- Deps: `deps(uow=no_uow, gw=gateway()[0], cases=cast(Any, spy))`.
- Call: `escalation(st, run(turn_ctx(turn=TURN_4)), deps=d)`.

The tests:
- `test_booking_moves_the_burning_case_due`:
  - Input: `state(settled=settled(open_case=_case(HandoffReason.BURNING_RULED_OUT)), specialist_results=[_written()])`.
  - Expect `set(update) == {"escalation"}`, `update["escalation"].outcome == "none"` and `spy.calls == [(THREAD, START, TURN_4, NOW)]`.
- `test_no_move_without_a_burning_case_or_a_booking`: `spy.calls == []` in each of three cases:
  - a `REFUND` open case with `_written()`;
  - a burning case with `SchedulingResult(status="windows_shown", tools=(), calls=())`;
  - `settled()` with no open case, plus `_written()`.
- `test_failed_move_signals_and_keeps_the_turn(caplog)`:
  - Setup: `watch_signals(caplog)`; the spy raises `RuntimeError("case store unavailable (test)")`.
  - Expect the update to still be `{"escalation": ...}`.
  - Expect exactly one record in `signals(caplog)` with `name == "case_write_failed"`, `node == "escalation"` and `cause == "write_error"`.

**`tests/unit/policy/test_window_start_of.py`**
- `test_issued_windows_start_in_chicago`: for each of `"08:00-12:00"`, `"12:00-16:00"`, `"13:00-17:00"` and `"16:00-19:00"` on `dt.date(2026, 10, 19)`, the result equals `dt.datetime(2026, 10, 19, H, 0, tzinfo=ZoneInfo("America/Chicago"))`, and `utcoffset()` is not `None`.
- `test_unknown_window_raises`: `"09:00-11:00"` → `pytest.raises(ValueError)`.

**`tests/services/test_cases_burning_due.py`**
- Module docstring: `"""FU-identity-plan (AEA-51 finding F-2): CaseService.align_burning_due on a temp copy of the issued DB (CAS-16 A)."""`
- Imports from `tests.services._case_fixtures`: `CHI`, `NOW`, `ctx`, `new_thread`, `new_turn`, `request`, `services`, `store`, `wp4`.
- `START = dt.datetime(2026, 10, 19, 8, 0, tzinfo=CHI)`.

The tests:
- `test_align_moves_due_once_to_the_window_start`:
  - Setup:
    - `with store() as s:` then `cases, handoff, _, _ = services(s.uow)`.
    - Thread: in a write uow, `new_thread(tx, customer_text="I smell something burning from the vents")`, then commit.
    - Case: `req = request(thread, HandoffReason.BURNING_RULED_OUT)`, `opened = handoff.open(req, ctx(thread, req.turn_id))`.
  - Expect, before the move: `opened.case.due_at == opened.case.promise.due_at` (R-4).
  - Expect the move: `cases.align_burning_due(thread, START, new_turn(), NOW) is True`.
  - Then in a read uow:
    - `row = tx.cases.cases.get(opened.case.case_ref)`; `row.due_at == START` and `row.version == opened.case.version + 1`;
    - the last of `tx.cases.case_events.list_for_case(ref)` has `kind == "due_moved"` and `detail["rule_id"] == "CAS16.booked_window"`.
  - Expect a second call with `START + dt.timedelta(days=1)` to return `False`, leaving the due and version unchanged.
- `test_align_ignores_other_cases`:
  - Fee-bearing case: in a write uow, `thread, req = wp4(tx)`, commit, then `handoff.open(req, ctx(thread, req.turn_id))`. Expect `align_burning_due(...)` to be `False` and the due to be unchanged.
  - Thread with no case: `new_thread` plus commit, then expect `align_burning_due(...)` to be `False`.

### While iterating

```bash
cd /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-identity-plan && export UV_LINK_MODE=hardlink
uv run pytest tests/unit/domain/test_identity_resume_plan.py tests/unit/agent/nodes/test_open_task_carry.py \
  tests/unit/agent/nodes/test_burning_due_align.py tests/unit/policy/test_window_start_of.py \
  tests/services/test_cases_burning_due.py -q
uv run pytest tests/unit/agent tests/unit/domain tests/unit/policy tests/unit/gates \
  tests/services/test_cases.py tests/services/test_handoff.py -q
uv run pytest tests/graph -q          # the three un-xfailed tests must pass; the rest stay green
```

### Before the final commit (once, cheapest first; stop at the first red)

1. `uv run ruff check src tests` and `uv run ruff format --check src tests`: clean.
2. `uv run mypy`: clean. It uses `[tool.mypy] files = ["src/meridian", "tests", "eval"]`, strict; do not narrow it.
3. The full non-journey suite, **once**:
   ```bash
   timeout 2400 uv run --with pytest-xdist pytest -n 2 -m "not journey" -q
   ```
   - Why the full suite: the trigger is `build-loop-test-scope` "a module imported across the codebase". `domain/state.py` (`ConversationState`, `OpenTask`) is imported by almost every graph, service and API test.
   - **Passing:** green, apart from the known reds on main. These are `tests/unit/test_affected_journeys.py::test_no_journey_yet_prints_zero_and_exits_0` and `test_wf15_reset_script`, plus the `-n 2` timing flake `test_wf13_wrong_project_keys_turn_export_off[right]`, which passes when run alone. Re-run that one alone to show it.
   - **Any other red:** stop and report. Do not edit the test.
4. The affected journeys, serial, with the record:
   ```bash
   uv run python -m tests.journeys.affected --base main -- --journey-record=FU-identity-plan
   ```
   - **Passing:** green.
   - **The record:** open `docs/testing/journeys/2026-10-22-FU-identity-plan.md` and make sure it reads:
     - **Claim:** "FU-identity-plan: WP-6 'no' (unverified) opens P2 burning_ruled_out; WF-1 three wrong codes open identity_unverified P3; the P2 due moves to the booked window start"
     - **Level:** `integrated with a scripted model` (API level)
     - **Evidence:** the three un-xfailed tests by name
     - **Remaining limitations:** "locate no-match still opens no case (residual F-1c); CodeCapReached not resumed"
     - **Blocked by:** "browser legs of WP-6 / WF-1 wait on AEA-62"
   - Correct those fields by hand if the recorder wrote "browser level", as AEA-51 deviation 6 did.
5. Put the command outputs (pass counts, known reds) in the implementer report.

---

## 8. Risks and requests

1. **Residual F-1c (report it; do not build it).**
   - **The gap:** R-16 and AC-34 also say a locate no-match or an ambiguous match hands off as `identity_unverified` P3. Today a `NotVerified` locate opens no case, because escalation sees no plan.
   - **Why it is not built here:** `identity_resume_plan` would make that easy. But `test_wf1_identity_failure_reveals_nothing` compares the no-match and real-name-other-phone replies byte for byte, normalising only `block_id` and `at`. Two cases would put two different `reference` values in the handoff cards, and that test may not be edited.
   - **Request to the orchestrator:** a follow-up that also normalises `reference` in that comparison (or compares the cards minus the reference), then adds `"not_verified"` to the resume kinds.
   - **`CodeCapReached`:** this item does not resume it either. That is the "no more codes can be sent" leg of "a failed code". The same follow-up should decide it.
2. **Side effect, intended and noted.** Any act plan whose request was lost to the identity detour now survives to the code turn. That includes WP-8's identity-first variant (`membership_cancel`, AEA-51 plan 8 F-1) and a dispute asked before verifying. This is the PRD's behaviour.
   - If a currently-green test asserts *no* case after such a detour, stop and report it as a finding; do not edit the test.
   - None was found by reading the scenarios on main. Every identity-first scenario except WP-6 has `handoff_request=None`, so its path is unchanged.
3. **Contract notes (for the orchestrator to fold into the contracts at merge, as a "Changed at merge" note).** These are additive internal-contract changes, with no signed UI contract touched:
   - DO-4 §1 `OpenTask` gains `handoff_request: HandoffReason | None = None`;
   - graph-core §3 `IdentityNodeUpdate` gains `plan`;
   - stage7 `cases.md` `CaseService` gains `align_burning_due(thread_id, window_start, turn_id, now) -> bool`;
   - `policy/handoff.py` gains `window_start_of`.

   None changes an existing signature, and the OpenAPI is untouched. `stage7/cases.md` §3.3 still says CAS-16 is "PENDING Innocent", which has been stale since D-14.
4. **Shift-end conversion.** `CaseService._convert` (`cases.py` lines 342–357) recomputes a live-queued case's due from `change_request.window_start`, which is `None` for a burning case. A burning case first opened as *live queued* (simulated on-shift) and then converted would drop back to the standard due. The demo runs `nobody_online` and the WP-6 tests never take that path. Note it as a follow-up and leave it unbuilt.
5. **Shared file.** `docs/design/code-design.md` is appended by FU-person-request too. A conflict confined to it is resolved by keeping both lines (rule `build-loop-test-scope`, *Merge in batches*).
6. **Size.** `cases.py` lands near its 600-line hard cap (~578). The wrapper stays thin and the body lives in `_case_actions.py`. If ruff format pushes it over 600, move the docstring onto one line rather than splitting the file.

---

## 9. Readiness

**READY.** Nothing needs Innocent: D-14 settled CAS-16 on option A, and its due rule is written in `docs/plans/7b-decisions/cases.md`. Every signature is copied from `main` `8785135`. No sibling ticket must merge first.

- **blockedOn:** none.
- **Owned files:** the §2 table.
- **Shared surfaces at risk of collision:** `docs/design/code-design.md` (append-only, with FU-person-request).
