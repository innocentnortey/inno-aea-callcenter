## [AEA-34] graph: load-context node

_Conventions for every inno-aea-callcenter issue (from the approved breakdown, `docs/plans/slice-plan.md`):_
repository `/home/linuxuser/workspaces/inno-aea-callcenter` (package `src/meridian/`, tests `tests/`, eval `eval/`); GitLab
`innocentnortey/inno-aea-callcenter`. Read first: `CLAUDE.md`, `.claude/README.md`, `.claude/reference/area-map.md`, the
slice plan's row for this issue, `docs/design/code-design.md` (DO-3) and `docs/design/contracts/internal-components.md`
(DO-4: exact types and signatures). Vocabulary: PRD R-n, US-n, WP-n, HP-n, WF-n, CAP-n, E-n, M-n, CON-n as their owner
documents define them. Workflow: `lane::build-loop` issues run plan (`fanout-planner`, plan meets
`to-tickets/templates/implementation-plan.md`) → implement (`fanout-implementer`) → test → `code-review-agent`; affected tests
only (`.claude/rules/build-loop-test-scope.md`); `risk::security` issues get frozen failing tests first and the security
agent at their wave merge. **Siblings in the same or a later wave are called through their DO-4 signature by injection
(constructor, `GraphDeps`, or `web/deps.py`) and tested with a double; a plan that needs more than that signature records
`blocked-on AEA-NN` instead of inventing behaviour.** Never: edit the briefing, issued data or `docs/archive/`; edit
`docs/ux/03-structure/ui-contracts.openapi.yaml` or `UI_CONTRACTS.md` (a needed change stops the issue and goes to
Innocent); touch `apps/web/**` or `docs/ux/**`; edit another issue's owned file (collision map, slice plan §3); put a
secret, verification code, card-like number or full phone number in code, logs, traces, fixtures or test names; call a
paid model in a default test (mark `live`); bind ports 4019 or 5184; `git add -A`. Evidence: every criterion names its
test or command and the result a reviewer should see; numbers come from runs, never from targets.

### What to build

> **US-17:** As a **homeowner** mid-booking, I need "what about Monday?" to apply to the visit we were just arranging, so
> that I don't start over every message. Acceptance: … a 20-turn chat keeps my verified identity and the open task; a
> safety phrase mid-chat still comes first.

**`agent/nodes/load_context.py`**, the first node of every turn (DO-3 §5.4: `invoke → load_context → gates`). It replaces
AEA-21's stub in place with exactly the signature of `docs/design/contracts/stage7/graph-nodes.md` §9.2:

`load_context(state, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> LoadContextUpdate`

Every turn it rebuilds, **from the database**, the DB-authority keys it alone writes at turn start (DO-3 §5.3), inside
**one read-only** `deps.uow()` that closes before the node returns (no model call runs while it is open; DO-3 §2.3 rule 1):

- `settled: Settled` = `tx.core.settled_for(ctx.ids.thread_id, ctx.now)`, the one builder of `Settled` from `actions` and
  the open case and its promise (graph-core §6, GRC-12; DO-4 §1). `ctx.now` is the turn's one demo-clock reading. Never
  built from model text or from the checkpoint; the incoming checkpoint's `settled` is replaced, not merged.
- `controller: Controller` from `tx.core.conversations.lookup(thread_id)`, the authority for who is replying (code-design
  C-7): `kind` `ai` or `human`, and while a person owns the chat the representative's name and case reference as the
  live-chat service writes them on join (staff.md §5 table; invariant `controller = human` exactly when live state is
  `joined`).
- `identity: IdentityState` = `tx.core.reads.identity_state(thread_id)` (GRC-8; cases.md §1.2; derived from
  `identity_threads` and the newest `identity_codes` row as graph-tools §5 states), so code expiry and tries are re-read
  before use (R-45: "Facts that go stale are re-read before use"). No `IdentityService` method is added or called.
- `chat_window: list[ChatLine]` built from `tx.core.messages.recent(thread_id, turns=deps.limits.context.window_turns)`
  with `Limits.context` (graph-core §7, GRC-9, GRC-14; all [A]): the lines of the last 10 turn ids plus representative
  and event lines (turn id None) since the oldest kept turn, oldest first; each line cut to 600 characters with "…"; then
  the oldest lines dropped until the total is at most 8,000 characters. Rows are used as stored (customer text already
  STORE-redacted at intake: `[code entered]`, `[card number removed]`, `[code]`; data.md §1), speakers `customer`,
  `assistant`, `representative`, `event`. Never tool output (R-45): `lookup_log` is not read.
- `counters`: only `timeouts` changes, copied from `tx.core.turns.timeouts_for(thread_id)`, because a timed-out turn never
  reaches the facts node (graph-core §8, GRC-13); every other `FailureCounters` field is returned as the state holds it.

The node returns only those keys (`LoadContextUpdate`: `settled`, `controller`, `identity`, `chat_window`, `counters`),
writes nothing to `check_events` (its reducer resets per turn, graph-core §11), holds no business rule, makes no model or
service call and never calls `TraceSink`: its timed span comes from AEA-21's `timed_node` wrapper (GRC-6). The checkpoint
stays the authority for open tasks, shown slots, last lookups, pending change and the other counters; this node does
not touch them. The responder (AEA-38) and planner (AEA-37) render from `chat_window` and never re-read `messages`.

Produces the per-turn state every later node reads (gates AEA-36, plan AEA-37, act AEA-39, reply AEA-38, compose AEA-21),
proven through the compiled graph at AEA-51.

**Example pair (WP-4F, the SP-1 state seam).** Input: turn 3 of the fee-free reschedule: the customer picked Mon Oct 19
8–12; the scheduling service committed the move and its `actions(moved)` row, then the process died before the
checkpoint was written. Turn 4: "Great, so I'm all set for Monday?" → `load_context` returns `settled.actions` including
the `moved` action with `after = {"date": "2026-10-19", "window": "08:00-12:00", …}` and `settled.current_visit()` is the
Monday visit (graph-core §14), so the responder can confirm it (SP-1 failure: "the move happened but the next turn's
responder said it had not", DO-5 *Failure categories* "State seam").

### Source

- `docs/design/contracts/stage7/graph-nodes.md` §9.1 (`LoadContextUpdate`), §9.2 (signature and reads); `stage7/graph-core.md`
  §4 (`GraphDeps`, `timed_node`), §6 (`settled_for`), §7 (`ContextLimits`), §8 (`FailureCounters.timeouts`), §11
  (`check_events` reducer), §14 (`VisitView`, `current_visit`); `stage7/cases.md` §1.2 (`conversations.lookup`,
  `reads.identity_state`, `messages.recent`, `turns.timeouts_for`); `stage7/graph-tools.md` §5 (how `IdentityState` is
  derived); `stage7/staff.md` §5 (controller writes); `stage7/data.md` §1 (STORE placeholders); DO-4 §1 (`Settled`,
  `OpenCase`, `Controller`, `IdentityState`, `ChatLine`), §16.
- Decisions: `docs/plans/7b-decisions/graph-core.md` GRC-6, GRC-8, GRC-9, GRC-12, GRC-13, GRC-14; `graph-nodes.md` GRN-11.
- DO-3 §5.1 (what the DB is the authority for), §5.2, §5.3 (who writes which key), §5.4, §2.3 rule 1, §10 C-7.
- PRD R-45 (typed durable state; window about 10 [A]; stale facts re-read; tool output never in chat history); system
  design §9 (*Write order across the two files*), §A.3.
- Workspace rule `context-management-multi-turn.md` rules 1, 2, 4, 6; project rule `agent-architecture.md` rule 12.
- DO-5 *Failure categories* (State seam); DO-6 WF-1; US-17; WP-4F; HP-1.
- Router rows: area map A7a Graph spine; ICM progress row *Routes verified against code and tests*.
- **Brief check:** serves "Handle the full flow: the caller asks for an appointment, the agent checks availability, and
  either confirms the booking or offers alternatives." (the confirmation must reflect what was written); touches nothing
  out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `settled` is rebuilt from the database every turn: WP-4F's `moved` action committed with no checkpoint update appears in the next turn's `settled.actions` and `settled.current_visit()` is the Monday 08:00-12:00 visit; a stale `settled` carried in the incoming state (with an extra action the DB lacks) is replaced, never merged; `read_at` equals `ctx.now` — verify: `tests/unit/agent/nodes/test_load_context.py::test_action_without_checkpoint_is_seen` and `::test_stale_checkpoint_settled_replaced` (AEA-10's `temp_sqlite()`) — evidence: the `moved` action present; the stale copy's extra action absent; `read_at` equal.
- [ ] AC-2 [invariant] `settled.open_case` reflects the thread's open case and its stored promise (reason, priority, state, promise text, follow-up, `live_queued`) and is None for a thread with no open case — verify: `test_load_context.py::test_open_case_from_rows` — evidence: fields equal the seeded rows; None for a clean thread.
- [ ] AC-3 [invariant] `controller` follows the `conversations` row each turn: a representative joining between turns (row changed outside a graph run, as AEA-46 writes it) gives `kind = "human"` with the name and case reference on the next turn while the checkpoint still says `ai`; a hand-back gives `kind = "ai"` with no name — verify: `test_load_context.py::test_controller_from_conversation_row` — evidence: values follow the row, not the checkpoint.
- [ ] AC-4 [invariant] `identity` is re-read through `core.reads.identity_state` every turn: a verified status with its `customer_id` survives turns 1 → 20; a `code_sent` row whose `expires_at` has passed on the demo clock shows the stored `code_expires_at` before `ctx.now`, and `tries_left` / `codes_sent` follow the newest code row — verify: `test_load_context.py::test_identity_kept_over_twenty_turns` and `::test_identity_reread_with_expiry` — evidence: `status = verified`, same `customer_id` at turn 20; expiry and counts equal the rows.
- [ ] AC-5 [invariant] `chat_window` applies `Limits.context` (GRC-9, GRC-14): at turn 20 it holds the lines of the last 10 turn ids plus representative and event lines since the oldest kept turn, oldest first, turn 1's line absent; a 900-character stored reply is cut to 600 characters ending "…"; when the lines exceed 8,000 characters the oldest are dropped until it fits; the limits are read from `deps.limits.context`, never a literal in the node — verify: `test_load_context.py::test_window_limits` (a `Limits` with smaller values proves the node reads them) — evidence: line count, cut length and total within the configured bounds in both runs.
- [ ] AC-6 [negative] Tool output and secrets never enter `chat_window`: a seeded `lookup_log` row with a distinctive snapshot string, a code turn stored as `[code entered]`, a free-text message stored with `[code]` and one stored with `[card number removed]` → the snapshot string is absent, and no 6-digit run and no 13–19-digit run appears in any `ChatLine.text`; the synthetic code and card number are generated in the test and only their redacted forms are seeded — verify: `test_load_context.py::test_window_has_no_tool_output_or_codes` — evidence: every assertion passes.
- [ ] AC-7 [invariant] `counters.timeouts` equals `core.turns.timeouts_for(thread_id)` (two seeded timed-out turns → 2) and every other `FailureCounters` field comes back unchanged from the incoming state — verify: `test_load_context.py::test_only_timeouts_counter_copied` — evidence: `timeouts = 2`; the other five fields equal the input.
- [ ] AC-8 [invariant] Key ownership and transaction scope: the returned dict's keys are a subset of `LoadContextUpdate` (`settled`, `controller`, `identity`, `chat_window`, `counters`; never `check_events`, `gate`, `open_tasks`, `shown_slots`, `last_lookups`, `pending_change`); the node opens exactly one read-only unit of work and it is closed before the node returns; the node calls no gateway, service or `TraceSink` method — verify: `test_load_context.py::test_returns_only_its_keys` and `::test_one_read_only_uow_closed_before_return` (recording `UnitOfWorkFactory`, gateway and sink doubles) — evidence: key set as stated; one enter/exit pair with `write=False`; zero gateway, service and sink calls.
- [ ] AC-9 [capture] Registered through AEA-21's `timed_node("load_context", …)` with AEA-11's `InMemoryTraceSink`, one node span named `load_context` with `elapsed_ms` and status `ok` is recorded per turn, and its attributes hold no message text (a sentinel phrase in a seeded customer message is absent from the span) — verify: `test_load_context.py::test_node_span_via_timed_node` — evidence: one span, status `ok`, sentinel absent. (CAP-1 at the real CON-2 entry point is AEA-51's.)
- [ ] AC-10 [journey] Extends J-3 (slice plan §0a journey map; backend-amendments §3): the follow-up turn after a booking loads the completed action, controller and identity from the working copy, and its reply names the new window; asserting what the user sees and what is stored, in `tests/journeys/j3/test_aea_34.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j3/test_aea_34.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-51 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-34.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-51 (`integrated-journeys.md` §4).
- [ ] AC-11 [regression/context] Docs updated in the same change — verify: `git diff --name-only` — evidence: `.claude/reference/area-map.md` A7a row (`agent/nodes/load_context.py` stub → actual with the commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §3 `nodes/load_context.py` status planned → built, all three in the diff with only this ticket's rows changed.

### Observability

- Responsibilities (WF-1): the node writes no rows, no check events and no signals; its timed span (name, timing, status,
  no text) comes from AEA-21's `timed_node` wrapper, which this ticket must not bypass or duplicate (GRC-6; DO-6
  *Content and redaction*: traces hold IDs, timings, counts). It preserves what WF-1's later records depend on: `settled`
  from `actions` rows (each carrying its `ActionKey`), the controller, the identity state and the timeouts counter.
- Capture evidence: AC-9 with the in-memory sink; CAP-1 at the real CON-2 entry point is AEA-51's.

### Evaluation

- Checks: E-1 and E-3 trajectory and hard-gate items that depend on cross-turn facts — WP-4F (the move carried to the next
  turn), the 20-turn identity-and-task check (R-45 acceptance), R-46's completion check reading `settled`; a miss here is
  filed under DO-5's failure category "State seam".
- Expected-answer authority: the `actions` and `cases`/`promises` rows (DB authority, DO-3 §5.1); WP-4F's case checklist
  written from the KB and DB (DO-5 *Expected-answer authority*).

### Metrics

- References: M-21 action-rule violations (the "no completion claim without a write" rule reads `settled`); M-2 north star
  on the dev split (state-seam failures lower it); M-24 tool and model failure rate (the `timeouts` counter feeds
  escalation rule 7, not the metric, which reads `turn.degrade_reason`).
- Acceptance conditions: M-21 stays computable because `settled` is built only from `actions` rows that carry their
  `ActionKey` (thread, turn, kind, record); M-2 and M-24 are read from eval results and turn rows this node does not
  write. No target is set here.

### Blocked by

AEA-10 (`settled_for`, `conversations.lookup`, `reads.identity_state`, `messages.recent`, `turns.timeouts_for`,
`temp_sqlite()`), AEA-21 (graph spine, `GraphDeps`, the `load_context` stub and `timed_node`). The `[journey]` AC-10's
integrated level only (not this ticket's merge): AEA-57 (harness) and AEA-51 (lands J-3, wave 3).

### Agent handoff

- Area / owner: A7a Graph spine; owns `src/meridian/agent/nodes/load_context.py` (replacing AEA-21's stub in place) and
  `tests/unit/agent/nodes/test_load_context.py`.
- Contracts and shared surfaces: consumes `ConversationState`, `LoadContextUpdate`, `Settled`, `Controller`,
  `IdentityState`, `ChatLine`, `FailureCounters`, `TurnContext` (AEA-02); `GraphDeps.uow` and `GraphDeps.limits` with the
  repository reads above (AEA-10) and `Limits.context` (AEA-01); `timed_node` (AEA-21); `InMemoryTraceSink` (AEA-11).
  Produces the DB-authority keys for AEA-36, 37, 38, 39 and AEA-21's compose; proven end to end at AEA-51. Must not edit
  `agent/{graph,routers,context}.py`, other node files, `domain/*`, `policy/limits.py` or any repository.
- Scope boundary / refusal: no gate, routing, model call, service call or write; never builds `settled` from model text or
  the checkpoint; never puts tool output, codes or card-like numbers in `chat_window`; never touches checkpoint-authority
  keys (open tasks, shown slots, counters other than `timeouts`); adds no `IdentityService` method (GRC-8).
- Evidence level (`.claude/rules/integrated-journeys.md` §4): the node tests are `mock-tested`; the J-3 journey step
  (AC-10) records `mock-tested` and `Blocked by: AEA-57, AEA-51` until both merge.
- Wave and gates: wave 2; no human or external gate.
- Lane: build-loop — changes source and tests (ticket-lanes).
- Risk: None (slice plan row: no `risk::security`; it reads stored, already-redacted rows only).
- Entry points added or changed: None
