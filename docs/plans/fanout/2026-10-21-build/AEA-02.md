# Plan — [AEA-02] foundation: domain types, ports, typed settings, repository shells

**Status:** planned — **READY**. AEA-01 (`07924f5`) and AEA-04 (`ef03e05`) are on `main`; nothing blocks. See §9.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/2 · **Base revision:** `16ca639`
(main at the refresh; first planned at `9c3e7e7`)
**Planner:** fanout-planner on `claude-opus-5-5`, 2026-10-21; refreshed the same day against `16ca639` (see *Refresh
notes* below). **Implementer:** `fanout-implementer` on Sonnet.
**Risk:** `risk::security` → `test-writer-agent` freezes the tests in §3.3 **before** the implementer starts;
`security-privacy-agent` reads this diff at the wave-0 merge. **Lane:** `lane::build-loop`.

**Refresh notes (16ca639).** Checked against the code on `main` and every source the first pass used.
- **Unchanged since `9c3e7e7`:** the ticket, the slice plan, every `stage7/*` addendum, every `7b-decisions/*` ruling
  and the OpenAPI file (last touched `bff374e`). §4's shapes and Appendix A stand as written. Spot-checked again:
  graph-core §12 (`Settings`), §3 (gate table), §11 (`add_turn_events`), §14 (`VisitView`); staff.md §1
  (`ROLE_ACTIONS`: 14 + 9 + 0 keys, the OpenAPI `allowed_actions` enum has 16); the OpenAPI error enums (22 + 6 + 7 =
  35 distinct codes).
- **Now on `main`:** AEA-01's scaffold (`pyproject.toml`, every package marker, `tests/conftest.py`,
  `tests/unit/test_import_direction.py`, `tests/journeys/affected.py`, `policy/limits.py`, `web/container.py`), AEA-03's
  `policy/texts.py`, AEA-04's `privacy/redact.py` (`RedactionProfile`). So the old `blocked-on AEA-01` and the
  `config.py`-only `blocked-on AEA-04` are gone (§9).
- **AEA-08 (`c0621de`)** moved DO-3 to revision 3 (11 `domain/` files; `repos_cases.py` belongs to A0 / AEA-10 whole;
  the seven shells are still this ticket's, DO-4 §13 note) and fixed one contradiction this plan reported (§8.4).
  No field, type or signature changed.
- **Context files changed under us:** the area map's A0 Status cell, DO-3 §3's new `**Built:**` line and a duplicated
  ICM row. Step 21 now says exactly which text to extend.
- **Still open, outside this ticket:** the AEA-02b follow-up of §8.2. AEA-21 and AEA-35 both carry it as their R-1.

---

## 1. Goal and sources

### 1.1 Goal (from the issue, `docs/plans/tickets/AEA-02.md` *What to build*)

> As a **homeowner** mid-booking, I need "what about Monday?" to apply to the visit we were just arranging, so that I
> don't start over every message. (US-17; R-45)

Build every shared type and port in the homes DO-3 §3 gives, with the shapes of DO-4 §0–§14 **as amended by the Stage 7
addenda** (DO-4 §16: the addendum wins), plus the one typed `Settings` (graph-core §12) and seven empty repository
shells. Eleven `domain/` files, two `ports/` files, `config.py`, seven `adapters/sqlite/repos_*.py`, `.env.example`.

**Example pair 1 (WP-4F, this ticket's worked pair).** The `actions` rows of Linda Foster's (fictional, MHC-10001)
thread after turn 3 hold one `CompletedAction` with `kind = moved`, `records = {appointment, slot, old_slot}`,
`after = {date: 2026-10-19, window: 08:00-12:00, technician, service_type, fee_line}`. Then
`Settled.has(ActionKind.MOVED)` is true, `Settled.current_visit()` returns a `VisitView` for 2026-10-19 08:00-12:00
with `status="moved"`, `change_request=None`, and `Settled.only_turn(<turn 4 id>)` holds no action.
Test: `tests/unit/domain/test_actions.py::test_wp4f_move_is_settled`.

**Example pair 2 (DO-3 S-2).** An environment that configures Jev (`openrouter_jev`) for the responder role fails
`Settings` validation at start-up, naming the field and the rule, with no secret value in the error.
Test: `tests/unit/test_config.py::test_jev_in_structured_or_tool_role_rejected` (frozen).

### 1.2 Context (why this ticket exists now)

Wave 0, critical path (AEA-02 → 10 → 29 → 51 → 62 → 55 → 56). Every later ticket imports these types; after wave 0
the files are frozen and a missing field is its own small follow-up ticket (slice plan §3). Merge order inside wave 0:
**AEA-04 → AEA-02 → AEA-05** (R-G-18); AEA-01 and AEA-03 in parallel. AEA-01, AEA-03 and AEA-04 are merged
(`16ca639`). `src/meridian/domain/`, `ports/` and `adapters/sqlite/` hold only AEA-01's empty `__init__.py` markers;
`config.py` does not exist.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-02.md` (= issue #2) | File table, ports, `Settings`, shells, AC-1…AC-22 |
| Slice plan | `docs/plans/slice-plan.md` §1 row AEA-02, §2, §3 | Owned files; frozen after wave 0; wave-0 merge order |
| Code design (DO-3) | `docs/design/code-design.md` revision 3 (AEA-08, `c0621de`): §2.1 (dependency direction), §3 (homes; `**Built:**` line), §4.1 rows incl. `domain/staff.py`, `domain/identity.py`, §4.2, §5.2–§5.3 (state, writers), §9 (tests) | Pure core, no I/O; `ConversationState` keys and reducers; 11 `domain/` files |
| Component contracts (DO-4) | `docs/design/contracts/internal-components.md` §0–§14, §16 | Field names, types, validators |
| Addenda (win over DO-4) | `docs/design/contracts/stage7/graph-core.md` §1–§3, §8, §9, §11, §12, §14; `graph-nodes.md` §1, §4, §5, §9.1; `graph-tools.md` §1–§3, §5; `models.md` §1, §4, §5; `cases.md` §1.0, §1.2, §2, §3.4, §4.1, A-1…A-4; `staff.md` §1; `web.md` §1 | Every shape this plan copies (§4 below) |
| Residual rulings | `docs/plans/7b-decisions/residuals-graph.md` R-G-1…R-G-21; `residuals-web.md` R-W-1, R-W-13, R-W-14, R-W-15 | Already folded into the addenda |
| Decisions taken | `docs/plans/stage7-signoff.md` D-4…D-15 | D-14: CAS-16 on its recommended option A → `HandoffReason.BURNING_RULED_OUT` is added now |
| Signed wire contract (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` | Field names of every wire-facing type (`blocks.py`, payloads, `InboxMessage`, `ApiErrorCode`); `CaseSummary.allowed_actions` enum |
| Issued data (read only) | `docs/data/issued/meridian_dataset/scheduling_db/SCHEMA.md` and the sqlite `CHECK` constraints | `Window`, `ServiceType`, `Customer`, `Technician`, `Invoice` columns |
| Evaluation plan (DO-5) | `docs/design/evaluation-plan.md` *Failure categories: State seam* | E-1's WP-4F item relies on `Settled` reading `actions`; AC-5 is its unit guard. No check added |
| Observability (DO-6) | `docs/design/observability-contract.md` *Status values* (lines 48–57), *Records*, *Content and redaction* | `gate_result`, `outcome`, `degrade_reason`, `trace_export` value sets; no code/card/phone/token field in a record |
| Metrics (DO-7) | `docs/design/key-metrics-registry.md` M-3, M-16–M-18, M-20, M-22, M-24, M-29 | They read the value sets defined here; nothing computed here |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md`, `safe-validation-errors.md`, `synthetic-test-data.md`; workspace `code-design-solid-modularity.md` | Test scope; journey record at `mock-tested`; context rows; errors never carry values |
| Code on `main` (read only) | `pyproject.toml` (ruff `E,W,F,I,B,UP,S,RUF`, line length 110, `S105`/`S106` ignored only under `tests/**`; mypy strict + `pydantic.mypy` with `init_typed`, `init_forbid_extra`, `files = src/meridian, tests, eval`; pytest `--strict-markers --strict-config`, `pythonpath = ["."]`, `testpaths = ["tests", "eval"]`; dev group has `pyyaml`, `types-pyyaml`, `jsonschema`), `src/meridian/privacy/redact.py` (`RedactionProfile.STORE/SONNET/JEV/TRACE/LOG`), `tests/unit/test_import_direction.py` (AEA-01's `_imports`, `SRC`, two tests; AEA-04's and AEA-03's tests), `tests/journeys/affected.py` (`--base`, prints `N journeys affected`), `src/meridian/web/container.py` (`Container.settings` typed `Any`) | Tool config, the import this plan needs, the file this plan appends to |
| Sibling plans (read only) | `AEA-05.md` (imports `RuleMatches`, `SafetyKind` from `meridian.domain.turn`, `HandoffReason` from `meridian.domain.handoff`); every wave-1+ plan in `docs/plans/fanout/2026-10-21-build/` (168 `from meridian.domain/ports/config import …` names swept 2026-10-21; each exists in §4 under the module the consumer uses, except the §8.2 types) | Import paths this plan must keep |

---

## 2. Boundary

### 2.1 Files this ticket owns (the only files the implementer may create or edit)

| File | Create / modify | Written by |
|---|---|---|
| `src/meridian/domain/common.py` | create | implementer |
| `src/meridian/domain/records.py` | create | implementer |
| `src/meridian/domain/actions.py` | create | implementer |
| `src/meridian/domain/identity.py` | create | implementer |
| `src/meridian/domain/specialists.py` | create | implementer |
| `src/meridian/domain/handoff.py` | create | implementer |
| `src/meridian/domain/blocks.py` | create | implementer |
| `src/meridian/domain/turn.py` | create | implementer |
| `src/meridian/domain/tools.py` | create | implementer |
| `src/meridian/domain/state.py` | create | implementer |
| `src/meridian/domain/staff.py` | create | implementer |
| `src/meridian/ports/models.py` | create | implementer |
| `src/meridian/ports/runtime.py` | create | implementer |
| `src/meridian/config.py` | create | implementer |
| `src/meridian/adapters/sqlite/repos_{core,spend,identity,booking,cases,staff,ops}.py` | create (7 files) | implementer |
| `.env.example` (repo root, tracked; today it holds the parked names, §4.16) | rewrite whole file | implementer |
| `tests/unit/domain/test_conventions.py` | create | **test-writer (frozen)** |
| `tests/unit/domain/test_identity.py` | create | **test-writer (frozen)** |
| `tests/unit/test_config.py` | create | **test-writer (frozen)** |
| `tests/unit/domain/conftest.py` | create (fixtures for this folder only) | test-writer creates; implementer may **append** fixtures, never change existing ones |
| `tests/unit/domain/test_ids.py`, `test_enums.py`, `test_actions.py`, `test_handoff.py`, `test_bounds.py`, `test_state.py`, `test_turn.py`, `test_staff.py`, `test_wire_shapes.py` | create | implementer |
| `tests/unit/ports/test_protocol_shapes.py`, `tests/unit/ports/test_call_record.py` | create | implementer |
| `tests/unit/adapters/test_repo_shells.py` | create | implementer |
| `tests/unit/test_import_direction.py` | **append one function** (`test_domain_ports_config_imports`) and, if needed, one private helper prefixed `_aea02_`; the file already holds AEA-01's, AEA-04's and AEA-03's functions (never change them); AEA-05 appends after this merges | implementer |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-02.md` | create (journey record) | implementer |
| `.claude/reference/area-map.md` | edit the **A0 row's Status cell only** | implementer (context commit) |
| `docs/design/code-design.md` | extend the existing `**Built:**` line under `## 3. The module map (every path planned)` | implementer (context commit) |
| `.claude/state/icm-progress.md` | edit **one** row *Routes verified against code and tests* (the one whose evidence starts `2026-10-21: first backend slice AEA-04`) | implementer (context commit) |

### 2.2 Shared surfaces read, never edited

`pyproject.toml`, `uv.lock`, every `__init__.py` (AEA-01), `tests/conftest.py` (AEA-01), `tests/unit/*/__init__.py`
(AEA-01), `src/meridian/web/container.py` (AEA-01; `Container.settings` stays typed `Any`, so this ticket never edits
it), `tests/journeys/**` (AEA-01, AEA-57), `src/meridian/privacy/redact.py` (AEA-04), `src/meridian/policy/*` (AEA-01, AEA-03), `src/meridian/gates/*`
(AEA-05, AEA-12), the OpenAPI file and `UI_CONTRACTS.md`, `docs/ux/**`, `apps/web/**`, `docs/design/contracts/**`
(AEA-08 reconciles them; this plan only **reports** contradictions, §8.4), the issued data, `docs/parked/**`,
`docs/archive/**`.

### 2.3 Owned by other tickets — do not create

`GraphDeps`, `ModelsStatus` (AEA-21), `ModelGateway`, `ModelOutcome` (AEA-20), `Limits` (AEA-01),
`LangfuseExportSettings` (AEA-19), `EndedThread`, `Cleared`, `SqliteUnitOfWork` (AEA-10), `LoginSessions`,
`StaffAccess` (AEA-23), `RoleCard`, `ROLE_CARDS` (AEA-44), `WindowQuery`, `WindowsFound`, `OutOfArea`, `SlotTaken`,
`Refused` (AEA-28), case/demo view types of cases A-2 except `FollowUp` (AEA-02 follow-up ticket), `PROMISE_TABLE`,
`promise_for` (AEA-14), `match_rules` (AEA-05), `QuoteCheck`, `COMPLETION_WORDS` (AEA-15), `RunTurn`, `TurnResponse`
(AEA-40), `SpecialistSpec`, `RunOutcome`, `SpecialistRunner` (AEA-35), `ToolRegistry`, `ToolDispatcher` (AEA-22).

---

## 3. Requirements table

### 3.1 Acceptance criteria (the issue's, verbatim IDs) → implementation → verification

| AC | Requirement (short; full text in the issue) | How it is implemented (plan step) | Verified by |
|---|---|---|---|
| AC-1 | Every pydantic model in `domain/*`, `ports/*`, `config.py` uses `MeridianModel`'s config (`extra="forbid"`, frozen, `hide_input_in_errors`, `str_strip_whitespace`) | All models inherit `MeridianModel` or `LLMFacing` (§5 steps 2–14) | `tests/unit/domain/test_conventions.py::test_every_model_uses_meridian_config` (frozen) |
| AC-2 | Malformed IDs rejected with field, code, constraint | `_PatternId` str subclasses with `str_schema(pattern=…, strict=True)` (§4.2) | `tests/unit/domain/test_ids.py::test_malformed_ids_rejected` (parametrised) |
| AC-3 | A rejected value is absent from `SafeError` and `str()` of the error | `hide_input_in_errors`; `SafeError.from_validation_error` uses `errors(include_input=False)` | `test_conventions.py::test_rejected_value_absent_from_safe_error` (frozen) |
| AC-4 | Enum and status value sets equal their sources | Enums/Literals transcribed (§4) | `tests/unit/domain/test_enums.py` (reads the OpenAPI, never writes it) |
| AC-5 | `Settled.has` / `current_visit` / `only_turn` per WP-4F and graph-core §14 | `domain/actions.py` (§5 step 4, algorithm §4.4) | `tests/unit/domain/test_actions.py::test_wp4f_move_is_settled`, `::test_cancelled_visit_is_not_current`, `::test_change_request_keeps_original`, `::test_only_turn_filters_to_one_turn` |
| AC-6 | `Brief` accepts only the fixed 8-heading shape | `Brief` model validator (§4.7) | `tests/unit/domain/test_handoff.py::test_brief_shape` |
| AC-7 | Every sketched bound holds on both sides | `Field(ge/le/min_length/max_length)` as listed in §4 | `tests/unit/domain/test_bounds.py::test_bound` (parametrised, one case per side) |
| AC-8 | Reducers: `specialist_results` appends; `halt` first writer; `add_turn_events` | `operator.add`, `first_halt`, `add_turn_events` in `state.py` | `tests/unit/domain/test_state.py::test_reducers` |
| AC-9 | `CheckEvent` builders; `gate_result()` for the four `clear` kinds | `turn.py` classmethods (§4.9) | `tests/unit/domain/test_turn.py::test_check_event_builders`, `::test_gate_result_mapping` |
| AC-10 | Private values only in `SecretStr`; record types hold codes only | `SecretStr` fields; no free-text field on 4 record types | `test_conventions.py::test_secret_fields_absent_from_repr_and_dump`, `::test_record_types_hold_codes_only` (frozen) |
| AC-11 | `Locator` exactly one locator; `from_form` → `None` when incomplete | `identity.py` validator + classmethod (§4.5) | `tests/unit/domain/test_identity.py::test_locator_exactly_one`, `::test_from_form_incomplete_is_none` (frozen) |
| AC-12 | `Settings` builds from a complete environment with the code-default role maps; `.env.example` names = `Settings` names | `Settings.from_env`, `default_model_settings`, `ENV_NAMES` (§4.14); `.env.example` (§4.16) | `tests/unit/test_config.py::test_valid_environment_builds`, `::test_env_example_matches_settings` (frozen) |
| AC-13 | Jev in a structured/tool role, or a role in the wrong map, fails naming field and rule; a missing required secret names the variable | Typed role maps + `_every_role_once` validator; `SettingsError` | `test_config.py::test_jev_in_structured_or_tool_role_rejected`, `::test_role_in_wrong_map_rejected`, `::test_missing_required_secret_named` (frozen) |
| AC-14 | A sentinel secret is absent from `repr`, `str`, `role_model_map()`, error reports, logs | `SecretStr` everywhere; `SettingsError` built from `SafeError` | `test_config.py::test_secret_values_absent_from_repr_errors_and_logs` (frozen) |
| AC-15 | `langfuse_complete()` true only with all four; absent keys leave `Settings` valid | `Settings.langfuse_complete` | `test_config.py::test_langfuse_complete_needs_all_four` (16 combinations; frozen) |
| AC-16 | Ports have the DO-4 §12–§13 + addenda signatures; `CallRecord.from_provider` copies every field | `ports/models.py`, `ports/runtime.py` (§4.12–§4.13) | `uv run mypy` over `tests/unit/ports/test_protocol_shapes.py`; `uv run pytest tests/unit/ports/test_call_record.py` |
| AC-17 | Seven shells, one constructor each; `UnitOfWork`'s `TYPE_CHECKING` types resolve | §4.15; `ports/runtime.py` | `tests/unit/adapters/test_repo_shells.py::test_seven_shells_one_constructor`; `uv run mypy` |
| AC-18 | Dependency direction (static scan) | §4.0 import rules | `tests/unit/test_import_direction.py::test_domain_ports_config_imports` |
| AC-19 | `gate_result()` implements graph-core §3's whole table | `GateDecision.gate_result` (§4.9) | `tests/unit/domain/test_turn.py::test_gate_result_table` |
| AC-20 | `ROLE_ACTIONS`, `CUSTOMER_SPEAKER_NAME` equal staff.md §1 and the OpenAPI enum | `domain/staff.py` (§4.11) | `tests/unit/domain/test_staff.py::test_role_actions_and_customer_speaker_match_staff_md` |
| AC-21 [journey] | Runs no journey yet; record at `mock-tested`, *Blocked by* AEA-57, journeys J-1…J-10 named | Record file (§5 step 19) | `docs/testing/journeys/<date>-AEA-02.md`; `uv run python -m tests.journeys.affected --base main` prints `0 journeys affected` |
| AC-22 | Context updated in the same change | Context commit (§5 step 21); DO-4 contradictions reported in §8.4 | `git diff` of the three context files |

### 3.2 Plan-added criteria (reconciliation found them; the issue gets a comment proposing them)

| ID | Obligation | Source | Verified by |
|---|---|---|---|
| PA-1 | Every domain module imports on its own in a fresh interpreter (no import cycle) | DO-3 §2.1; the type-home table in §4.0 | `test_conventions.py::test_each_domain_module_imports_alone` (frozen with the file) |
| PA-2 | Every wire-facing model's field names equal its OpenAPI schema's property names (blocks, payloads, `Notice`, `SettledView`, `FollowUp`, `InboxMessage` minus `body`); `ReplyBlock` and `TurnPayload` discriminator values equal the OpenAPI mappings | ticket: "every member takes its fields from the OpenAPI schema of the same name"; graph-core §13 | `tests/unit/domain/test_wire_shapes.py::test_wire_models_match_openapi`, `::test_union_discriminators_match_openapi` |
| PA-3 | `CodePayload.code` accepts exactly six ASCII digits; error carries no digits | OpenAPI `CodePayload.code` pattern `^[0-9]{6}$` | `test_bounds.py::test_bound` (two cases) + AC-10 test |

### 3.3 Frozen tests (the test-writer writes these first; the implementer must not edit them)

The issue freezes AC-3, AC-10, AC-11, AC-13, AC-14, AC-15. To keep the tamper check per file, **the three files that
hold those tests are frozen whole**, so AC-1, AC-12 and PA-1 (same files) are frozen with them.

| Frozen file | Functions (exact names) | AC |
|---|---|---|
| `tests/unit/domain/test_conventions.py` | `test_every_model_uses_meridian_config` | AC-1 |
| | `test_rejected_value_absent_from_safe_error` | AC-3 |
| | `test_secret_fields_absent_from_repr_and_dump` | AC-10 |
| | `test_record_types_hold_codes_only` | AC-10 |
| | `test_each_domain_module_imports_alone` | PA-1 |
| `tests/unit/domain/test_identity.py` | `test_locator_exactly_one` (parametrised) | AC-11 |
| | `test_from_form_incomplete_is_none` (parametrised) | AC-11 |
| `tests/unit/test_config.py` | `test_valid_environment_builds` | AC-12 |
| | `test_env_example_matches_settings` | AC-12 |
| | `test_jev_in_structured_or_tool_role_rejected` (parametrised; WP pair 2) | AC-13 |
| | `test_role_in_wrong_map_rejected` (parametrised) | AC-13 |
| | `test_missing_required_secret_named` (parametrised over 5 names) | AC-13 |
| | `test_secret_values_absent_from_repr_errors_and_logs` | AC-14 |
| | `test_langfuse_complete_needs_all_four` (parametrised, 16 cases) | AC-15 |

What each frozen test asserts is specified in §7.2. Red-for-the-right-reason before the implementer starts:
`ModuleNotFoundError: No module named 'meridian.domain.<x>'` / `'meridian.config'`.

### 3.4 Source-contract reconciliation (obligations the sources place on this ticket)

| Obligation | Governing source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| Types and homes per DO-3 §3, shapes per DO-4 + addenda | DO-4 §16 | yes | in-ticket (AC-1…AC-20) | §5 steps 2–15 |
| `domain/` may import only pydantic, stdlib, `domain` | DO-3 §2.1 | AC-18 | in-ticket; **requires moving five types' definitions** (§4.0) | §5 steps 2–12 |
| `CallRecord` (ports) is a field of `SpecialistResult` (domain) | DO-4 §5 vs models.md §1 + DO-3 §2.1 | no | added: define `Role`, `ProviderName`, `ProviderCall`, `CallRecord` in `domain/common.py`, re-export from `ports/models.py` (precedent: `SpanHandle`, graph-core §1, X-1) | §4.0; reported §8.4 |
| `RetrievalResult` (ports) is a field of `KnowledgeCapture` (domain) | DO-4 §13 vs graph-tools §3 | no | added: define in `domain/records.py`, re-export from `ports/runtime.py` | §4.0 |
| `ExportStatus` (ports) is a field of `TurnRecord` (domain) | models.md §4 vs graph-core §2 | no | added: define in `domain/turn.py`, re-export from `ports/runtime.py` | §4.0 |
| Types named but never sketched | ticket "Types DO-4 names that no section sketches" | yes | **not built**, listed as blocked-on their owning topic (§8.2); containing types built without those fields | §8.2 |
| `HandoffReason.BURNING_RULED_OUT` | CAS-16 option A; sign-off D-14 | yes (AC-4 count 16) | in-ticket | §4.1 |
| Errors never carry values; one module for stable codes | `safe-validation-errors.md` rules 1–5 | AC-3 | in-ticket | `SafeError` §4.1 |
| `TurnTrace` / `ExportStatus` equal DO-6 *Status values* | DO-6 lines 52–54; models.md §4 | AC-4 | in-ticket | §4.9 |
| No field that carries a code, card, phone or token into a record | DO-6 *Content and redaction* | AC-10 | in-ticket | §4 |
| The journey criterion | `integrated-journeys.md` §3 rule 1, §4 | AC-21 | in-ticket (record at `mock-tested`) | step 19 |
| Context rows | `context-maintenance.md` 1, 3, 6 | AC-22 | in-ticket | step 21 |
| Capture checks CAP-1…CAP-3 | DO-6 | no | other-ticket (AEA-51); AC-4/AC-10 are component guards only | — |
| E-1 WP-4F state seam | DO-5 | indirectly | other-ticket (AEA-51 runs it); AC-5 is the unit guard | — |
| `ModelOutcome` (DO-4 §12) | DO-4 §12 | not in the ticket's lists | other-ticket: AEA-20 (`agent/gateway.py`) | §8.3 |

### 3.5 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

---

## 4. Shared code to use (exact shapes)

### 4.0 Module rules that apply to every file

1. **First line after the docstring:** `from __future__ import annotations`. Import dates as `import datetime as dt`
   and write `dt.date` / `dt.datetime` everywhere (several models have a field named `date`).
2. **One field per line.** The sketches below use `;` as shorthand; ruff `E702` rejects it in code. Never put two
   statements on one line.
3. **Absolute imports only** (`from meridian.domain.common import …`). No relative imports (the AC-18 scan rejects them).
4. **Allowed imports.** `domain/*`: standard library, `pydantic`, `pydantic_core`, `meridian.domain.*`. `ports/*`: the
   same plus, **only under `if TYPE_CHECKING:`**, `meridian.adapters.sqlite.repos_*`. `config.py`: standard library,
   `pydantic`, `pydantic_core`, `meridian.domain.*`, `meridian.ports.*`, `meridian.privacy.redact`. `typing_extensions`
   is not allowed (Python 3.12's `typing` has everything). Never import `anthropic`, `httpx`, `fastembed`, `langfuse`,
   `langgraph`, `sqlite3` here (the repository shells import `sqlite3`; they are not in the scan set).
5. **Re-exports.** Where §4.0's table says "defined in X, re-exported from Y", Y contains
   `from meridian.domain.X import Name as Name` (the `as Name` form marks it public for mypy strict and ruff).
   Consumers import from the home the ticket names (e.g. `from meridian.domain.handoff import HandoffReason`); both
   names are the same object.
6. **No module-level instances** other than immutable constants (`MappingProxyType`, tuples, frozensets, strings,
   regex strings). No settings object, no client, no clock read at import time.
7. **Errors.** A validator raises `pydantic_core.PydanticCustomError(<stable code>, <message>)`. The message names the
   rule and may name codes (a role, a heading number); it never contains an input value.
8. **Generics** use PEP 695 syntax (`class Attempt[T: BaseModel](MeridianModel)`), proven in a scratch run with mypy
   strict + `pydantic.mypy` (AEA-01's config) and pydantic 2.14.
9. **Mypy strict with `init_typed = true`** (AEA-01's `pyproject.toml`): in source and tests, build an ID field from a
   literal as `ThreadId("…")`, an enum field as `ActionKind.MOVED`; pass deliberately invalid input with
   `Model.model_validate({...})`, never through the constructor.

**Why some types are defined below their ticket home (decided here, engineering).** The ticket's homes form import
cycles (`actions.OpenCase` needs `handoff` types while `handoff.HandoffResult` needs `actions.CompletedAction`;
`turn` needs `state` parts while `state` needs `turn`; `specialists` needs `ToolCallRecord` while `tools.ToolResult`
needs the specialist captures; `specialists` needs the ports' `CallRecord` while `domain` may not import `ports`).
The fix keeps every import path the ticket and the sibling tickets use, and changes no shape: each type below is
**defined** in a lower module and **re-exported** from its home.

| Type | Defined in | Re-exported from (its home) | Why |
|---|---|---|---|
| `HandoffReason`, `Priority`, `Presence`, `CaseState`, `Promise`, `FollowUp` | `domain/common.py` | `domain/handoff.py` | `actions.OpenCase` needs them; `handoff` needs `actions` |
| `SafetyKind` | `domain/common.py` | `domain/turn.py` | `handoff.HandoffRequest` needs it; `turn` is above `handoff` |
| `ToolKind`, `ToolCallRecord` | `domain/common.py` | `domain/tools.py` | `specialists` results hold `ToolCallRecord`; `tools` is above `specialists` |
| `FailureCounters` | `domain/common.py` | `domain/state.py` | `turn.EscalationInputs` needs it |
| `Role`, `ProviderName`, `ProviderCall`, `CallRecord` | `domain/common.py` | `ports/models.py` | `specialists` results hold `CallRecord`; `domain` may not import `ports` |
| `ShownSlot` | `domain/records.py` | `domain/state.py` | `specialists` and `turn` need it |
| `RetrievalResult` | `domain/records.py` | `ports/runtime.py` | `specialists.KnowledgeCapture` holds it |
| `FormValues` | `domain/identity.py` | `domain/turn.py` | `identity.Locator.from_form` takes it |
| `IdentityState` | `domain/identity.py` | `domain/state.py` | `handoff.HandoffRequest` and `turn.EscalationInputs` hold it |
| `ExportStatus`, `SpanHandle` | `domain/turn.py` | `ports/runtime.py` | `TurnRecord`, `TurnContext` hold them (SpanHandle: graph-core §1) |

**Import order (low → high), which must hold:** `common` → `records` → `actions` → `identity` → `specialists` →
`handoff` → `blocks` → `turn` → `tools` → `state`; `staff` imports `common` only. `ports/models.py` and
`ports/runtime.py` import `domain`; `config.py` imports `domain`, `ports.models`, `privacy.redact`. A module never
imports one to its right. PA-1's test catches a cycle.

### 4.1 `src/meridian/domain/common.py`

```python
from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler, ValidationError
from pydantic_core import core_schema


class MeridianModel(BaseModel):
    """Base for every typed hand-off (DO-4 §0). Errors never carry the input."""
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)


class LLMFacing(MeridianModel):
    """Schemas a model fills; extra="forbid" makes an invented field a loud failure. Pipeline-assigned fields
    (ids, times, turn_id) never appear here."""


class _PatternId(str):
    """A str subclass validated by one regex (DO-4 §0 'validated ID types'). Error code: string_pattern_mismatch."""
    PATTERN: ClassVar[str] = ""

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(pattern=cls.PATTERN, strict=True),
            serialization=core_schema.to_string_ser_schema(),
        )

_UUID4_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"   # canonical, lower case

class ThreadId(_PatternId):   PATTERN = _UUID4_PATTERN          # minted by SessionService.open (CON-1)
class TurnId(_PatternId):     PATTERN = _UUID4_PATTERN          # minted by the browser per CON-2 send
class RequestId(_PatternId):  PATTERN = _UUID4_PATTERN          # minted by middleware
class CustomerId(_PatternId): PATTERN = r"^MHC-[0-9]{5}$"
class InvoiceId(_PatternId):  PATTERN = r"^INV-[0-9]{6}$"
class CaseRef(_PatternId):    PATTERN = r"^MHC-C-[0-9]{4}$"
class PassageId(_PatternId):  PATTERN = r"^[^#\s]+#[0-9]+$"     # "<file path>#<chunk n>"
EventId = Annotated[int, Field(ge=0)]                            # monotonically increasing per stream; 0 = none yet
```

Use `[0-9]`, never `\d` (Python's `\d` matches non-ASCII digits). Put each class on its own lines (the table layout
above is for reading).

```python
class SafeError(MeridianModel):
    """One validation problem as a caller may serialise it: field, stable code, constraint; never the input."""
    field: str                 # dotted loc, e.g. "values.customer_id"; "" for a model-level rule
    code: str                  # pydantic error type or our PydanticCustomError type, e.g. "string_pattern_mismatch"
    constraint: str            # pydantic's message for that type (it never interpolates the input)

    @classmethod
    def from_validation_error(cls, exc: ValidationError) -> tuple[SafeError, ...]:
        # for err in exc.errors(include_url=False, include_context=False, include_input=False):
        #     cls(field=".".join(str(p) for p in err["loc"]), code=err["type"], constraint=err["msg"])
        ...

class ApiErrorCode(StrEnum):   # = OpenAPI Notice.code (6) ∪ ErrorBlock.code (7) ∪ ApiError.error.code (22); 35 members
    # composed notices (HTTP 200, NoticeBlock + Notice)
    TURN_TIMEOUT = "TURN_TIMEOUT"; BUSY = "BUSY"; SPEND_CAP_REACHED = "SPEND_CAP_REACHED"; RATE_LIMITED = "RATE_LIMITED"
    BOOKING_CAP = "BOOKING_CAP"; AI_PAUSED = "AI_PAUSED"
    # composed errors (HTTP 200, ErrorBlock)
    SLOT_TAKEN = "SLOT_TAKEN"; OUT_OF_AREA = "OUT_OF_AREA"; CODE_WRONG = "CODE_WRONG"; CODE_EXPIRED = "CODE_EXPIRED"
    CODE_LOCKED = "CODE_LOCKED"; CODE_CAP_REACHED = "CODE_CAP_REACHED"; NOT_VERIFIED = "NOT_VERIFIED"
    # HTTP errors (ApiError {code, field, constraint, details})
    VALIDATION_ERROR = "VALIDATION_ERROR"; UNAUTHENTICATED = "UNAUTHENTICATED"; LOGIN_FAILED = "LOGIN_FAILED"
    LOGIN_RATE_LIMITED = "LOGIN_RATE_LIMITED"; REQUEST_RATE_LIMITED = "REQUEST_RATE_LIMITED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"; SESSION_ENDED = "SESSION_ENDED"; TURN_IN_PROGRESS = "TURN_IN_PROGRESS"
    RESET_IN_PROGRESS = "RESET_IN_PROGRESS"; RESET_FAILED = "RESET_FAILED"; HANDOFF_FAILED = "HANDOFF_FAILED"
    ROLE_NOT_ALLOWED = "ROLE_NOT_ALLOWED"; CASE_NOT_FOUND = "CASE_NOT_FOUND"; FLAG_NOT_FOUND = "FLAG_NOT_FOUND"
    CASE_ALREADY_CLAIMED = "CASE_ALREADY_CLAIMED"; VERSION_CONFLICT = "VERSION_CONFLICT"
    NOT_ALLOWED_IN_STATE = "NOT_ALLOWED_IN_STATE"; REASON_REQUIRED = "REASON_REQUIRED"
    WAKE_UP_REQUIRED = "WAKE_UP_REQUIRED"; OUTCOME_REQUIRED = "OUTCOME_REQUIRED"; NOT_LIVE = "NOT_LIVE"
    NOT_CLAIMED_BY_YOU = "NOT_CLAIMED_BY_YOU"
    # NOT present: STAFF_AUTH_REQUIRED (web.md §1, WEB-9)

class ToolErrorCode(StrEnum):  # graph-tools §1, 13 values
    NOT_ALLOWED = "not_allowed"; BAD_ARGUMENTS = "bad_arguments"; UNKNOWN_TOOL = "unknown_tool"
    NOT_VERIFIED = "not_verified"; NOT_SHOWN = "not_shown"; FEE_BEARING = "fee_bearing"
    OUTSIDE_SERVICE_AREA = "outside_service_area"; SLOT_TAKEN = "slot_taken"; BOOKING_CAP = "booking_cap"
    IDENTICAL_CALL = "identical_call"; TOOL_FAILED = "tool_failed"
    WRONG_SERVICE_TYPE = "wrong_service_type"; NOT_OWNED = "not_owned"

class ToolKind(StrEnum):       # graph-tools §1, 7 values (home: domain/tools.py, re-exported there)
    KB_SEARCH = "kb_search"; ACCOUNT_READ = "account_read"; SLOT_SEARCH = "slot_search"
    BOOK = "book"; MOVE = "move"; CANCEL = "cancel"; CHANGE_REQUEST = "change_request"

class ProviderFailureKind(StrEnum):   # DO-4 §11, 14 values
    TIMEOUT = "timeout"; CONNECTION = "connection"; RATE_LIMITED = "rate_limited"; OVERLOADED = "overloaded"
    SERVER = "server"; PROVIDER_SPEND_CAP = "provider_spend_cap"; OUR_SPEND_LIMIT = "our_spend_limit"
    BAD_REQUEST = "bad_request"; AUTH = "auth"; NOT_FOUND = "not_found"; BODY_ERROR = "body_error"
    REFUSAL = "refusal"; MAX_TOKENS = "max_tokens"; INVALID_OUTPUT = "invalid_output"

ProviderName = Literal["anthropic", "openrouter_jev"]   # models.md §1 (home: ports/models.py)

class ProviderFailure(MeridianModel):  # DO-4 §11
    kind: ProviderFailureKind
    provider: ProviderName
    http_status: int | None
    retry_after_s: float | None
    retryable: bool
    provider_request_id: str | None

class HaltReason(StrEnum):   # DO-4 §11, 8 values
    DEADLINE = "deadline"; BRAKE_TASKS = "brake_tasks"; BRAKE_TOOL_ROUNDS = "brake_tool_rounds"
    BRAKE_SONNET_CALLS = "brake_sonnet_calls"; BRAKE_IDENTICAL_CALL = "brake_identical_call"
    RECURSION_LIMIT = "recursion_limit"; SPEND_CAP = "spend_cap"; PROVIDER_SPEND_CAP = "provider_spend_cap"

class Halt(MeridianModel):
    reason: HaltReason
    node: str
    elapsed_ms: int

class Role(StrEnum):   # DO-4 §12 (home: ports/models.py)
    PLANNER = "planner"; CLASSIFIER = "classifier"; PLANNER_FALLBACK = "planner_fallback"
    SPECIALIST = "specialist"; RESPONDER = "responder"; BRIEF = "brief"

class ProviderCall(MeridianModel):   # models.md §1 (home: ports/models.py)
    provider: ProviderName
    model: str
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    thinking_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    cost_source: Literal["reported", "price_table"]
    status: Literal["ok", "error"]
    failure: ProviderFailure | None
    provider_request_id: str | None
    stop_reason: str | None

class CallRecord(ProviderCall):   # models.md §1 (home: ports/models.py)
    role: Role
    attempt: int = Field(ge=1, le=2)

    @classmethod
    def from_provider(cls, call: ProviderCall, *, role: Role, attempt: int) -> CallRecord:
        # return cls.model_validate({**call.model_dump(), "role": role, "attempt": attempt})
        ...

class HandoffReason(StrEnum):   # DO-4 §7 (15) + CAS-16 option A (D-14) = 16 (home: handoff.py)
    SAFETY = "safety"; DANGER = "danger"; BURNING_UNCLEAR = "burning_unclear"
    CUSTOMER_REQUESTED_PERSON = "customer_requested_person"; REFUND = "refund"; BILLING_DISPUTE = "billing_dispute"
    COMPLAINT_OR_MANAGER = "complaint_or_manager"; LEGAL_OR_CHARGEBACK = "legal_or_chargeback"; COMMERCIAL = "commercial"
    LATE_TECHNICIAN = "late_technician"; FEE_BEARING_CHANGE = "fee_bearing_change"; MEMBERSHIP_CANCEL = "membership_cancel"
    UNSUPPORTED_ACTION = "unsupported_action"; IDENTITY_UNVERIFIED = "identity_unverified"; AI_FAILURE = "ai_failure"
    BURNING_RULED_OUT = "burning_ruled_out"

class Priority(StrEnum):   # (home: handoff.py)
    P0 = "P0"; P1 = "P1"; P2 = "P2"; P3 = "P3"; P4 = "P4"

Presence = Literal["nobody_online", "simulated_on_shift"]   # cases.md A-1 (home: handoff.py)
CaseState = Literal["live_queued", "unassigned", "claimed", "in_progress", "waiting", "resolved", "closed_unresolved"]
    # (home: handoff.py) = OpenAPI CaseSummary.lifecycle enum; DO-4 names it without values

class Promise(MeridianModel):   # DO-4 §7; fields only, NO text validator (graph-core §10, GRC-2) (home: handoff.py)
    policy_row: str
    text: str
    due_at: dt.datetime | None
    due_label: str | None
    extra_lines: tuple[str, ...] = ()
    live_queued: bool = False

class FollowUp(MeridianModel):   # = OpenAPI FollowUpView (cases.md §5) (home: handoff.py)
    channel: Literal["email", "phone"]
    destination_label: str
    on_record: bool
    window: Literal["morning", "afternoon", "any"]
    saved_line: str

class SafetyKind(StrEnum):   # DO-4 §3 (home: turn.py, R-G-1)
    GAS = "gas"; CO = "co"; SPARKS_SMOKE_FLAMES = "sparks_smoke_flames"; BURNING_WITH_BREAKER = "burning_with_breaker"

class ToolCallRecord(MeridianModel):   # graph-tools §1 (home: tools.py)
    tool_call_id: str
    name: str = Field(max_length=64)   # as the model sent it; dispatch truncates an unknown name to 64 chars
    kind: ToolKind | None
    outcome: Literal["ok", "refused", "failed"]
    error: ToolErrorCode | None
    record_ids: tuple[str, ...]
    passage_ids: tuple[PassageId, ...]
    lookup_id: int | None
    elapsed_ms: int

class FailureCounters(MeridianModel):   # DO-4 §1 (home: state.py); writers: graph-core §8
    failed_answers: int = 0
    tool_failures: int = 0
    identity_failures: int = 0
    corrections: int = 0
    timeouts: int = 0
    bookings: int = 0
```

### 4.2 `src/meridian/domain/records.py`

```python
Zone = Literal["north", "central", "south"]                                   # cases.md §2 (CAS-34)
Window = Literal["08:00-12:00", "12:00-16:00", "13:00-17:00", "16:00-19:00"]  # issued appointment_slots CHECK
ServiceType = Literal["hvac_repair", "hvac_tune_up", "plumbing", "estimate"]   # issued appointment_slots CHECK
MembershipTier = Literal["none", "standard", "plus"]                           # issued customers CHECK

class FeeNote(MeridianModel):   # cases.md §2, transcribed unchanged (R-G-2)
    service_type: ServiceType
    tier: MembershipTier
    fee_row: str | None
    amount_cents: int = Field(ge=0)
    waived: bool
    line: str = Field(min_length=1, max_length=120)

class Customer(MeridianModel):   # issued customers columns (SCHEMA.md); decision §8.1 D-5
    customer_id: CustomerId
    name: str
    phone: SecretStr
    email: SecretStr | None
    service_address: str
    city: str
    zip: str
    membership_tier: MembershipTier
    membership_renewal_date: dt.date | None
    system_brand: str | None
    system_install_date: dt.date | None

class Technician(MeridianModel):   # issued technicians columns; skills parsed from the comma list
    tech_id: int
    name: str
    skills: tuple[Literal["hvac", "plumbing", "estimate"], ...]
    home_zone: Zone

class InvoiceLineItem(MeridianModel):   # one element of invoices.line_items JSON ({desc, cents})
    desc: str
    cents: int

class Invoice(MeridianModel):   # issued invoices columns
    invoice_id: InvoiceId
    customer_id: CustomerId
    appointment_id: int | None
    issued_date: dt.date
    due_date: dt.date
    amount_cents: int
    balance_cents: int
    line_items: tuple[InvoiceLineItem, ...]

class Slot(MeridianModel):   # cases.md §4.1 (CAS-36)
    slot_id: int
    slot_date: dt.date
    window: Window
    tech_id: int
    zone: Zone
    service_type: ServiceType
    status: Literal["open", "booked", "reserved_members", "blocked"]

class Appointment(MeridianModel):   # cases.md §4.1 (CAS-36)
    appointment_id: int
    slot_id: int
    customer_id: CustomerId
    issue_description: str
    created_at: dt.date
    status: Literal["scheduled", "completed", "cancelled", "no_show"]
    is_warranty_visit: bool

class Passage(MeridianModel):   # DO-4 §5
    passage_id: PassageId
    file: str
    section: str
    version_label: str
    version_date: dt.date | None
    text: str
    score: float

class RetrievalResult(MeridianModel):   # DO-4 §13 (home: ports/runtime.py)
    passages: tuple[Passage, ...]
    below_floor: bool

class ShownSlot(MeridianModel):   # DO-4 §1 (home: state.py)
    slot_id: int
    date: dt.date
    window: Window
    technician: str
    service_type: ServiceType
    zone: Zone
    member_reserved: bool
    shown_turn: TurnId
```

### 4.3 `src/meridian/domain/actions.py`

```python
class ActionKind(StrEnum):   # DO-4 §1, 7 values
    BOOKED = "booked"; MOVED = "moved"; CANCELLED = "cancelled"; CHANGE_REQUEST_SENT = "change_request_sent"
    CASE_OPENED = "case_opened"; FOLLOWUP_SAVED = "followup_saved"; VERIFIED = "verified"

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

class OpenCase(MeridianModel):
    case_ref: CaseRef
    reason: HandoffReason
    priority: Priority
    state: CaseState
    promise: Promise
    followup: FollowUp | None
    live_queued: bool

class VisitChange(MeridianModel):   # graph-core §14 = OpenAPI SettledVisit.change_request
    change: Literal["move", "cancel"]
    wanted_text: str
    fee_line: str

class VisitView(MeridianModel):   # graph-core §14 = OpenAPI SettledVisit minus window_label
    appointment_id: int
    date: dt.date
    window: Window
    technician: str
    service_type: ServiceType
    fee_line: str
    status: Literal["booked", "moved", "original_stays"]
    change_request: VisitChange | None

class Settled(MeridianModel):
    """Everything the conversation has done. Built ONLY from actions + cases/promises rows."""
    actions: tuple[CompletedAction, ...]
    open_case: OpenCase | None
    read_at: dt.datetime
    def has(self, kind: ActionKind, record_id: str | None = None) -> bool: ...
    def current_visit(self) -> VisitView | None: ...
    def only_turn(self, turn_id: TurnId) -> Settled: ...
```

**Algorithms (pure; no I/O; the invariant each step protects):**

`has(kind, record_id=None)`:
1. Return `True` if any `a` in `actions` has `a.kind == kind` and (`record_id is None` or `a.key.record_id ==
   record_id`); else `False`. *Invariant:* "done" is answered from stored actions only (R-46).

`current_visit()`:
1. Number the actions by position: `ordered = sorted(enumerate(self.actions), key=lambda p: (p[1].at, p[0]))`.
   "Later" means a greater `(at, position)`. *Invariant:* ties in `at` keep stored order.
2. Walk `ordered` from newest to oldest. Consider only `a.kind in {BOOKED, MOVED}` with `"appointment" in a.records`.
3. Skip it if any **later** action has `kind == CANCELLED` and the same `records["appointment"]`. *Invariant:* a
   cancelled visit is never "the visit"; it stays in `actions`.
4. The first one not skipped is the visit. If none, return `None`.
5. Find the **latest later** action with `kind == CHANGE_REQUEST_SENT` and the same `records["appointment"]`.
6. Build with `VisitView.model_validate({...})` from: `appointment_id = int(records["appointment"])`; `date`,
   `window`, `technician`, `service_type`, `fee_line` from the visit's `after` dict (strings; pydantic parses the
   date); if step 5 found one: `status="original_stays"`, `change_request = {"change", "wanted_text", "fee_line"}`
   from **that** action's `after`; else `status = visit.kind.value` (`"booked"` or `"moved"`), `change_request=None`.
   *Invariant:* the panel and the words read the same rows (N-27). A missing `after` key raises `ValidationError`
   (loud: X-10 obliges AEA-28 to write the keys).

`only_turn(turn_id)`:
1. `kept = tuple(a for a in actions if a.key.turn_id == turn_id)`.
2. `open_case` is kept only if some action in `kept` has `kind == CASE_OPENED` and `key.record_id ==
   open_case.case_ref`; otherwise `None`. *Invariant:* R-46's literal "this turn" reading (DO-4 §10, review C-1).
3. Return `Settled(actions=kept, open_case=…, read_at=self.read_at)`.

### 4.4 `src/meridian/domain/identity.py`

```python
class FormValues(MeridianModel):   # DO-4 §3 (home: turn.py); CON-2 form payload values
    name: str | None = None
    phone: SecretStr | None = None
    customer_id: CustomerId | None = None
    invoice_number: InvoiceId | None = None
    zip_or_city: str | None = None

class Locator(MeridianModel):   # graph-tools §5
    name: str | None = None
    phone: SecretStr | None = None
    customer_id: CustomerId | None = None
    invoice_number: InvoiceId | None = None
    # model_validator(mode="after") _exactly_one: see rule below
    @classmethod
    def from_form(cls, form: FormValues) -> Locator | None: ...

class Located(MeridianModel):        kind: Literal["located"] = "located"; masked_hint: str
class NotVerified(MeridianModel):    kind: Literal["not_verified"] = "not_verified"          # no other field
class CodeSent(MeridianModel):       kind: Literal["code_sent"] = "code_sent"; masked_hint: str; expires_at: dt.datetime; sends_left: int = Field(ge=0, le=2)
class CodeCapReached(MeridianModel): kind: Literal["code_cap_reached"] = "code_cap_reached"
class Verified(MeridianModel):       kind: Literal["verified"] = "verified"; customer_id: CustomerId; action: CompletedAction
class CodeWrong(MeridianModel):      kind: Literal["code_wrong"] = "code_wrong"; tries_left: int = Field(ge=1, le=2)
class CodeExpired(MeridianModel):    kind: Literal["code_expired"] = "code_expired"; resend_offered: bool; sends_left: int = Field(ge=0, le=2)
class CodeLocked(MeridianModel):     kind: Literal["code_locked"] = "code_locked"

IdentityStep = Annotated[
    Located | NotVerified | CodeSent | CodeCapReached | Verified | CodeWrong | CodeExpired | CodeLocked,
    Field(discriminator="kind"),
]   # decision §8.1 D-7: the identity node maps a service result to IdentityStep (graph-tools §5; graph-core §8)

class InboxMessage(MeridianModel):   # graph-tools §5 = OpenAPI InboxMessage minus `body` (the route renders it)
    id: str
    at: dt.datetime
    to_masked: str
    code: SecretStr | None
    status: Literal["active", "used", "expired"]
    expires_at: dt.datetime

class IdentityState(MeridianModel):   # DO-4 §1 (home: state.py)
    status: Literal["not_checked", "located", "code_sent", "verified", "not_verified", "locked"]
    customer_id: CustomerId | None
    masked_hint: str | None
    code_expires_at: dt.datetime | None
    tries_left: int = Field(ge=0, le=3)
    codes_sent: int = Field(ge=0, le=3)
    verified_at: dt.datetime | None
```

**`Locator` rule (AC-11):**
1. A field "is set" when it is not `None` and, for `name`, its stripped text is non-empty; for `phone`,
   `phone.get_secret_value().strip()` is non-empty.
2. `pair = name set and phone set`; `half = exactly one of name/phone set`; `groups = pair + (customer_id set) +
   (invoice_number set)` (count of true values).
3. The validator raises `PydanticCustomError("locator_combination", "exactly one locator: name and phone together,
   or customer_id, or invoice_number")` when `half` is true or `groups != 1`. *Invariant:* no value in the message.
4. `from_form(form)`: compute the same `pair`, `customer_id set`, `invoice_number set` on the form (ignoring
   `zip_or_city`). If exactly one of the three groups is complete **and** `half` is false, return
   `Locator(...)` with only that group's fields; otherwise return `None` (incomplete, empty, or two complete groups).
   Never raises. *Decision §8.1 D-8.*

### 4.5 `src/meridian/domain/specialists.py`

```python
class ConfirmationView(MeridianModel):   # DO-4 §5 comment "date, window, technician, fee_note (R-20)"
    date: dt.date
    window: Window
    technician: str
    fee_note: FeeNote

class WriteResult(MeridianModel):
    action: CompletedAction
    confirmation: ConfirmationView

class ChangeRequestDraft(MeridianModel):
    appointment_id: int
    change: Literal["move", "cancel"]
    wanted_text: str
    windows_shown: tuple[int, ...]
    hours_before: float
    window_start: dt.datetime

class KnowledgePoint(MeridianModel):
    text: str = Field(max_length=500)
    passage_id: PassageId
    # "must be a passage returned in this run": enforced by AEA-35's builder (RunOutcome.passages_returned), not here (§8.3)

class InvoiceLineView(MeridianModel):  description: str; amount_cents: int
class InvoiceView(MeridianModel):      invoice_id: InvoiceId; lines: tuple[InvoiceLineView, ...]; total_cents: int; balance_cents: int; issued_on: dt.date; due_on: dt.date; paid: bool
class MembershipView(MeridianModel):   tier: MembershipTier; renewal_date: dt.date | None
class WarrantyView(MeridianModel):     install_date: dt.date; equipment_brand: str | None; sentence: str
class StaffNote(MeridianModel):
    kind: Literal["billed_differs_from_schedule", "diagnostic_without_credit"]
    record_id: InvoiceId
    text: str = Field(max_length=300)
    source_file: Literal["pricing/2026_fee_schedule.pdf", "faq/customer_faq.md"]

class KnowledgeCapture(MeridianModel):   kind: Literal["knowledge"] = "knowledge"; result: RetrievalResult
class AccountCapture(MeridianModel):
    kind: Literal["account"] = "account"
    invoices: tuple[InvoiceView, ...] = ()
    membership: MembershipView | None = None
    warranty: WarrantyView | None = None
    staff_notes: tuple[StaffNote, ...] = ()
class SchedulingCapture(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
    windows: tuple[ShownSlot, ...] = ()
    write: WriteResult | None = None
    change_request: ChangeRequestDraft | None = None
    refused: ToolErrorCode | None = None

class AppointmentView(MeridianModel):   # graph-tools §3 (R-G-19)
    appointment_id: int
    date: dt.date
    window: Window
    service_type: ServiceType
    technician: str | None
    is_warranty_visit: bool

class SchedulingSliceInputs(MeridianModel):
    zone: Zone | None
    member: bool
    appointments: tuple[AppointmentView, ...] = ()

class SchedulingSlice(MeridianModel):   # DO-4 §5
    customer_zone: Zone | None
    member: bool
    appointments: tuple[AppointmentView, ...]
    shown_slots: tuple[ShownSlot, ...]
    pending_change: bool
    bookings_left: int

class KnowledgeResult(MeridianModel):
    kind: Literal["knowledge"] = "knowledge"
    status: Literal["answered", "no_current_source", "failed"]
    passages: tuple[Passage, ...]
    points: tuple[KnowledgePoint, ...]
    quick_checks: tuple[PassageId, ...] = ()
    tools: tuple[ToolCallRecord, ...]
    calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None
    failure: ProviderFailure | None = None

class AccountResult(MeridianModel):
    kind: Literal["account"] = "account"
    status: Literal["read", "not_verified", "failed"]
    invoices: tuple[InvoiceView, ...] = ()
    membership: MembershipView | None = None
    warranty: WarrantyView | None = None
    staff_notes: tuple[StaffNote, ...] = ()
    tools: tuple[ToolCallRecord, ...]
    calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None
    failure: ProviderFailure | None = None

class SchedulingResult(MeridianModel):
    kind: Literal["scheduling"] = "scheduling"
    status: Literal["windows_shown", "written", "staff_change_request", "slot_taken", "out_of_area", "no_fit",
                    "not_verified", "booking_cap", "failed"]
    windows: tuple[ShownSlot, ...] = ()
    write: WriteResult | None = None
    change_request: ChangeRequestDraft | None = None
    quick_checks: tuple[Passage, ...] = ()   # graph-tools §3 (GRT-8)
    tools: tuple[ToolCallRecord, ...]
    calls: tuple[CallRecord, ...]
    brake: HaltReason | None = None
    failure: ProviderFailure | None = None

SpecialistResult = Annotated[KnowledgeResult | AccountResult | SchedulingResult, Field(discriminator="kind")]

class ReportedPoint(LLMFacing):   text: str = Field(max_length=500); passage_id: PassageId   # DO-4 §5 "{text ≤ 500, passage_id}"
class KnowledgeReport(LLMFacing): points: list[ReportedPoint] = Field(max_length=5); answered: bool
class AccountReport(LLMFacing):   summary: str = Field(max_length=300)
class SchedulingReport(LLMFacing): appointment_id: int; wanted_time: str; note: str = Field(max_length=200)
```

**Not built here (blocked, §8.2):** `SpecialistTask` (with `offer_quick_checks`), `KnowledgeSlice`, `AccountSlice`.

### 4.6 `src/meridian/domain/handoff.py`

Re-exports (rule 5): `HandoffReason`, `Priority`, `Presence`, `CaseState`, `Promise`, `FollowUp` from `common`.

```python
class CaseSummary(MeridianModel):   # DO-4 §7 + cases A-4
    case_ref: CaseRef
    reason: HandoffReason
    priority: Priority
    state: CaseState
    created_at: dt.datetime
    promise: Promise
    followup: FollowUp | None
    version: int
    seed: bool = False
    due_at: dt.datetime | None     # the CASE due (cases A-4); required, may be None

BRIEF_TITLES: tuple[str, ...] = ("Why this came to you", "What the customer needs", "What we know for sure",
                                 "What the customer says (not checked)", "What the AI did", "What we told the customer",
                                 "What you need to decide", "Who they are and how to reach them")
BRIEF_KEYS: tuple[str, ...] = ("why", "needs", "know", "says", "ai_did", "told", "decide", "who")
BRIEF_ORIGINS: tuple[str, ...] = ("state", "extraction", "state", "extraction", "state", "state", "extraction", "state")

class SourceRef(MeridianModel):
    kind: Literal["lookup_log", "message", "action", "policy_row", "rule"]
    ref: str

class BriefItem(MeridianModel):
    text: str
    kind: Literal["fact", "claim", "ai_action", "told_customer", "decision", "contact"]
    sources: tuple[SourceRef, ...]     # serialised as the wire's `source_ids` by the route (AEA-45), not here
    changed: bool

class BriefHeading(MeridianModel):
    number: int = Field(ge=1, le=8)
    key: Literal["why", "needs", "know", "says", "ai_did", "told", "decide", "who"]
    title: str
    origin: Literal["state", "extraction"]
    checked: bool
    items: tuple[BriefItem, ...]
    trimmed: bool
    trim_note: str | None
    not_generated: bool

class Brief(MeridianModel):
    case_ref: CaseRef
    thread_id: ThreadId
    assembled_at: dt.datetime
    status: Literal["ready", "being_written", "failed"]
    headings: tuple[BriefHeading, ...]
    # model_validator(mode="after") _fixed_shape — rules below

class Quote(LLMFacing):           message_id: int; text: str = Field(max_length=300)
class BriefExtraction(LLMFacing):
    needs: list[Quote] = Field(min_length=1, max_length=2)
    claims: list[Quote] = Field(max_length=5)
    open_decision: str = Field(max_length=200)

class HandoffRequest(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    reason: HandoffReason
    priority: Priority
    rule_id: str
    trigger: Literal["gate", "escalation", "con4", "safety"]
    identity: IdentityState
    change_request: ChangeRequestDraft | None = None
    safety_kind: SafetyKind | None = None

class HandoffResult(MeridianModel):
    case: CaseSummary
    created: bool
    action: CompletedAction
    alert: Literal["supervisor_now"] | None
```

**`Brief._fixed_shape` (AC-6), each failure a `PydanticCustomError("brief_shape", <rule>)`:**
1. `len(headings) == 8` else "a brief has exactly 8 headings".
2. For `i, h in enumerate(headings)`: `h.number == i + 1` ("headings are numbered 1 to 8 in order");
   `h.title == BRIEF_TITLES[i]` ("heading {n} title must be BRIEF_TITLES[{i}]"); `h.key == BRIEF_KEYS[i]`;
   `h.origin == BRIEF_ORIGINS[i]` (state for 1, 3, 5, 6, 8; extraction for 2, 4, 7).
3. Heading 4: `checked is False` ("heading 4 is never checked"); every other heading may be either.
4. `not_generated` may be `True` only for headings 2, 4, 7 (DO-4 §7 "extraction failed: headings 2, 4, 7 only").

### 4.7 `src/meridian/domain/blocks.py` (wire shapes from the OpenAPI)

**Rule:** every class takes its field names, required set and value sets from the OpenAPI schema named beside it
(`docs/ux/03-structure/ui-contracts.openapi.yaml`, `components.schemas`). The authoritative field lists, generated
from that file on 2026-10-21, are in **Appendix A**. Type mapping:

| OpenAPI | Python |
|---|---|
| `string` | `str` |
| `string` `format: date` | `dt.date` |
| `string` `format: date-time` | `dt.datetime` |
| `integer` / `boolean` | `int` / `bool` |
| `["string","null"]` (and other `[X,"null"]`) | `X \| None`, **required** (no default) |
| `enum: [...]` | `Literal[...]`, values verbatim |
| `const: x` | `Literal["x"] = "x"`; `const: true` → `Literal[True] = True` |
| `array` of X | `tuple[X, ...]`; `oneOf [array, null]` → `tuple[X, ...] \| None` |
| `$ref: Name` | the class `Name` |
| `oneOf [$ref, null]` | `Name \| None` |

Every property listed in these schemas is required; give a default **only** to `const` fields.

**Classes (Python name ← OpenAPI schema):** `Speaker`, `SourceChip`, `Option`, `Money`, `FollowUpOptions`,
`SettledRequest`, `Write`, `Notice`, `BlockBase` (fields `block_id`, `speaker`, `at` only — each block declares its
own `type` literal; do not put `type` on `BlockBase`), and the 24 blocks: `TextBlock`, `SourceChipBlock`,
`SafetyBlock`, `ConditionalSafetyBlock`, `BurningCheckBlock`, `EmergencyLineBlock`, `QuickChecksBlock`,
`UrgencyQuestionsBlock`, `WherePromptBlock`, `LocatePromptBlock`, `CodePromptBlock`, `SlotCardBlock`,
`ConfirmationBlock`, `AppointmentBlock`, `CancelledBlock`, `AccountCardBlock`, `ChangeRequestBlock`, `HandoffBlock`,
`LiveQueuedBlock`, `FailureOfferBlock`, `NoInfoBlock`, `NoticeBlock`, `ErrorBlock`, `SessionEndedBlock` (each
`class XBlock(BlockBase)`).

**Special cases:**
- `SettledVisit(VisitView)` (from `actions`) adds only `window_label: str` (graph-core §14: "VisitView = SettledVisit
  minus window_label"). Its `change_request` is `VisitChange` (from `actions`).
- `SettledView` ← OpenAPI `Settled` (DO-3 name): `built_from: Literal["conversation_state"] = "conversation_state"`,
  `visit: SettledVisit | None`, `request: SettledRequest | None`, `identity: SettledIdentity`,
  `replying: SettledReplying`, `actions: tuple[Write, ...]`.
- `FollowUpView` is `common.FollowUp`; `SettledRequest.followup: FollowUp | None`. Do not define a second class.

**Inline nested objects get these class names** (each a `MeridianModel`, fields per Appendix A):

| Class | OpenAPI path |
|---|---|
| `FollowUpChannelOption` | `FollowUpOptions.channels[]` |
| `FollowUpWindowOption` | `FollowUpOptions.windows[]` |
| `SettledIdentity` | `Settled.identity` |
| `SettledReplying` | `Settled.replying` |
| `CallKey` | `SafetyBlock.call_key` |
| `QuickCheck` | `QuickChecksBlock.checks[]` |
| `UrgencyQuestion` | `UrgencyQuestionsBlock.questions[]` |
| `SlotDay` | `SlotCardBlock.days[]` |
| `SlotWindow` | `SlotCardBlock.days[].windows[]` |
| `AccountInvoice` | `AccountCardBlock.invoice` |
| `AccountInvoiceLine` | `AccountCardBlock.invoice.lines[]` |
| `AccountMembership` | `AccountCardBlock.membership` |
| `AccountWarranty` | `AccountCardBlock.warranty` |
| `ShownWindow` | `ChangeRequestBlock.windows_shown[]` |

Then:

```python
ReplyBlock = Annotated[
    TextBlock | SourceChipBlock | SafetyBlock | ConditionalSafetyBlock | BurningCheckBlock | EmergencyLineBlock
    | QuickChecksBlock | UrgencyQuestionsBlock | WherePromptBlock | LocatePromptBlock | CodePromptBlock | SlotCardBlock
    | ConfirmationBlock | AppointmentBlock | CancelledBlock | AccountCardBlock | ChangeRequestBlock | HandoffBlock
    | LiveQueuedBlock | FailureOfferBlock | NoInfoBlock | NoticeBlock | ErrorBlock | SessionEndedBlock,
    Field(discriminator="type"),
]
```

### 4.8 `src/meridian/domain/turn.py`

Re-exports: `SafetyKind` (from `common`), `FormValues` (from `identity`). Define in this order:

```python
ExportStatus = Literal["off", "sent", "failed"]                                       # models.md §4 (re-exported by ports/runtime)
TurnPath = Literal["safety", "burning_questions", "burning_unclear", "danger", "person", "talk", "act",
                   "handoff", "code", "paused", "degraded"]                          # DO-4 §9 comment (complete list)
GateResult = Literal["clear", "safety", "burning_unclear", "danger", "person_requested", "ai_paused"]   # DO-6
TurnOutcome = Literal["answered", "acted", "safety_reply", "handed_off", "to_staff", "degraded_handoff"]  # DO-6
DegradeReason = Literal["model_error", "tool_error", "timeout", "brake", "spend_cap", "rate_limit"]      # DO-6
RunTag = Literal["live", "eval", "load"]
Topic = Literal["booking", "membership", "billing", "warranty", "other"]
SpecialistKind = Literal["knowledge", "account", "scheduling"]

class TurnIds(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    request_id: RequestId
    run_tag: RunTag
    run_id: str | None
    agent_version: str

@dataclass(frozen=True)
class TurnBudget:
    started: float          # time.monotonic()
    deadline: float         # started + 60 s (AEA-40 builds it from Limits)
    def remaining(self) -> float: ...        # max(0.0, self.deadline - time.monotonic())
    def timeout_for(self, cap_s: float, min_call_s: float = 1.0) -> float | None: ...
        # left = self.remaining(); None if left < min_call_s; else min(cap_s, left)

@dataclass(frozen=True)
class SpanHandle:            # models.md §4, file per graph-core §1
    turn_id: TurnId
    trace_id: str | None
    native: object = field(default=None, compare=False, repr=False)

class CardChoice(MeridianModel):     card_id: str; option: str
class TextPayload(MeridianModel):    kind: Literal["text"] = "text"; text: str = Field(min_length=1, max_length=2000)
class ChoicePayload(CardChoice):     kind: Literal["choice"] = "choice"
class CodePayload(MeridianModel):    kind: Literal["code"] = "code"; card_id: str; code: SecretStr
    # field_validator("code"): re.fullmatch(r"[0-9]{6}", code.get_secret_value()) else
    #   PydanticCustomError("invalid_format", "expected exactly six digits")
class FormPayload(MeridianModel):    kind: Literal["form"] = "form"; card_id: str; values: FormValues
TurnPayload = Annotated[TextPayload | ChoicePayload | CodePayload | FormPayload, Field(discriminator="kind")]

class Intake(MeridianModel):
    kind: Literal["text", "choice", "code", "form"]
    text_store: str
    code_digits: SecretStr | None
    form: FormValues | None
    card_number_seen: bool
    choice: CardChoice | None
    card_id: str | None = None

class TurnInput(MeridianModel):      # graph-core §2; never code digits, never FormValues
    turn_id: TurnId
    message_id: int
    kind: Literal["text", "choice", "code", "form"]
    text_store: str
    card_id: str | None = None
    choice: CardChoice | None = None
    card_number_seen: bool = False
    received_at: dt.datetime

@dataclass(frozen=True)
class TurnContext:                   # graph-core §2
    ids: TurnIds
    budget: TurnBudget
    now: dt.datetime
    demo_session: str
    span: SpanHandle
    intake: Intake | None = None

class RuleMatches(MeridianModel):    # DO-4 §3 + graph-core §8 (seven fields; AEA-05 checks the names)
    safety: SafetyKind | None
    burning_unclear: bool
    danger_words: bool
    person: bool
    policy_trigger: HandoffReason | None
    rule_ids: tuple[str, ...]
    correction: bool

class GateKind(StrEnum):             # 10 values
    AI_PAUSED = "ai_paused"; SAFETY = "safety"; BURNING_ASK = "burning_ask"; BURNING_ANSWER = "burning_answer"
    DANGER_RULE = "danger_rule"; PERSON = "person"; CODE_ENTRY = "code_entry"; LOCATE = "locate"
    CARD_CHOICE = "card_choice"; FREE_TEXT = "free_text"

class GateFlags(MeridianModel):      # graph-core §3
    ai_paused: bool
    burning_card_id: str | None
    code_card_open: bool
    open_task_ids: tuple[str, ...]

class GateDecision(MeridianModel):
    kind: GateKind
    rules: RuleMatches
    burning_answer: Literal["yes", "no", "unsure"] | None = None
    resume_task_id: str | None = None
    def gate_result(self) -> GateResult: ...       # table below

class TaskIntent(StrEnum):           # 9 values
    ANSWER_QUESTION = "answer_question"; READ_INVOICE = "read_invoice"; READ_MEMBERSHIP = "read_membership"
    READ_APPOINTMENTS = "read_appointments"; READ_WARRANTY = "read_warranty"; BOOK_NEW = "book_new"
    RESCHEDULE = "reschedule"; CANCEL = "cancel"; CONFIRM = "confirm"

class StateFlags(MeridianModel):
    verified: bool
    open_task: Literal["none", "knowledge", "account", "scheduling"]
    open_task_intent: TaskIntent | None
    slots_shown: int
    has_open_case: bool
    pending_change: bool

class PlannerInput(MeridianModel):   latest_message: str; recent_chat: tuple[str, ...]; flags: StateFlags

class PlannerChoices(LLMFacing):
    knowledge: Literal["no", "yes"]
    account: Literal["none", "invoice", "membership", "appointments", "warranty"]
    scheduling: Literal["none", "book_new", "reschedule", "cancel", "confirm"]
    handoff: Literal["none", "refund", "billing_dispute", "membership_cancel", "unsupported_other",
                     "complaint_or_manager", "late_technician"]      # + late_technician (cases A-6)
    topic: Topic

class PlannerOutcome(MeridianModel):
    choices: PlannerChoices | None
    probabilities: dict[str, dict[str, float]] | None
    model: str
    fallback_used: bool
    failure: ProviderFailure | None

class DangerAssessment(MeridianModel):
    label: Literal["normal", "burning_unclear", "danger"]
    raised: bool
    confidence: float | None = Field(default=None, ge=0, le=1)
    failure: ProviderFailure | None

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
    planner_failed: bool = False                                     # graph-nodes §5

class EscalationInputs(MeridianModel):
    gate: GateDecision
    plan: Plan | None
    results: tuple[SpecialistResult, ...]
    counters: FailureCounters
    identity: IdentityState
    halt: Halt | None
    models_disabled: bool
    now: dt.datetime                                                 # R-G-15

class EscalationDecision(MeridianModel):
    outcome: Literal["none", "offer", "escalate"]
    reason: HandoffReason | None
    priority: Priority | None
    rule_id: str
    degraded: bool = False

class Claim(MeridianModel):
    kind: Literal["completion", "number", "date", "time", "id", "amount", "quote"]   # + quote (graph-nodes §2)
    span: tuple[int, int]
    value: str
    action_kind: ActionKind | None = None

class Removal(MeridianModel):        claim: Claim; reason: Literal["no_completed_action", "not_in_evidence", "quote_not_found"]
class CheckResult(MeridianModel):    text: str; removals: tuple[Removal, ...]; passed: bool
class EvidenceSet(MeridianModel):
    amounts_cents: frozenset[int]
    dates: frozenset[dt.date]
    times: frozenset[str]
    ids: frozenset[str]
    numbers: frozenset[str]
    sources: dict[str, SourceRef]

CheckKind = Literal["completion", "fact", "brief_fact", "brief_quote", "gate", "classifier", "brake"]

class CheckEvent(MeridianModel):     # graph-nodes §1
    check: CheckKind
    turn_id: TurnId
    result: Literal["pass", "trimmed", "fallback", "fired", "raised"]
    removed: int = 0
    claim_kinds: tuple[str, ...] = ()
    codes: tuple[str, ...] = ()
    @classmethod
    def from_check(cls, check: Literal["completion", "fact", "brief_fact", "brief_quote"], turn_id: TurnId,
                   removals: Sequence[Removal], *, fallback: bool = False) -> CheckEvent: ...
    @classmethod
    def from_gate(cls, turn_id: TurnId, gate: GateDecision) -> CheckEvent: ...
    @classmethod
    def from_danger(cls, turn_id: TurnId, danger: DangerAssessment) -> CheckEvent: ...
    @classmethod
    def from_halt(cls, turn_id: TurnId, halt: Halt) -> CheckEvent: ...

class SignalName(StrEnum):           # 8 values
    SAFETY_REPLY_SENT = "safety_reply_sent"; CASE_WRITE_FAILED = "case_write_failed"
    CLASSIFIER_FALLBACK = "classifier_fallback"; PLANNER_FALLBACK = "planner_fallback"
    SPECIALIST_FAILED = "specialist_failed"; BRAKE_FIRED = "brake_fired"
    RESPONDER_FALLBACK = "responder_fallback"; BRIEF_FAILED = "brief_failed"

class SignalRecord(MeridianModel):
    record: Literal["signal"] = "signal"
    name: SignalName
    turn_id: TurnId
    thread_id: ThreadId
    request_id: RequestId
    run_tag: RunTag
    node: str
    cause: str | None = None
    role: Literal["planner", "classifier", "specialist", "responder", "brief"] | None = None
    specialist: SpecialistKind | None = None
    attempt: int | None = None
    recovered: bool | None = None

class TurnFacts(MeridianModel):      # DO-4 §8 WITHOUT account, missing, notices (blocked, §8.2)
    turn_id: TurnId
    gate_kind: GateKind
    plan_mode: Literal["talk", "act"] | None
    points: tuple[KnowledgePoint, ...]
    passages: tuple[Passage, ...]
    no_source_tasks: tuple[TaskIntent, ...]
    windows_shown: tuple[ShownSlot, ...]
    writes_this_turn: tuple[CompletedAction, ...]
    change_request: ChangeRequestDraft | None
    handoff: HandoffResult | None
    escalation: EscalationDecision | None
    identity_step: IdentityStep | None
    quick_checks: tuple[PassageId, ...] = ()

class ResponderDraft(LLMFacing):     text: str = Field(min_length=1, max_length=1200)
class CheckedReply(MeridianModel):   text: str; removals: tuple[Removal, ...]; fallback_used: bool; events: tuple[CheckEvent, ...]
class ComposedReply(MeridianModel):
    blocks: tuple[ReplyBlock, ...]
    settled_view: SettledView
    writes: tuple[CompletedAction, ...]
    notice: Notice | None
    path: TurnPath
    outcome: TurnOutcome
    degrade_reason: DegradeReason | None

class PlannerTrace(MeridianModel):   # graph-core §2
    model: str
    fallback_used: bool
    failure: ProviderFailureKind | None
    plan_mode: Literal["talk", "act"] | None
    plan_source: Literal["planner", "fallback_planner", "open_task", "card_choice", "rules_only"] | None
    intents: tuple[TaskIntent, ...] = ()
    handoff_request: HandoffReason | None = None
    topic: Topic | None = None
    planner_failed: bool = False

class TurnTrace(MeridianModel):
    gate_result: GateResult
    path: TurnPath
    outcome: TurnOutcome
    degrade_reason: DegradeReason | None = None
    planner: PlannerTrace | None = None
    danger_raised: bool = False
    specialists_run: tuple[SpecialistKind, ...] = ()

class TurnRecord(MeridianModel):
    status: Literal["completed", "failed"]
    trace: TurnTrace
    replied_at: dt.datetime
    server_ms: int
    model_calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    tool_calls: int
    trace_id: str | None
    trace_export: ExportStatus
    response: str

class GraphOutcome(MeridianModel):
    reply: ComposedReply
    turn_trace: TurnTrace
    check_events: tuple[CheckEvent, ...] = ()
    halt: Halt | None = None
    closed_every_open_task: bool = False

RunGraph = Callable[[TurnInput, TurnContext], GraphOutcome]
```

**Not built here (blocked, §8.2):** `ResponderInput` (needs `SettledForModel`, `ResponderRules`).

**`GateDecision.gate_result()` (AC-9, AC-19)** — graph-core §3 table; keep the fixed part in a module constant
`_GATE_RESULTS: Mapping[GateKind, GateResult] = MappingProxyType({...})`:

| `kind` | result |
|---|---|
| `SAFETY` | `"safety"` |
| `AI_PAUSED` | `"ai_paused"` |
| `BURNING_ASK` | `"burning_unclear"` |
| `BURNING_ANSWER` + `"yes"` / `"unsure"` / `"no"` | `"safety"` / `"burning_unclear"` / `"clear"` |
| `BURNING_ANSWER` + `None` | raise `ValueError("BURNING_ANSWER gate needs burning_answer")` |
| `DANGER_RULE` | `"danger"` |
| `PERSON` | `"person_requested"` |
| `CODE_ENTRY`, `LOCATE`, `CARD_CHOICE`, `FREE_TEXT` | `"clear"` |

**`CheckEvent` builders (AC-9; graph-nodes §1):**
1. `from_check(check, turn_id, removals, *, fallback=False)`: `result = "fallback" if fallback else ("pass" if not
   removals else "trimmed")`; `removed = len(removals)`; `claim_kinds = tuple(sorted({r.claim.kind for r in
   removals}))`; `codes = ()`.
2. `from_gate(turn_id, gate)`: `check="gate"`; `result = "fired"` if `gate.kind not in {FREE_TEXT, CODE_ENTRY, LOCATE,
   CARD_CHOICE}` **or** `gate.rules.rule_ids` is non-empty, else `"pass"`; `codes = (gate.kind.value,
   *gate.rules.rule_ids)`.
3. `from_danger(turn_id, danger)`: `check="classifier"`; if `danger.failure is not None` → `result="fallback"`,
   `codes=("fallback", danger.failure.kind.value)`; elif `danger.raised` → `"raised"`, `codes=(danger.label,)`; else
   `"pass"`, `codes=(danger.label,)`.
4. `from_halt(turn_id, halt)`: allowed reasons `{BRAKE_TASKS, BRAKE_TOOL_ROUNDS, BRAKE_SONNET_CALLS,
   BRAKE_IDENTICAL_CALL, RECURSION_LIMIT}`; any other → `ValueError(f"no brake event for halt reason
   {halt.reason.value}")`; else `check="brake"`, `result="fired"`, `codes=(halt.reason.value, halt.node)`.
*Invariant for all four:* the event holds codes and counts only, never text or a value (DO-6).

### 4.9 `src/meridian/domain/tools.py`

Re-exports: `ToolKind`, `ToolCallRecord` (from `common`).

```python
class ToolCallScope(MeridianModel):   # DO-4 §5; code binds it, the model never supplies it
    ids: TurnIds
    customer_id: CustomerId | None
    shown_slot_ids: frozenset[int]
    now: dt.datetime
    message_id: int

class LookupEntry(MeridianModel):
    tool: str
    record_ids: tuple[str, ...]
    passage_ids: tuple[PassageId, ...]
    result_seen: str
    message_id: int
    turn_id: TurnId

class LookupRow(LookupEntry):         # cases.md §1.2 (CAS-38, R-G-8)
    id: int
    thread_id: ThreadId

class ToolError(MeridianModel):       code: ToolErrorCode; message: str; retryable: bool

Capture = Annotated[KnowledgeCapture | AccountCapture | SchedulingCapture, Field(discriminator="kind")]

class ToolResult(MeridianModel):
    ok: bool
    for_model: ToolError | JsonValue = Field(union_mode="left_to_right")
    captured: Capture | None
    lookup: LookupEntry
    lookup_written: bool

class ToolDef(MeridianModel):
    name: str
    description: str
    args_model: type[LLMFacing]
    kind: ToolKind
    effect: Literal["read", "write"]
    requires_verified: bool
    executor: Callable[[LLMFacing, ToolCallScope], ToolResult] = Field(exclude=True)
```

(Verified in a scratch run: `ToolError` instances stay `ToolError`, dicts stay JSON; `executor` is excluded from
`model_dump`; mypy strict passes.)

### 4.10 `src/meridian/domain/state.py`

Re-exports: `FailureCounters` (common), `IdentityState` (identity), `ShownSlot` (records).

```python
class Controller(MeridianModel):
    kind: Literal["ai", "human"]
    representative_name: str | None = None
    case_ref: CaseRef | None = None

class TaskDetails(MeridianModel):   # DO-4 §1 comment "zip, city, service_type, wanted_text, appointment_id (all optional)"
    zip: str | None = None
    city: str | None = None
    service_type: ServiceType | None = None
    wanted_text: str | None = None
    appointment_id: int | None = None

class OpenTask(MeridianModel):      # DO-4 §1 WITHOUT `missing` (MissingInfo blocked, §8.2)
    task_id: str
    specialist: SpecialistKind
    intent: TaskIntent
    opened_turn: TurnId
    details: TaskDetails
    status: Literal["open", "waiting_identity", "done"]

class ChatLine(MeridianModel):
    speaker: Literal["customer", "assistant", "representative", "event"]
    text: str
    turn_id: TurnId | None
    at: dt.datetime

def first_halt(left: Halt | None, right: Halt | None) -> Halt | None: ...
    # return left if left is not None else right        (first writer wins; DO-3 §5.2)

def add_turn_events(left: tuple[CheckEvent, ...], right: tuple[CheckEvent, ...]) -> tuple[CheckEvent, ...]: ...
    # if not right: return left
    # turn = right[0].turn_id
    # return tuple(e for e in left if e.turn_id == turn) + tuple(right)      (graph-core §11)

def _identity_not_checked() -> IdentityState: ...
    # IdentityState(status="not_checked", customer_id=None, masked_hint=None, code_expires_at=None,
    #               tries_left=3, codes_sent=0, verified_at=None)

class ConversationState(MeridianModel):          # DO-3 §5.2 as changed by graph-core §3, §9, §11
    thread_id: ThreadId
    # DB-authority copies (load_context writes them every turn)
    settled: Settled | None = None               # decision §8.1 D-9: None only before load_context's first run
    controller: Controller = Field(default_factory=lambda: Controller(kind="ai"))
    identity: IdentityState = Field(default_factory=_identity_not_checked)
    # durable conversation state (checkpoint is the authority)
    open_tasks: list[OpenTask] = Field(default_factory=list)
    shown_slots: list[ShownSlot] = Field(default_factory=list)
    counters: FailureCounters = Field(default_factory=FailureCounters)
    burning_card_id: str | None = None           # graph-core §3; writer: gates node only
    # last_lookups, pending_change: NOT here (LastLookups, ChangeRequestRef blocked, §8.2)
    # turn-scoped
    turn_input: TurnInput
    chat_window: list[ChatLine] = Field(default_factory=list)
    gate: GateDecision | None = None
    planner: PlannerOutcome | None = None        # renamed from planner_choices (graph-core §9)
    danger: DangerAssessment | None = None
    plan: Plan | None = None
    identity_step: IdentityStep | None = None
    specialist_results: Annotated[list[SpecialistResult], operator.add] = Field(default_factory=list)
    escalation: EscalationDecision | None = None
    handoff: HandoffResult | None = None
    facts: TurnFacts | None = None
    draft: ResponderDraft | None = None
    brief_extraction: BriefExtraction | None = None
    checked: CheckedReply | None = None
    reply: ComposedReply | None = None
    halt: Annotated[Halt | None, first_halt] = None
    check_events: Annotated[tuple[CheckEvent, ...], add_turn_events] = ()
```

Node update `TypedDict`s (graph-nodes §9.1), all `total=False` except `ComposeUpdate`, one key per line:
`LoadContextUpdate{settled: Settled, controller: Controller, identity: IdentityState, chat_window: list[ChatLine],
counters: FailureCounters}`; `GatesUpdate{gate: GateDecision, check_events: tuple[CheckEvent, ...], plan: Plan, halt:
Halt, burning_card_id: str | None}`; `SafetyUpdate{handoff: HandoffResult, halt: Halt}`; `IdentityNodeUpdate{identity:
IdentityState, identity_step: IdentityStep, halt: Halt}`; `PlannerUpdate{planner: PlannerOutcome, halt: Halt}`;
`DangerUpdate{danger: DangerAssessment, check_events: tuple[CheckEvent, ...], halt: Halt}`; `PlanJoinUpdate{plan:
Plan, check_events: tuple[CheckEvent, ...], halt: Halt}`; `SpecialistUpdate{specialist_results:
list[SpecialistResult], check_events: tuple[CheckEvent, ...], halt: Halt}`; `EscalationUpdate{escalation:
EscalationDecision}`; `HandoffNodeUpdate{handoff: HandoffResult, halt: Halt}`; `FactsUpdate{facts: TurnFacts,
settled: Settled, open_tasks: list[OpenTask], shown_slots: list[ShownSlot], counters: FailureCounters}` (no
`last_lookups`, `pending_change`: blocked); `ResponderUpdate{draft: ResponderDraft | None, check_events:
tuple[CheckEvent, ...], halt: Halt}`; `BriefUpdate{brief_extraction: BriefExtraction | None, check_events:
tuple[CheckEvent, ...], halt: Halt}`; `ChecksUpdate{checked: CheckedReply}`; `ComposeUpdate(TypedDict)` (total)
`{reply: ComposedReply}`; and, after `ConversationState`:

```python
class SpecialistSend(TypedDict):   # graph-nodes §9.1 (R-G-12)
    planned: PlannedTask
    state: ConversationState
```

### 4.11 `src/meridian/domain/staff.py` (staff.md §1, verbatim shapes)

```python
class DemoRole(StrEnum):   CUSTOMER = "customer"; REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"
class StaffRole(StrEnum):  REPRESENTATIVE = "representative"; SUPERVISOR = "supervisor"; OWNER = "owner"

class StaffPersona(MeridianModel):   name: str; signature: str
STAFF_PERSONAS: Mapping[StaffRole, StaffPersona] = MappingProxyType({
    StaffRole.REPRESENTATIVE: StaffPersona(name="Riley", signature="Riley (demo)"),
    StaffRole.SUPERVISOR: StaffPersona(name="Demo supervisor", signature="Demo supervisor"),
    StaffRole.OWNER: StaffPersona(name="Demo business owner", signature="Demo business owner"),
})

class StaffActor(MeridianModel):
    role: StaffRole
    name: str
    signature: str
    def owns(self, owner_role: StaffRole | None) -> bool: ...     # return owner_role == self.role

def actor_for(role: StaffRole) -> StaffActor: ...
    # StaffActor(role=role, name=STAFF_PERSONAS[role].name, signature=STAFF_PERSONAS[role].signature)

ASSIGNEE_ROLES: Mapping[str, StaffRole] = MappingProxyType({"riley": StaffRole.REPRESENTATIVE,
                                                            "supervisor": StaffRole.SUPERVISOR})
LoginSessionId = NewType("LoginSessionId", str)

class LoginSession(MeridianModel):
    session_id: LoginSessionId
    role: DemoRole
    role_reset: bool
    signed_in_at: dt.datetime     # demo clock
    expires_at: dt.datetime       # wall clock UTC

class IssuedSession(MeridianModel):   session: LoginSession; token: SecretStr
class SessionMissing(MeridianModel):  """No fields."""
class SessionExpired(MeridianModel):  """No fields."""
class RoleRefusal(MeridianModel):
    role: DemoRole
    needs: tuple[StaffRole, ...]
    reason: Literal["wrong_role", "role_reset"]
class SessionInfoData(MeridianModel):
    role: DemoRole
    display_name: str
    sees: tuple[str, ...]
    signed_in_at: dt.datetime

CUSTOMER_SPEAKER_NAME = "Customer"
ROLE_ACTIONS: Mapping[StaffRole, frozenset[str]] = MappingProxyType({
    StaffRole.REPRESENTATIVE: frozenset({"claim", "claim_and_join", "release", "start", "wait", "resolve",
        "close_unresolved", "join_chat", "send_live_message", "hand_back", "close_chat", "log_call", "log_email",
        "flag"}),
    StaffRole.SUPERVISOR: frozenset({"claim", "release", "start", "wait", "resolve", "close_unresolved", "assign",
        "change_priority", "flag"}),
    StaffRole.OWNER: frozenset(),
})
```

### 4.12 `src/meridian/ports/models.py`

Re-exports: `Role`, `ProviderName`, `ProviderCall`, `CallRecord` (from `meridian.domain.common`).

```python
ChoiceRole = Literal[Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK]
StructuredRole = Literal[Role.RESPONDER, Role.BRIEF]
ToolRole = Literal[Role.SPECIALIST]
ProviderTurn = JsonValue      # decision §8.1 D-6: one provider message object, as in ProviderMessages.items (MOD-17)

@dataclass(frozen=True)
class TokenPrice:             # models.md §1 (R-G-5): US dollars per million tokens
    input: float
    output: float
    cache_write_5m: float
    cache_read: float

class ChoiceField(MeridianModel):    name: str; instructions: str; options: dict[str, str] = Field(max_length=255)
class ChoiceRequest(MeridianModel):  system: str; state: dict[str, JsonValue]; fields: tuple[ChoiceField, ...]
class ChoiceAnswer(MeridianModel):   choices: dict[str, str]; probabilities: dict[str, dict[str, float]] | None
class StructuredRequest[T: BaseModel](MeridianModel):
    system_prefix: str
    system_dynamic: str
    user: str
    output_model: type[T]
    max_tokens: int
    effort: Literal["low", "medium", "high"] | None
class ToolSchema(MeridianModel):     name: str; description: str; input_schema: dict[str, JsonValue]; strict: bool = True
class ToolCall(MeridianModel):       id: str; name: str; args: dict[str, JsonValue] | None
class ProviderMessages(MeridianModel): provider: ProviderName; model: str; items: tuple[JsonValue, ...]
class ToolStepRequest(MeridianModel):
    system_prefix: str
    system_dynamic: str
    messages: ProviderMessages
    tools: tuple[ToolSchema, ...]
    max_tokens: int
    effort: Literal["low", "medium", "high"] | None
class ToolStep(MeridianModel):       text: str; tool_calls: tuple[ToolCall, ...]; raw: ProviderTurn; stop_reason: str | None
class Attempt[T: BaseModel](MeridianModel):
    value: T | None
    record: ProviderCall                       # CHANGED by models.md §1: a ProviderCall, not a CallRecord
    failure: ProviderFailure | None

class ChoiceModel(Protocol):
    provider: ClassVar[ProviderName]
    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]: ...

class StructuredModel(Protocol):
    provider: ClassVar[ProviderName]
    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]: ...

class ToolCallingModel(Protocol):
    provider: ClassVar[ProviderName]
    def start(self, user: str) -> ProviderMessages: ...
    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...

class ToolTranscript(Protocol):      # graph-tools §2
    def start(self, user: str) -> ProviderMessages: ...
    def append(self, messages: ProviderMessages, step: ToolStep,
               results: Sequence[tuple[str, str]]) -> ProviderMessages: ...
```

**`provider` is `ClassVar[ProviderName]` on the Protocols** (decision §8.1 D-4). In a scratch run, mypy accepted both a
`@property` and a `ClassVar` member, but pyright rejected an adapter's `ClassVar` against a `@property` member; with
`ClassVar` on both sides both checkers pass. models.md §2's adapters already declare
`provider: ClassVar[ProviderName] = "anthropic"`; every double must do the same.

### 4.13 `src/meridian/ports/runtime.py`

```python
from meridian.domain.records import Passage as Passage, RetrievalResult as RetrievalResult
from meridian.domain.turn import ExportStatus as ExportStatus, SpanHandle as SpanHandle, TurnIds as TurnIds
from meridian.domain.common import CallRecord

if TYPE_CHECKING:
    from meridian.adapters.sqlite.repos_booking import BookingRepos
    from meridian.adapters.sqlite.repos_cases import CaseRepos
    from meridian.adapters.sqlite.repos_core import CoreRepos
    from meridian.adapters.sqlite.repos_identity import IdentityRepos
    from meridian.adapters.sqlite.repos_ops import OpsRepos
    from meridian.adapters.sqlite.repos_spend import SpendRepo
    from meridian.adapters.sqlite.repos_staff import StaffRepos

class IndexInfo(MeridianModel):
    embedding_model: Literal["BAAI/bge-small-en-v1.5"]
    dimension: int
    chunks: int
    manifest_hash: str
    files: int

class RetrievalIndex(Protocol):
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult: ...
    def info(self) -> IndexInfo: ...

class Clock(Protocol):
    def now(self) -> dt.datetime: ...

class TraceSink(Protocol):
    def turn(self, ids: TurnIds) -> AbstractContextManager[SpanHandle]: ...
    def model_call(self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str) -> None: ...
    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...
    def export_status(self, turn: SpanHandle) -> ExportStatus: ...

class UnitOfWork(Protocol):
    core: CoreRepos
    spend: SpendRepo
    identity: IdentityRepos
    booking: BookingRepos
    cases: CaseRepos
    staff: StaffRepos
    ops: OpsRepos
    def commit(self) -> None: ...

class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
```

`AbstractContextManager` from `contextlib`. With `from __future__ import annotations`, the repository names are only
needed by the type checker.

### 4.14 `src/meridian/config.py`

```python
from meridian.domain.common import MeridianModel, SafeError
from meridian.ports.models import ChoiceRole, Role, StructuredRole, ToolRole
from meridian.privacy.redact import RedactionProfile          # AEA-04 (data.md §1)

JEV_MODEL = "typesafe/jev-1.13"            # models.md §2 JEV_PRICES key
SONNET_MODEL = "claude-sonnet-5-5"         # models.md §2 ANTHROPIC_PRICES key

class RoleSpec(MeridianModel):             # DO-4 §12
    model: str
    effort: Literal["low", "medium", "high"] | None
    cap_s: float
    max_tokens: int
    redaction: RedactionProfile

class ModelSettings(MeridianModel):        # DO-4 §12
    choice: dict[ChoiceRole, tuple[Literal["openrouter_jev", "anthropic"], RoleSpec]]
    structured: dict[StructuredRole, tuple[Literal["anthropic"], RoleSpec]]
    tools: dict[ToolRole, tuple[Literal["anthropic"], RoleSpec]]
    # model_validator(mode="after") _every_role_once: choice keys == {PLANNER, CLASSIFIER, PLANNER_FALLBACK},
    #   structured keys == {RESPONDER, BRIEF}, tools keys == {SPECIALIST}; else
    #   PydanticCustomError("missing_role", "every role needs one entry in its own map; missing: {missing}",
    #                       {"missing": ", ".join(sorted(role.value for role in missing))})

def default_model_settings() -> ModelSettings: ...   # the code defaults below; one literal per value

ENV_NAMES: Mapping[str, str] = MappingProxyType({   # Settings field → environment variable (graph-core §12)
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "openrouter_api_key": "OPENROUTER_API_KEY",
    "langfuse_public_key": "LANGFUSE_PUBLIC_KEY",
    "langfuse_secret_key": "LANGFUSE_SECRET_KEY",
    "langfuse_base_url": "LANGFUSE_BASE_URL",
    "langfuse_project_id": "LANGFUSE_PROJECT_ID",
    "demo_username": "MERIDIAN_DEMO_USERNAME",
    "demo_password": "MERIDIAN_DEMO_PASSWORD",
    "session_secret": "MERIDIAN_SESSION_SECRET",
    "eval_key": "MERIDIAN_EVAL_KEY",
    "cookie_secure": "MERIDIAN_COOKIE_SECURE",
    "trust_proxy_headers": "MERIDIAN_TRUST_PROXY_HEADERS",
    "web_dist_dir": "MERIDIAN_WEB_DIST_DIR",
    "require_frontend": "MERIDIAN_REQUIRE_FRONTEND",
    "data_dir": "MERIDIAN_DATA_DIR",
    "index_dir": "MERIDIAN_INDEX_DIR",
    "agent_version": "MERIDIAN_AGENT_VERSION",
})                                                    # 17 names; `models` and `issued_db_path` have none

class SettingsError(ValueError):
    """Start-up refusal. Names variables, codes and rules; never a value."""
    def __init__(self, problems: tuple[SafeError, ...]) -> None: ...
        # self.problems = problems
        # super().__init__("invalid settings: " + "; ".join(f"{p.field}: {p.code} ({p.constraint})" for p in problems))

class Settings(MeridianModel):              # graph-core §12, exactly these fields
    anthropic_api_key: SecretStr
    openrouter_api_key: SecretStr
    models: ModelSettings = Field(default_factory=default_model_settings)
    langfuse_public_key: SecretStr | None = None
    langfuse_secret_key: SecretStr | None = None
    langfuse_base_url: str | None = None
    langfuse_project_id: str | None = None
    demo_username: SecretStr
    demo_password: SecretStr
    session_secret: SecretStr
    eval_key: SecretStr | None = None
    cookie_secure: bool = False
    trust_proxy_headers: bool = False
    web_dist_dir: Path = Path("apps/web/dist")
    require_frontend: bool = False
    data_dir: Path = Path("var")
    index_dir: Path = Path("var/index")
    issued_db_path: Path = Path("docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite")
    agent_version: str = "dev"

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> Settings: ...
    def role_model_map(self) -> Mapping[str, Any]: ...
    def langfuse_complete(self) -> bool: ...
```

**Code defaults (`default_model_settings`, DO-1 §8.1 caps; SP-1 option B for effort and max tokens):**

| Map | Role | Provider | `model` | `effort` | `cap_s` | `max_tokens` | `redaction` |
|---|---|---|---|---|---|---|---|
| choice | `PLANNER` | `openrouter_jev` | `JEV_MODEL` | `None` | 3.0 | 1500 | `RedactionProfile.JEV` |
| choice | `CLASSIFIER` | `openrouter_jev` | `JEV_MODEL` | `None` | 3.0 | 800 | `RedactionProfile.JEV` |
| choice | `PLANNER_FALLBACK` | `anthropic` | `SONNET_MODEL` | `"low"` | 8.0 [A, D-10] | 1500 | `RedactionProfile.SONNET` |
| structured | `RESPONDER` | `anthropic` | `SONNET_MODEL` | `"low"` | 12.0 | 1500 | `RedactionProfile.SONNET` |
| structured | `BRIEF` | `anthropic` | `SONNET_MODEL` | `"low"` | 12.0 | 1200 | `RedactionProfile.SONNET` |
| tools | `SPECIALIST` | `anthropic` | `SONNET_MODEL` | `"medium"` | 8.0 | 3000 | `RedactionProfile.SONNET` |

Comment each cap `# proposal (DO-1 §8.1)`; the planner-fallback cap `# [A] plan decision D-10`.

**`Settings.from_env(environ)` (numbered; invariant per step):**
1. `data = {field: environ[env] for field, env in ENV_NAMES.items() if env in environ and environ[env].strip()}`.
   Only the 17 names are read; a blank value counts as unset. *Invariant:* no unrelated variable reaches the model
   (`extra="forbid"` would reject it).
2. `try: return cls.model_validate(data)` (`models` and `issued_db_path` come from their code defaults).
3. `except ValidationError as exc:` build `problems` from `SafeError.from_validation_error(exc)`, replacing each
   problem's `field` with `ENV_NAMES[<first loc part>]` when the first dotted part is a key of `ENV_NAMES` (so a
   missing secret is named by its variable, AC-13); then `raise SettingsError(problems) from None`. *Invariant:*
   `from None` drops the pydantic exception (whose `.errors()` holds inputs) from the chain (AC-14).
- `from_env` never reads `os.environ` itself and is never called at import time; the container's caller passes
  `os.environ` once.

**`role_model_map()`**: `{role.value: {"provider": p, "model": s.model, "effort": s.effort, "cap_s": s.cap_s,
"max_tokens": s.max_tokens, "redaction": s.redaction.value}}` for every role of the three maps, keys sorted by role
value. Plain JSON-safe values, no secrets (data.md §7 `compute_agent_version`).

**`langfuse_complete()`**: `True` only when `langfuse_public_key` and `langfuse_secret_key` are not `None` with a
non-blank secret value, and `langfuse_base_url` and `langfuse_project_id` are not `None` and non-blank.

### 4.15 Repository shells: `src/meridian/adapters/sqlite/repos_*.py`

Seven files, the same shape (cases.md §1.0: "every repository class has exactly this constructor"):

| File | Class | Docstring names the body owner |
|---|---|---|
| `repos_core.py` | `CoreRepos` | AEA-10 (cases.md §1.2) |
| `repos_spend.py` | `SpendRepo` | AEA-26 (models.md §6) |
| `repos_identity.py` | `IdentityRepos` | AEA-27 (graph-tools §5) |
| `repos_booking.py` | `BookingRepos` | AEA-28 (cases.md §4.1) |
| `repos_cases.py` | `CaseRepos` | AEA-10 (cases.md §1.2) |
| `repos_staff.py` | `StaffRepos` | AEA-44 (staff.md §3) |
| `repos_ops.py` | `OpsRepos` | AEA-32 (cases.md §8) |

```python
"""Repository shell for <tables> (AEA-02 shell; body: AEA-NN, <addendum section>)."""
from __future__ import annotations

import sqlite3


class SpendRepo:
    """<one line: tables>. Body by AEA-NN; AEA-02 creates the constructor only."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
```

No other method, attribute or import.

### 4.16 `.env.example` (repo root)

Rewrite the whole file. Keep the first comment line as it is today (it states where the Anthropic key comes from, no
value). Then one `NAME=` line per `ENV_NAMES` value, **nothing after `=`**, grouped with `#` comments: required
(`ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD`,
`MERIDIAN_SESSION_SECRET`), optional Langfuse (four; "all four or export stays off"), optional web/storage/version
(`MERIDIAN_EVAL_KEY`, `MERIDIAN_COOKIE_SECURE`, `MERIDIAN_TRUST_PROXY_HEADERS`, `MERIDIAN_WEB_DIST_DIR`,
`MERIDIAN_REQUIRE_FRONTEND`, `MERIDIAN_DATA_DIR`, `MERIDIAN_INDEX_DIR`, `MERIDIAN_AGENT_VERSION`). Remove
`MERIDIAN_LLM_MODEL`, `MERIDIAN_FAST_MODEL`, `MERIDIAN_TODAY`, `MERIDIAN_DAILY_SPEND_CAP_USD` (graph-core §12 "not
carried over"). Comments never show a value or default for a secret. **Never open or read `.env`.**

---

## 5. Steps (build order; each step ends with a check)

Work in the worktree and branch the orchestrator gives you (pattern: `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-02`).
`export UV_LINK_MODE=hardlink` in every shell. Never copy a venv; never create `node_modules` in the worktree. Branch
from `main` at `16ca639` or later (AEA-01 and AEA-04 are merged there).

0. **Preconditions.** `git log --oneline -15 main` shows `07924f5 Merge AEA-01 foundation` and `ef03e05 Merge AEA-04`.
   `uv sync`. `uv run python -c "from meridian.privacy.redact import RedactionProfile; print([p.value for p in RedactionProfile])"`
   prints `['store', 'sonnet', 'jev', 'trace', 'log']`.
   `ls src/meridian/domain/__init__.py src/meridian/ports/__init__.py src/meridian/adapters/sqlite/__init__.py
   tests/unit/domain/__init__.py tests/unit/ports/__init__.py tests/unit/adapters/__init__.py
   tests/unit/test_import_direction.py` lists all seven (AEA-01 owns them). If any is missing, **stop and report**; do
   not create it. Read the frozen test files the test-writer committed; do not edit them.
1. **`domain/common.py`** (§4.1). Check: `uv run python -c "import meridian.domain.common"`.
2. **`domain/records.py`** (§4.2). Check: import it alone.
3. **`domain/actions.py`** (§4.3) incl. the three `Settled` methods. Check: import alone.
4. **`domain/identity.py`** (§4.4). Check: import alone.
5. **`domain/specialists.py`** (§4.5). Check: import alone.
6. **`domain/handoff.py`** (§4.6) incl. `Brief._fixed_shape`. Check: import alone.
7. **`domain/blocks.py`** (§4.7, Appendix A). Check: import alone.
8. **`domain/turn.py`** (§4.8) incl. `gate_result` and the four builders. Check: import alone.
9. **`domain/tools.py`** (§4.9). Check: import alone.
10. **`domain/state.py`** (§4.10). Check: import alone.
11. **`domain/staff.py`** (§4.11). Check: import alone.
12. **`ports/models.py`, `ports/runtime.py`** (§4.12–§4.13) and the seven **repository shells** (§4.15). Check:
    `for m in domain.common domain.records domain.actions domain.identity domain.specialists domain.handoff
    domain.blocks domain.turn domain.tools domain.state domain.staff ports.models ports.runtime; do uv run python -c
    "import meridian.$m" || echo "FAIL $m"; done` prints no FAIL.
13. **Implementer tests** for steps 1–12 (§7.1 list). Run them and the frozen domain tests:
    `uv run pytest tests/unit/domain tests/unit/ports tests/unit/adapters -q`.
14. **`config.py`** (§4.14). Check:
    `uv run pytest tests/unit/test_config.py -q` (frozen tests go green).
15. **`.env.example`** (§4.16). Check: `test_env_example_matches_settings` green.
16. **Append** `test_domain_ports_config_imports` to `tests/unit/test_import_direction.py` (§7.1). Do not change
    AEA-01's functions (or any sibling's that landed first).
17. **Fast gates, cheapest first** (§7.3 G-1…G-4). Fix and re-run until green.
18. **Affected tests** (§7.3 G-5): the whole suite. `build-loop-test-scope.md` allows it here for two of its listed
    reasons: the change adds settings and configuration (`config.py`, `.env.example`) and a module imported across the
    codebase (`domain/*`, `ports/*`). The suite is small at wave 0 (AEA-01, 03, 04 tests only).
19. **Journey record** `docs/testing/journeys/<YYYY-MM-DD>-AEA-02.md` (§7.4) and the affected-journeys command (G-6).
20. **Code commit.** `git add` the explicit paths of §2.1 except the three context files; message
    `feat(domain): AEA-02 domain types, ports, typed settings, repository shells` + body listing ACs + last line
    `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Never `git add -A`.
21. **Context commit** (AC-22), using the SHA of step 20:
    - `.claude/reference/area-map.md` A0 row, **Status cell only**. Today the cell starts `partly built:` and ends
      `; the rest planned`. Insert this text (copy exactly; `<sha>` = the step-20 commit) immediately before
      `; the rest planned`:
      ```text
      ; `config.py`, `domain/*` (11 files), `ports/{models,runtime}.py` and the seven `repos_*.py` shells actual (AEA-02, `<sha>`)
      ```
      If a sibling has changed the cell since, keep its text and insert the same clause before its closing phrase.
    - `docs/design/code-design.md`: under `## 3. The module map (every path planned)` there is one line starting
      `**Built:**` (today: ``**Built:** `policy/texts.py` (AEA-03, `2689582`).``; a sibling may have extended it).
      Replace that line's final `.` with the text below. Add no other line.
      ```text
      ; `config.py`, `domain/{common,records,actions,identity,specialists,handoff,blocks,turn,tools,state,staff}.py`, `ports/{models,runtime}.py`, `adapters/sqlite/repos_{core,spend,identity,booking,cases,staff,ops}.py` (shells) (AEA-02, `<sha>`).
      ```
    - `.claude/state/icm-progress.md`: the file has two rows named *Routes verified against code and tests* (a merge
      left both). Edit only the one whose evidence cell starts `2026-10-21: first backend slice AEA-04`: keep status
      `provisional` and the next-check cell; replace the evidence cell with the text below (`<n>` = the passed count of
      the step-18 run). Row ≤ 400 characters. Leave the other row; report the duplicate.
      ```text
      2026-10-21: A0 types AEA-02 `<sha>`: `tests/unit/domain`, `tests/unit/ports`, `tests/unit/adapters`, `tests/unit/test_config.py`, `test_import_direction.py::test_domain_ports_config_imports` pass (<n> passed)
      ```
    - Commit with explicit paths, same trailer.
22. **Report** each AC as verified / not verified with its command and result (§7.3), the DO-4 contradictions of
    §8.4 (for AEA-08), and the blocked types of §8.2.

**Must not do:** edit any file outside §2.1 (in particular `web/container.py`, `tests/conftest.py`, `pyproject.toml`,
`uv.lock`, any `__init__.py`, and the other tickets' functions in `test_import_direction.py`); edit a frozen test (if one is wrong, stop and report to the orchestrator);
create `__init__.py` files; add a dependency (a new one is an AEA-01 follow-up); read `.env`; put a real key, a phone
number, a six-digit code or a card-like number literally in any file (build sentinels at run time); call a model or
the network in a test; add a field, method or type the plan does not list (a missing one is a follow-up ticket);
define any blocked type of §8.2 or guess its fields; add a `Promise` text validator (GRC-2); import `gates/`,
`policy/`, `services/`, `agent/`, `web/` or any adapter from `domain/`/`ports/`/`config.py`; bind ports 4019 or 5184;
push; force-push.

---

## 6. Data and fixtures (synthetic or issued only)

| Fixture | Value | Source |
|---|---|---|
| Thread / turn / request IDs | fixed canonical UUID4 literals, e.g. `ThreadId("3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10")`; turn 3 `TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")`, turn 4 `TurnId("a2b4c6d8-1e3f-4a5b-8c7d-9e0f1a2b3c4d")` | synthetic |
| WP-4F `moved` action | `ActionKey(thread_id, turn_id=<turn 3>, kind=MOVED, record_id="159")`; `records={"appointment": "159", "slot": "56", "old_slot": "159"}`; `before={"date": "2026-10-22", "window": "08:00-12:00"}`; `after={"date": "2026-10-19", "window": "08:00-12:00", "technician": "Marta Kowalski", "service_type": "hvac_repair", "fee_line": "fee line (fixture)"}`; `at = 2026-10-16 10:12 America/Chicago` | issued appointment 159 (MHC-10001, 2026-10-22 08:00-12:00), issued slot 56 (2026-10-19 08:00-12:00, tech 5 Marta Kowalski, north); DEMO_START 2026-10-16 10:00 (cases.md §1.1) |
| Cancelled / change-request cases | a `BOOKED` action for appointment `"160"` then a later `CANCELLED` for `"160"`; a `MOVED` then a later `CHANGE_REQUEST_SENT` whose `after = {"change": "move", "wanted_text": "Thursday afternoon", "fee_line": "fee line (fixture)"}` | synthetic |
| Sentinel secrets | `f"sentinel-{uuid.uuid4().hex}"` per field, built at run time | synthetic |
| Sentinel code digits | `"".join(str((i * 7 + 3) % 10) for i in range(6))` (computed, never a literal) | synthetic |
| Sentinel phone | `"-".join(["512", "555", f"{secrets.randbelow(10_000):04d}"])` (assembled at run time) | synthetic, fictional 555 range |
| Sentinel token | `secrets.token_urlsafe(32)` | synthetic |
| Sentinel rejected ID | `"MHC-" + uuid.uuid4().hex[:6]` (never matches `MHC-[0-9]{5}`) | synthetic |
| OpenAPI | `Path(__file__).resolve().parents[3] / "docs/ux/03-structure/ui-contracts.openapi.yaml"` loaded with `yaml.load(text, Loader=yaml.BaseLoader)` (keeps `yes`/`ON`/timestamps as strings) — read only | signed contract |

Shared fixtures for `tests/unit/domain/` go in `tests/unit/domain/conftest.py` (`ids`, `wp4f_settled`, builders for
`RuleMatches`, `GateDecision`, `Brief`). Tests in other folders build what they need inline.

---

## 7. Checks

### 7.1 Tests the implementer writes with the code (names are binding)

| File | Functions | What they assert |
|---|---|---|
| `tests/unit/domain/test_ids.py` | `test_malformed_ids_rejected` (parametrised: non-UUID4 / upper-case / version-1 UUID for `ThreadId`, `TurnId`, `RequestId`; `MHC-1234`, `MHC-123456`, `mhc-12345` for `CustomerId`; `INV-12345` for `InvoiceId`; `MHC-C-123` for `CaseRef`; `faq/x.md` (no `#n`) and `faq/x.md#a` for `PassageId`); `test_valid_ids_round_trip` | Through a holder model's `model_validate`: raises; `SafeError.from_validation_error` gives `field == "value"`, `code == "string_pattern_mismatch"`, the pattern in `constraint`. Valid values keep their subclass and dump as plain strings |
| `tests/unit/domain/test_enums.py` | `test_enum_value_sets` (parametrised over the AC-4 list with literal expected sets typed from the sources); `test_api_error_code_equals_openapi`; `test_status_values_equal_do6` | Counts: `ActionKind` 7, `GateKind` 10, `HandoffReason` 16, `Priority` 5, `ToolErrorCode` 13, `ToolKind` 7, `CheckKind` 7 (`typing.get_args`), `SignalName` 8, `DemoRole` 4, `StaffRole` 3, `ProviderName` 2. `ApiErrorCode` values == OpenAPI `ApiError.error.code` enum ∪ `Notice.code` enum ∪ `ErrorBlock.code` enum, and `"STAFF_AUTH_REQUIRED"` absent. `get_args(GateResult)`, `get_args(TurnOutcome)`, `get_args(DegradeReason)`, `get_args(ExportStatus)` equal DO-6 lines 52–54 and models.md §4; `TurnTrace.model_fields["gate_result"].annotation == GateResult` etc. Each comparison prints both sets |
| `tests/unit/domain/test_actions.py` | `test_wp4f_move_is_settled` (WP-4F pair), `test_cancelled_visit_is_not_current`, `test_change_request_keeps_original`, `test_only_turn_filters_to_one_turn`, `test_has_with_record_id` | §4.3 algorithms with §6 fixtures. WP-4F: `has(MOVED)`, `has(MOVED, "159")`, not `has(MOVED, "160")`; `current_visit()` == `VisitView(appointment_id=159, date=2026-10-19, window="08:00-12:00", technician="Marta Kowalski", service_type="hvac_repair", fee_line=…, status="moved", change_request=None)`; `only_turn(<turn 4>)` has `actions == ()` and `open_case is None`; `only_turn(<turn 3>)` keeps the action |
| `tests/unit/domain/test_handoff.py` | `test_brief_shape` (parametrised: valid; 7 headings; 9; numbers out of order; wrong title; wrong key; wrong origin on heading 2; heading 4 `checked=True`; `not_generated=True` on heading 1) | Valid passes; each broken shape raises `ValidationError` with `code == "brief_shape"` |
| `tests/unit/domain/test_bounds.py` | `test_bound` (parametrised: one in-bound and one out-of-bound case per bound) | Bounds of AC-7 plus PA-3 and `TextPayload.text` 1–2000, `FeeNote.line` 1–120, `CodeExpired.sends_left` 0–2, `KnowledgeReport.points` ≤ 5, `AccountReport.summary` ≤ 300, `SchedulingReport.note` ≤ 200, `ToolCallRecord.name` ≤ 64. Each case: `Model.model_validate(valid | {field: value})`; in-bound passes, out-of-bound raises |
| `tests/unit/domain/test_state.py` | `test_reducers`; `test_conversation_state_defaults` | `operator.add` concatenates; `first_halt(None, h) is h`, `first_halt(h1, h2) is h1`; `add_turn_events(left, ())` returns `left`; a new turn's first event drops the old turn's events; two writers in one turn keep both, in order. Defaults: `ConversationState(thread_id=…, turn_input=…)` builds with `controller.kind == "ai"`, `identity.status == "not_checked"`, `tries_left == 3`, empty lists, `halt is None` |
| `tests/unit/domain/test_turn.py` | `test_check_event_builders`, `test_gate_result_mapping`, `test_gate_result_table` (one parametrised case per graph-core §3 row, table printed), `test_turn_budget_timeout_for` | §4.8 rules; `from_halt` raises `ValueError` for `DEADLINE`, `SPEND_CAP`, `PROVIDER_SPEND_CAP`; `timeout_for` returns `None` under `min_call_s` and `min(cap, left)` otherwise |
| `tests/unit/domain/test_staff.py` | `test_role_actions_and_customer_speaker_match_staff_md` | AC-20 exactly; every key ∈ OpenAPI `CaseSummary.properties.allowed_actions.items.enum`; REPRESENTATIVE == that enum − {`assign`, `change_priority`}; prints the three sets. Also `actor_for(SUPERVISOR).owns(SUPERVISOR)` |
| `tests/unit/domain/test_wire_shapes.py` | `test_wire_models_match_openapi` (parametrised over every Python ← OpenAPI pair of §4.7, plus `TextPayload`, `ChoicePayload`, `CodePayload`, `FormPayload`, `FormValues` ← `FormPayload.values`, `FollowUp` ← `FollowUpView`, `InboxMessage` ← OpenAPI `InboxMessage` minus `body`); `test_union_discriminators_match_openapi` | `set(cls.model_fields) == set(<OpenAPI properties, allOf merged with BlockBase>)`; every `const` property's default equals the const (compare `str(default).lower()`); the `type` literals of `ReplyBlock`'s members == the discriminator mapping keys; same for `TurnPayload`'s `kind` |
| `tests/unit/ports/test_protocol_shapes.py` | `test_stubs_satisfy_ports` | Module-level stub classes (each with `provider: ClassVar[ProviderName] = "anthropic"` where the Protocol has it) assigned to annotated variables `ChoiceModel`, `StructuredModel`, `ToolCallingModel`, `ToolTranscript`, `TraceSink`, `RetrievalIndex`, `Clock`, `UnitOfWorkFactory`, `UnitOfWork`; the test body asserts the objects exist. The proof is `uv run mypy` over this file (G-3) |
| `tests/unit/ports/test_call_record.py` | `test_from_provider_copies_every_field`, `test_attempt_bounds`, `test_reexports_are_the_domain_types` | `set(CallRecord.model_fields) == set(ProviderCall.model_fields) | {"role", "attempt"}` and every value equal; `attempt` 0 and 3 rejected; `meridian.ports.models.CallRecord is meridian.domain.common.CallRecord`, same for `Role`, `ProviderCall`; `meridian.ports.runtime.SpanHandle is meridian.domain.turn.SpanHandle`, same for `ExportStatus`, `RetrievalResult` |
| `tests/unit/adapters/test_repo_shells.py` | `test_seven_shells_one_constructor` | For each of the 7 (module, class): `typing.get_type_hints(cls.__init__)` == `{"conn": sqlite3.Connection, "return": NoneType}`; `[n for n in vars(cls) if not n.startswith("_")] == []`; `"__init__" in vars(cls)`; prints the seven class names |
| `tests/unit/test_import_direction.py` (append) | `test_domain_ports_config_imports` | `ast` scan of `src/meridian/domain/*.py` (except `__init__.py`), `src/meridian/ports/*.py`, `src/meridian/config.py`. Collect every `Import`/`ImportFrom`; a relative import fails. Top-level module name must be in `sys.stdlib_module_names`, or `pydantic`, `pydantic_core`, or `meridian`. `meridian.*` allowed: domain → `meridian.domain.*`; ports → `meridian.domain.*` (plus `meridian.adapters.sqlite.repos_*` only inside an `if TYPE_CHECKING:` block); config → `meridian.domain.*`, `meridian.ports.*`, `meridian.privacy.redact`. Nothing anywhere imports `anthropic`, `httpx`, `fastembed`, `langfuse`, `langgraph`, `sqlite3`. Prints every import seen |

### 7.2 What the frozen tests assert (for the test-writer)

`tests/unit/domain/test_conventions.py`
- `test_every_model_uses_meridian_config`: import the 11 domain modules, `meridian.ports.models`,
  `meridian.ports.runtime`, `meridian.config`; collect every class `c` in their `vars()` with
  `isinstance(c, type) and issubclass(c, pydantic.BaseModel) and c.__module__.startswith("meridian.")`, de-duplicated
  by identity; for each assert `c.model_config.get("extra") == "forbid"`, `.get("frozen") is True`,
  `.get("hide_input_in_errors") is True`, `.get("str_strip_whitespace") is True`. Dataclasses `TurnBudget`,
  `TurnContext`, `SpanHandle`, `TokenPrice` are listed by name and skipped (assert each is a dataclass). Print the count.
- `test_rejected_value_absent_from_safe_error`: a holder `class _Holder(MeridianModel): customer_id: CustomerId`;
  `_Holder.model_validate({"customer_id": sentinel})` raises; `sentinel` not in `str(exc)`, not in `repr(exc)`, not in
  any `SafeError.model_dump_json()` of `SafeError.from_validation_error(exc)`; each `SafeError` has non-empty `field`,
  `code`, `constraint`. Repeat with `Locator.model_validate({"name": sentinel_name})` (half pair).
- `test_secret_fields_absent_from_repr_and_dump`: build `FormValues(phone=SecretStr(phone))`,
  `Intake(kind="code", text_store="[code entered]", code_digits=SecretStr(digits), form=None, card_number_seen=False,
  choice=None)`, `Locator(name="Test Name", phone=SecretStr(phone))`, `IssuedSession(session=…, token=SecretStr(token))`,
  `InboxMessage(..., code=SecretStr(digits), ...)`, `CodePayload(card_id="code-x", code=SecretStr(digits))`; for each,
  the sentinel is absent from `repr(obj)`, `str(obj)` and `obj.model_dump_json()`; and
  `isinstance(Model.model_fields[name].annotation …)` shows `SecretStr` for `FormValues.phone`, `Intake.code_digits`,
  `Locator.phone`, `IssuedSession.token`, `InboxMessage.code`; `"code_digits" not in TurnInput.model_fields` and
  `"form" not in TurnInput.model_fields`.
- `test_record_types_hold_codes_only`: `set(CheckEvent.model_fields) == {"check", "turn_id", "result", "removed",
  "claim_kinds", "codes"}`; `SignalRecord` == `{"record", "name", "turn_id", "thread_id", "request_id", "run_tag",
  "node", "cause", "role", "specialist", "attempt", "recovered"}`; `PlannerTrace` == `{"model", "fallback_used",
  "failure", "plan_mode", "plan_source", "intents", "handoff_request", "topic", "planner_failed"}`; `TurnTrace` ==
  `{"gate_result", "path", "outcome", "degrade_reason", "planner", "danger_raised", "specialists_run"}`; none of the
  four has a field named `text`, `message`, `content`, `body`, `quote`, `wanted_text`, `phone` or `code_digits`.
  Print the four lists.
- `test_each_domain_module_imports_alone`: for each of the 11 `meridian.domain.<m>`, `meridian.ports.models`,
  `meridian.ports.runtime`: `subprocess.run([sys.executable, "-c", f"import {name}"], check=False,
  capture_output=True, timeout=60)` returns 0 (stderr printed on failure).

`tests/unit/domain/test_identity.py`
- `test_locator_exactly_one`: parametrised invalid dicts — `{}`, `{"name": n}`, `{"phone": p}`,
  `{"name": n, "phone": p, "customer_id": "MHC-10001"}`, `{"customer_id": "MHC-10001", "invoice_number":
  "INV-204411"}`, `{"name": n, "phone": p, "invoice_number": "INV-204411"}` — each `Locator.model_validate` raises
  with a `SafeError` of `code == "locator_combination"`, and neither `n` nor `p` (run-time sentinels) appears in
  `str(exc)`. Valid: `{"name": n, "phone": p}`, `{"customer_id": "MHC-10001"}`, `{"invoice_number": "INV-204411"}`
  pass. (`MHC-10001`, `INV-204411` are issued test data, allowed.)
- `test_from_form_incomplete_is_none`: `Locator.from_form(FormValues.model_validate(d))` is `None` for `{}`,
  `{"name": n}`, `{"phone": p}`, `{"zip_or_city": "78701"}`, `{"name": "  ", "phone": p}`, and for two complete groups
  `{"name": n, "phone": p, "customer_id": "MHC-10001"}`; returns a `Locator` with only that group for
  `{"name": n, "phone": p}`, `{"customer_id": "MHC-10001"}`, `{"invoice_number": "INV-204411"}`.

`tests/unit/test_config.py` (imports `Settings`, `SettingsError`, `ModelSettings`, `RoleSpec`, `ENV_NAMES`,
`default_model_settings`, `JEV_MODEL`, `SONNET_MODEL` from `meridian.config`; `Role` from `meridian.ports.models`;
`RedactionProfile` from `meridian.privacy.redact`; `SafeError` from `meridian.domain.common`). A helper
`_env(**overrides) -> dict[str, str]` returns the five required names with run-time sentinels.
- `test_valid_environment_builds`: `Settings.from_env({**_env(), "PATH": "/usr/bin", "MERIDIAN_DATA_DIR": "/tmp/x",
  "MERIDIAN_COOKIE_SECURE": "true"})` builds; `data_dir == Path("/tmp/x")`, `cookie_secure is True`,
  `agent_version == "dev"`, `web_dist_dir == Path("apps/web/dist")`; `models == default_model_settings()`; planner and
  classifier map to `("openrouter_jev", …)` with `model == JEV_MODEL`; planner fallback, responder, brief, specialist
  map to `"anthropic"` with `SONNET_MODEL`; caps 3.0, 3.0, 8.0, 12.0, 12.0, 8.0.
- `test_env_example_matches_settings`: parse the repo-root `.env.example` (skip blank and `#` lines; split on the
  first `=`); every value is `""`; the name set == `set(ENV_NAMES.values())` (17 names); print the sorted list.
- `test_jev_in_structured_or_tool_role_rejected` (WP pair 2; parametrised over `structured`/`RESPONDER`,
  `structured`/`BRIEF`, `tools`/`SPECIALIST`): build the defaults' maps, replace that role's provider with
  `"openrouter_jev"`, `ModelSettings.model_validate({...})` raises; then the same through `Settings.model_validate`
  with `_env`-style secrets: raises; at least one `SafeError` has the map name in `field` and `code ==
  "literal_error"`; no sentinel in `str(exc)`.
- `test_role_in_wrong_map_rejected` (parametrised: `RESPONDER` in `choice`; `PLANNER` in `structured`; `PLANNER` in
  `tools`; a missing `BRIEF`): raises; `code` is `"literal_error"` (wrong map) or `"missing_role"` (missing).
- `test_missing_required_secret_named` (parametrised over `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`,
  `MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD`, `MERIDIAN_SESSION_SECRET`): `_env()` without it, and with it
  blank (`"  "`): `Settings.from_env` raises `SettingsError`; the name is in `str(exc)`; a problem has `field ==` that
  name and `code == "missing"`.
- `test_secret_values_absent_from_repr_errors_and_logs`: distinct run-time sentinels in all eight `SecretStr` fields;
  build; sentinels absent from `repr(s)`, `str(s)`, `s.model_dump_json()`, `json.dumps(s.role_model_map())`;
  then `Settings.from_env` with the same secrets plus `MERIDIAN_COOKIE_SECURE = "not-a-bool-" + sentinel` raises
  `SettingsError`; no sentinel in `str(exc)`, `repr(exc)`, `exc.__cause__` is `None`; log `logger.warning("settings
  %r", s)` and `logger.exception("start-up failed")` inside the `except` with `caplog` at DEBUG; no sentinel in
  `caplog.text`.
- `test_langfuse_complete_needs_all_four` (16 cases, `itertools.product([True, False], repeat=4)`): set each of the
  four `LANGFUSE_*` names (to a run-time value) when its flag is True; `Settings.from_env` builds every time;
  `langfuse_complete()` is True only when all four flags are True.

### 7.3 Gates (cheapest first; stop at the first red)

| # | Command | Passing looks like |
|---|---|---|
| G-1 | `uv run ruff check` | `All checks passed!` (if `S105`/`S106` flags `ENV_NAMES`, add `# noqa: S105  env var name, not a secret` on that line only) |
| G-2 | `uv run ruff format --check` | `N files already formatted` |
| G-3 | `uv run mypy` (AEA-01's config: strict, pydantic plugin, `files = src/meridian, tests, eval`) | `Success: no issues found in N source files` — covers AC-16 (`test_protocol_shapes.py`) and AC-17 (`ports/runtime.py`) |
| G-4 | the import loop of step 12 | no `FAIL` |
| G-5 | `uv run pytest -q -rP` (serial, both `testpaths`; only if slow: `uv run --with pytest-xdist pytest -q -n 2`, never more than `-n 2`) | all pass, 0 failed; the AC-1/AC-20/AC-18/AC-19 tests print their lists. While iterating, run only `uv run pytest tests/unit/domain tests/unit/ports tests/unit/adapters tests/unit/test_config.py tests/unit/test_import_direction.py -q` |
| G-6 | `uv run python -m tests.journeys.affected --base main` | `changed files: <k> (base main)` then `0 journeys affected`, exit 0 |
| G-7 | `git diff --stat main -- docs/parked docs/ux apps docs/design/contracts docs/source docs/data/issued` | empty |
| G-8 | `git diff --name-only main` | only §2.1 paths |
| Capture verification | n/a: this ticket adds no entry point and emits nothing; CAP-1…CAP-3 are AEA-51's. AC-4 and AC-10 are the component guards | — |
| Evaluation check | n/a: no check added; AC-5 (`test_wp4f_move_is_settled`) is E-1's WP-4F state-seam guard at unit level (DO-5 *Failure categories*) | — |

Copy each gate's last lines into the report with the commit SHA.

### 7.4 Journey record (AC-21): `docs/testing/journeys/<YYYY-MM-DD>-AEA-02.md`

Same layout as `docs/testing/journeys/2026-10-21-AEA-04.md`: a `# Journey record: AEA-02 …` title, then this table.

| Field | Value |
|---|---|
| Claim | AEA-02 domain types, ports, `Settings`, repository shells; journeys J-1…J-10 all import them |
| Level | `mock-tested` |
| Tested revision | the step-20 commit SHA |
| Environment | VPS, `uv run`, Python 3.12, no server, no DB, no model |
| Command | G-5 and G-6 above |
| Result | unit tests pass (count); affected journeys: 0 |
| Evidence location | the implementer's report; CI output pasted |
| Remaining limitations | no journey exists yet; no real entry point drives these types |
| Blocked by | AEA-57 (journey harness, wave 2) |
| Journeys that will exercise this code | J-1…J-10 (every path imports the domain types and ports), once AEA-57, AEA-51, AEA-52 and AEA-53 land |

No secret, password or personal data in the record.

---

## 8. Risks and requests

### 8.1 Decisions made in this plan (engineering; each reversible by a follow-up before wave-1 consumers merge)

| ID | Decision | Basis |
|---|---|---|
| D-1 | Type homes: ten groups of types are **defined** in a lower module and **re-exported** from their ticket home (§4.0 table); import paths unchanged | Ticket homes form import cycles; DO-3 §2.1 forbids `domain → ports`; precedent graph-core §1 (`SpanHandle`), X-1 |
| D-2 | `Role`, `ProviderName`, `ProviderCall`, `CallRecord` defined in `domain/common.py`, re-exported by `ports/models.py`; `RetrievalResult` in `domain/records.py`, `ExportStatus` and `SpanHandle` in `domain/turn.py`, re-exported by `ports/runtime.py` | `SpecialistResult.calls`, `KnowledgeCapture.result`, `TurnRecord.trace_export` are domain fields |
| D-3 | `pydantic_core` counts as "pydantic" for AC-18 | `core_schema` and `PydanticCustomError` are pydantic's own core; needed for the ID types and stable error codes |
| D-4 | Model ports declare `provider: ClassVar[ProviderName]` | Scratch run: mypy and pyright both accept ClassVar↔ClassVar; pyright rejects ClassVar against `@property`; adapters use ClassVar (models.md §2) |
| D-5 | `Customer.phone`, `Customer.email` are `SecretStr` | Issued columns hold PII; same rule as `FormValues.phone` (D2) |
| D-6 | `ProviderTurn = JsonValue` (`ToolStep.raw`) | DO-4 names it without a sketch; MOD-17 makes provider message objects `JsonValue` items |
| D-7 | `IdentityStep` = discriminated union of the eight identity result types | graph-core §8 counts "NotVerified or CodeWrong (graph-tools types)"; graph-tools §5 "maps result → IdentityStep"; every result carries `kind` |
| D-8 | `Locator.from_form` returns `None` for two complete groups too; never raises | graph-tools §5 "None when the form holds no complete locator"; the card offers one set at a time |
| D-9 | `ConversationState`: `settled: Settled \| None = None`; defaults for `controller` (ai), `identity` (not_checked, tries 3), lists, counters and every turn-scoped key; only `thread_id` and `turn_input` required | LangGraph validates the invocation input against a pydantic state schema; `TurnService` never reads state (web.md §9) |
| D-10 | Planner-fallback `RoleSpec`: Sonnet, effort `low`, cap **8.0 s [A]**, max tokens 1500 | DO-1 §8.1 names no cap for it; 8 s = the other single-step Sonnet cap; replaced by the Sonnet-planner p95 from the first E-1 run |
| D-11 | `CaseState` = OpenAPI `CaseSummary.lifecycle` enum; `Window`, `ServiceType` = issued `CHECK` values | DO-4 names them without values; the signed contract and the issued schema are the authorities |
| D-12 | `TaskDetails`, `ConfirmationView`, `ReportedPoint`, `TurnPath` built from DO-4's complete comment lists | A comment that lists every field/value is a sketch; one ending in "…" is not (§8.2) |
| D-13 | `.env.example` lives at the repo root (the tracked template), not under `src/meridian/` | It is the file developers copy to `.env`; AEA-09 reads it; `.gitignore` already whitelists it |
| D-14 | `ModelSettings` also rejects a missing role (`missing_role`) | DO-3 S-2 "validated at start-up"; the gateway needs every role |
| D-15 | `Brief` validator also checks keys and that `not_generated` appears only on 2, 4, 7 | DO-4 §7 heading table and its "headings 2, 4, 7 only" comment |
| D-16 | `ToolCallRecord.name` ≤ 64 | graph-tools §1 comment "(an unknown name is kept, ≤ 64 chars)"; AEA-22 truncates before building |

### 8.2 Types not built (no sketch, no addendum, no OpenAPI schema) — request one AEA-02 follow-up

Per the ticket ("listed in the plan as blocked-on the owning topic, never filled by guess"):

| Type | Used by (field) | Owning topic / ticket that must sketch it | Effect here |
|---|---|---|---|
| `LastLookups` | `ConversationState.last_lookups`, `FactsUpdate.last_lookups` | graph-nodes / AEA-38 (facts) | field omitted |
| `ChangeRequestRef` | `ConversationState.pending_change`, `FactsUpdate.pending_change` | graph-nodes / AEA-38 | field omitted |
| `MissingInfo` (DO-4 lists "locate_needed, zip_needed, slot_pick_needed, code_needed …") | `OpenTask.missing`, `TurnFacts.missing` | graph-nodes / AEA-38, AEA-37 | field omitted |
| `NoticeCode` ("card_number_removed, booking_cap, out_of_area …") | `TurnFacts.notices` | graph-nodes / AEA-38, AEA-21 | field omitted |
| `AccountFactsView` | `TurnFacts.account` | graph-nodes / AEA-38 | field omitted |
| `SettledForModel`, `ResponderRules` | `ResponderInput.settled`, `.rules` | graph-nodes / AEA-38 | **`ResponderInput` not built** (a partial one would let a prompt render without "ALREADY DONE", the WP-4F bug) |
| `KnowledgeSlice`, `AccountSlice` | `SpecialistTask.slice` | graph-tools / AEA-35, AEA-39 | **`SpecialistTask` not built** (incl. `offer_quick_checks`) |

**Request to the orchestrator:** cut one small follow-up ("AEA-02b: the reply/specialist types") after an Opus
residual pass sketches these, merged **before AEA-21 and AEA-15** (AEA-21 AC-4 names `last_lookups` and
`pending_change` as durable keys; AEA-15's `build_evidence(facts…)` and AEA-21's compose read `TurnFacts.account` /
`.notices`) and before AEA-35, AEA-37, AEA-38, AEA-39. Not a wave move if it lands in wave 1 ahead of those merges;
the orchestrator decides. Two sibling plans already record it as their R-1: `AEA-21.md` (tolerates the absence) and
`AEA-35.md` (blocked; it offers a sketch of `KnowledgeSlice`, `AccountSlice`, `SpecialistTask` as input to that pass,
and notes `SpecialistTask` holds `PlannedTask` from `domain/turn.py`, so it must be defined in `turn.py` or later, not
in `specialists.py` as DO-3 places it). This plan does not adopt that sketch: the ticket says an unsketched type is
never filled by guess.

### 8.3 Things deliberately left to other tickets

- `ModelOutcome` (DO-4 §12) is not in this ticket's lists → AEA-20 defines it in `agent/gateway.py`.
- `KnowledgePoint`'s "passage returned in this run" check needs run context → AEA-35's builder enforces it.
- `BriefItem.sources` ↔ wire `source_ids`: the route (AEA-45) maps; domain keeps DO-4's `sources`.
- Turn-scoped reducer keys (`specialist_results`, `halt`) cannot be reset by an ordinary update; AEA-21 resets them
  per invocation (e.g. LangGraph's `Overwrite`, if 1.2.16 has it) — its AC-4.
- `meridian/domain/__init__.py` is AEA-01's empty marker: consumers import from the submodules (AEA-05 PD-9 agrees).

### 8.4 Contradictions to report to AEA-08 (not edited here; AC-22)

DO-4 lines still contradicting an addendum or this plan, with no "Superseded" note:
1. §1 `TurnInput` lacks `form` kind, `message_id`, `card_id`, `card_number_seen` (graph-core §2).
2. §3 `RuleMatches` still commented `# gates/rules.py` and lacks `correction` (graph-core §8, R-G-1); `Intake` lacks
   `card_id`.
3. §4 `PlannerChoices.handoff` lacks `late_technician` (cases A-6); `Plan` lacks `planner_failed` (graph-nodes §5).
4. §5 `SpecialistTask` lacks `offer_quick_checks`; `SchedulingResult` lacks `quick_checks` (graph-tools §2–§3);
   `run_specialist` is now `SpecialistRunner.run`; `KnowledgeSlice`, `AccountSlice` never sketched.
5. §6 `EscalationInputs` lacks `now` (R-G-15); rows 4, 6, 7 superseded by cases §3.4.
6. §7 `Promise` docstring still says a validator rejects text (GRC-2 removed it); `HandoffReason` lacks
   `burning_ruled_out` (CAS-16 A, D-14); `CaseSummary` lacks `due_at` (cases A-4).
7. §8 `TurnFacts` types `AccountFactsView`, `MissingInfo`, `NoticeCode` never sketched; §9 `SettledForModel`,
   `ResponderRules` never sketched.
8. §10 `CheckEvent.check` / `.result` narrower than graph-nodes §1; `Claim.kind` lacks `quote`.
9. §11 `ApiErrorCode` lists `STAFF_AUTH_REQUIRED` (note exists, enum not edited).
10. §12 the three model Protocols lack the `provider` ClassVar (models.md cross-topic 2); `ToolStep.raw: ProviderTurn`
    never sketched (this plan: `JsonValue`).
11. §13 `RetrievalResult` home moves to `domain/records.py` (re-exported). (The §14 `IdentityService` "cap reached"
    comment this item also named was fixed by AEA-08, `c0621de`.)
12. This plan's D-1/D-2 homes: DO-3 §3/§4.1 tables should say which types are defined in `common`, `records`,
    `identity`, `turn` and re-exported; DO-3 §4.1 "domain/turn.py depends on common, records, actions" is now
    "common, records, actions, identity, specialists, handoff, blocks" (DO-3 revision 3 line 340 still says "common,
    records, actions"). The slice plan row still says 9 domain files (11).

### 8.5 Collisions with sibling tickets

| Surface | Sibling | Handling |
|---|---|---|
| `tests/unit/test_import_direction.py` | AEA-01, 04, 03 functions are on `main`; AEA-05 appends after this merges | Append one uniquely named function at the end of the file; the merge agent resolves add/add hunks by keeping all functions |
| `.claude/reference/area-map.md` A0 row, `docs/design/code-design.md` §3 `**Built:**` line, `icm-progress.md` | AEA-01, 03, 04 already edited them; AEA-10 and AEA-11 will | Edit only the cell/line named in step 21; expect a trivial text conflict at merge |
| `docs/testing/journeys/` | AEA-01 and others add their own records | One file per ticket |
| `tests/unit/domain/conftest.py` | none (this folder is AEA-02's at wave 0) | Later tickets add their own folders' fixtures |

### 8.6 Other risks

- **Mypy strict + `init_typed`** will reject `ActionKey(thread_id="…")`; build IDs with their classes, invalid input
  via `model_validate` (§4.0 rule 9).
- **`FormValues.customer_id: CustomerId`** means a malformed ID in the locate form is a 400 at the route, not
  `NOT_VERIFIED` (DO-4's typing). Flag for AEA-12/AEA-40 reviewers; no change here.
- **The `.env.example` write** may be refused by a tool that guards `.env*` names; if so, stop and report.
- **Frozen whole files**: if the test-writer's file and §7.2 disagree, the implementer reports rather than edits.
- **Duplicate ICM row** (*Routes verified against code and tests* appears twice since the AEA-01/03/04 merges): step 21
  edits one and reports the other for the next `context-maintenance` pass; it does not consolidate them.
- **`.env.example` today** carries `MERIDIAN_LLM_MODEL`, `MERIDIAN_FAST_MODEL`, `MERIDIAN_TODAY`,
  `MERIDIAN_DAILY_SPEND_CAP_USD` with non-secret values; graph-core §12 drops all four. Nothing on `main` reads them
  (`grep -rn "MERIDIAN_LLM_MODEL\|MERIDIAN_FAST_MODEL\|MERIDIAN_TODAY\|MERIDIAN_DAILY_SPEND" src tests` is empty at
  `16ca639`).

---

## 9. Readiness

**READY.** No `blocked-on`: AEA-01 (`07924f5`: `pyproject.toml`, markers, `tests/unit/test_import_direction.py`,
`tests/journeys/affected.py`) and AEA-04 (`ef03e05`: `RedactionProfile`) are on `main` at `16ca639`. Order: the
test-writer freezes §3.3's three files first, then the implementer runs steps 0–22.
- No NEEDS-DECISION: CAS-16 is decided (sign-off D-14 → option A, `burning_ruled_out`); no signed contract changes
  (the OpenAPI file is only read); every open shape is either decided above (§8.1, engineering) or listed as blocked
  for the AEA-02b follow-up (§8.2), as the ticket instructs. That follow-up blocks AEA-35 and later consumers, not
  this ticket.

**Gates:** none (no human, paid or live gate). Security review at the wave-0 merge.

---

## Appendix A — OpenAPI field lists for `blocks.py` (generated 2026-10-21 from `ui-contracts.openapi.yaml`)

`?` would mark an optional property; none occurs. `X|null` = nullable, still required. `const true` is the YAML
boolean `true`. `BASE BlockBase` = the block also has `block_id`, `speaker`, `at` (and `type`, declared per block).

```
## BlockBase
  block_id: string ; type: string ; speaker: Speaker ; at: string format=date-time
## Speaker
  kind: string enum=['assistant', 'customer', 'representative', 'event'] ; display_name: string|null
## SourceChip
  passage_id: string ; file: string ; section: string ; version_date: string|null format=date ; excerpt: string
  audience: const 'customer' ; version_label: string
## Option
  option: string ; label: string ; disabled: boolean ; reason: string|null
## Money
  amount_cents: integer ; display: string
## FollowUpOptions
  legend: string
  channels: array[object{ channel: string enum=['email', 'phone']; label: string; on_record: boolean }]
  windows: array[object{ window: string enum=['morning', 'afternoon', 'any']; label: string }]
  general_only: boolean
## FollowUpView   (= domain.common.FollowUp)
  channel: string enum=['email', 'phone'] ; destination_label: string ; on_record: boolean
  window: string enum=['morning', 'afternoon', 'any'] ; saved_line: string
## SettledVisit   (= SettledVisit(VisitView) + window_label)
  appointment_id: integer ; date: string format=date ; window: string ; window_label: string ; technician: string
  service_type: string ; fee_line: string ; status: string enum=['booked', 'moved', 'original_stays']
  change_request: object{ change: string enum=['move', 'cancel']; wanted_text: string; fee_line: string } | null
## SettledRequest
  reference: string ; promise_text: string ; due_at: string|null format=date-time ; due_label: string|null
  extra_lines: array[string] ; live_queued: boolean ; followup: FollowUpView | null
## Write
  kind: string enum=['booked', 'moved', 'cancelled', 'change_request_sent', 'case_opened', 'followup_saved', 'verified']
  summary: string ; turn_id: string ; at: string format=date-time
## Settled   (Python: SettledView)
  built_from: const 'conversation_state' ; visit: SettledVisit | null ; request: SettledRequest | null
  identity: object{ status: string enum=['not_checked', 'code_sent', 'verified', 'not_verified', 'locked']; hint: string|null }
  replying: object{ kind: string enum=['ai', 'human']; display_name: string|null }
  actions: array[Write]
## Notice
  code: string enum=['RATE_LIMITED', 'BOOKING_CAP', 'SPEND_CAP_REACHED', 'TURN_TIMEOUT', 'BUSY', 'AI_PAUSED']
  actions: array[string enum=['try_again', 'talk_to_person']] ; retry_turn_id: string|null
  delivered_to_representative: boolean
## TextBlock (BASE BlockBase)
  type: const 'text' ; text: string ; sources: array[SourceChip]
## SourceChipBlock (BASE BlockBase)
  type: const 'source_chip' ; source: SourceChip
## SafetyBlock (BASE BlockBase)
  type: const 'safety' ; level: const 'DANGER' ; signal_word: string ; steps: array[string]
  call_key: object{ label: string; number: string } ; contact_line: string ; case_priority: const 'P0'
  case_reference: string|null ; fixed_text: const true ; pinned: const true
## ConditionalSafetyBlock (BASE BlockBase)
  type: const 'conditional_safety' ; level: const 'WARNING' ; text: string ; emergency_line: string
  case_priority: const 'P1' ; case_reference: string|null ; fixed_text: const true
## BurningCheckBlock (BASE BlockBase)
  type: const 'burning_check' ; card_id: string ; options: array[Option] ; answered: string|null ; question: string
## EmergencyLineBlock (BASE BlockBase)
  type: const 'emergency_line' ; lead_text: string ; number: string ; number_note: string ; separate_line: string|null
  case_priority: const 'P1' ; case_reference: string
## QuickChecksBlock (BASE BlockBase)
  type: const 'quick_checks' ; card_id: string ; options: array[Option] ; answered: string|null ; offer_text: string
  checks: array[object{ text: string; source: SourceChip }] | null
## UrgencyQuestionsBlock (BASE BlockBase)
  type: const 'urgency_questions' ; card_id: string ; options: array[Option] ; answered: string|null
  questions: array[object{ question_id: string; text: string; answers: array[Option] }] ; skippable: const true
## WherePromptBlock (BASE BlockBase)
  type: const 'where_prompt' ; card_id: string ; options: array[Option] ; answered: string|null ; label: string
  submit_label: string
## LocatePromptBlock (BASE BlockBase)
  type: const 'locate_prompt' ; card_id: string ; options: array[Option] ; answered: string|null ; reason_text: string
  field_sets: array[array[string enum=['name', 'phone', 'customer_id', 'invoice_number']]]
## CodePromptBlock (BASE BlockBase)
  type: const 'code_prompt' ; card_id: string ; options: array[Option] ; answered: string|null
  state: string enum=['sent', 'wrong', 'expired', 'locked'] ; hint: string ; tries_left: integer|null
  expires_at: string|null format=date-time ; resend_offered: boolean ; resends_left: integer|null ; inbox_link: string
  code_in_response: const 'never'
## SlotCardBlock (BASE BlockBase)
  type: const 'slot_card' ; card_id: string ; options: array[Option] ; answered: string|null ; urgent: boolean
  days: array[object{ date: string format=date; label: string; open_count: integer;
                      windows: array[object{ slot_id: string; date: string format=date; window: string;
                                             window_label: string; technician: string; member_only: boolean;
                                             taken: boolean }] }]
  standard_fee: Money ; hint: string ; members_note: string|null
## ConfirmationBlock (BASE BlockBase)
  type: const 'confirmation' ; appointment_id: integer ; date: string format=date ; window_label: string
  technician: string ; fee_line: string ; timeline: array[string] ; free_change_note: string
## AppointmentBlock (BASE BlockBase)
  type: const 'appointment' ; appointment_id: integer ; date: string format=date ; window_label: string
  technician: string ; fee_line: string ; label: const 'Your booked visit'
## CancelledBlock (BASE BlockBase)
  type: const 'cancelled' ; appointment_id: integer ; date: string format=date ; fee_line: string
## AccountCardBlock (BASE BlockBase)
  type: const 'account_card' ; kind: string enum=['invoice', 'membership', 'warranty']
  invoice: object{ invoice_id: string; lines: array[object{ description: string; amount: Money; source: SourceChip | null }];
                   total: Money; balance: Money; due_on: string format=date; paid: boolean } | null
  membership: object{ tier: string; renewal_date: string format=date } | null
  warranty: object{ install_date: string format=date; sentence: string } | null
## ChangeRequestBlock (BASE BlockBase)
  type: const 'change_request' ; change: string enum=['move', 'cancel'] ; fee_line: string ; original_stays_line: string
  wanted_text: string ; windows_shown: array[object{ slot_id: string; window_label: string; date: string format=date }]
  reference: string ; promise_text: string ; due_at: string|null format=date-time ; due_label: string|null
  extra_lines: array[string] ; cant_guarantee_line: string|null ; phone_support_line: string|null
  produced_by_code: const true
## HandoffBlock (BASE BlockBase)
  type: const 'handoff' ; card_id: string ; options: array[Option] ; answered: string|null ; reference: string
  variant: string enum=['nobody_online', 'refund', 'staffed'] ; promise_text: string
  due_at: string|null format=date-time ; due_label: string|null ; extra_lines: array[string]
  produced_by_code: const true ; followup_chooser: FollowUpOptions
## LiveQueuedBlock (BASE BlockBase)
  type: const 'live_queued' ; reference: string ; promise_text: string ; produced_by_code: const true
## FailureOfferBlock (BASE BlockBase)
  type: const 'failure_offer' ; text: string ; person_key: boolean
## NoInfoBlock (BASE BlockBase)
  type: const 'no_info' ; text: string ; person_key: boolean
## NoticeBlock (BASE BlockBase)
  type: const 'notice' ; code: string enum=['RATE_LIMITED', 'BOOKING_CAP', 'SPEND_CAP_REACHED', 'TURN_TIMEOUT', 'BUSY', 'AI_PAUSED']
  text: string ; person_key: boolean
## ErrorBlock (BASE BlockBase)
  type: const 'error'
  code: string enum=['SLOT_TAKEN', 'OUT_OF_AREA', 'CODE_WRONG', 'CODE_EXPIRED', 'CODE_LOCKED', 'CODE_CAP_REACHED', 'NOT_VERIFIED']
  text: string ; tries_left: integer|null ; fresh_windows: SlotCardBlock | null ; person_key: boolean
## SessionEndedBlock (BASE BlockBase)
  type: const 'session_ended' ; text: string ; new_chat_action: string
```

Payloads (for `turn.py` and the wire-shape test): `TextPayload {kind: const 'text'; text: string minLength 1
maxLength 2000}`; `ChoicePayload {kind: const 'choice'; card_id; option}`; `CodePayload {kind: const 'code'; card_id;
code: string pattern ^[0-9]{6}$}`; `FormPayload {kind: const 'form'; card_id; values: object{name?, phone?,
customer_id?, invoice_number?, zip_or_city?} (all optional)}`; `InboxMessage {id, at, to_masked, body, code, status
enum [active, used, expired], expires_at}` (domain drops `body`).
