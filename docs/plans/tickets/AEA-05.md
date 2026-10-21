## [AEA-05] gates: typo-tolerant word rules

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

> As a **homeowner** who smells gas, hears a CO alarm or sees sparks, smoke or flames, I need the safety instruction
> before anything else, so that I leave the home before I'm asked for a name or an account. (US-3; also US-2, US-4,
> US-5)

**Example pairs.**
- WP-5: "My carbon monoxide detector is going off." → `RuleMatches(safety = co, burning_unclear = False, …)` with the CO
  rule's ID in `rule_ids`. HP-2's short, lower-case form "co alarm keeps going off" → the same.
- WP-6: "I need to schedule a service call. I smell something burning from the vents." → `safety = None`,
  `burning_unclear = True` (no breaker state stated, R-7).
- WP-3 / NODANGER: "My AC isn't cooling." → nothing fires: a normal booking (R-8, Innocent's WP-3 decision).
- DANGER: "my mother is 88 and it's 95 degrees in here" → `danger_words = False`. Danger is a combination with no word
  list; the raise-only classifier catches it (HP-2 option C, R-47; AEA-37), so the rule half stays narrow.
- WP-7: "I want a full refund on the repair. It didn't fix anything and I had to call another company." →
  `policy_trigger = refund`.
- GRC-13: "that's not what I asked" → `correction = True`, nothing else (the facts node counts it toward escalation
  rule 7's `corrections ≥ 2` offer, cases.md §3.4).

`gates/rules.py`: `match_rules(text) -> RuleMatches` (DO-3 §4.1 row `gates/rules.py`; DO-4 §3), pure, typo-tolerant,
run on every message wherever it sits in the chat (R-5: "including phrases mid-chat and with typos"). It answers which
fixed rule a message matches and decides nothing else. `RuleMatches` and `SafetyKind` are AEA-02's, defined in
`domain/turn.py` with exactly DO-4 §3's fields plus `correction` (stage7/graph-core.md §8, GRC-13; R-G-1, which
supersedes the slice plan's "`RuleMatches` stays in `rules.py`"); this ticket fills them:

- **`safety`** (`SafetyKind`: `gas`, `co`, `sparks_smoke_flames`, `burning_with_breaker`, DO-4 §3): gas or rotten-egg
  smell; carbon monoxide alarm; visible sparks, smoke or flames from a unit; an electrical burning smell with a tripped
  breaker. The list is the KB's (`policies/escalation_and_safety.md`, *Immediate safety escalation*).
- **`burning_unclear`**: burning words with no breaker state stated and no safety kind (R-7, D2).
- **`danger_words`**: narrow, explicit danger phrases only (R-8's rule half; SP-1 build §5 step 1 lists the narrow set it
  measured).
- **`person`**: a direct request for a person in words (R-2: "button or words").
- **`policy_trigger`**: one of the five `HandoffReason` values DO-4 §3 names: `refund`, `billing_dispute`,
  `complaint_or_manager`, `legal_or_chargeback`, `commercial` (the KB's *Supervisor escalation* list and *Department
  redirects*; R-24). A question about a duplicate charge is billing information, not a dispute (PRD §3.2 driver B).
  Membership cancel is not a word rule: it reaches escalation as the planner's `handoff_request` (cases.md §3.4 row 4).
- **`correction`** (GRC-13): the customer correcting the AI: "that's not what I asked", "that's wrong", "no, I said …",
  typo-tolerant (OD-6 signal; graph-core.md §8).
- **`rule_ids`**: a stable ID per rule that fired. They become `CheckEvent.codes` (`(GateKind value, *rule_ids)`,
  stage7/graph-nodes.md §1 `from_gate`), which hold "stable codes only, never message text or a value".

Starting material: the parked `docs/parked/2026-10-21-first-attempt/src_meridian/triggers.py` patterns and order, **read and copied, never imported**, adapted
as SP-1 build §4.5 says (the CO typo pattern), and its §5 step 1 functions; follow DO-4's fields (SP-1 merged legal into
complaints and put membership cancel here; DO-4 keeps `legal_or_chargeback` apart and leaves membership cancel to the
planner). How typo tolerance works is the planner's choice; the tests below decide whether it is enough.

**Not here:** the gate order and the decision (`decide_gate`, AEA-12); reading the burning-smell answer (a `burn-` card
choice, AEA-12, graph-core.md §3); code, card and form parsing (AEA-12); the raise-only classifier (AEA-37); counting
corrections (facts node, AEA-38); priorities and promises (AEA-14); any reply text (AEA-03).

**Resolved R-G-1** (`docs/plans/7b-decisions/residuals-graph.md`; graph-core §8): `SafetyKind`, `RuleMatches` and
`HandoffReason` are imported from `meridian.domain` (AEA-02); this ticket owns `match_rules` and its phrase lists only.
`policy_trigger` is typed `HandoffReason | None` as DO-4 types it. Merge after AEA-02 inside wave 0 (graph-core §12;
wave-0 order AEA-04 → AEA-02 → AEA-05, R-G-18); if AEA-02 is not on `main` when the plan is written, record `blocked-on
AEA-02` for the import and build the rest. The slice plan's "pure, no imports" is read as "no I/O imports": `gates →
domain` is pure core → pure core (DO-3 §2.1).

### Source

- DO-4 §3 (`SafetyKind`, `RuleMatches`), §6 table rows 1–2, §7 (`HandoffReason` values)
- stage7/graph-core.md §8 (`RuleMatches.correction`, GRC-13); ledger `docs/plans/7b-decisions/graph-core.md` GRC-13
- stage7/graph-nodes.md §1 (`CheckEvent.from_gate` codes); stage7/cases.md §3.4 rows 4 and 7
- DO-3 §2.4 (`triggers.py` row), §4.1 (`gates/rules.py`), §7 R-2, R-5, R-7, R-8, R-24, R-47 rows
- PRD R-2, R-5, R-7, R-8, R-24, R-47; §3.2 (driver B includes duplicate-charge explanation)
- KB `policies/escalation_and_safety.md` (issued, read-only)
- HP-2 (option C chosen, Innocent ✓ 2026-10-20); WP-3, WP-5, WP-6, WP-7
- SP-1 build plan `docs/plans/fanout/2026-10-20-sp1/build.md` §4.5, §5 step 1
- Call map `docs/data/handoff-inventory-call-map.csv` (420 calls, 46 opening templates; 9 safety calls: SAF-CO 5,
  SAF-GAS 3, SAF-SPARK 1; 16 SCH-BURNING)
- Slice plan §1 row AEA-05, §2 (edge AEA-02 → AEA-05 removed there; restored inside wave 0 by R-G-1 and R-G-18)
- Residual rulings `docs/plans/7b-decisions/residuals-graph.md` R-G-1 (type home), R-G-18 (wave-0 merge order);
  stage7/graph-core.md §8, §12
- Journey map: slice plan §0a; `.claude/rules/integrated-journeys.md`; `docs/plans/ux-join/backend-amendments.md` §3
- **Brief check:** serves "Everything the agent cannot handle must escalate cleanly to a human" and the brief's "catch
  the traps" (a safety report must never wait behind a model); touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] All 46 opening templates in the call map get the label their `initial` category implies: the three safety templates their `SafetyKind`; SCH-BURNING `burning_unclear`; BILL-REFUND `refund`; BILL-DISPUTE `billing_dispute`; COMPLAINT-CONDUCT, COMPLAINT-REPEAT, COMPLAINT-OPINION `complaint_or_manager`; COMMERCIAL `commercial`; every other template (including BILL-DUP "i think i got charged twice …") no safety, no burning, no danger, no correction and no policy trigger — verify: `tests/unit/gates/test_rules.py::test_issued_templates_labelled` (expected labels in the test's own fixture, each citing its category) — evidence: 46 of 46 pass.
- [ ] AC-2 [invariant] Safety recall on the full corpus: run over every customer line of the 420 issued transcripts; safety fires in all 9 safety calls; every other line where any rule fires is listed in the test's expected file with its call ID and the planner's reviewed reason (no unreviewed firing) — verify: `tests/unit/gates/test_rules.py::test_corpus_firings_reviewed` — evidence: 9 of 9 safety calls; the reviewed list printed with its count.
- [ ] AC-3 [invariant] Labelled synthetic variants, each changing one named dimension (typo, mid-chat, paraphrase, case, shorthand) of a clean safety line, fire the right kind: at least one per kind per dimension, including HP-2's "co alarm keeps going off" and "smells like rotten eggs" — verify: `tests/unit/gates/test_rules.py::test_safety_variants` (each case records its varied dimension, rule `synthetic-test-data` 4) — evidence: all pass; the dimension × kind table printed.
- [ ] AC-4 [invariant] Burning: burning words with a tripped breaker stated → `burning_with_breaker`; burning with sparks, smoke or flames → `sparks_smoke_flames`; burning with no breaker state → `burning_unclear` only (R-7) — verify: `tests/unit/gates/test_rules.py::test_burning_paths` — evidence: three passes.
- [ ] AC-5 [negative] No-danger comfort reports fire nothing (HP-2: over-firing buries real P1 cases): "My AC isn't cooling", "the furnace wont kick on", "the ac runs but the air is warm", "my thermostat is blank", "the water heater pilot light keeps going out", and DANGER's "my mother is 88 and it's 95 degrees in here" for `danger_words` — verify: `tests/unit/gates/test_rules.py::test_comfort_reports_do_not_fire` — evidence: all pass.
- [ ] AC-6 [invariant] Narrow danger phrases from SP-1 build §5 step 1 set `danger_words` — verify: `tests/unit/gates/test_rules.py::test_explicit_danger_phrases` — evidence: passes.
- [ ] AC-7 [invariant] Direct requests for a person in words set `person` (R-2); a request for a manager sets `policy_trigger = complaint_or_manager` (DO-4 §3); the plan states, with a test, whether it also sets `person` (both route to a P3 handoff, DO-4 §6 rows 1–2) — verify: `tests/unit/gates/test_rules.py::test_person_requests` — evidence: passes.
- [ ] AC-8 [invariant] Corrections (GRC-13): "that's not what I asked", "that's wrong", "no, I said …" and one typo variant of each set `correction` and nothing else — verify: `tests/unit/gates/test_rules.py::test_correction_phrases` — evidence: all pass.
- [ ] AC-9 [negative] Card answers and ordinary replies do not count as corrections: "no", "no thanks", "not sure", "yes" leave `correction` False (a false correction would push escalation rule 7's `corrections ≥ 2` offer early, cases.md §3.4) — verify: `tests/unit/gates/test_rules.py::test_plain_replies_are_not_corrections` — evidence: all pass.
- [ ] AC-10 [negative] `RuleMatches` carries no message text: a distinctive sentinel phrase inside a firing message is absent from `model_dump_json()`, from `repr()` and from every `rule_id`, and every `rule_id` matches one fixed ID pattern (stable codes only, graph-nodes §1) — verify: `tests/unit/gates/test_rules.py::test_rule_matches_hold_no_text` — evidence: sentinel not found; pattern holds.
- [ ] AC-11 [invariant] Pure and fast: no I/O; `gates/rules.py` imports only the standard library and `meridian.domain` (for `RuleMatches`, `SafetyKind`, `HandoffReason`; R-G-1), defines no `RuleMatches` or `SafetyKind` of its own, and imports no other `meridian` package (DO-3 §2.1: pure core → pure core) — verify: `tests/unit/test_import_direction.py::test_rules_imports` — evidence: passes; the import list printed; `RuleMatches is meridian.domain.turn.RuleMatches` asserted.
- [ ] AC-12 [journey] Runs no journey yet: wave 0 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-05.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-5 (safety words) and J-7 ("talk to a person" words) as the journeys that will exercise this code once AEA-51 and AEA-52 land, so the seam audit knows where to look — verify: the record — evidence: the record's Level, Blocked-by and journey fields.
- [ ] AC-13 [regression/context] Context updated in the same change — verify: `git diff --name-only` — evidence: `.claude/reference/area-map.md` A1 row notes `gates/rules.py` planned → actual with the commit; `.claude/state/icm-progress.md` row *Routes verified against code and tests* has its evidence link replaced; `docs/design/code-design.md` §3 status line notes `gates/rules.py` built; the reviewed corpus-firing list (AC-2) is referenced from the plan.

### Observability

- Responsibilities: for WF-1, every rule that fires returns a stable ID in `rule_ids`; the gates node (AEA-36) builds
  the gate `check_event` from it with `CheckEvent.from_gate` (codes `(GateKind value, *rule_ids)`, graph-nodes §1;
  DO-6 *Records*: "which gate or check fired … its input IDs and result"), and `TurnTrace.gate_result` comes from the
  gate decision (AEA-12; graph-core §2). This module stores and logs nothing itself.
- Capture evidence: CAP-2 (AEA-51) drives CON-2 with WP-5 and asserts `gate_result = safety`, `outcome = safety_reply`,
  a P0 case and no model span before the instruction (DO-6 CAP-2, as corrected by GRN-9). AC-10 is this module's
  negative guard only.

### Evaluation

- Checks: E-5 (safety and danger slice: safety instruction first, danger path) and E-1's WP-5 and WP-6 hard gates rest
  on this rule half; AC-1…AC-5 are the unit-level set (the 9 issued safety calls plus labelled synthetic variants, as
  HP-2 *How we'll know it worked* names).
- Expected-answer authority: the KB safety policy for the safety list; Innocent's decisions for the paths (D2 for burning,
  R-8 as narrowed at the WP-3 check, HP-2 C); danger labels on synthetic cases written from R-8's rule; the correction
  phrases from GRC-13 (DO-5 *Expected-answer authority*).

### Metrics

- References: M-14 (safety instruction first, hard gate 100%), M-15 (person on first request, 100%: the words half),
  M-16 (danger recall, 100%: the rule half; the classifier half is AEA-37), M-17 (false alarms ≤ 10% on no-danger
  comfort cases).
- Acceptance conditions: on this ticket's unit set, safety recall is 9 of 9 issued calls and every synthetic variant,
  and no comfort report fires (AC-5); the metrics themselves are computed at E-5 from eval runs, never from these tests.

### Blocked by

AEA-02, inside wave 0 (R-G-1: `RuleMatches`, `SafetyKind` and `HandoffReason` are imported from `meridian.domain`).
**Wave-0 merge order: AEA-04 → AEA-02 → AEA-05** (R-G-18; graph-core §12); this ticket merges last of the three. If
AEA-02 is not on `main` when the plan is written, the plan records `blocked-on AEA-02` for the import only and builds the
rest. The edge is inside wave 0; no wave moves (slice plan §2's removal of this edge is superseded; the orchestrator adds
the in-wave edge 02 → 05).

### Agent handoff

- Area / owner: A1 Gates (area map row A1).
- Contracts and shared surfaces: consumes `RuleMatches` (with `correction`), `SafetyKind` and `HandoffReason` from
  AEA-02's `domain/turn.py` and `domain/handoff.py` (R-G-1); produces `match_rules` for AEA-12 (`decide_gate` runs it on
  every turn, and `GateDecision.rules` holds its result), AEA-36 (gates node builds the gate `check_event`
  from `rule_ids`), AEA-37 (the classifier sees the rules' verdict and may only raise it, R-47) and AEA-38 (counts
  `correction`). Must not edit: `gates/gate.py` (AEA-12), `domain/*` (AEA-02), the parked `docs/parked/2026-10-21-first-attempt/src_meridian/triggers.py`
  (read only), the KB.
- Scope boundary / refusal: rules only; no reply text, no priority, no gate order, no model call; no broad danger word
  list (HP-2: "danger has no word list"; a broad list over-fires on "it's hot"); no membership-cancel rule (planner's,
  cases.md §3.4 row 4).
- Wave and gates: wave 0, merged after AEA-02 (R-G-1, R-G-18); gate: none (the type-home question was resolved by
  R-G-1).
- Lane: build-loop — source and tests (`ticket-lanes`).
- Risk: None (slice plan).
- Entry points added or changed: None
