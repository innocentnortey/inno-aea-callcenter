## [AEA-12] gates: intake parsing and the gate decision

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

> **US-3 · Get the safety instruction first.** "As a homeowner who smells gas, hears a CO alarm or sees sparks, smoke or
> flames, I need the safety instruction before anything else, so that I leave the home before I'm asked for a name or an
> account." Also served: US-2 (a person on the first ask), US-4 (burning smell: asked, not told to check), US-5 (danger
> words), US-8 (the code is entered in chat and never shown).

`gates/gate.py` is the pure code that decides which turns never reach a model (DO-2 §A.1 *Code gates*; DO-3 §4.1 row
`gates/gate.py`). It exposes five functions, typed exactly as DO-4 §3 and stage7/graph-core.md §2–§3:

- **`parse_intake(payload: domain.turn.TurnPayload) -> Intake`**: turns the CON-2 payload (the pure `TurnPayload` union
  in `domain/turn.py`, AEA-02: `TextPayload`, `ChoicePayload(CardChoice)`, `CodePayload`, `FormPayload`, discriminated
  on `kind`, OpenAPI field names and limits; graph-core §2, R-G-20; `web/schemas/chat.py` validates into it, R-W-15;
  DO-4 §14 `RunTurn.payload`) into an `Intake` **before anything
  stores the text**. `TurnService` (AEA-40) calls it once at step 4 (graph-core §2 rule 1; web.md §9). `text_store` is
  the STORE-redacted text from `redact(text, RedactionProfile.STORE)` (AEA-04; stage7/data.md §1): a card-like number →
  `[card number removed]`, a standalone six-digit number in free text → `[code]`; a code payload → `"[code entered]"`; a
  locate form → `"[details submitted]"`; a where form → the ZIP or city (DO-4 §3); a choice → its option string
  (graph-core §3 step 11). `code_digits` and `FormValues.phone` stay `SecretStr`; `card_number_seen` is set when STORE
  replaced a card-like number (`Redacted.replaced`, R-13); `Intake.card_id` is the payload's `card_id` (graph-core §2,
  GRC-10); `choice` is a `CardChoice(card_id, option)`.
- **`decide_gate(intake, flags: GateFlags) -> GateDecision`**: runs `match_rules(intake.text_store)` (AEA-05) and returns
  one `GateKind` by graph-core.md §3's 11-step table (which supersedes DO-4 §3's order comment, internal-components §16):
  1 `rules.safety` → `SAFETY`; 2 `flags.ai_paused` → `AI_PAUSED`; 3 a choice on any `burn-` card, current or stale →
  `BURNING_ANSWER` with `yes` / `no` / `unsure` (option `not_sure`); 4 `rules.burning_unclear` → `BURNING_ASK`;
  5 `rules.danger_words` → `DANGER_RULE`; 6 `rules.person` → `PERSON`; 7 text while `flags.burning_card_id` is set and no
  step 1–6 match → `BURNING_ANSWER`, `unsure`; 8 kind `code`, or a choice on a `code` card while `flags.code_card_open`
  → `CODE_ENTRY`; 9 a form on a `locate` card → `LOCATE`; 10 a choice or form on a task card whose `task_id` is in
  `flags.open_task_ids` → `CARD_CHOICE`, `resume_task_id = task_id`; 11 anything else (text; a stale or unknown card) →
  `FREE_TEXT`, a stale form's values discarded. The order of steps 1 and 2 is **one tuple** in `gate.py` (GRC-3). A
  policy word (`rules.policy_trigger`) gets no kind of its own: it rides on the decision for `join_plan` (AEA-37) and
  escalation (AEA-14) (DO-4 §4).
- **`flags_from_state(state) -> GateFlags`** (pure): `ai_paused` = `state.controller.kind == "human"`;
  `burning_card_id` = `state.burning_card_id`; `code_card_open` = `state.identity.status == "code_sent"`;
  `open_task_ids` = the open tasks with status ≠ done (graph-core §3, GRC-5).
- **`card_target(card_id) -> CardTarget`** (pure): parses the code-minted prefixes `burn-`, `code-`, `locate-` and
  `<task_id>.<n>` into `(kind, task_id)`; anything else is `("unknown", None)`. The `card_id` is client-supplied and
  untrusted (graph-core §2 `CardChoice`): it is matched by these rules, never trusted.
- **`burning_card_id(turn_id) -> str`** (pure): `"burn-<turn_id>"`; compose (AEA-21) mints the R-7 card with it and the
  gates node (AEA-36) stores it (GRC-4).

**Example pair.** Input: WP-5, "My carbon monoxide detector is going off." (and HP-2's typo form "co alarm keeps going
off"). Expected output: `GateDecision(kind=SAFETY, rules.safety=co)`, `gate_result()` = `safety`, decided with no model
call, so the gates node (AEA-36) sends the KB instruction as the first words. Input: WP-6, "I need to schedule a service
call. I smell something burning from the vents." Expected output: `kind=BURNING_ASK`, `gate_result()` =
`burning_unclear`; the next turn's `choice` on card `burn-<turn_id>` with option `not_sure` → `BURNING_ANSWER`,
`burning_answer="unsure"` (R-7: "If unclear → a conditional safety instruction").

**Resolved R-G-20** (`docs/plans/7b-decisions/residuals-graph.md`; web side R-W-15): the pure `TurnPayload` union
lives in `domain/turn.py` (AEA-02, graph-core §2); `parse_intake(payload: domain.turn.TurnPayload)`.

### Source

- DO-4 §3 (`RuleMatches`, `FormValues`, `Intake`, `GateKind`, `GateDecision`, `decide_gate`), §1 (`Controller`), §4
  (`join_plan` takes the gate's policy word), §14 (`RunTurn.payload`, `TurnService` step 4); internal-components §16
  (addenda win)
- stage7/graph-core.md §2 (`CardChoice`, `Intake.card_id`, `TurnInput`, `TurnContext.intake`, rules 1–4), §3
  (`GateFlags`, `flags_from_state`, `card_target`, `burning_card_id`, card prefixes, the 11-step table); ledger
  `docs/plans/7b-decisions/graph-core.md` GRC-3, GRC-4, GRC-5, GRC-10
- stage7/data.md §1 (`redact`, `RedactionProfile.STORE`, `Redacted.replaced`, placeholder tokens; DAT-28)
- stage7/web.md §9 (`run_turn` step 4 runs `parse_intake` once)
- OpenAPI `TurnPayload`, `ChoicePayload`, `CodePayload` ("Never reaches the model, logs or traces"), `FormPayload`
  (phone "DATA CLASS: PII"), `BurningCheckBlock`
- DO-3 §2.1 (pure core), §4.1 (`gates/gate.py`), §5.4 (gate edges), §10 C-6; DO-2 §A.1 (*Code gates*), §10 (*Identity
  code*, *Cards*)
- DO-6 status values (`turn.gate_result`), *Content and redaction* step 1 (intake masks)
- PRD R-2, R-5, R-7, R-13, R-15, R-31, R-47; US-2…US-5, US-8; HP-2; WP-5, WP-6; SCREEN_SPECS SCR-1 copy notes
  (burning-smell question)
- Slice plan §1 row AEA-12 (`risk::security`; links CAP-2)
- Residuals R-G-10 (`gate_result()` table), R-G-20 (`TurnPayload` home) in `docs/plans/7b-decisions/residuals-graph.md`;
  R-W-15 in `residuals-web.md`; journey criterion `docs/plans/ux-join/backend-amendments.md` §3
- **Brief check:** serves "Escalation must be graceful: the agent recognizes it is out of scope, tells the caller what
  is happening, and hands off" (safety, person and paused turns are decided by code before any model); touches nothing
  out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] The gate order is graph-core §3's table with steps 1 and 2 as one tuple: under the interim order (GRC-3 option A) a CO-alarm message with `flags.ai_paused` → `SAFETY`; with the tuple flipped (option B) the same input → `AI_PAUSED`; other combinations take the earliest step (safety + person words → `SAFETY`; burning + person words → `BURNING_ASK`; person words in a code turn → `PERSON`) — verify: `tests/unit/gates/test_gate.py::test_order_first_match_wins` (parametrised over both tuples) — evidence: each combination's kind under each order.
- [ ] AC-2 [invariant] Safety: WP-5's sentence and "co alarm keeps going off" → `SAFETY` with `rules.safety = co`, `gate_result()` = `safety` (R-5, HP-2) — verify: `test_gate.py::test_wp5_co_alarm_is_safety` — evidence: both inputs.
- [ ] AC-3 [invariant] Burning smell with no breaker information: WP-6's sentence → `BURNING_ASK`, `gate_result()` = `burning_unclear` (R-7) — verify: `test_gate.py::test_wp6_burning_smell_asks` — evidence: kind and status.
- [ ] AC-4 [invariant] Burning answers (GRC-4): a choice on a `burn-` card with option `yes`, `no`, `not_sure` → `BURNING_ANSWER` with `yes`, `no`, `unsure`; a choice on a stale `burn-` card still counts; free text while `flags.burning_card_id` is set and no step 1–6 rule fires → `BURNING_ANSWER`, `unsure`; the same text with person words → `PERSON`; `gate_result()` for the three `BURNING_ANSWER` answers is `safety` (yes), `burning_unclear` (unsure), `clear` (no) (graph-core §3 table, R-G-10) — verify: `test_gate.py::test_burning_answers` — evidence: each case's kind and answer, and the three `gate_result()` values.
- [ ] AC-5 [invariant] A direct request for a person in words → `PERSON`, `gate_result()` = `person_requested`, on the first such message (R-2) — verify: `test_gate.py::test_person_words_first_ask` — evidence: kind on turn 1.
- [ ] AC-6 [invariant] Danger words matched by the rules → `DANGER_RULE`, `gate_result()` = `danger` (R-8 rule half, R-47) — verify: `test_gate.py::test_danger_words` — evidence: kind and status.
- [ ] AC-7 [invariant] A representative controls the chat (`flags.ai_paused`, from `controller.kind == "human"`) and a free-text message with no safety rule → `AI_PAUSED`, `gate_result()` = `ai_paused` (R-31) — verify: `test_gate.py::test_human_controller_pauses_ai` — evidence: kind for a free-text message.
- [ ] AC-8 [invariant] Code and cards: a code payload → `Intake.kind = "code"`, `text_store` = `"[code entered]"`, `code_digits` a `SecretStr`, `card_id` kept, and `CODE_ENTRY` (R-15: no model); a `new_code` choice on a `code-` card while `flags.code_card_open` → `CODE_ENTRY`; a locate form → `text_store` `"[details submitted]"`, `FormValues.phone` a `SecretStr`, `LOCATE`; a where form on a task card in `open_task_ids` → `text_store` equal to the ZIP or city and `CARD_CHOICE` with `resume_task_id`; a slot choice on a task card → `CARD_CHOICE` with `resume_task_id` — verify: `test_gate.py::test_code_cards_and_forms` — evidence: intake fields, kind and task id per case.
- [ ] AC-9 [failure/refusal] An untrusted or stale `card_id` is never trusted: an unknown prefix, a task card whose task is not in `open_task_ids`, and a `code-` choice while no code card is open all → `FREE_TEXT`; the stale choice's `text_store` is its option string and a stale form's is `"[details submitted]"` with its values discarded (graph-core §3 step 11) — verify: `test_gate.py::test_untrusted_and_stale_cards_are_free_text` — evidence: kind and stored text per case; no `FormValues` on the stale-form decision path.
- [ ] AC-10 [invariant] The helpers are pure and exact: `card_target` maps `burn-<id>`, `code-<id>`, `locate-<id>`, `<task_id>.<n>` and anything else to `burning`, `code`, `locate`, `task` (with the task id) and `unknown`; `burning_card_id(turn_id)` returns `"burn-<turn_id>"`; `flags_from_state` sets each `GateFlags` field from the state field graph-core §3 names — verify: `test_gate.py::test_card_target_burning_card_id_and_flags` — evidence: each mapping.
- [ ] AC-11 [invariant] A free-text message containing a card-like number has it replaced by `[card number removed]` in `text_store` and `card_number_seen` True; a standalone six-digit number becomes `[code]` (R-13; STORE profile, data.md §1) — verify: `test_gate.py::test_card_and_code_removed_at_intake` — evidence: stored text and flag.
- [ ] AC-12 [negative] A code, a card-like number and a full phone number, each generated inside the test (never a literal in fixtures or names), are absent from `Intake.text_store`, from `repr()` and `model_dump_json()` of the `Intake` and the `GateDecision`, from `GateDecision.rules.rule_ids`, from the message of a validation error raised on a malformed payload, and from captured logs — verify: `test_gate.py::test_secrets_absent_from_intake_decision_errors_logs` — evidence: every assertion passes.
- [ ] AC-13 [invariant] The module is pure: the same input gives the same decision, and `gates/gate.py` imports no I/O (`sqlite3`, `httpx`, a vendor SDK, a clock read) and nothing from `agent/`, `services/`, `web/` or `adapters/` (DO-3 §2.1) — verify: `test_gate.py::test_gate_module_is_pure` — evidence: repeated calls equal; the forbidden modules absent from the module's imports.
- [ ] AC-14 [journey] Runs no journey yet: wave 1 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-12.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-3 (code and form intake), J-5 (the gate decision) and J-7 (the person request) as the journeys that will exercise this code once AEA-51 and AEA-52 land, so the seam audit knows where to look (`backend-amendments.md` §3, pattern C) — verify: the record and the affected-journey command (AEA-01) run on this diff — evidence: the record's Level, Blocked-by and journey fields; the command prints "0 journeys affected".
- [ ] AC-15 [regression/context] Docs updated in the same change — verify: `git diff --name-only` — evidence: `.claude/reference/area-map.md` A1 row (`gates/gate.py` planned → actual with the commit), `.claude/state/icm-progress.md` row *Routes verified against code and tests* (evidence link replaced), `docs/design/code-design.md` §3 status planned → built, all three in the diff.

### Observability

- Responsibilities: produces the values WF-1's records carry: `GateDecision` whose `gate_result()` becomes
  `TurnTrace.gate_result` (graph-core §2, via compose's `turn_trace`) and whose `rules.rule_ids` become the gate
  `check_event`'s codes (`CheckEvent.from_gate`, graph-nodes §1). It writes and logs nothing itself (pure). The intake
  masks of DO-6 *Content and redaction* step 1 happen here, before any store, model or trace.
- Capture evidence: AC-12 here; at WF-1's real entry point, CAP-2 (WP-5: safety turn, no model span before the reply)
  and CAP-1 (code and card absent everywhere) in AEA-51, plus AEA-51's sentinel test of graph-core §2 rule 4 (code
  digits and a form phone in no checkpoint, row, log, span or model request).

### Evaluation

- Checks: E-5 safety and danger slice (rule half) and E-1's WP-5 and WP-6; the person-request gate in E-1/E-3.
- Expected-answer authority: KB `policies/escalation_and_safety.md` for the safety triggers, Innocent's decisions for the
  paths (R-5–R-8, R-47, D2), labelled synthetic cases for typo and mid-chat variants (DO-5 *Expected-answer authority*).

### Metrics

- References: M-14 (safety first), M-15 (person on first request), M-16 (danger recall, rule half), M-17 (false alarms).
- Acceptance conditions: all four stay computable from `turn.gate_result` (AC-2, AC-5, AC-6); targets are DO-7's (100%,
  100%, 100%, ≤ 10%), measured at Stage 9, not here.

### Blocked by

AEA-02, AEA-04, AEA-05; AEA-01 (the `journey` marker and affected-journey command AC-14 runs; wave 0, so no wave change)

### Agent handoff

- Area / owner: A1 Gates (`src/meridian/gates/gate.py`).
- Contracts and shared surfaces: consumes `match_rules` / `RuleMatches` (AEA-05), `redact` and `RedactionProfile.STORE`
  (AEA-04), and from AEA-02 the DO-4 §3 types plus `GateFlags`, `CardChoice`, `Intake.card_id`, `ConversationState`
  (with `burning_card_id`), the `TurnPayload` union (R-G-20) and `GateDecision.gate_result()` (AEA-02 implements that
  method); AEA-01's affected-journey command for AC-14. Produces `parse_intake` for
  `TurnService` (AEA-40); `decide_gate`, `flags_from_state` and `card_target` for the gates node (AEA-36);
  `burning_card_id` for compose (AEA-21) and AEA-36; the `GateDecision` for the routers (AEA-21), `join_plan` (AEA-37)
  and `decide_escalation` (AEA-14). Must not edit `gates/rules.py`, `privacy/redact.py` or `domain/*`.
- Scope boundary / refusal: no safety text (AEA-03/AEA-36), no case creation, no identity verification (AEA-27), no
  state writes (the gates node writes `burning_card_id`), no model call, no new word rule (a missing rule goes to
  AEA-05). `gate_result()` is AEA-02's method, implementing graph-core §3's table; this ticket asserts `gate_result()`
  for the three `BURNING_ANSWER` answers: `safety`, `burning_unclear`, `clear` (R-G-10; AC-4).
- Awaiting Innocent: GRC-3 — built on the recommended option A (`SAFETY` before `AI_PAUSED`, the order one tuple in
  `gate.py`, AC-1 covers both orders); if he picks B the tuple flips and AC-1's interim expectation swaps; if he picks C
  steps 3–6 (burning, danger words, person) also move ahead of `AI_PAUSED` and AC-1 gains those cases.
- Wave and gates: wave 1; no gate (the `TurnPayload` home is resolved, R-G-20).
- Lane: build-loop — source and tests.
- Risk: security — a bug in `parse_intake` could store a verification code, card-like number or phone in
  `text_store`, a log or state (DO-6 *Content and redaction* step 1), and an untrusted `card_id` could route a turn
  into another task; frozen failing tests first and the security agent at the wave-1 merge.
- Entry points added or changed: None
