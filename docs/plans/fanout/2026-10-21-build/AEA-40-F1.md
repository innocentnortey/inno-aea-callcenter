# Plan: [AEA-40-F1] safety turn still answered at the spend cap

**Status:** planned (READY)
**Issue:** none (wave-fix item cut from AEA-51 plan §8 R-14) · **Base revision:** `main` at `9d12b8f`
**Lane:** `lane::build-loop` (changes `src/`). **Not** `risk::security`: no auth, secret, PII or network surface; the
safety path it re-opens is fixed text with no model call. No test-writer, no security review.
**Planner model:** claude-opus-5-5. **Implementer:** Sonnet, from this file alone.

## 1. Goal and sources

**What it delivers.** Today, once our $30/day cap is reached, a customer who types *"My carbon monoxide detector is
going off."* gets *"I can't answer more questions right now. A person can pick this up."* instead of the fixed DANGER
card and a P0 case. After this fix:

- a turn that the deterministic gates answer with **no model call** (safety words, danger words, the burning question,
  a "yes" or "not sure" on the burning card) runs as normal at the cap: fixed safety text, its case, zero model calls;
- every other turn at the cap still gets `SPEND_CAP_REACHED`, with no graph call and no model call (unchanged).

**Why it happens.** `src/meridian/services/turn.py` `TurnService._run` (line 317) calls `self._spend.allow_turn()`
(line 318) **before** `parse_intake(cmd.payload)` (line 322), so the gate never sees the message.

**Sources (exact):**

| Source | Where | What it says |
|---|---|---|
| AEA-51 plan | `docs/plans/fanout/2026-10-21-build/AEA-51.md` §8 row **R-14**, refresh 4 item 4, AC-24 row | Cut AEA-40-F1: "at our cap, a message the deterministic safety gate catches (CO alarm, gas, smoke words; R-6) still gets the WP-5 instruction and its P0 case, with no model call; every other message keeps `SPEND_CAP_REACHED`. The mechanism is F1's planner's to choose." |
| DO-4 §11 | `docs/design/contracts/internal-components.md` §11, table row "Our $30/day cap reached" | `degraded_handoff` / `spend_cap`; notice `SPEND_CAP_REACHED` + person key; **"safety and CON-4 still work"** |
| DO-4 §14 / stage7 web.md §9 | `internal-components.md` §14 `TurnService.run_turn`; `docs/design/contracts/stage7/web.md` ("Settled elsewhere and carried by `run_turn`…": "admission checks `ledger.allow_turn()` only"; "Step 4 runs `parse_intake` once") | The step order this fix reorders (see §3 reconciliation). `parse_intake` still runs exactly once |
| AEA-40 plan | `docs/plans/fanout/2026-10-21-build/AEA-40.md` (~line 108) | Order (1) admission (2) `spend.allow_turn()` (3) `turns.begin` (4) `parse_intake` …; "`TurnService` never reads `ConversationState`" (kept) |
| Gate order | `src/meridian/gates/gate.py` `decide_gate`; `src/meridian/agent/routers.py` `route_after_gates` | SAFETY, BURNING_ASK, DANGER_RULE and BURNING_ANSWER yes/unsure route to `safety` → `compose` → END: no model node on that path (`agent/graph.py` edges) |

## 2. Boundary

**Owned files (the only files the implementer may create or edit):**

| File | Action | Size now → cap |
|---|---|---|
| `src/meridian/services/turn.py` | modify | 563 → about 585 (service cap 600) |
| `tests/services/test_turn_spend_cap.py` | **create** | about 170 (test cap 500). A new file because `tests/services/test_turn.py` is already 684 lines |
| `tests/journeys/j5/test_aea_40.py` | **create** | about 130. Name is forced by `tests/journeys/support/steps.py::convention_violations` (`test_aea_<NN>.py` only; `test_aea_40_f1.py` would fail `tests/journeys/support/test_support.py`) |

**Read only (never edit):** `src/meridian/gates/gate.py`, `src/meridian/gates/rules.py`, `src/meridian/domain/turn.py`,
`src/meridian/domain/blocks.py`, `src/meridian/policy/texts.py`, `src/meridian/services/ledger.py`,
`src/meridian/web/container.py`, `src/meridian/agent/**`, `tests/services/test_turn.py`,
`tests/services/chat_doubles.py`, `tests/services/chat_storage.py`, `tests/journeys/support/**`,
`tests/journeys/j5/test_aea_36.py`, `tests/journeys/j9/test_aea_26.py`, `tests/journeys/j9/test_aea_40.py`.

**Owned by others, do not touch:** `tests/integration/test_customer_failures.py` and its
`test_spend_cap_safety_still_answered` (AEA-51; not on `main`; AEA-51 un-skips it after this lands), every file on the
`aea-51-aea-51-customer-path` branch (checked: it does not touch `services/turn.py`, `tests/services/` or
`tests/journeys/j5/`), `docs/**`, `apps/web/**`, the OpenAPI and UI contracts, `.claude/**`.

## 3. Requirements table (source reconciliation)

| # | Requirement / obligation | Source | Disposition | How implemented | How verified |
|---|---|---|---|---|---|
| F1-1 | At our cap, a safety turn (WP-5 CO alarm) gets the fixed DANGER card, `notice = None`, outcome `safety_reply`, **zero model calls**, and is never refused | R-14; DO-4 §11 | in-ticket | Step 2–3: `answered_without_model(intake)` checked before `allow_turn()` | `tests/services/test_turn_spend_cap.py::test_safety_turn_at_cap_answered_without_model` |
| F1-2 | At our cap, a normal turn still returns `SPEND_CAP_REACHED` with the person key, no graph call, no model call, no stored customer message; turn row `failed / degraded_handoff / spend_cap` | R-14; DO-4 §11; AEA-40 AC-5 | in-ticket | Unchanged `_reject` path | `::test_normal_turn_at_cap_still_refused`; existing `tests/services/test_turn.py::test_spend_cap_notice_no_model` stays green |
| F1-3 | Exactly which turns skip the cap: gate kinds whose graph path has no model node, decided **without** conversation state | R-14 ("mechanism is F1's planner's"); AEA-40 plan ("never reads `ConversationState`") | added (plan decision D1) | `_NO_MODEL_GATES` + stateless `GateFlags` | `::test_answered_without_model_table` (8 rows) |
| F1-4 | Danger words (R8, e.g. "can't breathe") are answered at the cap too | R-14 "danger or safety turn"; graph-core §3 | added | `GateKind.DANGER_RULE` in the set | table row 3 |
| F1-5 | A refused turn stores nothing from the customer | AEA-40 AC-5 (`customer_messages == []`) | in-ticket | `parse_intake` is pure (no I/O, no log, no clock: `gate.py` docstring), so moving it first stores nothing | F1-2 test asserts `customer_messages(store, thread) == []` |
| F1-6 | `parse_intake` runs once per turn | web.md §9 "Step 4 runs `parse_intake` once" | in-ticket | Moved, not duplicated; T1 keeps using the same `intake` | code review; existing `test_intake_redacted_and_never_in_turn_input` stays green |
| F1-7 | No unit of work open across `run_graph` | DO-3 §2.3 rule 1 | n/a (unchanged) | No change to T1/T2 | existing `test_no_uow_open_during_run_graph` |
| F1-8 | Step order of DO-4 §14 / AEA-40 plan: `allow_turn()` (2) before `parse_intake` (4) | DO-4 §14; web.md §9 | reconciled: the orchestrator cut F1 citing DO-4 §11 as the governing line, so §11's "safety still works" wins over §14's ordering. No response shape, notice code, OpenAPI field or UI contract changes; nothing signed is edited | `_run` order becomes: parse → (skip cap if no-model gate) → cap → begin… | this plan; reviewer checks no `docs/` diff |
| F1-9 | CON-4 (person key) still works at the cap | DO-4 §11 | other-ticket: the person-request route is AEA-42's and does not pass through `TurnService._run`; AEA-51 AC-24 owns the CON-4 half | none here | AEA-51 `test_spend_caps` |
| F1-10 | `[journey]` J-5 at the cap: the WP-5 message gets the safety card first and one P0 case with no model call; a normal message after it gets `SPEND_CAP_REACHED` (J-9 leg) | integrated-journeys rule §3 rule 5 ("every bug fix … adds a test that protects the intended success") | added | `tests/journeys/j5/test_aea_40.py::test_j5_co_alarm_at_spend_cap_still_gets_safety_card` | Level target **integrated with a scripted model**. Today its turn steps report `blocked` (owner AEA-51: `run_graph`, `reply_composer` not bound on `main`) and pytest-skip; they run when AEA-51 merges |

**Entry-point registration:** None. CON-2 (`submitTurn`) keeps its route, response model and WF row; no new entry point.

## 4. Shared code to use (copied from `main` at `9d12b8f`)

```python
# src/meridian/gates/gate.py  (pure; no I/O)
def parse_intake(payload: TurnPayload) -> Intake: ...
def decide_gate(intake: Intake, flags: GateFlags) -> GateDecision: ...
GATE_ORDER_HEAD: tuple[GateKind, GateKind] = (GateKind.SAFETY, GateKind.AI_PAUSED)

# src/meridian/domain/turn.py
class Intake(MeridianModel):
    kind: Literal["text", "choice", "code", "form"]
    text_store: str
    code_digits: SecretStr | None
    form: FormValues | None
    card_number_seen: bool
    choice: CardChoice | None
    card_id: str | None = None

class GateKind(StrEnum):
    AI_PAUSED = "ai_paused"; SAFETY = "safety"; BURNING_ASK = "burning_ask"; BURNING_ANSWER = "burning_answer"
    DANGER_RULE = "danger_rule"; PERSON = "person"; CODE_ENTRY = "code_entry"; LOCATE = "locate"
    CARD_CHOICE = "card_choice"; FREE_TEXT = "free_text"

class GateFlags(MeridianModel):
    ai_paused: bool
    burning_card_id: str | None
    code_card_open: bool
    open_task_ids: tuple[str, ...]

class GateDecision(MeridianModel):
    kind: GateKind
    rules: RuleMatches
    burning_answer: Literal["yes", "no", "unsure"] | None = None
    resume_task_id: str | None = None

class TextPayload(MeridianModel):   kind: Literal["text"] = "text"; text: str  (1..2000 chars)
class CardChoice(MeridianModel):    card_id: str; option: str
class ChoicePayload(CardChoice):    kind: Literal["choice"] = "choice"

class TurnTrace(MeridianModel):
    gate_result: GateResult; path: TurnPath; outcome: TurnOutcome
    degrade_reason: DegradeReason | None = None; planner: PlannerTrace | None = None
    danger_raised: bool = False; specialists_run: tuple[SpecialistKind, ...] = ()
class ComposedReply(MeridianModel):
    blocks: tuple[ReplyBlock, ...]; settled_view: SettledView; writes: tuple[CompletedAction, ...]
    notice: Notice | None; path: TurnPath; outcome: TurnOutcome; degrade_reason: DegradeReason | None
class GraphOutcome(MeridianModel):
    reply: ComposedReply; turn_trace: TurnTrace; check_events: tuple[CheckEvent, ...] = ()
    halt: Halt | None = None; closed_every_open_task: bool = False
# TurnPath includes "safety"; GateResult includes "safety"; TurnOutcome includes "safety_reply".

# src/meridian/domain/blocks.py
class BlockBase(MeridianModel): block_id: str; speaker: Speaker; at: dt.datetime
class CallKey(MeridianModel): label: str; number: str
class SafetyBlock(BlockBase):
    type: Literal["safety"] = "safety"; level: Literal["DANGER"] = "DANGER"
    signal_word: str; steps: tuple[str, ...]; call_key: CallKey; contact_line: str
    case_priority: Literal["P0"] = "P0"; case_reference: str | None
    fixed_text: Literal[True] = True; pinned: Literal[True] = True

# src/meridian/policy/texts.py
TEXTS: Final[Mapping[TextId, str]]   # TextId.SAFETY_LEAVE_NOW, SAFETY_DONT_TOUCH, SAFETY_CONTACT_LINE

# src/meridian/services/ledger.py
class SpendGuard(Protocol):
    def allow_turn(self) -> bool: ...
class LedgerService:
    def record(self, call: CallRecord, ids: TurnIds) -> None: ...
    def allow_turn(self) -> bool: ...          # spend_today() < daily_cap_usd

# src/meridian/web/container.py
class Container: def get[T](self, key: Key[T]) -> T; limits -> Limits (property)   # Key("ledger") is LedgerService

# tests/services/chat_doubles.py (import, do not edit)
ASSISTANT_SPEAKER; FakeSpendGuard(allow: bool = True)  # .allow, .calls
ScriptedRunGraph(*items)   # items: GraphOutcome | Callable[[TurnInput, TurnContext], GraphOutcome]; .calls: list[Call]
Call(turn_input, context, input_json); empty_view() -> SettledView
make_cmd(thread_id, payload: dict, *, turn_id=None, ...) -> RunTurn
make_turn_service(store, *, run_graph=None, spend=None, ...) -> TurnService
text_payload(text) -> dict; choice_payload(card_id, option) -> dict

# tests/services/chat_storage.py (import, do not edit)
seed_thread(uow, demo_session=DEMO_SESSION, *, ...) -> ThreadId
turn_row(store, turn_id) -> TurnRow | None    # .status .gate_result .path .outcome .degrade_reason .model_calls
customer_messages(store, thread_id, turn_id=None) -> list; messages_of(store, thread_id) -> list (.role, .turn_id)
conversation(store, thread_id) -> ConversationRow (.outcome); count_rows(store, table, where="1=1", params=())
notice_codes(blocks) -> list[str]; has_person_key(blocks) -> bool

# tests/fixtures/sqlite.py
temp_sqlite() -> ContextManager[TempStore]
```

## 5. Steps

**D1 (decision made here, F1-3).** The cap is skipped exactly when `decide_gate(intake, <stateless flags>)` returns
`SAFETY`, `DANGER_RULE` or `BURNING_ASK`, or `BURNING_ANSWER` with `burning_answer` in `("yes", "unsure")`. Why:
those are the kinds `route_after_gates` sends to `safety` → `compose` → END, a path with no model node. Stateless flags
(`ai_paused=False`, no burning card, no code card, no open tasks) keep the AEA-40 rule that `TurnService` never reads
`ConversationState`; SAFETY is checked before AI_PAUSED (D-14, `GATE_ORDER_HEAD`), so the safety row is correct for
every conversation. A burning-card "no" is excluded: it plans a booking, which needs the specialist model.

**D2.** A turn that skips the cap never calls `allow_turn()` at all (`and` short-circuits). So a safety turn is answered
even if the ledger read fails. Test F1-1 asserts `guard.calls == 0`.

**D3.** The predicate is a public module-level pure function `answered_without_model(intake: Intake) -> bool` in
`services/turn.py`, beside `next_outcome` and `reopened_outcome` (same style: pure, unit-tested directly). No new
module, no change to `gates/` (not owned; DO-3 already lets `services/` import `gates/`, as `parse_intake` does).

Build order:

1. **Worktree.** Work in the orchestrator's worktree for AEA-40-F1 (if none was given:
   `git -C /home/linuxuser/workspaces/inno-aea-callcenter worktree add ../inno-aea-callcenter-wt/AEA-40-F1 -b aea-40-f1-safety-at-cap main`).
   `export UV_LINK_MODE=hardlink`. No baseline suite; an import check is enough:
   `uv run python -c "import meridian.services.turn"`.

2. **Reproduce first** (integrated-journeys rule §3 rule 5): write `tests/services/test_turn_spend_cap.py` (Step 5's
   content) and run `uv run pytest tests/services/test_turn_spend_cap.py -q`. Expected **red** before the fix:
   `test_safety_turn_at_cap_answered_without_model` fails (the notice is `SPEND_CAP_REACHED`) and the table test fails
   on import (`answered_without_model` missing). Note both in the report.

3. **Edit `src/meridian/services/turn.py`:**
   1. Imports: add `GateFlags`, `GateKind`, `Intake` to the existing `from meridian.domain.turn import (...)` block
      (keep it sorted, ruff `I`); change `from meridian.gates.gate import parse_intake` to
      `from meridian.gates.gate import decide_gate, parse_intake`.
   2. After `_NOTICE_TEXT`, add:
      ```python
      # AEA-40-F1 (DO-4 section 11: "safety and CON-4 still work" at our cap). These gate kinds route to
      # safety -> compose with no model node. Decided with no conversation state: TurnService never reads it.
      _NO_MODEL_GATES: Final = frozenset({GateKind.SAFETY, GateKind.DANGER_RULE, GateKind.BURNING_ASK})
      _STATELESS_FLAGS: Final = GateFlags(
          ai_paused=False, burning_card_id=None, code_card_open=False, open_task_ids=()
      )
      ```
   3. After `reopened_outcome`, add:
      ```python
      def answered_without_model(intake: Intake) -> bool:
          """True when the deterministic gates answer this turn with no model call, so our spend cap never refuses it."""
          gate = decide_gate(intake, _STATELESS_FLAGS)
          if gate.kind in _NO_MODEL_GATES:
              return True
          return gate.kind is GateKind.BURNING_ANSWER and gate.burning_answer in ("yes", "unsure")
      ```
   4. Replace the head of `_run` (lines 317–323) with:
      ```python
      def _run(self, cmd: RunTurn, now: dt.datetime, mono_start: float) -> TurnResponse:
          intake = parse_intake(cmd.payload)  # pure: a refused turn still stores nothing
          if not answered_without_model(intake) and not self._spend.allow_turn():
              return self._reject(
                  cmd, code="SPEND_CAP_REACHED", reason="spend_cap", now=now, mono_start=mono_start
              )
          ids = self._ids(cmd)
      ```
      Everything from the `# T1:` comment down is unchanged. The second `intake = parse_intake(...)` line is gone (it
      runs once).
   5. Module docstring, first paragraph: change "admits the turn (30 in flight), checks the spend gate, records…" to
      "admits the turn (30 in flight), parses the intake, checks the spend gate unless the deterministic gates answer
      the turn with no model (AEA-40-F1), records…". Keep the rest.
   Invariants: `parse_intake` is pure, so step 4 adds no write before `_reject` (F1-5); `allow_turn()` is still called
   for every turn that could reach a model (F1-2); nothing reads `ConversationState` (AEA-40 plan).

4. Run `uv run pytest tests/services/test_turn_spend_cap.py tests/services/test_turn.py -q`: all green.

5. **Test file `tests/services/test_turn_spend_cap.py`** (module docstring: "AEA-40-F1: at our spend cap a turn the
   deterministic gates answer with no model still runs; every other turn is refused. Level: mock-tested (real
   TurnService on a temp SQLite copy; run_graph and SpendGuard doubled). No model, no network."). Tests, each docstring
   naming its failure mode:
   - **`test_safety_turn_at_cap_answered_without_model`** (regression, WP-5): `FakeSpendGuard(allow=False)`;
     `graph = ScriptedRunGraph(lambda i, c: safety_outcome(i.turn_id, c.now))`; `thread = seed_thread(store.uow)`;
     `cmd = make_cmd(thread, text_payload(WP5))`; `result = service.run_turn(cmd)`. Assert:
     `result.notice is None`; `notice_codes(result.blocks) == []`; `result.blocks[0].type == "safety"`;
     `result.blocks[0].steps == (TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH])`;
     `len(graph.calls) == 1`; `graph.calls[0].turn_input.text_store == WP5`; `guard.calls == 0` (D2);
     `row = turn_row(store, cmd.turn_id)`; `(row.status, row.gate_result, row.outcome, row.degrade_reason) ==
     ("completed", "safety", "safety_reply", None)`; `row.model_calls == 0`;
     `count_rows(store, "spend_ledger") == 0`; `len(customer_messages(store, thread, cmd.turn_id)) == 1`;
     `conversation(store, thread).outcome == "safety_reply"`.
   - **`test_normal_turn_at_cap_still_refused`** (failure/refusal, WP-5's twin): same setup with
     `text_payload(NORMAL)` and `ScriptedRunGraph()`. Assert: `result.notice is not None and result.notice.code ==
     "SPEND_CAP_REACHED"`; `result.notice.actions == ("talk_to_person",)`; `notice_codes(result.blocks) ==
     ["SPEND_CAP_REACHED"]`; `has_person_key(result.blocks)`; `graph.calls == []`; `guard.calls == 1`;
     `(row.status, row.outcome, row.degrade_reason) == ("failed", "degraded_handoff", "spend_cap")`;
     `row.model_calls == 0`; `customer_messages(store, thread) == []`.
   - **`test_safety_then_normal_at_cap`** (boundary): one thread, the cap stays reached. Turn 1 `WP5` (graph returns
     `safety_outcome`) is answered; turn 2 `NORMAL` gets `SPEND_CAP_REACHED`; `len(graph.calls) == 1`;
     `guard.calls == 1`.
   - **`test_answered_without_model_table`** (invariant, `@pytest.mark.parametrize("payload, expected", ROWS, ids=...)`),
     calling `answered_without_model(parse_intake(payload))` directly. `ROWS` (texts taken from
     `tests/unit/gates/test_gate.py`, which proves their gate kinds):

     | id | payload | expected | gate kind |
     |---|---|---|---|
     | `safety-wp5` | `TextPayload(text=WP5)` | True | SAFETY |
     | `safety-plus-person` | `TextPayload(text="co alarm keeps going off, can I talk to a person")` | True | SAFETY |
     | `danger-words` | `TextPayload(text="My son can't breathe, can I talk to a person")` | True | DANGER_RULE |
     | `burning-ask` | `TextPayload(text="I smell something burning, can I talk to a person")` | True | BURNING_ASK |
     | `burning-yes` | `ChoicePayload(card_id="burn-t1", option="yes")` | True | BURNING_ANSWER yes |
     | `burning-unsure` | `ChoicePayload(card_id="burn-t1", option="not_sure")` | True | BURNING_ANSWER unsure |
     | `burning-no` | `ChoicePayload(card_id="burn-t1", option="no")` | False | BURNING_ANSWER no (booking needs a model) |
     | `person` | `TextPayload(text="can I talk to a person")` | False | PERSON (the brief model) |
     | `free-text` | `TextPayload(text=NORMAL)` | False | FREE_TEXT |

   Module constants: `WP5 = "My carbon monoxide detector is going off."`,
   `NORMAL = "what does this invoice line mean?"`. Helper in the test file (do not add it to `chat_doubles.py`):
   ```python
   def safety_outcome(turn_id: TurnId, at: dt.datetime) -> GraphOutcome:
       block = SafetyBlock(
           block_id=f"blk-{turn_id}-1", speaker=ASSISTANT_SPEAKER, at=at, signal_word="DANGER",
           steps=(TEXTS[TextId.SAFETY_LEAVE_NOW], TEXTS[TextId.SAFETY_DONT_TOUCH]),
           call_key=CallKey(label="Call 911 (from outside)", number="911"),
           contact_line=TEXTS[TextId.SAFETY_CONTACT_LINE], case_reference=None,
       )
       reply = ComposedReply(blocks=(block,), settled_view=empty_view(), writes=(), notice=None,
                             path="safety", outcome="safety_reply", degrade_reason=None)
       return GraphOutcome(reply=reply, turn_trace=TurnTrace(gate_result="safety", path="safety", outcome="safety_reply"))
   ```
   Wrap each service test in `with temp_sqlite() as store:` and build the service with
   `make_turn_service(store, run_graph=graph, spend=guard)`.

6. **Journey file `tests/journeys/j5/test_aea_40.py`**, one test
   **`test_j5_co_alarm_at_spend_cap_still_gets_safety_card(journey: JourneyRun)`**, `pytestmark = pytest.mark.journey`.
   Module docstring: J-5 at the spend cap (AEA-40-F1, DO-4 §11); level target `integrated with a scripted model`;
   turn steps report blocked until AEA-51 binds `run_graph` and `reply_composer`; the run record's spend total
   includes one **synthetic** ledger row worth the daily cap, written to reach the cap (no model was paid).
   Constants copied (not imported) from `tests/journeys/j5/test_aea_36.py`: `SIGN_IN_NEEDS`, `CHAT_NEEDS`, `WP5`; plus
   `CAP_NEEDS = ("ledger",)`, `TURN_NEEDS = (*CHAT_NEEDS, "turn_service", "run_graph")`,
   `SAFETY_TURN_NEEDS = (*TURN_NEEDS, "handoff_service")`, `NORMAL = "How much is a furnace tune-up?"`.
   `_ids()` and `_call(cost)` copied verbatim from `tests/journeys/j9/test_aea_26.py`. Steps:
   1. `journey.step("J-5", "1 login", needs=SIGN_IN_NEEDS, operations=("login",))`: `signed = journey.login()`.
   2. `"2 start session"`, `needs=CHAT_NEEDS`, `operations=("startChatSession",)`: POST `/api/chat/sessions`, 201,
      keep `thread_id`.
   3. `"3 day's spend reaches the cap"`, `needs=CAP_NEEDS`: `ledger = journey.container.get(Key[LedgerService]("ledger"))`;
      `ledger.record(_call(journey.container.limits.spend.daily_cap_usd), _ids())`; `assert ledger.allow_turn() is False`.
   4. `"4 CO alarm at the cap: instruction first, P0 case"`, `needs=SAFETY_TURN_NEEDS`, `operations=("submitTurn",)`:
      `calls_before = len(journey.script.calls)`; POST the WP5 turn; assert 200, `body["notice"] is None`, first block
      `type == "safety"` with steps `[SAFETY_LEAVE_NOW, SAFETY_DONT_TOUCH]` texts, `len(journey.script.calls) ==
      calls_before`, `journey.script.problems() == ()`, `journey.db.count("spend_ledger", "turn_id = ?", (turn_id,)) == 0`,
      one `cases` row for the thread with `priority == "P0"` and `reason == "safety"`, `first["case_reference"] ==
      case["case_ref"]`, turns row `status == "completed"`, `gate_result == "safety"`, `outcome == "safety_reply"`.
   5. `journey.step("J-9", "5 normal question at the cap: SPEND_CAP_REACHED", needs=TURN_NEEDS,
      operations=("submitTurn",))`: POST `NORMAL` with a new turn id; assert 200, `notice["code"] == "SPEND_CAP_REACHED"`,
      `notice["actions"] == ["talk_to_person"]`, no new script calls, turns row `(status, outcome, degrade_reason) ==
      ("failed", "degraded_handoff", "spend_cap")`, `journey.db.count("messages", "turn_id = ?", (turn2,)) == 0`.
   End with one `print(...)` line of codes only (no ids beyond the case ref, no secrets), like `test_aea_36.py`.

7. Fast gates and affected tests (§7), then commit on the branch with explicit paths:
   `git add src/meridian/services/turn.py tests/services/test_turn_spend_cap.py tests/journeys/j5/test_aea_40.py`.
   Message: `fix(AEA-40-F1): safety turns still answered at the spend cap`, body naming R-14 and DO-4 §11, last line
   `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push.

**The implementer must not:** edit `gates/`, `domain/`, `agent/`, `web/`, `chat_doubles.py`, `chat_storage.py`,
`test_turn.py` or any doc; read conversation state in `TurnService`; call `allow_turn()` twice or `parse_intake` twice;
change the `SPEND_CAP_REACHED` notice, its text or its stored trace; add a model call or a live/paid test; skip or
weaken an existing test; add the PERSON, CODE_ENTRY, AI_PAUSED or FREE_TEXT kinds to the no-model set; `git add -A`;
read `.env`.

## 6. Data and fixtures

Synthetic only. WP-5 text is the worked pair already used in `tests/unit/gates/test_gate.py` (`WP5`) and
`tests/journeys/j5/test_aea_36.py`; the other gate texts are copied from `test_gate.py` rows 131–133. No names, phone
numbers, codes or card numbers. The journey's cap row is a synthetic `CallRecord` (copied builder from
`tests/journeys/j9/test_aea_26.py`), written to the disposable journey DB copy; the issued DB is never touched.

## 7. Checks

Run cheapest first; stop at the first red. `export UV_LINK_MODE=hardlink`. pytest with `-n 2` at most.

| # | Check | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check src/meridian/services/turn.py tests/services/test_turn_spend_cap.py tests/journeys/j5/test_aea_40.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check src/meridian/services/turn.py tests/services/test_turn_spend_cap.py tests/journeys/j5/test_aea_40.py` | `3 files already formatted` |
| 3 | Type check | `uv run mypy` | `Success: no issues found in N source files` (baseline 468 at `f466ff7`; now N = baseline + 2) |
| 4 | New tests | `uv run pytest tests/services/test_turn_spend_cap.py -q` | 12 passed (3 + 9 parametrized rows) |
| 5 | Affected tests (importers of `meridian.services.turn`, `chat_doubles`/`chat_support` users, gate tests) | `uv run --with pytest-xdist pytest -n 2 -q tests/services/test_turn_spend_cap.py tests/services/test_turn.py tests/services/test_session.py tests/services/test_live_chat.py tests/services/test_live_chat_events.py tests/unit/web/test_register_chat.py tests/integration/test_staff_composition.py tests/api/test_chat.py tests/api/test_chat_capture.py tests/api/test_contract_cases_chat.py tests/unit/gates/test_gate.py` | all pass; `test_spend_cap_notice_no_model` and the other AEA-40 tests green |
| 6 | Journey conventions | `uv run pytest tests/journeys/support/test_support.py -q` | pass (`convention_violations(REPO_ROOT) == []`) |
| 7 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | Adding a file under `tests/journeys/` selects **every** journey (`ALWAYS_PREFIXES`). Pass = no `fail`; steps needing `run_graph`/`reply_composer` are reported `blocked` (owner AEA-51) and skip. Quote the pass/blocked counts and the new test's line |

No full suite: no shared fixture, setting, dependency or cross-package module changes (`build-loop-test-scope`).
Evidence record for the report: claim F1-1/F1-2 at level `mock-tested` (checks 4–5); F1-10 at `integrated with a scripted
model` is **Blocked by AEA-51** (state it; do not claim it).

## 8. Risks and requests

- **R-1 (request to the orchestrator, AEA-51).** After this merges, AEA-51 removes the `blocked-on AEA-40-F1` skip on
  `tests/integration/test_customer_failures.py::test_spend_cap_safety_still_answered` and its §8 R-14 row closes. This
  plan does not touch AEA-51's files.
- **R-2 (limitation, stated not fixed).** Danger that only the **classifier** can raise (DANGER case: "my mother is 88
  and it's 95 degrees in here") needs a Jev model call, so at the cap it still gets `SPEND_CAP_REACHED` with the person
  key. That follows "the cap refuses only turns that would need a model call"; listed so nobody reads F1 as covering it.
- **R-3 (limitation).** A typed (not clicked) answer to an open burning card is BURNING_ANSWER only with conversation
  state; at the cap it is refused. The card's buttons (choice payloads) are covered.
- **R-4 (follow-up suggestion, AEA-40-F2).** At the cap, when a representative owns the chat (`controller = human`,
  AI_PAUSED, no model needed), `_reject` neither stores the customer message nor appends the CON-21 event, so the rep
  never sees it. Pre-existing, outside F1's finding, needs the conversation row's controller before the cap check.
  Likewise BUSY (admission) still precedes safety. Recommend the orchestrator decide whether to cut F2.
- **R-5 (collision).** None found: the AEA-51 branch does not touch any owned file; `tests/journeys/j5/test_aea_40.py`
  does not exist on `main` or that branch.
- **R-6 (journey evidence).** The synthetic cap row makes the run record's `spend_total_usd` show the cap amount; the
  docstring and report say it is synthetic.

## 9. Readiness

**READY.** No product decision or signed-contract change is needed: the orchestrator cut F1 with DO-4 §11 as the source
of truth, no response shape or UI contract changes, and D-4…D-15 are not touched. Nothing blocks the unit-level work;
the journey's integrated level waits on AEA-51 (recorded as *Blocked by*, not a blocker for merging F1).

## Gates

None (no human, external, paid or live gate).
