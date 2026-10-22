# Plan — [FU-pending-change] `pending_change`: one source for the planner and the scheduling specialist; one area-map row per area

**Status:** planned (READY).
**Issue:** none. This is a wave-fix item, not a ticket: the Wave 3 seam audit's medium finding on `pending_change`, plus area-map drift. This plan is its spec and its item note.
**Base revision:** main `8669ed0` (Wave 4 context upkeep: resume note).
**Lane / risk:** `lane::build-loop`, no `risk::security`. The fix changes how one boolean in the specialist's slice is computed. It adds no auth, secret, PII store, model input or network surface (the slice already carries the flag; only its value changes from always `False` to correct). So there are no frozen tests and no security review (rule `build-loop-test-scope`).
**Models:** planner `claude-opus-5-5`; implementer Sonnet.
**Slug:** `fu-pending-change`.

---

## 1. Goal and sources

### What this item delivers, concretely

**One chat, before and after.** MHC-57204 asks to move a tune-up that is less than 24 hours away. That move is fee-bearing, so the scheduling specialist files a change request for staff (WP-4), a P2 case opens, and the stored record now holds a `CHANGE_REQUEST_SENT` action for that appointment. On the next turn the customer writes "can you move it to Friday instead?".

- **Today:** the planner sees `StateFlags.pending_change = True` (it reads the stored record). The scheduling specialist sees `SchedulingSlice.pending_change = False`, always, because `act.py` reads a state key that does not exist. The two halves of the same turn disagree about whether a request is already filed.
- **After this item:** the specialist's slice says `True` too. Both values come from the same stored source: `state.settled.current_visit().change_request is not None`.

**And the area map** has one row per area again, every commit it cites resolves on `main`, and no row says "planned" for files that are built.

### Why it is wrong today (what was read on `main`)

- `src/meridian/agent/nodes/plan.py` lines 245–253 (`build_planner_input`):
  `visit = state.settled.current_visit() if state.settled is not None else None` and
  `pending_change=visit is not None and visit.change_request is not None`. This is AEA-37's R-5: read from `settled` because the state key was never built.
- `src/meridian/agent/nodes/act.py` lines 97–99:
  ```python
  def _has_pending_change(state: ConversationState) -> bool:
      # graph-nodes 9.5; ConversationState has no pending_change yet (AEA-02 8.2), so False until it lands
      return getattr(state, "pending_change", None) is not None
  ```
  used at line 143 (`pending_change=_has_pending_change(state),`). This is AEA-39's PD-13.
- `src/meridian/domain/state.py` `ConversationState` (lines 108–138) has no `pending_change` field; its module docstring says so ("Not built here (plan 8.2): `last_lookups`, `pending_change`").
- `src/meridian/agent/graph.py` line 153 lists `"pending_change"` in `DURABLE_KEYS`, with the comment (lines 126–128) that it is "durable once AEA-02b builds" it and "may be absent from the model today". Nothing writes it: AEA-38's `facts` node writes no `pending_change` (AEA-38 PD-4).

### The decision this plan makes (option chosen, not open)

The orchestrator offered two fixes: derive the slice value from the planner's source, or add the field and have a node write it. **This plan derives it.** Reasons:

1. **Adding the field reaches files this item does not own.** `ConversationState` is A0's `domain/state.py`; the writer named by DO-3 §5 and graph-nodes `FactsUpdate` is the `facts` node in `reply.py` (AEA-38); the field's type `ChangeRequestRef` does not exist on `main`. The finding's own wording ("have act write it") would also break DO-3 §5's one-writer rule, since `facts` is the one committer of durable task state.
2. **Deriving needs only `act.py`** and gives the same value the planner already gets from the same stored rows, which are the authority (`Settled` is "built ONLY from actions + cases/promises rows", D-9).
3. **The AEA-37 and AEA-39 plans both anticipated a state key that never came.** AEA-37 R-2 said "when `ConversationState` gains `pending_change`, switch". With this item, the stored record is the single source for both nodes; nobody needs to switch later.

**Where the one source lives.** Not in a shared helper module: `act.py` (area A7b) must not import `plan.py` (A7d), because DO-3 §8 lets an area depend only on its own files and earlier waves, and both are wave 3. Not on `Settled` either: `domain/actions.py` is A0's and is not owned here. So the source is `Settled.current_visit()` (A0, already shared by both nodes), each node applies the same one-line predicate to it, and a **parity test** pins the two nodes to the same answer on every state shape. A `Settled` method is listed under §8 as a deferred seam.

### Sources (each was read for this plan)

| Source | Location | What it obliges here |
|---|---|---|
| Seam finding (the orchestrator's task text) | Wave 3 seam audit, finding "pending_change" (medium) | Derive `SchedulingSlice.pending_change` from the planner's source; remove the `getattr` fallback; a unit test True/False; plan-node and act-node tests stay green |
| DO-4 slice and flags | `docs/design/contracts/internal-components.md` §3 `StateFlags` (line 226 `pending_change: bool`), §5 `SchedulingSlice` (line 315 `pending_change: bool`) | Both stay `bool`. No contract change |
| Graph-nodes addendum (wins over DO-4) | `docs/design/contracts/stage7/graph-nodes.md` §9.5 `build_specialist_task` (line 373: "`pending_change = state.pending_change is not None`") and `FactsUpdate` (line 311) | The addendum names a state key that was never built. This item reads the same fact from `settled`, exactly as AEA-37 R-5 did for the planner. Recorded as a deviation in §8; not a signed UI contract |
| DO-3 state ownership | `docs/design/code-design.md` §5.2 (line 475 `pending_change: ChangeRequestRef | None  # R-21`), the writer table (line 517) | The key stays *planned* in DO-3; this item builds no key and writes no state. §8 asks the integrator to mark it derived |
| AEA-37 plan | `docs/plans/fanout/2026-10-21-build/AEA-37.md` R-2 (line 1308), R-5 (line 1330), reconciliation row (line 310) | The planner's source is `settled.current_visit().change_request` |
| AEA-39 plan | `docs/plans/fanout/2026-10-21-build/AEA-39.md` PD-13 (line 1283), step 2 (lines 762–768) | PD-13's `getattr` is superseded by this item |
| Domain source | `src/meridian/domain/actions.py` `Settled.current_visit` (lines 100–142), `VisitView.change_request: VisitChange | None` (line 84) | `change_request` is set when a later `CHANGE_REQUEST_SENT` action names the current visit's appointment; a cancellation after it makes `current_visit()` return `None` |
| Context upkeep | `.claude/rules/context-maintenance.md` rules 1, 3 | One true row per area; planned vs actual kept distinct; hashes must resolve |
| Test scope | `.claude/rules/build-loop-test-scope.md` with its *AEA addition* | Affected tests while iterating; fast gates + affected tests + affected journeys before the commit. No full suite (§7 says why) |
| Journeys | `.claude/rules/integrated-journeys.md` §4 | One `[journey]` criterion with its level and *Blocked by* |
| Sign-off decisions | `docs/plans/stage7-signoff.md` D-4…D-15 | None bears on `pending_change`; nothing here answers one differently |

---

## 2. Boundary

### Owned files (the only files the implementer may create or edit)

| File | Create / modify | Size now → after (cap) |
|---|---|---|
| `src/meridian/agent/nodes/act.py` | modify (one function body and its comment) | 326 → about 328 lines (orchestrator role: 700) |
| `tests/unit/agent/nodes/test_pending_change.py` | **create** | new, about 110 lines (tests: 500) |
| `.claude/reference/area-map.md` | modify (header line 5; collapse rows lines 31–42) | 70 → 64 lines |

**`src/meridian/agent/nodes/plan.py` is authorised but needs no edit.** Its expression is already the source. Do not touch it.

**`tests/unit/agent/nodes/test_act.py` is not edited.** It is 720 lines, past the 500-line test cap; new tests go in the new file. Its line 672 (`assert built.slice.pending_change is False`) stays true, because `make_state` builds `Settled(actions=(), ...)`.

### Shared surfaces, read only

- `src/meridian/domain/actions.py` (`Settled`, `CompletedAction`, `ActionKey`, `ActionKind`, `VisitView`) — A0.
- `src/meridian/domain/state.py` (`ConversationState`) — A0.
- `src/meridian/domain/specialists.py` (`SchedulingSlice`) — A0.
- `src/meridian/agent/graph.py` (`DURABLE_KEYS`) — A7a. Leave `"pending_change"` in it (see §8 R-2).
- `src/meridian/agent/nodes/plan.py` (`build_planner_input`) — read by the parity test.
- `tests/unit/agent/nodes/act_fixtures.py`, `tests/graph/_spine_doubles.py`, `tests/fakes` — imported by the new test, never edited.

### Owned by others; do not touch

`domain/*`, `agent/graph.py`, `agent/nodes/reply.py`, every design doc under `docs/design/`, the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`, `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `CLAUDE.md` (it has uncommitted edits from another session in the main checkout), `.claude/state/*`.

---

## 3. Requirements table

| # | Requirement (source) | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 | A settled visit that holds a `change_request` makes `build_specialist_task` return `slice.pending_change is True` (finding acceptance; **WP-4**, R-21) | Step 1: `_has_pending_change` reads `state.settled.current_visit()` | `test_wp4_filed_change_request_sets_slice_pending_change` |
| AC-2 | With no change request, `slice.pending_change is False` (finding acceptance; **WP-4F**, the fee-free move) | Same function; `None` visit or `None` `change_request` → `False` | `test_no_change_request_leaves_slice_pending_change_false[*]` (five cases) |
| AC-3 | The planner's flag and the specialist's slice come from one source and never disagree (finding title) | Same predicate over `Settled.current_visit()` in both nodes | `test_planner_flag_and_specialist_slice_agree[*]` (six cases) |
| AC-4 | Remove the `getattr` fallback (finding) | Step 1 deletes it | `grep -n "getattr" src/meridian/agent/nodes/act.py` prints nothing |
| AC-5 | Plan-node and act-node tests stay green (finding) | No change to `plan.py`; `test_act.py` unchanged | `tests/unit/agent/nodes` all pass |
| AC-6 | One row per area for A6, A7a, A8, A11, A12; hashes resolve in `git log main` (finding part 2; context-maintenance rules 1 and 3) | Step 3 replaces the block with the exact text in §5 | §7 G-7 and G-8 |
| AC-7 | `[journey]` J-4 (fee-bearing change, WP-4) and every other journey the affected command selects stay green. **Level:** as each file states; J-4's `tests/journeys/j4/test_aea_39.py` is `mock-tested`, `test_aea_51.py` is `integrated with a scripted model`. **Blocked by:** the scripted model ignores the slice, so no journey can observe this flag; an observable effect needs a live run (AEA-61, `gate::paid`) | No journey edit | §7 G-5 |
| AC-8 | ruff and mypy clean (orchestrator) | — | §7 G-1…G-3 |

---

## 4. Shared code to use (copied from `main`)

```python
# src/meridian/domain/actions.py
class ActionKind(StrEnum): ...            # members used here: BOOKED = "booked", CANCELLED = "cancelled",
                                          #   CHANGE_REQUEST_SENT = "change_request_sent"
class ActionKey(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    kind: ActionKind
    record_id: str

class CompletedAction(MeridianModel):
    key: ActionKey
    kind: ActionKind
    records: dict[Literal["appointment", "slot", "old_slot", "case", "customer", "promise"], str]
    before: dict[str, str] | None = None
    after: dict[str, str] | None = None
    at: dt.datetime
    source: Literal["actions_table"] = "actions_table"

class Settled(MeridianModel):
    actions: tuple[CompletedAction, ...]
    open_case: OpenCase | None
    read_at: dt.datetime
    def current_visit(self) -> VisitView | None: ...
        # "The newest booked or moved visit with no later cancellation"; its change_request is set from the newest
        # later CHANGE_REQUEST_SENT action for the same appointment, else None.

class VisitView(MeridianModel):
    ...
    change_request: VisitChange | None
```

```python
# src/meridian/domain/state.py
class ConversationState(MeridianModel):
    thread_id: ThreadId
    settled: Settled | None = None  # decision D-9: None only before load_context's first run
    ...
```

```python
# src/meridian/domain/specialists.py
class SchedulingSlice(MeridianModel):
    """DO-4 section 5."""
    customer_zone: Zone | None
    member: bool
    appointments: tuple[AppointmentView, ...]
    shown_slots: tuple[ShownSlot, ...]
    pending_change: bool
    bookings_left: int
```

```python
# src/meridian/agent/nodes/act.py (unchanged signature)
def build_specialist_task(
    planned: PlannedTask,
    state: ConversationState,
    ctx: TurnContext,
    *,
    scheduling: SchedulingSliceInputs | None,
    limits: Limits,
) -> SpecialistTask: ...

# src/meridian/agent/nodes/plan.py (unchanged)
def build_planner_input(state: ConversationState, limits: ContextLimits) -> PlannerInput: ...
# PlannerInput.flags: StateFlags; StateFlags.pending_change: bool
```

```python
# src/meridian/policy/limits.py
class Limits:            # dataclass; Limits() gives defaults
    booking: BookingLimits
    context: ContextLimits
```

Test helpers, all existing:

```python
from tests.graph._spine_doubles import THREAD            # ThreadId("6f1c2d3e-4b5a-4c6d-8e7f-0a1b2c3d4e5f")
from tests.fakes import WORKED_PAIRS_NOW                 # tz-aware datetime
from tests.unit.agent.nodes.act_fixtures import T1, WP4_INPUTS, act_ctx, make_state, task
# T1: TurnId; WP4_INPUTS = SchedulingSliceInputs(zone="central", member=False, appointments=(WP4_APPOINTMENT,))
# WP4_APPOINTMENT.appointment_id == 1, window "12:00-16:00"
# make_state(*, turn_id=T1, text="Hello", ...) -> ConversationState with settled=Settled(actions=(), open_case=None,
#     read_at=WORKED_PAIRS_NOW) and identity verified MHC-57204
# task(order, specialist, intent, *, needs_identity=None, resumes=None) -> PlannedTask
# act_ctx(turn_id=T1, *, now=WORKED_PAIRS_NOW, thread=THREAD) -> TurnContext
```

---

## 5. Steps

Work in the item's worktree (if the orchestrator has not made one:
`git -C /home/linuxuser/workspaces/inno-aea-callcenter worktree add /home/linuxuser/workspaces/inno-aea-callcenter-wt/FU-pending-change -b fu-pending-change main`, then `export UV_LINK_MODE=hardlink` and `uv sync` there; no `node_modules`, never copy a venv).

### Step 1 — `act.py`: derive the slice flag from the stored record

Replace lines 97–99 of `src/meridian/agent/nodes/act.py` with exactly:

```python
def _has_pending_change(state: ConversationState) -> bool:
    """graph-nodes 9.5 `pending_change`, from the same stored source as the planner's `StateFlags.pending_change`
    (`plan.build_planner_input`): the current visit's filed change request (FU-pending-change). There is no
    `pending_change` state key; `settled` is the authority (D-9)."""
    visit = state.settled.current_visit() if state.settled is not None else None
    return visit is not None and visit.change_request is not None
```

Invariants this protects:
1. **Same source, same predicate as `plan.py` line 245 and 252.** Do not "simplify" it to something else (for example checking `settled.has(ActionKind.CHANGE_REQUEST_SENT)`): that would say `True` for a request on a cancelled or superseded visit, and the planner would say `False`.
2. **`settled is None` → `False`.** Only before `load_context`'s first run (D-9); never raise.
3. **No `getattr`, no new state key, no state write.** The node stays pure (R-G-12).

Line 143 (`pending_change=_has_pending_change(state),`) stays as is. Change nothing else in `act.py`. Do not add imports (none are needed).

### Step 2 — the new test file

Create `tests/unit/agent/nodes/test_pending_change.py` with these exact names. Docstring first line:
`"""SchedulingSlice.pending_change and StateFlags.pending_change share one source (FU-pending-change; WP-4, WP-4F)."""`

Module-level builders (private, in this file):

```python
LIMITS = Limits()
T0 = WORKED_PAIRS_NOW - dt.timedelta(minutes=30)
APPT = "1"          # WP4_APPOINTMENT.appointment_id
OTHER_APPT = "2"

def _key(kind: ActionKind, record: str) -> ActionKey:
    return ActionKey(thread_id=THREAD, turn_id=T1, kind=kind, record_id=record)

def _booked(appointment: str = APPT, *, at: dt.datetime = T0) -> CompletedAction:
    return CompletedAction(
        key=_key(ActionKind.BOOKED, appointment),
        kind=ActionKind.BOOKED,
        records={"appointment": appointment, "slot": "60"},
        after={
            "date": "2026-10-16",
            "window": "12:00-16:00",
            "technician": "Marta Kowalski",
            "service_type": "hvac_repair",
            "fee_line": "fee line (fixture)",
        },
        at=at,
    )

def _change_request(appointment: str = APPT, *, at: dt.datetime) -> CompletedAction:
    return CompletedAction(
        key=_key(ActionKind.CHANGE_REQUEST_SENT, appointment),
        kind=ActionKind.CHANGE_REQUEST_SENT,
        records={"appointment": appointment},
        after={"change": "move", "wanted_text": "Friday morning", "fee_line": "fee line (fixture)"},
        at=at,
    )

def _cancelled(appointment: str = APPT, *, at: dt.datetime) -> CompletedAction:
    return CompletedAction(
        key=_key(ActionKind.CANCELLED, appointment),
        kind=ActionKind.CANCELLED,
        records={"appointment": appointment},
        at=at,
    )

def _state(*actions: CompletedAction, settled: bool = True) -> ConversationState:
    base = make_state(text="Can you move it to Friday instead?")
    value = Settled(actions=actions, open_case=None, read_at=WORKED_PAIRS_NOW) if settled else None
    return base.model_copy(update={"settled": value})

def _slice_flag(state: ConversationState) -> bool:
    built = build_specialist_task(
        task(1, "scheduling", TaskIntent.RESCHEDULE), state, act_ctx(), scheduling=WP4_INPUTS, limits=LIMITS
    )
    assert isinstance(built.slice, SchedulingSlice)
    return built.slice.pending_change
```

Then a module-level case table, used by the tests' `pytest.mark.parametrize` with `ids=`:

| id | state | expected |
|---|---|---|
| `wp4_request_filed` | `_state(_booked(), _change_request(at=T0 + dt.timedelta(minutes=5)))` | `True` |
| `wp4f_booked_only` | `_state(_booked())` | `False` |
| `no_actions` | `_state()` | `False` |
| `settled_none` | `_state(settled=False)` | `False` |
| `cancelled_after_request` | `_state(_booked(), _change_request(at=T0 + 5 min), _cancelled(at=T0 + 10 min))` | `False` |
| `request_for_other_appointment` | `_state(_booked(), _change_request(OTHER_APPT, at=T0 + 5 min))` | `False` |

Build the states inside the test bodies (or via a small `_CASES: dict[str, Callable[[], ConversationState]]`), not at import time, so a validation error shows as a test failure, not a collection error.

Tests:

1. `test_wp4_filed_change_request_sets_slice_pending_change()` — the `wp4_request_filed` state; `assert _slice_flag(state) is True`. Also assert the planner side for the same state: `build_planner_input(state, LIMITS.context).flags.pending_change is True`.
2. `test_no_change_request_leaves_slice_pending_change_false(case)` — parametrized over the five `False` ids; `assert _slice_flag(state) is False`.
3. `test_planner_flag_and_specialist_slice_agree(case)` — parametrized over all six ids; `assert build_planner_input(state, LIMITS.context).flags.pending_change == _slice_flag(state) == expected`.

Imports the file needs (ruff `I` sorts them; `known-first-party = ["meridian", "tests", "eval"]`):
`datetime as dt`, `collections.abc.Callable` (if the dict form is used), `pytest`;
`meridian.agent.nodes.act.build_specialist_task`; `meridian.agent.nodes.plan.build_planner_input`;
`meridian.domain.actions.{ActionKey, ActionKind, CompletedAction, Settled}`; `meridian.domain.specialists.SchedulingSlice`;
`meridian.domain.state.ConversationState`; `meridian.domain.turn.TaskIntent`; `meridian.policy.limits.Limits`;
`tests.fakes.WORKED_PAIRS_NOW`; `tests.graph._spine_doubles.THREAD`; `tests.unit.agent.nodes.act_fixtures.{T1, WP4_INPUTS, act_ctx, make_state, task}`.

Red check before Step 1 (optional but recommended, it proves the test catches the bug): with `act.py` unchanged, `wp4_request_filed` must fail in tests 1 and 3 and every `False` case must pass.

### Step 3 — the area map

All edits are in `.claude/reference/area-map.md`. Match by content, not line number (other wave-4 items may append rows).

**3a.** Replace header line 5, which starts `> As of: 2026-10-21, reconciled with the slice plan (AEA-08)`, with exactly:

```
> As of: 2026-10-22 (FU-pending-change): one row per area; each row says which files are actual, with the commit or merge on `main`, and which are still planned. Reconciled with the slice plan (AEA-08) and DO-3 revision 3 (Stage 7 addenda and the three slice-plan deviations applied).
```

**3b.** Delete these six stale rows (each is a second or third copy of an area):
- the A6 row whose status is exactly `planned; \`policy/handoff.py\` actual (AEA-14, \`af848c9\`)` (third A6 row);
- the A6 row whose status contains `f4aa2cb` (second A6 row);
- the A11 row whose status starts `partly built: \`eval/cases/\` actual (AEA-06, branch`;
- the A7a row whose status is exactly `planned; integrated (AEA-51, 6fe5459)`;
- the A8 row whose status does **not** contain `AEA-40 (e74e3c2)` (the older A8 row);
- the A12 row whose status is exactly `planned`.

**3c.** Replace the remaining A6, A11, A7a, A8, A12 rows and the A9 row between them with the exact rows below, in this order (A6, A11, A7a, A9, A8, A12), where the first A6 row stood. Keep every other row byte-for-byte.

```
| 1 | **A6 Cases and handoff** | Cases, promises, brief assembly, demo clock and staffing, scheduler job, reset (storage is A0's `repos_cases.py`) | `policy/handoff.py`, `services/{cases,handoff,demo,scheduler,reset}.py` | AEA-14, 29, 30, 31 | built: `policy/handoff.py` actual (AEA-14, `af848c9`); `services/reset.py` actual (AEA-31, `8192d2b`), incl. the demo seed loader (seed list: stage7/cases.md §7); `services/cases.py`, `services/handoff.py` (+ `_case_rules.py`, `_case_views.py`, `_case_actions.py`) actual (AEA-29, `d3facfe`); `services/demo.py`, `services/scheduler.py` actual (AEA-30, `5f4e879`, merged `cf8fd78`; signatures stage7/cases §6; view types from `domain/views.py`, AEA-02b); FU-identity-plan (merged `1949d5a`): `CaseService.align_burning_due` (CAS-16 A) and its `policy/handoff.py` edit; FU-saveFollowUp-text (merged `0a01219`) edits `_case_actions.py`; integrated (AEA-52, merged `55d9adf`): CON-7…9 and the scheduler proven in `tests/integration/`, `tests/capture/test_cap5_clock_and_scheduler.py` |
| 1 | **A11 Eval harness** | Score the agent through its HTTP API; frozen per scored run | `eval/harness/`, `eval/cases/{dev,heldout,retrieval}/`, `eval/reports/` | AEA-06, 24 | built: `eval/cases/` actual (AEA-06, merged `e63c8fa`; held-out keys not yet written or sealed, DAT-2 B); `eval/harness/`, `eval/run_retrieval.py` actual (AEA-24, merged `7fddbf5`); `eval/reports/` written by the harness at Stage 9 |
| 2 | **A7a Graph spine** | Graph skeleton, routers, context, failure signals, load and compose; stubs of the node groups | `agent/{graph,routers,context,signals}.py`, `agent/nodes/{load_context,compose,compose_cards}.py`, stubs of `agent/nodes/{front,plan,act,reply}.py` | AEA-21, 21b, 34 | built: `agent/{graph,routers,context,signals}.py`, `nodes/compose.py` actual (AEA-21, `6df4f4c`, merged `5531664`); `nodes/load_context.py` actual (AEA-34, `8d6be78`, merged `dd31214`); the node-group stubs are replaced by `front.py` (AEA-36), `plan.py` (AEA-37), `act.py` (AEA-39), `reply.py` (AEA-38): see A7b, A7c, A7d; `nodes/compose_cards.py` actual (AEA-21b, merged `9b3824e`: card builders split out of compose.py: slot card, SLOT_TAKEN, account, appointment, where prompt, urgency questions; card-number notice deferred); integrated (AEA-51, `6fe5459`, merged `5539bca`) |
| 2 | **A9 Staff console** | Staff routes (CON-8 advance, CON-10…CON-17, CON-21 staff SSE), live takeover, staff sessions and the role check (`require_staff`, declared in `web/deps.py`), flags | `web/routes/staff_{session,cases,live,clock}.py` each with its own `web/schemas/<name>.py`; `services/{live_chat,staff}.py`; `adapters/sqlite/repos_staff.py` (body) | AEA-44, 45, 46, 47 | built: AEA-46 (0d152ee): services/live_chat.py, web/routes/staff_live.py, web/schemas/staff_live.py; AEA-47 (0d75351): web/routes/staff_clock.py, web/schemas/staff_clock.py, register_staff_clock hunk; `services/staff.py`, `adapters/sqlite/repos_staff.py` (body), `web/routes/staff_session.py`, `web/schemas/staff_session.py` actual (AEA-44, `1a8fa94`); `schema/90_staff.sql` is AEA-10's (`ff4b9bd`); AEA-45 (c6cdab6): web/routes/staff_cases.py, web/schemas/staff_cases.py, register_staff_cases hunk; integrated (AEA-52, merged `55d9adf`) |
| 2 | **A8 Customer API** | The web shell (app, middleware, dependency providers, errors, logging, frontend serving), the login, and the customer and demo routes (CON-1…CON-7, CON-8 read, CON-9, CON-22), turn, session, reset-gate and person-request services, CON-3 SSE (polls `events`); AEA-49 serves `apps/web/dist` with fallback to `index.html` (`web/frontend.py`, `register_frontend`) | `web/{app,middleware,deps,errors,logging,frontend}.py`; `web/routes/{auth,chat,events,handoff,demo}.py` each with its own `web/schemas/<name>.py`; `services/{turn,session,reset_gate,person_request}.py` | AEA-23, 40, 41, 42, 43, 49 | built: AEA-23 (merged `1e6889a`): `web/{app,middleware,deps,errors,logging}.py`, `web/routes/auth.py`, `web/schemas/auth.py`, `services/reset_gate.py`, `tests/api/openapi_check.py`; AEA-41 (merged `9806170`): `web/routes/events.py`, `web/schemas/events.py`; AEA-42 (`55b5e7c`): `web/routes/handoff.py`, `web/schemas/handoff.py`, `services/person_request.py`; FU-person-request (merged `ff6a130`) edits `services/person_request.py`; AEA-49 (`49ba7ff`): `web/frontend.py` + the `register_frontend` hunk (static mount, SPA fallback, public `/login`, `/assets/`, `/fonts/`); AEA-40 (`e74e3c2`): `services/{turn,session}.py`, `web/routes/chat.py`, `web/schemas/chat.py`, register_chat hunk; AEA-40-F1 (merged `47da752`): `services/turn.py` `answered_without_model` lets no-model gate turns (safety, danger words, burning) past the spend cap; AEA-43 (`db9ef50`): `web/routes/demo.py`, `web/schemas/demo.py` and the register_demo_routes hunk; integrated (AEA-51, `6fe5459`, merged `5539bca`) |
| 2 | **A12 Deploy** | Image build (index built here; Node build stage for `apps/web` with `docs/ux/03-structure/ui-contracts.openapi.yaml` in the build context), agent version stamp, reset command | `Dockerfile`, `.dockerignore`, `railway.json`, `scripts/{agent_version,serve,reset,image_check}.py`, `scripts/log_config.json` | AEA-50 | built: actual (AEA-50, `05395df`, merged `67c5ffe`); the host is Render since 2026-10-22, so `railway.json` is unused: service facts live in `CLAUDE.md` *Hosting* |
```

Do not change the A0, A1–A5, A7b, A7c, A7d, A10b or *Integration and journeys* rows (their remaining branch citations are out of this item's scope; §8 R-4).

**3d.** Line 8 ("**Every code path below is planned unless its row marks it actual.**") stays.

### Step 4 — gates, then commit

Run §7 in order. Commit on the item branch only, with explicit paths:

```
git add src/meridian/agent/nodes/act.py tests/unit/agent/nodes/test_pending_change.py .claude/reference/area-map.md
git commit -m "fix(FU-pending-change): specialist slice reads pending_change from settled, like the planner; one area-map row per area

<one short paragraph: the seam finding, the derive decision, the parity test, the six rows removed>

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

No push (only the merge step pushes `main`), no force push, never `git add -A`.

---

## 6. Data and fixtures

Synthetic only, no new fixture files.

- Thread and turn ids: `THREAD` (`tests/graph/_spine_doubles.py`) and `T1` (`act_fixtures.py`), both synthetic UUIDs.
- Action rows: shaped on `tests/unit/domain/test_actions.py` `_booked` / `_change_request` / `_cancelled` (AEA-02 AC-5). Appointment id `"1"` is the issued `appointments` row WP-4 uses (`WP4_APPOINTMENT.appointment_id == 1`); `"2"` is only a different id. Technician "Marta Kowalski" is the issued fixture name already used in `test_actions.py`. Fee line is the literal `"fee line (fixture)"`; wanted text `"Friday morning"`.
- Customer text: `"Can you move it to Friday instead?"`. No phone, card-like number, code or email anywhere.
- No model call, no DB, no network: `build_specialist_task` and `build_planner_input` are pure.

---

## 7. Checks

Run from the worktree root with `export UV_LINK_MODE=hardlink`. Cheapest first; stop at the first red.

| # | Check | Command | Pass looks like |
|---|---|---|---|
| G-0 (iterating) | New tests | `uv run pytest tests/unit/agent/nodes/test_pending_change.py -q` | 12 passed (1 + 5 + 6) |
| G-1 | Lint | `uv run ruff check src/meridian/agent/nodes/act.py tests/unit/agent/nodes/test_pending_change.py` | `All checks passed!` |
| G-2 | Format | `uv run ruff format --check src/meridian/agent/nodes/act.py tests/unit/agent/nodes/test_pending_change.py` | `2 files already formatted` |
| G-3 | Type check | `uv run mypy` (config `files = ["src/meridian", "tests", "eval"]`, strict) | `Success: no issues found` |
| G-4 | Affected tests | `uv run --with pytest-xdist pytest -n 2 -q tests/unit/agent/nodes tests/graph tests/contract/test_prompts_vs_consumers.py` | all pass; existing xfails stay xfail (`xfail_strict = true`) |
| G-5 | Affected journeys `[journey]` | `uv run python -m tests.journeys.affected --base main -- -n 2` (needs xdist: if `-n` is rejected, drop `-- -n 2`) | every selected journey passes; skips keep their existing reasons |
| G-6 | `getattr` gone | `grep -n "getattr" src/meridian/agent/nodes/act.py` | no output |
| G-7 | One row per area | the G-7 command in the block below | no output (on today's `main` it prints the five duplicated areas A11, A6, A12, A7a, A8) |
| G-8 | Hashes resolve on `main` | the G-8 command in the block below | no `BAD` line |
| G-9 | Context shape | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL |

G-7 and G-8 commands (copy as is; they contain pipes, so they are kept out of the table):

```bash
# G-7: no area appears twice
grep -o '^| [0-9+]* | \*\*A[0-9a-z]*' .claude/reference/area-map.md | sort | uniq -d
# G-8: every 7-character hash in the area map is on main
for h in $(grep -o '\b[0-9a-f]\{7\}\b' .claude/reference/area-map.md | sort -u); do
  git merge-base --is-ancestor "$h" main || echo "BAD $h"
done
```

**Why these tests are "affected":** `act.py` is imported by `tests/unit/agent/nodes/{test_act,test_burning_due_align,act_fixtures}.py`, `tests/graph/_spine_doubles.py` (so all of `tests/graph/`), `tests/contract/_prompts_malformed.py` (used by `test_prompts_vs_consumers.py`) and `tests/journeys/j{3,4}/test_aea_39.py` (covered by G-5). The plan-node tests (`test_plan.py`, `test_join_plan.py`, `test_plan_graph.py`) are in `tests/unit/agent/nodes`.

**No full suite.** `act.py` is not a shared fixture, setting, dependency or module imported across the codebase, and this is not a cross-package seam fix (rule `build-loop-test-scope`, *The full suite runs only in two places*).

**Evidence for the report:** the G-0…G-9 outputs (counts only), the commit SHA, and a journey line in the item note: claim "J-4 and the affected journeys stay green after FU-pending-change", level per file (J-4 `test_aea_39` mock-tested; `test_aea_51` integrated with a scripted model), blocked by "the scripted model ignores the slice; observable only in a live run (AEA-61, gate::paid)". No record file is required for an unchanged journey; if the orchestrator wants one, it goes in `docs/testing/journeys/2026-10-22-FU-pending-change.md` in the §4 format.

---

## 8. Risks and requests

- **R-1 (design-doc drift, request to the integrator, not done here).** DO-3 §5.2 (`code-design.md` line 475) and graph-nodes §9.5 / `FactsUpdate` still describe a `pending_change: ChangeRequestRef | None` state key written by `facts`. After this item both nodes derive the flag from `settled`, so the key is redundant. Request: mark it in DO-3 §5 as "derived from `settled.current_visit().change_request` (FU-pending-change); no state key", with a `Changed at merge` note. `docs/design/` is not owned here. This is not a signed UI contract (DO-4 `bool` fields are unchanged), so it is not a NEEDS-DECISION.
- **R-2 (`DURABLE_KEYS`).** `agent/graph.py` (A7a, not owned) keeps `"pending_change"` in `DURABLE_KEYS`. Harmless: its comment already says the key "may be absent from the model today", and `test_load_context.py` line 434 only asserts `load_context` does not write it. Request to the integrator: drop it together with R-1, or leave it. Do not edit `graph.py` here.
- **R-3 (deferred seam).** The cleanest single source would be a method on `Settled` (A0, `domain/actions.py`), for example `Settled.has_pending_change() -> bool`, called by both nodes. Deferred: A0 is not owned, and the parity test already pins the two nodes together. Cut it only if a third reader appears.
- **R-4 (area map, out of scope).** Other rows still cite branches rather than `main` hashes: A0 (AEA-02b, AEA-35b, AEA-03b, FU-saveFollowUp-text text), the *Integration and journeys* row (AEA-59, AEA-51 pass 1). Merges exist on `main` for each (`5305d57`, `3725c90`, `19e046b`, `0a01219`, `cf74674`, `5539bca`). Left for the next context-upkeep pass so this item's diff stays on the five rows the finding names.
- **R-5 (collision).** `.claude/reference/area-map.md` is an append-style shared context file; another wave-4 item may change it. Per the batch-merge rule, a conflict confined to it is resolved by keeping both sides' rows, then re-running G-7 and G-8. `act.py` was last changed by FU-identity-plan (`1949d5a`, `_align_burning_due`); Step 1 touches only lines 97–99, away from that code.
- **R-6 (behaviour change the specialist now sees).** With `pending_change=True` the scheduling specialist's prompt may now steer toward "a request is already with staff" instead of filing a second one. That is the intended effect; the scripted journeys cannot show it, and no live run is part of this item (AC-7 *Blocked by*).

### What the implementer must not do

- Do not add a `pending_change` field to `ConversationState`, write any state key from `act.py`, or edit `domain/*`, `graph.py`, `reply.py` or `plan.py`.
- Do not import `plan.py` from `act.py` (cross-area import, DO-3 §8). The test file may import both.
- Do not edit `tests/unit/agent/nodes/test_act.py` (over the size cap) or any journey file.
- Do not change the predicate to `settled.has(ActionKind.CHANGE_REQUEST_SENT)` or anything that disagrees with `current_visit()`.
- Do not edit design docs, `CLAUDE.md`, `.claude/state/*`, `docs/ux/**`, `apps/web/**` or the OpenAPI file.
- Do not run the full suite, push, force-push, or `git add -A`.

---

## 9. Readiness

**READY.** No blocker: every import exists on `main` `8669ed0`. No product decision is needed, and no signed contract changes. Owned files: `src/meridian/agent/nodes/act.py`, `tests/unit/agent/nodes/test_pending_change.py` (new), `.claude/reference/area-map.md`.
