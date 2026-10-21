# Plan — [AEA-26] spend: ledger and spend guard

**Status:** planned. READY to build once **AEA-02** and **AEA-10** are merged on `main` (both earlier waves; AEA-10 is the
build ledger's only listed blocker and itself waits on AEA-02). See §9.
**Issue:** GitLab `innocentnortey/inno-aea-callcenter` #26 (= `docs/plans/tickets/AEA-26.md`) · **Base revision:** `16ca639`
(main, 2026-10-21; first written against `c15a6b1`, refreshed against `16ca639`: only README/ledger docs changed between them)
**Lane / risk:** `lane::build-loop` · no `risk::security` (slice plan: not **Sec**). Normal loop: the implementer writes the
code **and** the tests named in §7 together. No test-writer, no frozen tests, no security agent.
**Planner:** Claude Opus 5.5 (`claude-opus-5-5`), 2026-10-21. **Implementer:** `fanout-implementer` on Sonnet.
**Worktree / branch:** whatever the orchestrator gives you (convention: `/home/linuxuser/workspaces/inno-aea-callcenter-wt/AEA-26`,
branch `aea-26-spend-ledger`). All paths below are relative to the repository root.

**What changed in this refresh (read if you saw the earlier version):**
1. The `register_spend` hunk no longer calls `deps.get_wall_clock()`. In AEA-23's plan that provider takes a `Request`;
   hunks read **container keys** (AEA-23 plan D-P3). The hunk now gets `Key(...)("wall_clock")` and
   `Key(...)("uow_factory")` from the container, built **by name** (keys are equal by name), so this ticket imports
   nothing from `web/deps.py` and AEA-23 is no longer a prerequisite.
2. `SpendRepo.append` uses AEA-10's `last_row_id(cur, "spend_ledger")` (AEA-10 plan: "every append that returns an id uses it").
3. The `SpendRepo` class docstring **must drop** the phrase `AEA-02 creates the constructor only` (AEA-10 scopes the
   shell test's "no public member" check to classes whose docstring still has it; §8 R-2).
4. `provider_request_id` is stored from the record only (no fallback to the failure's); `record` builds the row with
   `model_dump()` (prototyped against AEA-02's branch: works).
5. PA-2's "no 60" check is a word-boundary grep, so the contract default `600.0` does not trip it.
6. AC-15's DO-3 edit follows house style: the one `**Built:**` line under §3, not the tree lines. The ICM row is named
   by its stable last cell.

---

## 1. Goal and sources

### 1.1 Goal (quoted from the issue, *What to build*)

> The one place that records what every model call cost and stops model use at a cap (DO-3 §4.4 `services/ledger.py`;
> DO-4 §14 `LedgerService` as revised by `stage7/models.md` §6, which wins):
> 1. `adapters/sqlite/repos_spend.py` (body of AEA-02's shell, over the `20_spend.sql` that AEA-10 writes) …
> 2. `services/ledger.py` (models §6; MOD-11, MOD-13, MOD-18) …
> 3. A `register_spend()` hunk in `web/container.py` (own hunk only) that builds the one `LedgerService` and binds it for
>    the gateway (AEA-20), the turn service (AEA-40, as `SpendGuard`), the alert evaluator (AEA-32) and the metrics reader (AEA-53).

**What it does, concretely.** Every model-call attempt the gateway makes becomes one row in `spend_ledger`, stamped with
the real (wall) time in UTC. Before a turn, `TurnService` asks `allow_turn()`: "is today's spend, midnight to midnight in
Chicago, still under $30?". Separately, when a provider itself says "you are out of credit", the ledger opens that
provider's circuit: calls to it are refused, and after 10 minutes one probe call is let through to see if it is fixed.

**Example pair (the ticket's; no worked pair spends money).** Input: the ledger holds $29.98 since Chicago midnight and a
turn starts; its calls add $0.039. Output: `allow_turn()` was `True` at the start, so the turn finishes and every attempt
is recorded; the next `allow_turn()` is `False`; at the next Chicago midnight it is `True` again. Separately, an
Anthropic `PROVIDER_SPEND_CAP` at 14:00 makes `admit_call("anthropic")` `REFUSE` until 14:10, then `PROBE` once; the
gateway calls `close_provider_cap("anthropic")` after the probe succeeds, and calls flow (`ALLOW`) again.

### 1.2 Context

Wave 2, area A2 (DO-3 §8). On `main` today (`16ca639`): AEA-01 (`policy/limits.py`, `web/container.py` with 27 no-op
stubs, `tests/journeys/` skeleton), AEA-03, AEA-04 (in progress of merge), AEA-07/08/25 (docs). AEA-02 is being built
(worktree `inno-aea-callcenter-wt/AEA-02`; its `domain/common.py`, `domain/turn.py`, `ports/*`, `repos_spend.py` shell
were read for this refresh). AEA-10 (`db.py`, `20_spend.sql`, `SqliteUnitOfWorkFactory`, `format_wall`, `temp_sqlite()`)
is planned. Signatures below are copied from the stage7 addenda, AEA-02's branch and the AEA-10 plan. **If merged code
differs from a name below, the merged code wins**: use the merged name and note it in your report.

### 1.3 Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-26.md` | AC-1…AC-15, owned files, must-not-edit list, example pair |
| Slice plan | `docs/plans/slice-plan.md` §1 wave-2 row AEA-26 (blocked by 10); §0 deviation 1 (AEA-10 writes every DDL); §0a J-9 row (*proposed:* 26); §3 rows `repos_*.py`, `web/container.py`, `tests/journeys/` | Own hunk only; never `schema/*.sql`; one journey file `tests/journeys/j9/test_aea_26.py` |
| Build ledger | `.claude/state/build-ledger.md` row AEA-26 | Blockers: AEA-10 |
| Requirements | PRD R-41; PRD §5 *Spend* ($30/day, Q-061) | Spend cap falls back to handoff (the handoff itself is AEA-40's) |
| Component contracts | DO-4 `docs/design/contracts/internal-components.md` §11 (`ProviderFailure`, kinds, `retryable` rule l. 712), §13 (`UnitOfWork.spend`), §14 `LedgerService` | `record`, `spend_today`, `allow_turn`, `trip_provider_cap`, `models_disabled` |
| Addendum (wins) | `docs/design/contracts/stage7/models.md` §1 (`ProviderCall`, `CallRecord`), §5 rules 1, 6, 7, §6 (whole section), §7 | Every signature in §4.5; circuit table; column list |
| Addendum | `stage7/cases.md` §1.0 (unit of work, `format_wall`), §1.3 *Kept* (reset keeps `spend_ledger`), §8 (`AlertEvaluator` reads `spend_today`, `open_circuits`) | Write unit of work per record; append-only |
| Addendum | `stage7/web.md` §4 (`get_wall_clock`: the one wall clock, MC-20), §15 (`ContainerOverrides.wall_clock`, D-13) | The ledger gets the same wall-clock callable as every MC-20 consumer: the container key `wall_clock` that AEA-23's `register_web` provides from `create_app`'s choice |
| Sibling plan | `docs/plans/fanout/2026-10-21-build/AEA-23.md` §5 step 5 (key table: `uow_factory`, `wall_clock`), step 9, D-P3 ("hunks never call providers") | Hunk reads keys, never providers |
| Sibling plan | `AEA-10.md` §4.3 (`db.py`, `last_row_id`, fixtures), step 9, R-2, R-13 (`test_container.py` guard on "No-op until") | Exact storage names; docstring markers |
| Sibling plan | `AEA-32.md` §4 (reads `Key[SpendReader]("ledger")`) | Key name `"ledger"` is binding |
| Addendum | `stage7/graph-core.md` §4 (`GraphDeps.ledger: ModelsStatus`, `models_disabled()`) | `LedgerService` satisfies `ModelsStatus` structurally (same method) |
| Decisions | `docs/plans/7b-decisions/models.md` MOD-5, MOD-11, MOD-13, MOD-15, MOD-18, MOD-19; merge MC-10, MC-20, MC-22; `docs/plans/stage7-signoff.md` D-13 | Our cap only in `allow_turn`; circuit per provider in memory; probe-only release; no persistence |
| Code design | DO-3 `docs/design/code-design.md` §2.1 (`SVC --> SQL`, `SVC --> PORTS` allowed; services never `sqlite3`), §3 (`**Built:**` line), §4.4 row `services/ledger.py` ("UoW (`repos_spend`), limits") | `services/ledger.py` imports no `sqlite3`; may import `policy.limits` and the repo's row type |
| Evaluation plan | DO-5 | N/A (ticket *Evaluation*: no suite judges the ledger) |
| Observability | DO-6 `docs/design/observability-contract.md` rows `spend_ledger`, *Storage*, *Missing instrumentation*; WF-1 row | One row per attempt with `turn_id`, `thread_id`, `run_tag`; no prompt, output, customer text or key |
| Metrics | DO-7 M-24, M-25, M-26 | Columns keep M-24/25/26 computable from rows alone |
| Rules | `.claude/rules/build-loop-test-scope.md` (+ AEA addition), `integrated-journeys.md` §3–§4, `context-maintenance.md`, workspace `code-design-solid-modularity.md` | Affected tests + fast gates + affected journeys; journey record at `mock-tested`; context rows in the same change; no new seam |

---

## 2. Boundary

### 2.1 Owned files (the only files you may create or edit)

| File | Create / modify | Change |
|---|---|---|
| `src/meridian/adapters/sqlite/repos_spend.py` | modify (AEA-02's shell) | `SpendRow`, SQL constants, row reader, the three `SpendRepo` methods; new docstrings (§5 step 2) |
| `src/meridian/services/ledger.py` | create | `CallAdmission`, `SpendGuard`, `LedgerService` (§5 step 3) |
| `src/meridian/web/container.py` | modify **only the body and docstring of `register_spend`** | §5 step 4 |
| `tests/services/test_ledger.py` | create | AC-1…AC-13, the example pair, PA-3 (§7.1) |
| `tests/unit/web/test_register_spend.py` | create | The hunk test PA-1 (§7.1) |
| `tests/journeys/j9/test_aea_26.py` | create | AC-14 journey step at mock level (§7.1) |
| `docs/testing/journeys/<run-date>-AEA-26.md` | create | Journey record (§7.4) |
| `.claude/reference/area-map.md` | modify (A2 row, last cell only) | AC-15 (§5 step 7) |
| `.claude/state/icm-progress.md` | modify (one row's evidence cell) | AC-15 |
| `docs/design/code-design.md` | modify (the `**Built:**` line under §3 only) | AC-15 |

`<run-date>` is the build day in America/Chicago: `TZ=America/Chicago date +%F`.

### 2.2 Shared surfaces you read but never edit

`src/meridian/adapters/sqlite/db.py`, `schema/20_spend.sql`, `repos_core.py`, `migrate.py`, `rows.py` (AEA-10);
`src/meridian/domain/*`, `src/meridian/ports/*`, `src/meridian/config.py` (AEA-02); `src/meridian/policy/limits.py`,
every other function in `src/meridian/web/container.py`, `tests/unit/web/test_container.py`,
`tests/unit/test_import_direction.py`, `tests/conftest.py`, `tests/journeys/affected.py`, `tests/journeys/README.md`,
`pyproject.toml`, `uv.lock`, every `__init__.py` (AEA-01); `tests/fixtures/sqlite.py` (AEA-10);
`tests/unit/adapters/test_repo_shells.py` (AEA-02/AEA-10); `src/meridian/web/deps.py`, `web/app.py` (AEA-23, if merged).

### 2.3 Owned by other tickets — do not create or edit

`agent/gateway.py` (AEA-20: decides when to admit, record, trip and close), `services/turn.py` (AEA-40: composes the
`SPEND_CAP_REACHED` notice), `services/health.py`, `repos_ops.py` (AEA-32: alerts), `services/metrics_reader.py`
(AEA-53), any other `register_<x>()` hunk, `tests/journeys/support/` (AEA-57), `tests/fakes/` (AEA-11), any
`schema/*.sql`. Never edit: the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`,
`ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, DO-4 or the stage7 addenda. Never read `.env`.

---

## 3. Requirements

### 3.1 Acceptance criteria → implementation → verification

All `::name` tests are in `tests/services/test_ledger.py` unless another file is named. Full AC text is in the ticket.

| AC | Requirement (issue, abridged) | Implemented by (§5) | Verified by |
|---|---|---|---|
| AC-1 [invariant] | One row per `CallRecord` (`ok` and `error`), every models §6 column; `recorded_at` UTC `+00:00` from the injected wall clock; a failed row reads back with its kind and HTTP status | Step 2 (`append`, `_row_from_db`), step 3 (`record`, `_now`) | `::test_record_one_row_per_attempt_including_failures` |
| AC-2 [invariant] | `spend_today()` = 00:00–24:00 America/Chicago; live, eval, load together; 23:59:59 counts, 00:00:00 is the next day; UTC midnight is not a boundary | Step 3 (`_day_bounds_utc`, `spend_today`), step 2 (`total_between`) | `::test_spend_today_is_the_chicago_day` |
| AC-3 [invariant] | The 25-hour day of Sun 2026-11-01 | Same (zoneinfo bounds) | `::test_spend_day_across_dst_end` |
| AC-4 [invariant] | `allow_turn()` `True` below the injected cap, `False` at/above; overrun rows still written; cap 5.0 moves the boundary; no `30` in `ledger.py` | Step 3 (`allow_turn`) | `::test_allow_turn_at_cap_and_overrun_recorded`; `grep -c "30" src/meridian/services/ledger.py` prints `0` |
| AC-5 [invariant] | Our cap releases at the next Chicago midnight with no action | Step 3 | `::test_allow_turn_releases_at_chicago_midnight` |
| AC-6 [failure/refusal] | Circuit probe cycle (REFUSE at T+9 min, PROBE once at T+10 min, second caller REFUSE, ALLOW after close; re-trip resets the trip time; lost probe after more than 60 s) | Step 3 (circuit) | `::test_provider_circuit_probe_cycle` |
| AC-7 [failure/refusal] | Only `PROVIDER_SPEND_CAP`, `OUR_SPEND_LIMIT` trip, only `failure.provider`; `open_circuits()` is `("anthropic",)` | Step 3 (`trip_provider_cap`, `open_circuits`) | `::test_trip_by_kind_and_per_provider` (parametrised over all 14 kinds) |
| AC-8 [invariant] | Not released by Chicago midnight; not persisted; trip row stays in `spend_ledger` | Step 3 | `::test_circuit_not_released_by_midnight_and_not_persisted` |
| AC-9 [invariant] | `allow_turn` = our cap only; `models_disabled` = either cause | Step 3 | `::test_models_disabled_either_cause` |
| AC-10 [invariant] | 20 concurrent `record` calls all land; exact sum | Step 3 (one write unit of work per record) | `::test_concurrent_records_all_written` |
| AC-11 [invariant] | `SpendRepo` public methods exactly `append`, `total_between`, `for_turn`; `isinstance(ledger, SpendGuard)` | Step 2, step 3 (`@runtime_checkable`) | `::test_spend_repo_append_only_and_spend_guard` |
| AC-12 [negative] | Rows and log lines hold allow-listed fields only; seeded key-shaped string and customer sentence absent from table, log and trace | Step 3 (fixed log strings, no `exc_info`; the ledger takes no trace sink) | `::test_rows_and_logs_hold_allow_listed_fields_only` |
| AC-13 [capture] | Rows readable per `turn_id`, summable per `thread_id` with `run_tag` | Step 2 (`for_turn`; indexes are AEA-10's) | `::test_rows_queryable_by_turn_and_thread` |
| AC-14 [journey] | Extends J-9: spend-cap turn shows `SPEND_CAP_REACHED` + person action; `turn` row `degraded_handoff`/`spend_cap`; no `spend_ledger` row of its own. Level `integrated with a scripted model` needs AEA-57 + AEA-51; until then `mock-tested` | Step 6 (mock-level journey step + record) | `uv run pytest -m journey tests/journeys/j9/test_aea_26.py -q`; record `docs/testing/journeys/<run-date>-AEA-26.md` (level `mock-tested`, *Blocked by* AEA-57, AEA-51) |
| AC-15 [regression/context] | Area map A2, ICM row, DO-3 §3 status updated; no `schema/*.sql` in the diff | Step 7 | `git diff --name-only main...HEAD` |
| Example pair | $29.98 → allow; +$0.039 overrun recorded → deny; Chicago midnight → allow; Anthropic cap at 14:00 → REFUSE to 14:10 → PROBE → close → ALLOW | Step 3 | `::test_example_pair_cap_overrun_midnight_and_probe` |

### 3.2 Plan-added criteria (engineering; report them in the issue comment at merge)

| ID | Criterion | Why | Verified by |
|---|---|---|---|
| PA-1 | `register_spend` provides the one `LedgerService` under `Key[LedgerService]("ledger")`, built lazily from the container's `"uow_factory"` and `"wall_clock"` keys and `limits.spend.daily_cap_usd`; the same object on every `get` | Ticket item 3 has no test | `tests/unit/web/test_register_spend.py::test_register_spend_provides_one_ledger_from_limits_and_wall_clock` |
| PA-2 | `LedgerService.__init__` gains two **optional** keyword parameters after the contract's four: `monotonic: Callable[[], float] = time.monotonic` and `probe_lost_after_s: float = _PROBE_LOST_AFTER_S` | AC-6 asks for a fake monotonic clock; the 60 s "probe lost" figure is the turn deadline (`Limits.turn.deadline_s`), so it must not be a second literal. Callers using the models §6 signature are unaffected | AC-6 test; `grep -nE '\b60(\.0)?\b' src/meridian/services/ledger.py` prints nothing |
| PA-3 | A naive datetime from `wall_clock` raises `ValueError`; a missing `America/Chicago` zone fails at construction (container build), not mid-turn | Fail loudly where it is cheap | `::test_naive_wall_clock_rejected` |

### 3.3 Source-contract reconciliation

| Obligation | Source | In ticket | Disposition | Step / owner |
|---|---|---|---|---|
| One row per attempt, failed included | models §5 rule 6, §6 | AC-1 | in-ticket | step 3 |
| `recorded_at` via `format_wall` | cases §1.0, MC-20 | AC-1 | in-ticket | step 2 |
| Chicago day via `zoneinfo` | models §6, DO-3 C-12 | AC-2, AC-3 | in-ticket | step 3 |
| `allow_turn` our cap only; gateway never checks it | MOD-11 | AC-9 | in-ticket | step 3 |
| Circuit table, probe-only release, no persistence | MOD-13 | AC-6, AC-8 | in-ticket | step 3 |
| `SpendGuard` one-method Protocol | MOD-18 | AC-11 | in-ticket | step 3 |
| `SpendRow`/`SpendRepo` signatures | MOD-19 | AC-1, AC-11, AC-13 | in-ticket | step 2 |
| `cost_source` column | MOD-5 | AC-1 | in-ticket | step 2 |
| Reset keeps `spend_ledger` | cases §1.3 *Kept* | AC-11 | in-ticket (no delete method); the reset itself is AEA-31/AEA-10 (`KEPT_TABLES`) | other-ticket |
| The ledger's wall clock is the one MC-20 wall clock (D-13 override reaches it) | web.md §4, §15; AEA-23 D-P3 | — | added PA-1 (hunk reads key `"wall_clock"`) | step 4 |
| `ModelsStatus` structural fit for `GraphDeps.ledger` | graph-core §4 | Agent handoff | in-ticket (method exists); wiring is AEA-51 | other-ticket |
| Probe-lost window = turn deadline, no second literal | models §6 table + MC-22 | — | added PA-2 | steps 3, 4 |
| Hunk binds the one ledger | ticket item 3 | — | added PA-1 | step 4 |
| `retryable` not stored; rebuilt from kind on read | models §6 ("rebuilt on read"), DO-4 §11 l. 712 | AC-1 | in-ticket; `BODY_ERROR` reads back `False` (its inner code is not stored), recorded §8 R-10 | step 2 |
| 90-day bound on spend rows | DO-6 *Storage* | — | n/a here: no pruning is specified for this ticket and AC-11 forbids a delete method; §8 R-6 | — |
| Notice composition, alerts, monitoring read | DO-4 §11, cases §8, §9 | Scope boundary | other-ticket (AEA-40, AEA-32, AEA-53) | — |

### 3.4 Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

---

## 4. Shared code to use (exact shapes; copied, not paraphrased)

**Check each import against merged `main` before writing code:**
`grep -n "^class ThreadId\|^class TurnId\|^class RequestId\|^class ProviderFailure\|^class CallRecord\|^ProviderName\|^class Role" src/meridian/domain/common.py`;
`grep -n "^RunTag\|^class TurnIds" src/meridian/domain/turn.py`;
`grep -n "^def format_wall\|^def parse_wall\|^def integrity_errors\|^def last_row_id\|^class StorageError" src/meridian/adapters/sqlite/db.py`.

### 4.1 From AEA-02 (`domain/common.py`, re-exported by `ports/models.py`; `domain/turn.py`; `ports/runtime.py`)

Copied from AEA-02's branch (`inno-aea-callcenter-wt/AEA-02`, 2026-10-21):

```python
# meridian.domain.common
class MeridianModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True)
class _PatternId(str): ...          # strict str schema with a regex; build through pydantic, never ThreadId("...")
class ThreadId(_PatternId)          # UUID4, lower case
class TurnId(_PatternId)            # UUID4
class RequestId(_PatternId)         # UUID4
class ProviderFailureKind(StrEnum):   # 14 values
    TIMEOUT = "timeout"; CONNECTION = "connection"; RATE_LIMITED = "rate_limited"; OVERLOADED = "overloaded"
    SERVER = "server"; PROVIDER_SPEND_CAP = "provider_spend_cap"; OUR_SPEND_LIMIT = "our_spend_limit"
    BAD_REQUEST = "bad_request"; AUTH = "auth"; NOT_FOUND = "not_found"; BODY_ERROR = "body_error"
    REFUSAL = "refusal"; MAX_TOKENS = "max_tokens"; INVALID_OUTPUT = "invalid_output"
ProviderName = Literal["anthropic", "openrouter_jev"]      # a plain Literal alias: get_args(ProviderName) works
class ProviderFailure(MeridianModel):
    kind: ProviderFailureKind
    provider: ProviderName
    http_status: int | None
    retry_after_s: float | None
    retryable: bool
    provider_request_id: str | None
class Role(StrEnum):
    PLANNER = "planner"; CLASSIFIER = "classifier"; PLANNER_FALLBACK = "planner_fallback"
    SPECIALIST = "specialist"; RESPONDER = "responder"; BRIEF = "brief"
class ProviderCall(MeridianModel):
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
class CallRecord(ProviderCall):
    role: Role
    attempt: int = Field(ge=1, le=2)
    @classmethod
    def from_provider(cls, call: ProviderCall, *, role: Role, attempt: int) -> CallRecord: ...

# meridian.ports.models re-exports: CallRecord, ProviderCall, Role (and imports ProviderFailure, ProviderName)
#   → import CallRecord and Role from meridian.ports.models; ProviderFailure, ProviderFailureKind, ProviderName and
#     the ID types from meridian.domain.common.

# meridian.domain.turn
RunTag = Literal["live", "eval", "load"]
class TurnIds(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    request_id: RequestId
    run_tag: RunTag
    run_id: str | None
    agent_version: str

# meridian.ports.runtime
class UnitOfWork(Protocol):
    core: CoreRepos; spend: SpendRepo; identity: IdentityRepos; booking: BookingRepos
    cases: CaseRepos; staff: StaffRepos; ops: OpsRepos
    def commit(self) -> None: ...
class UnitOfWorkFactory(Protocol):
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]: ...
```

The `repos_spend.py` shell AEA-02 leaves (keep the constructor exactly; **replace** both docstrings, §5 step 2):

```python
"""Repository shell for the spend ledger (AEA-02 shell; body: AEA-26, models.md section 6)."""
from __future__ import annotations
import sqlite3
class SpendRepo:
    """the spend ledger. Body by AEA-26; AEA-02 creates the constructor only."""
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
```

Conventions (AEA-02): `from __future__ import annotations` first; `import datetime as dt` and `dt.datetime`; absolute
imports only; build models from dicts with `Model.model_validate({...})` (mypy `init_typed = true`), never pass a plain
`str` to an ID field through the constructor.

### 4.2 From AEA-10 (`adapters/sqlite/db.py`, `tests/fixtures/sqlite.py`, `schema/20_spend.sql`) — from the AEA-10 plan §4.3

```python
# meridian.adapters.sqlite.db
BUSY_TIMEOUT_MS = 5000
class StorageError(Exception):            # str(exc) == f"{table}: {constraint}"; never a value
    def __init__(self, table: str, constraint: str) -> None: ...
@contextmanager
def integrity_errors(table: str) -> Iterator[None]: ...   # sqlite3.IntegrityError → StorageError(table, kind) from None
def format_wall(dt: datetime) -> str: ...  # tz-aware → dt.astimezone(UTC).isoformat(); naive → ValueError("naive datetime")
def parse_wall(text: str) -> datetime: ... # datetime.fromisoformat(text) → tz-aware; .astimezone(UTC)
def last_row_id(cur: sqlite3.Cursor, table: str) -> int: ...   # cur.lastrowid; None → StorageError(table, "no row id")
class SqliteUnitOfWorkFactory:            # __call__(*, write=False, exclusive=False) -> ContextManager[SqliteUnitOfWork]
    # write=False → PRAGMA query_only=ON + BEGIN DEFERRED; write=True → BEGIN IMMEDIATE (waits ≤ 5 s for the lock);
    # exit without commit() → ROLLBACK; exception → ROLLBACK and propagate. One new connection per unit of work.

# tests.fixtures.sqlite
@dataclass(frozen=True)
class TempStore:
    data_dir: Path; db_path: Path; issued_path: Path; uow: SqliteUnitOfWorkFactory
@contextmanager
def temp_sqlite(*, issued_path: Path = ISSUED_DB) -> Iterator[TempStore]: ...   # migrated copy; removed afterwards
```

`20_spend.sql` (AEA-10; read only):

```sql
CREATE TABLE IF NOT EXISTS spend_ledger (
  id INTEGER PRIMARY KEY,
  recorded_at TEXT NOT NULL,
  thread_id TEXT, turn_id TEXT, request_id TEXT,
  run_tag TEXT CHECK (run_tag IN ('live','eval','load')), run_id TEXT, agent_version TEXT,
  role TEXT, provider TEXT, model TEXT, attempt INTEGER, latency_ms INTEGER,
  input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER, cache_write_tokens INTEGER, thinking_tokens INTEGER,
  cost_usd REAL, cost_source TEXT, status TEXT, failure_kind TEXT, http_status INTEGER,
  provider_request_id TEXT, stop_reason TEXT
);
-- indexes ix_spend_recorded_at, ix_spend_turn, ix_spend_thread
```

AEA-10's storage hunk provides `Key[SqliteUnitOfWorkFactory]("uow_factory")`. AEA-10 also adds (R-13), as the first two
lines inside `for name, func in originals.items():` of `tests/unit/web/test_container.py::test_every_register_stub_present`:

```python
        if "No-op until" not in (func.__doc__ or ""):
            continue  # filled by its ticket, whose own test covers the hunk
```

### 4.3 From AEA-01 (`web/container.py`, `policy/limits.py`) — on main now

```python
@dataclass(frozen=True)
class Key[T]:
    """Names one provided object, e.g. Key[LedgerService]("ledger"). Two keys are equal when their names are."""
    name: str
class Container:
    def __init__(self, *, settings: Any, limits: Limits) -> None: ...
    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None: ...  # ContainerError on duplicate / after build
    def get[T](self, key: Key[T]) -> T: ...      # lazy, memoised; ContainerError("not provided: <name>") when unknown
    def build(self) -> None: ...                 # resolves every provided factory once
def register_spend(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-26 spend: LedgerService and the spend guard (models.md §6).

    No-op until AEA-26 fills it.
    """

# meridian.policy.limits
@dataclass(frozen=True)
class TurnLimits:   deadline_s: int = 60 …
@dataclass(frozen=True)
class SpendLimits:  daily_cap_usd: float = 30.0
@dataclass(frozen=True)
class Limits:       turn: TurnLimits …; spend: SpendLimits …   # Limits(spend=SpendLimits(daily_cap_usd=0.5)) is valid
```

Module-level imports of `container.py` must stay exactly `__future__`, stdlib, `meridian.policy.limits` (+ `fastapi`
under `TYPE_CHECKING`): `tests/unit/test_import_direction.py::test_container_imports_only_policy_limits`. **Your hunk
imports inside its own function body.**

### 4.4 Container keys the hunk reads (names are binding; built by name, no import from `web/deps.py`)

| Key name | Provided by | Value |
|---|---|---|
| `"uow_factory"` | AEA-10 `register_storage` (AEA-23 names it `deps.UOW_FACTORY`) | the `SqliteUnitOfWorkFactory` (a `UnitOfWorkFactory`) |
| `"wall_clock"` | AEA-23 `register_web` (`deps.WALL_CLOCK`; `create_app`'s choice: `datetime.now(UTC)` or `ContainerOverrides.wall_clock`, D-13) | `Callable[[], datetime]` |

`Key` equality is by name, so `Key[UnitOfWorkFactory]("uow_factory") == deps.UOW_FACTORY`. Hunks never call
`deps.get_*` providers (they take a `Request`; AEA-23 plan D-P3).

### 4.5 What this ticket exports (exact; consumers AEA-20, 32, 40, 51, 53 build against it)

```python
# src/meridian/adapters/sqlite/repos_spend.py
class SpendRow(CallRecord):
    id: int | None = None
    recorded_at: dt.datetime
    thread_id: ThreadId
    turn_id: TurnId
    request_id: RequestId
    run_tag: RunTag
    run_id: str | None
    agent_version: str

class SpendRepo:
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def append(self, row: SpendRow) -> int: ...
    def total_between(self, start_utc: dt.datetime, end_utc: dt.datetime) -> float: ...
    def for_turn(self, turn_id: TurnId) -> tuple[SpendRow, ...]: ...

# src/meridian/services/ledger.py
class CallAdmission(StrEnum):
    ALLOW = "allow"
    PROBE = "probe"
    REFUSE = "refuse"

@runtime_checkable
class SpendGuard(Protocol):
    def allow_turn(self) -> bool: ...

class LedgerService:
    def __init__(self, uow: UnitOfWorkFactory, *, wall_clock: Callable[[], dt.datetime], daily_cap_usd: float,
                 probe_after_s: float = 600.0, monotonic: Callable[[], float] = time.monotonic,
                 probe_lost_after_s: float = _PROBE_LOST_AFTER_S) -> None: ...
    def record(self, call: CallRecord, ids: TurnIds) -> None: ...
    def spend_today(self) -> float: ...
    def allow_turn(self) -> bool: ...
    def trip_provider_cap(self, failure: ProviderFailure) -> None: ...
    def admit_call(self, provider: ProviderName) -> CallAdmission: ...
    def close_provider_cap(self, provider: ProviderName) -> None: ...
    def open_circuits(self) -> tuple[ProviderName, ...]: ...
    def models_disabled(self) -> bool: ...

# container key (consumers: AEA-20 gateway, AEA-32 as Key[SpendReader]("ledger"), AEA-40 as SpendGuard, AEA-51, AEA-53)
Key[LedgerService]("ledger")
```

---

## 5. Steps (build order; each step ends with a check)

Module boundaries (DO-3 §2.1, §4.4): `repos_spend.py` is a concrete SQLite repository (the only place with SQL for
`spend_ledger`); `services/ledger.py` uses it only through `tx.spend` on a unit of work and imports the `SpendRow` type
from it (`SVC --> SQL` is an allowed edge), plus `policy.limits` (DO-3 §4.4: "UoW (`repos_spend`), limits"). It never
imports `sqlite3`, `meridian.web`, `meridian.agent` or any other adapter. `web/container.py` wires the concrete objects.
No new Protocol other than the contract's `SpendGuard`; no new seam.

### Step 0 — environment and preconditions

1. `export UV_LINK_MODE=hardlink`; `uv sync` (never copy a venv; no `node_modules`).
2. Confirm the prerequisites are merged: `ls src/meridian/domain/common.py src/meridian/domain/turn.py src/meridian/ports/runtime.py src/meridian/adapters/sqlite/db.py src/meridian/adapters/sqlite/repos_spend.py src/meridian/adapters/sqlite/schema/20_spend.sql tests/fixtures/sqlite.py`. If any is missing, stop and report `blocked-on AEA-02` (domain/ports/shell) or `blocked-on AEA-10` (db, schema, fixture).
3. `grep -n "No-op until" tests/unit/web/test_container.py` must show AEA-10's guard (§4.2). If it does not, see §8 R-1.
4. `grep -n "constructor only" tests/unit/adapters/test_repo_shells.py` (if the file exists): note whether the
   "no public member" check is scoped to that docstring phrase (§8 R-2).

### Step 1 — read the merged shapes (no code)

Open `src/meridian/adapters/sqlite/db.py`, `repos_spend.py`, `schema/20_spend.sql`, `src/meridian/domain/common.py`,
`domain/turn.py`, `ports/models.py`, `ports/runtime.py`, `tests/fixtures/sqlite.py`. Confirm every name in §4. Write
down any difference (it goes in your report).

### Step 2 — `src/meridian/adapters/sqlite/repos_spend.py`

File header:

```python
"""spend_ledger repository (AEA-02 shell; body: AEA-26, stage7/models.md §6, MOD-19).

Append-only: the only write is ``append``. No update, delete or clear (the demo reset keeps spend_ledger, cases.md §1.3).
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from typing import Final

from meridian.adapters.sqlite.db import format_wall, integrity_errors, last_row_id, parse_wall
from meridian.domain.common import ProviderFailure, ProviderFailureKind, RequestId, ThreadId, TurnId
from meridian.domain.turn import RunTag
from meridian.ports.models import CallRecord

__all__ = ["SpendRepo", "SpendRow"]
```

1. **`SpendRow(CallRecord)`** with exactly the fields of §4.5, in that order, each on its own line, docstring:
   `"""One spend_ledger row: CallRecord's fields plus the row id, the wall time and the TurnIds fields (models.md §6)."""`
2. **Constants** (SQL as adjacent string literals, never `+`, `%`, `.format` or f-strings; ruff `S608`):

   ```python
   _INSERT: Final = (
       "INSERT INTO spend_ledger (recorded_at, thread_id, turn_id, request_id, run_tag, run_id, agent_version, "
       "role, provider, model, attempt, latency_ms, input_tokens, output_tokens, cache_read_tokens, "
       "cache_write_tokens, thinking_tokens, cost_usd, cost_source, status, failure_kind, http_status, "
       "provider_request_id, stop_reason) "
       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
   )
   _SELECT_FOR_TURN: Final = (
       "SELECT id, recorded_at, thread_id, turn_id, request_id, run_tag, run_id, agent_version, "
       "role, provider, model, attempt, latency_ms, input_tokens, output_tokens, cache_read_tokens, "
       "cache_write_tokens, thinking_tokens, cost_usd, cost_source, status, failure_kind, http_status, "
       "provider_request_id, stop_reason FROM spend_ledger WHERE turn_id = ? ORDER BY id"
   )
   _SUM_BETWEEN: Final = (
       "SELECT COALESCE(SUM(cost_usd), 0.0) FROM spend_ledger WHERE recorded_at >= ? AND recorded_at < ?"
   )
   _RETRYABLE_KINDS: Final = frozenset(
       {
           ProviderFailureKind.TIMEOUT,
           ProviderFailureKind.CONNECTION,
           ProviderFailureKind.RATE_LIMITED,
           ProviderFailureKind.OVERLOADED,
           ProviderFailureKind.SERVER,
       }
   )  # DO-4 §11: retryable kinds; BODY_ERROR's inner code is not stored, so it reads back False
   ```
   Count: 24 column names and 24 `?` in `_INSERT`; 25 names in `_SELECT_FOR_TURN`.
3. **`class SpendRepo`** — replace the class docstring with
   `"""spend_ledger rows (models.md §6, MOD-19). Append-only: append, total_between, for_turn; nothing else."""`
   (it must **not** contain `AEA-02 creates the constructor only`; §8 R-2). Keep `__init__` exactly.
4. **`append(self, row: SpendRow) -> int`:**
   1. `if row.id is not None: raise ValueError("append takes a row without an id")` (a row is inserted once).
   2. `failure = row.failure`. Build the 24 values in `_INSERT` order:
      `format_wall(row.recorded_at)`, `str(row.thread_id)`, `str(row.turn_id)`, `str(row.request_id)`, `row.run_tag`,
      `row.run_id`, `row.agent_version`, `row.role.value`, `row.provider`, `row.model`, `row.attempt`,
      `row.latency_ms`, `row.input_tokens`, `row.output_tokens`, `row.cache_read_tokens`, `row.cache_write_tokens`,
      `row.thinking_tokens`, `row.cost_usd`, `row.cost_source`, `row.status`,
      `failure.kind.value if failure is not None else None`,
      `failure.http_status if failure is not None else None`,
      `row.provider_request_id`, `row.stop_reason`.
   3. `with integrity_errors("spend_ledger"): cur = self._conn.execute(_INSERT, values)`.
   4. `return last_row_id(cur, "spend_ledger")`.
   - Invariant: one INSERT per call, inside the caller's unit of work; the caller commits.
5. **`total_between(self, start_utc: dt.datetime, end_utc: dt.datetime) -> float`:**
   `(value,) = self._conn.execute(_SUM_BETWEEN, (format_wall(start_utc), format_wall(end_utc))).fetchone()`; `return float(value)`.
   - Invariant: `format_wall` writes the same UTC ISO form everywhere, so TEXT comparison is time order
     (`…T05:00:00+00:00` < `…T05:00:00.000001+00:00`, because `+` sorts before `.`). Naive bounds raise `ValueError`.
6. **`for_turn(self, turn_id: TurnId) -> tuple[SpendRow, ...]`:**
   `rows = self._conn.execute(_SELECT_FOR_TURN, (str(turn_id),)).fetchall()`; `return tuple(_row_from_db(r) for r in rows)`.
7. **Module-level `_row_from_db(r: tuple[object, ...]) -> SpendRow`** (a function, not a method, so AC-11's
   public-method check sees only the three): unpack the 25 values in `_SELECT_FOR_TURN` order; then
   - `failure = None` when `failure_kind is None`; otherwise
     `ProviderFailure.model_validate({"kind": failure_kind, "provider": provider, "http_status": http_status, "retry_after_s": None, "retryable": ProviderFailureKind(str(failure_kind)) in _RETRYABLE_KINDS, "provider_request_id": provider_request_id})`.
   - `return SpendRow.model_validate({"id": id_, "recorded_at": parse_wall(str(recorded_at)), "thread_id": thread_id, "turn_id": turn_id, "request_id": request_id, "run_tag": run_tag, "run_id": run_id, "agent_version": agent_version, "role": role, "provider": provider, "model": model, "attempt": attempt, "latency_ms": latency_ms, "input_tokens": input_tokens, "output_tokens": output_tokens, "cache_read_tokens": cache_read_tokens, "cache_write_tokens": cache_write_tokens, "thinking_tokens": thinking_tokens, "cost_usd": cost_usd, "cost_source": cost_source, "status": status, "failure": failure, "provider_request_id": provider_request_id, "stop_reason": stop_reason})`.
     (Values from sqlite are plain `str` / `int` / `float`; the strict pattern IDs accept plain `str` — verified.)
8. No other method, attribute or import. Check:
   `uv run ruff check src/meridian/adapters/sqlite/repos_spend.py && uv run mypy src/meridian/adapters/sqlite/repos_spend.py`.

### Step 3 — `src/meridian/services/ledger.py`

**Hard rules for this file:** the character pair `30` must not appear anywhere (code, comments, docstrings): AC-4's
review grep. Write "the daily cap" instead of the figure. No standalone `60` either (PA-2; `600.0` is fine).

```python
"""LedgerService: record every model-call attempt's cost and stop model use at a cap (stage7/models.md §6).

Our cap (allow_turn) is checked by TurnService before a turn (MOD-11). A provider's own cap is a per-provider circuit
held in memory and released only by a successful probe (MOD-13).
"""

from __future__ import annotations

import datetime as dt
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Protocol, cast, get_args, runtime_checkable
from zoneinfo import ZoneInfo

from meridian.adapters.sqlite.repos_spend import SpendRow
from meridian.domain.common import ProviderFailure, ProviderFailureKind, ProviderName
from meridian.domain.turn import TurnIds
from meridian.policy.limits import TurnLimits
from meridian.ports.models import CallRecord
from meridian.ports.runtime import UnitOfWorkFactory

__all__ = ["CallAdmission", "LedgerService", "SpendGuard"]

_log = logging.getLogger(__name__)

_DAY_ZONE: Final = "America/Chicago"  # the spend day (UX-3 CON-19; DO-3 C-12)
_CAP_KINDS: Final = frozenset({ProviderFailureKind.PROVIDER_SPEND_CAP, ProviderFailureKind.OUR_SPEND_LIMIT})
_PROVIDERS: Final = cast(tuple[ProviderName, ...], get_args(ProviderName))  # ("anthropic", "openrouter_jev")
_PROBE_LOST_AFTER_S: Final = float(TurnLimits().deadline_s)  # a probe in flight longer than one turn is lost
```

1. **`CallAdmission(StrEnum)`** and **`SpendGuard`** exactly as §4.5 (`@runtime_checkable` on `SpendGuard`).
2. **`@dataclass class _Circuit:`** `tripped_at: float` (monotonic seconds); `probe_started: float | None = None`.
3. **`LedgerService.__init__`** (signature §4.5):
   - `if daily_cap_usd < 0: raise ValueError("daily_cap_usd must be >= 0")`;
     `if probe_after_s <= 0 or probe_lost_after_s <= 0: raise ValueError("probe intervals must be > 0")`.
   - Store `self._uow`, `self._wall_clock`, `self._cap = daily_cap_usd`, `self._probe_after_s`,
     `self._probe_lost_after_s`, `self._monotonic`.
   - `self._zone = ZoneInfo(_DAY_ZONE)` (a missing tz database fails here, at container build: PA-3).
   - `self._circuits: dict[ProviderName, _Circuit] = {}`; `self._lock = threading.Lock()`.
4. **`_now(self) -> dt.datetime`** (private): `now = self._wall_clock()`; if `now.tzinfo is None or now.utcoffset() is None`:
   `raise ValueError("wall clock returned a naive datetime")`; return `now.astimezone(dt.UTC)`.
5. **`record(self, call: CallRecord, ids: TurnIds) -> None`:**
   1. `row = SpendRow.model_validate({**call.model_dump(), **ids.model_dump(), "recorded_at": self._now()})`.
   2. `with self._uow(write=True) as tx:` then `tx.spend.append(row)` then `tx.commit()` — one short write unit of work per row.
   3. No log line, no try/except: a storage error propagates to the caller (the gateway); a missing cost row must be
      loud, never silent (DO-6 *Missing instrumentation*).
   - Invariant: rows are written whatever the cap or circuit state (the overrun of a running turn is recorded: AC-4).
6. **`_day_bounds_utc(self, now: dt.datetime) -> tuple[dt.datetime, dt.datetime]`** (private):
   `local = now.astimezone(self._zone)`;
   `start = dt.datetime.combine(local.date(), dt.time(0), tzinfo=self._zone)`;
   `end = dt.datetime.combine(local.date() + dt.timedelta(days=1), dt.time(0), tzinfo=self._zone)`;
   `return start.astimezone(dt.UTC), end.astimezone(dt.UTC)`.
   - Invariant: both bounds are local midnights converted separately, so 2026-11-01 is 25 hours (05:00Z → 06:00Z
     next day) and a spring-forward day 23 hours. Never compute `end` as `start_utc + 24 h`.
7. **`spend_today(self) -> float`:** `start, end = self._day_bounds_utc(self._now())`;
   `with self._uow() as tx: return tx.spend.total_between(start, end)` (read unit of work; no `run_tag` filter: live,
   eval and load share the cap, M-26).
8. **`allow_turn(self) -> bool`:** `return self.spend_today() < self._cap`. Reads our cap only; never looks at circuits (MOD-11).
9. **`trip_provider_cap(self, failure: ProviderFailure) -> None`:**
   1. `if failure.kind not in _CAP_KINDS: return` (every other kind is ignored, no log).
   2. Under `self._lock`: `self._circuits[failure.provider] = _Circuit(tripped_at=self._monotonic())` (opens, or
      re-opens with a new trip time and no probe in flight; a straggler cap failure while open also restarts the window).
   3. `_log.warning("provider_circuit_open provider=%s failure_kind=%s", failure.provider, failure.kind.value)`.
10. **`admit_call(self, provider: ProviderName) -> CallAdmission`** — the whole decision under `self._lock`, so two
    callers can never both get `PROBE`:
    1. `c = self._circuits.get(provider)`; `None` → return `CallAdmission.ALLOW`.
    2. `now = self._monotonic()`.
    3. `if now - c.tripped_at < self._probe_after_s: return CallAdmission.REFUSE`.
    4. `if c.probe_started is not None and now - c.probe_started <= self._probe_lost_after_s: return CallAdmission.REFUSE` (a probe is in flight).
    5. `lost = c.probe_started is not None`; `c.probe_started = now`.
    6. If `lost`: `_log.warning("provider_circuit_probe_lost provider=%s", provider)`. Then
       `_log.info("provider_circuit_probe provider=%s", provider)`; return `CallAdmission.PROBE`.
    - Invariants: at most one probe in flight per provider; a probe in flight for **more than** `probe_lost_after_s`
      is replaced by exactly one new probe; nothing here reads the wall clock, the database or our cap.
11. **`close_provider_cap(self, provider: ProviderName) -> None`:** under the lock, `removed = self._circuits.pop(provider, None)`;
    if `removed is not None`: `_log.info("provider_circuit_closed provider=%s", provider)`. Closing a closed circuit is a no-op.
12. **`open_circuits(self) -> tuple[ProviderName, ...]`:** under the lock,
    `return tuple(p for p in _PROVIDERS if p in self._circuits)` (fixed order).
13. **`models_disabled(self) -> bool`:** `return bool(self.open_circuits()) or not self.allow_turn()`.
14. Nothing else: no persistence of circuits, no reset hook, no midnight release, no 80 % warning, no trace sink, no
    `datetime.now` call (always the injected clock).

Check: `uv run ruff check src/meridian/services/ledger.py && uv run mypy src/meridian/services/ledger.py && grep -c "30" src/meridian/services/ledger.py`
(must print `0`) `&& ! grep -nE '\b60(\.0)?\b' src/meridian/services/ledger.py`.

### Step 4 — the `register_spend` hunk in `src/meridian/web/container.py`

Edit **only** this function. Keep its name and parameters. The docstring keeps the token `AEA-26` (AEA-01's test checks
it) and **loses** `No-op until AEA-26 fills it.` (AEA-10's guard then skips it in the stub test). Replace the function with:

```python
def register_spend(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-26 spend: LedgerService and the spend guard (models.md §6).

    Provides Key[LedgerService]("ledger"), the one LedgerService, built from the "uow_factory" key (AEA-10), the
    "wall_clock" key (AEA-23, create_app's choice; MC-20, D-13) and limits.spend.daily_cap_usd (MC-22). The gateway
    (AEA-20), the turn service (AEA-40, typed as SpendGuard), the alert evaluator (AEA-32), the metrics reader (AEA-53)
    and GraphDeps.ledger (AEA-51) all get it with container.get(Key[LedgerService]("ledger")).
    """
    import datetime as dt

    from meridian.ports.runtime import UnitOfWorkFactory
    from meridian.services.ledger import LedgerService

    uow_key: Key[UnitOfWorkFactory] = Key("uow_factory")  # = web.deps.UOW_FACTORY (keys are equal by name)
    wall_key: Key[Callable[[], dt.datetime]] = Key("wall_clock")  # = web.deps.WALL_CLOCK

    def build(c: Container) -> LedgerService:
        return LedgerService(
            c.get(uow_key),
            wall_clock=c.get(wall_key),
            daily_cap_usd=limits.spend.daily_cap_usd,
            probe_lost_after_s=float(limits.turn.deadline_s),
        )

    container.provide(Key[LedgerService]("ledger"), build)
```

- `Callable` is already imported at module level in `container.py` (check with `grep -n "^from collections.abc" src/meridian/web/container.py`);
  if it is not, use `from collections.abc import Callable` **inside** the function body, never at module level.
- If mypy rejects the annotated `Key("…")` form, write `Key[UnitOfWorkFactory]("uow_factory")` and
  `Key[Callable[[], dt.datetime]]("wall_clock")` inline instead. Do not add a `# type: ignore`.
- The factory is lazy: the keys are resolved at `container.build()`, after `register_storage` and `register_web` have
  provided them. `settings` and `app` are unused; leave them (AEA-01's signature).

Check: `uv run pytest tests/unit/web tests/unit/test_import_direction.py -q`.

### Step 5 — tests (§7.1), written alongside steps 2–4

Run `uv run pytest tests/services/test_ledger.py tests/unit/web/test_register_spend.py -q` until green.

### Step 6 — journey step and record (AC-14)

1. Write `tests/journeys/j9/test_aea_26.py` (§7.1). `tests/journeys/j9/__init__.py` already exists.
2. `uv run pytest -m journey tests/journeys/j9/test_aea_26.py -q` → 1 passed.
3. `uv run python -m tests.journeys.affected --base main` → it selects every journey file (a change under
   `tests/journeys/` selects all; README "Commands") and they pass.
4. Write the record (§7.4) **after** the feat commit exists (it names the SHA).

### Step 7 — context (AC-15), in the docs commit

1. `.claude/reference/area-map.md`, the **A2 Models** row's last cell (`planned` on `16ca639`): set it to
   ``partly built: `services/ledger.py`, `adapters/sqlite/repos_spend.py` (body) actual (AEA-26, `<feat sha>`); the rest planned``.
   If a sibling (AEA-17/18/20) already changed that cell, keep its text and insert your part in the same style.
2. `.claude/state/icm-progress.md`: the row named *Routes verified against code and tests* whose **last cell** is
   `Each slice adds its route; verified when every area-map row is actual`. Replace its evidence (third) cell with
   ``<run-date>: area map A2 → `services/ledger.py`, `repos_spend.py` checked against `tests/services/test_ledger.py` (AEA-26, `<feat sha>`; <N> passed)``.
   Keep the row ≤ 400 characters; change no other cell or row.
3. `docs/design/code-design.md` §3: on the line that starts `**Built:**` (directly under the §3 heading, line ~181),
   insert before the final `.`: ``; `services/ledger.py`, `adapters/sqlite/repos_spend.py` body (AEA-26, `<feat sha>`)``.
   Find it with `grep -n '^\*\*Built:\*\*' docs/design/code-design.md`. Change nothing else.
4. `git diff --name-only main...HEAD` must list only §2.1's files (no `schema/*.sql`, no `test_container.py`).

### Step 8 — commits (explicit paths; never `git add -A`; never push)

1. `git add src/meridian/adapters/sqlite/repos_spend.py src/meridian/services/ledger.py src/meridian/web/container.py tests/services/test_ledger.py tests/unit/web/test_register_spend.py tests/journeys/j9/test_aea_26.py`
   then commit `feat(spend): ledger, spend guard and provider-cap circuit (AEA-26)` with a body listing AC results.
2. `git add docs/testing/journeys/<run-date>-AEA-26.md .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md`
   then commit `docs(AEA-26): journey record and context for services/ledger.py`.
3. The last line of **every** commit message: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

## 6. Data and fixtures (synthetic only)

- **Database:** AEA-10's `temp_sqlite()` (a migrated copy of the issued scheduling DB, removed after each test). Wrap it
  per test module:
  ```python
  @pytest.fixture
  def store() -> Iterator[TempStore]:
      with temp_sqlite() as s:
          yield s
  ```
  Raw reads in tests use `sqlite3.connect(store.db_path)` (close it in `finally`), never the repository.
- **Clocks** (define in each test file that needs them; no shared helper module):
  ```python
  class FakeWall:
      def __init__(self, now: dt.datetime) -> None:
          self.now = now
      def __call__(self) -> dt.datetime:
          return self.now
  class FakeMono:
      def __init__(self, t: float = 1000.0) -> None:
          self.t = t
      def __call__(self) -> float:
          return self.t
  CHI = ZoneInfo("America/Chicago")
  def chi(y: int, mo: int, d: int, h: int = 0, mi: int = 0, s: int = 0) -> dt.datetime:
      return dt.datetime(y, mo, d, h, mi, s, tzinfo=CHI)
  ```
  The fake wall clock may return a Chicago-aware time; the ledger converts to UTC.
- **IDs:** `TurnIds.model_validate({"thread_id": str(uuid.uuid4()), "turn_id": str(uuid.uuid4()), "request_id": str(uuid.uuid4()), "run_tag": tag, "run_id": None, "agent_version": "test-agent-0"})`.
- **Calls:** one builder (copy it, with the clock helpers, into each test file that needs it; no shared helper module):
  ```python
  RETRYABLE = {ProviderFailureKind.TIMEOUT, ProviderFailureKind.CONNECTION, ProviderFailureKind.RATE_LIMITED,
               ProviderFailureKind.OVERLOADED, ProviderFailureKind.SERVER}
  def make_failure(kind: ProviderFailureKind, provider: str = "anthropic", http_status: int | None = 429) -> ProviderFailure:
      return ProviderFailure.model_validate({"kind": kind, "provider": provider, "http_status": http_status,
          "retry_after_s": None, "retryable": kind in RETRYABLE, "provider_request_id": "req_test_0001"})
  def make_call(*, cost: float, provider: str = "anthropic", role: Role = Role.RESPONDER, attempt: int = 1,
                failure: ProviderFailure | None = None) -> CallRecord:
      return CallRecord.model_validate({
          "provider": provider, "model": "claude-sonnet-test" if provider == "anthropic" else "test/jev-model",
          "latency_ms": 1200, "input_tokens": 9000, "output_tokens": 700, "cache_read_tokens": 0,
          "cache_write_tokens": 0, "thinking_tokens": 0, "cost_usd": cost, "cost_source": "price_table",
          "status": "ok" if failure is None else "error", "failure": failure,
          "provider_request_id": "req_test_0001", "stop_reason": "end_turn" if failure is None else None,
          "role": role, "attempt": attempt})
  ```
  If AEA-02's merged models carry a cross-field validator that rejects one of these combinations, change only the
  helper values to satisfy it and say so in your report.
- **Costs** use exact binary fractions where a sum is compared exactly (0.25, 0.5, 1.0, 2.0 …); the ticket's figures
  ($29.98, $0.039) are compared with `pytest.approx` or by `<` / `>=` against the cap.
- **AC-12 seeds**, built at run time so no scanner sees a key prefix in the source:
  `SEED_KEY = "-".join(["sk", "ant", "api03", "SEEDONLY", "Z" * 24])`;
  `SEED_SENTENCE = "My furnace at 4417 Pecan Hollow smells like gas, call me back"`. No phone number, code or card.

---

## 7. Checks

### 7.1 Tests you write with the code (names are binding)

**`tests/services/test_ledger.py`** — every test builds `LedgerService(store.uow, wall_clock=wall, daily_cap_usd=…, monotonic=mono)` over the `store` fixture.

| Test | Steps and assertions |
|---|---|
| `test_record_one_row_per_attempt_including_failures` (AC-1) | wall = `chi(2026,10,21,14,0,0)`. Record `ok = make_call(cost=0.25, attempt=1)` and `err = make_call(cost=0.0, attempt=2, failure=make_failure(ProviderFailureKind.PROVIDER_SPEND_CAP))` with the same `ids`. Raw: `SELECT COUNT(*)` == 2; `{r[1] for r in conn.execute("PRAGMA table_info(spend_ledger)")}` == the 25 models §6 names (`id`, `recorded_at`, `thread_id`, `turn_id`, `request_id`, `run_tag`, `run_id`, `agent_version`, `role`, `provider`, `model`, `attempt`, `latency_ms`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `thinking_tokens`, `cost_usd`, `cost_source`, `status`, `failure_kind`, `http_status`, `provider_request_id`, `stop_reason`); raw `recorded_at` of both == `"2026-10-21T19:00:00+00:00"`; raw `failure_kind`, `http_status` of the ok row are `None`. Through `with store.uow() as tx: rows = tx.spend.for_turn(ids.turn_id)`: 2 rows, ids ascending; for each, `CallRecord.model_validate({k: getattr(row, k) for k in CallRecord.model_fields})` equals the input record; `rows[1].failure.kind is ProviderFailureKind.PROVIDER_SPEND_CAP` and `.http_status == 429`; `rows[0].failure is None`; each TurnIds field equals `ids`'s. Print the column list. |
| `test_spend_today_is_the_chicago_day` (AC-2) | Record one row each (set `wall.now` before each `record`): `chi(2026,10,20,23,59,59)` 1.0 live; `chi(2026,10,21,0,0,0)` 2.0 eval; `chi(2026,10,21,18,59,59)` 4.0 load; `chi(2026,10,21,19,0,0)` (= UTC midnight) 8.0 live; `chi(2026,10,21,23,59,59)` 16.0 eval; `chi(2026,10,22,0,0,0)` 32.0 live. Then `wall.now = chi(2026,10,21,12)` → `spend_today() == 30.0`; `chi(2026,10,20,12)` → `1.0`; `chi(2026,10,22,12)` → `32.0`. Exact equality (binary fractions). |
| `test_spend_day_across_dst_end` (AC-3) | UTC instants (`dt.datetime(..., tzinfo=dt.UTC)`): 2026-11-01 04:59:59 → 1.0; 05:00:00 → 2.0; 06:30:00 (01:30 CDT) → 4.0; 07:30:00 (01:30 CST) → 8.0; 2026-11-02 05:30:00 (Nov 1 23:30 CST) → 16.0; 2026-11-02 06:00:00 → 32.0. Query at 2026-11-01 18:00Z → 30.0; at 2026-11-02 05:59:59Z → 30.0; at 2026-11-02 06:00:00Z → 32.0; at 2026-11-01 04:00Z → 1.0. |
| `test_allow_turn_at_cap_and_overrun_recorded` (AC-4) | cap = `Limits().spend.daily_cap_usd` (read, not typed). Record 29.98 → `allow_turn() is True`. Record 0.039 → raw row count 2, `spend_today() == pytest.approx(30.019)`, `allow_turn() is False`; record one more 0.01 → it is written (count 3). Second ledger over a fresh `temp_sqlite()` with `daily_cap_usd=5.0`: record 2.5 and 2.0 → `True`; record 0.5 (sum 5.0) → `False`. |
| `test_allow_turn_releases_at_chicago_midnight` (AC-5) | cap 1.0; wall `chi(2026,10,21,9)`; record 1.0. `wall.now = chi(2026,10,21,23,59)` → `False`; `wall.now = chi(2026,10,22,0,0)` → `True`; rows unchanged (count 1). |
| `test_provider_circuit_probe_cycle` (AC-6) | `mono = FakeMono(1000.0)`. `trip_provider_cap(make_failure(PROVIDER_SPEND_CAP))`. `mono.t = 1540` → `REFUSE`; `1600` → `PROBE`; same time, second call → `REFUSE`; `close_provider_cap("anthropic")` → `ALLOW`, `open_circuits() == ()`. Trip again at `mono.t = 2000`; `2600` → `PROBE`; at `2605` `trip_provider_cap(...)` (probe met the cap) → at `3204` `REFUSE`, at `3205` `PROBE`; at `3265` (60 s in flight) → `REFUSE`; at `3266` → `PROBE` (lost probe replaced); same time second caller → `REFUSE`. Assert each step in order (a list of `(t, expected)` pairs is fine). |
| `test_trip_by_kind_and_per_provider` (AC-7) | `@pytest.mark.parametrize("kind", list(ProviderFailureKind), ids=lambda k: k.value)`. Fresh ledger. `trip_provider_cap(make_failure(kind, "anthropic"))`. If `kind in {PROVIDER_SPEND_CAP, OUR_SPEND_LIMIT}`: `admit_call("anthropic") is CallAdmission.REFUSE`, `open_circuits() == ("anthropic",)`; else `ALLOW` and `()`. Always `admit_call("openrouter_jev") is CallAdmission.ALLOW`. Also assert `len(list(ProviderFailureKind)) == 14`. |
| `test_circuit_not_released_by_midnight_and_not_persisted` (AC-8) | wall `chi(2026,10,21,23,55)`, mono 1000. `ids`; `f = make_failure(PROVIDER_SPEND_CAP)`; record `make_call(cost=0.0, failure=f)`, then `trip_provider_cap(f)`. `wall.now = chi(2026,10,22,0,0,1)`, `mono.t = 1360` → `admit_call("anthropic") is REFUSE`, `allow_turn() is True`. New `LedgerService` over the same `store.uow` → `open_circuits() == ()`, `admit_call("anthropic") is ALLOW`; `for_turn(ids.turn_id)` has 1 row whose `failure.kind is PROVIDER_SPEND_CAP`. |
| `test_models_disabled_either_cause` (AC-9) | Four cases over the same store, cap 1.0, a **new** ledger instance per case (circuits are per instance): (below cap, closed) → `models_disabled() is False`, `allow_turn() is True`; (below cap, Anthropic tripped) → `True`, `allow_turn() is True`; record 1.0, then (at cap, closed) → `True`, `allow_turn() is False`; (at cap, tripped) → `True`. |
| `test_concurrent_records_all_written` (AC-10) | One `ids`; `barrier = threading.Barrier(20)`; 20 workers in `ThreadPoolExecutor(max_workers=20)`, worker `i` waits on the barrier then records `make_call(cost=0.25 * (i + 1))`; call `.result()` on every future. `for_turn` has 20 rows; `spend_today() == 52.5`. |
| `test_spend_repo_append_only_and_spend_guard` (AC-11) | `{n for n, _ in inspect.getmembers(SpendRepo, inspect.isfunction) if not n.startswith("_")} == {"append", "total_between", "for_turn"}`; `isinstance(ledger, SpendGuard)`; `not isinstance(object(), SpendGuard)`. |
| `test_rows_and_logs_hold_allow_listed_fields_only` (AC-12) | `caplog.set_level(logging.DEBUG)`. Inside `try: raise RuntimeError(f"{SEED_KEY} {SEED_SENTENCE}")` / `except RuntimeError:` record an error call (`make_failure(PROVIDER_SPEND_CAP)`) and call `trip_provider_cap`, then (after setting `mono.t` past 600 s) `admit_call`, `close_provider_cap`. Raw `"\n".join(repr(r) for r in conn.execute("SELECT * FROM spend_ledger"))` contains neither seed; `caplog.text` contains `provider_circuit_open` (proves capture) and neither seed. Trace: `set(inspect.signature(LedgerService.__init__).parameters) == {"self", "uow", "wall_clock", "daily_cap_usd", "probe_after_s", "monotonic", "probe_lost_after_s"}` (the ledger takes no trace sink, so nothing can reach one). Print the log lines. |
| `test_rows_queryable_by_turn_and_thread` (AC-13) | Thread X, run_tag `eval`: turn A records attempt 1 (error `RATE_LIMITED`, 0.25) and attempt 2 (ok, 0.5); thread Y, run_tag `live`: turn B records 1.0. `for_turn(A)` → `[r.attempt for r in rows] == [1, 2]`; `for_turn(B)` → 1 row. Raw `SELECT thread_id, run_tag, SUM(cost_usd), COUNT(*) FROM spend_ledger GROUP BY thread_id, run_tag` → `{(X, "eval"): (0.75, 2), (Y, "live"): (1.0, 1)}`. |
| `test_example_pair_cap_overrun_midnight_and_probe` (example pair) | cap from `Limits()`; wall `chi(2026,10,21,14,0)`, mono 0. Record 29.98 (earlier turn) → `allow_turn()` `True`; the running turn records 0.039 as three attempts of 0.013 (planner, specialist, responder roles) → rows written; `allow_turn()` `False`; `wall.now = chi(2026,10,22,0,0)` → `True`. Then the Anthropic cap at 14:00: `trip_provider_cap(make_failure(PROVIDER_SPEND_CAP, http_status=429))` at `mono.t = 0`; `mono.t = 599` → `REFUSE`; `600` → `PROBE`; `close_provider_cap("anthropic")` → `ALLOW`. |
| `test_naive_wall_clock_rejected` (PA-3) | `wall = FakeWall(dt.datetime(2026, 10, 21, 14, 0))` (naive): `pytest.raises(ValueError)` on `spend_today()` and on `record(...)`; raw row count 0. |

**`tests/unit/web/test_register_spend.py`** (PA-1)

- `test_register_spend_provides_one_ledger_from_limits_and_wall_clock`:
  1. `with temp_sqlite() as store:`; `fake = FakeWall(chi(2026, 10, 21, 14, 0))`.
  2. `limits = Limits(spend=SpendLimits(daily_cap_usd=0.5))`;
     `c = Container(settings=SimpleNamespace(name="stand-in"), limits=limits)`;
     `c.provide(Key[object]("uow_factory"), lambda _c: store.uow)`;
     `c.provide(Key[object]("wall_clock"), lambda _c: fake)`;
     `register_spend(c, FastAPI(), settings=c.settings, limits=limits)`; `c.build()`.
  3. `ledger = c.get(Key[LedgerService]("ledger"))`; `ledger is c.get(Key[LedgerService]("ledger"))`;
     `isinstance(ledger, LedgerService)` and `isinstance(ledger, SpendGuard)`.
  4. `ledger.allow_turn() is True`; record `make_call(cost=0.5)` with a fresh `TurnIds` → `allow_turn() is False` (the
     cap came from `limits`, not the default); the raw `recorded_at` == `"2026-10-21T19:00:00+00:00"` (the wall clock
     came from the `"wall_clock"` key).
  5. `"AEA-26" in (register_spend.__doc__ or "")` and `"No-op until" not in (register_spend.__doc__ or "")`.
  6. `c.close()` at the end (in `finally`).

**`tests/journeys/j9/test_aea_26.py`** (AC-14; `pytestmark = pytest.mark.journey`)

Module docstring: "J-9 (proposed extension, slice plan §0a): a turn while the spend cap is reached. Level today:
mock-tested (real LedgerService on a temp SQLite copy; no server, no TurnService). The integrated steps (the
SPEND_CAP_REACHED notice with the person action; the turn row degraded_handoff / spend_cap; no spend_ledger row of its
own) are blocked by AEA-57 (harness) and AEA-51 (integrated turn, which wires AEA-40's TurnService)."

- `test_j9_spend_cap_guard_refuses_and_writes_nothing`: temp store; wall `chi(2026,10,21,14,0)`; ledger with cap
  `Limits().spend.daily_cap_usd`; `guard: SpendGuard = ledger`. Record 29.98 → `guard.allow_turn()` `True`; record the
  0.039 overrun → `False`; `ledger.models_disabled()` `True`. Take the raw row count; build a **new** `TurnIds`; call
  `guard.allow_turn()` and `ledger.models_disabled()` again; raw row count unchanged and
  `for_turn(new_ids.turn_id) == ()`. Move `wall.now` to `chi(2026,10,22,0,0)` → `guard.allow_turn()` `True`. Define the
  small helpers locally (do not import from `tests/services/`).

### 7.2 Existing tests that must stay green

`tests/unit/web/test_container.py` (all; with AEA-10's guard the filled hunk is skipped in the stub loop, §8 R-1),
`tests/unit/test_import_direction.py`, AEA-10's `tests/unit/adapters/` (including `sqlite/`: they build
`SqliteUnitOfWork`, which constructs `SpendRepo`) and `tests/unit/web/test_register_storage.py`, AEA-02's
`tests/unit/ports/`, `tests/unit/domain/` (untouched modules; run only if the affected grep below lists them).

### 7.3 Gates (cheapest first; stop at the first red)

Affected set: `grep -rl "repos_spend\|services.ledger\|services import ledger\|web.container\|web import container\|SpendRepo\|LedgerService" tests/`
plus the mirrors of the changed packages (`tests/services/`, `tests/unit/web/`, `tests/unit/adapters/`).

| # | Gate | Command | Passing looks like |
|---|---|---|---|
| 1 | Lint | `uv run ruff check src/meridian/adapters/sqlite/repos_spend.py src/meridian/services/ledger.py src/meridian/web/container.py tests/services/test_ledger.py tests/unit/web/test_register_spend.py tests/journeys/j9/test_aea_26.py` | `All checks passed!` |
| 2 | Format | `uv run ruff format --check <same six paths>` | `6 files already formatted` (run `uv run ruff format <paths>` first if not) |
| 3 | Type check | `uv run mypy` | `Success: no issues found` |
| 4 | Literals | `grep -c "30" src/meridian/services/ledger.py` and `grep -nE '\b60(\.0)?\b' src/meridian/services/ledger.py` | `0`, and no output |
| 5 | Affected tests | `uv run pytest tests/services/test_ledger.py tests/unit/web tests/unit/test_import_direction.py tests/unit/adapters -q` plus any other file the affected grep lists (add `--with pytest-xdist … -n 2` only if slow; never more than `-n 2`) | all passed; 0 failed |
| 6 | Affected journeys | `uv run python -m tests.journeys.affected --base main` | selects `tests/journeys/j9/test_aea_26.py` (and any other journey files present); all pass |
| 7 | Diff scope | `git diff --name-only main...HEAD` | only §2.1 files |

Full suite: **not** required (no shared fixture, settings, dependency or lock change; `container.py` changes in one
hunk). Iterate with `tests/services/test_ledger.py` only; run all gates once before the final commit and paste the
results in your report.

### 7.4 Journey record — `docs/testing/journeys/<run-date>-AEA-26.md`

```markdown
# Journey record: AEA-26 spend ledger and spend guard

| Field | Value |
|---|---|
| Claim | AEA-26 `services/ledger.py`, `adapters/sqlite/repos_spend.py`: rows per attempt, the Chicago spend day, our cap (`allow_turn`), the provider circuit (AC-1…AC-13); J-9 step at mock level: with the cap reached the `SpendGuard` refuses and the ledger writes nothing for the refused turn |
| Level | `mock-tested` |
| Tested revision | `<feat sha>` |
| Environment | VPS, Python 3.12, `uv`; temp SQLite copy from `tests/fixtures/sqlite.py`; no server; no model adapter |
| Command | `uv run pytest tests/services/test_ledger.py tests/unit/web/test_register_spend.py -q`; `uv run pytest -m journey tests/journeys/j9/test_aea_26.py -q`; `uv run python -m tests.journeys.affected --base main` |
| Result | <N> passed; journey 1 passed; affected: <output summary> |
| Evidence location | GitLab issue #26 comment; this file |
| Remaining limitations | No CON-2 turn driven: the `SPEND_CAP_REACHED` notice, the person action and the `turn` row (`degraded_handoff` / `spend_cap`) are AEA-40's and are not exercised; circuit wiring with the real gateway is AEA-51's; the deploy image's time-zone database is unchecked (plan §8 R-5) |
| Blocked by | AEA-57 (journey harness) and AEA-51 (integrated turn, wiring AEA-40) |
| Journeys that will exercise this code | J-9 (spend cap reached, at `integrated with a scripted model`); J-1 and every turn journey record spend rows once AEA-51 lands |
```

---

## 8. Risks and requests

| ID | Risk / request | What to do |
|---|---|---|
| R-1 | `tests/unit/web/test_container.py::test_every_register_stub_present` (AEA-01's file) asserts every `register_*` is a no-op (`assert not fresh._factories`); a filled `register_spend` fails it. AEA-10 (this ticket's blocker) adds a guard that skips hunks whose docstring lacks `No-op until` (§4.2). | Satisfy the guard from your own hunk (docstring keeps `AEA-26`, drops `No-op until`). If the guard is **not** on `main` when you start, **stop**: do not edit `test_container.py`; report "request: AEA-10 R-13 guard missing on main". |
| R-2 | AEA-02's shell test (`tests/unit/adapters/test_repo_shells.py`) may assert each shell has no public member. AEA-10's R-2 scopes that check to classes whose docstring still says `AEA-02 creates the constructor only`. | Your new `SpendRepo` docstring drops that phrase (step 2.3). If the merged test is not scoped that way and fails only because `SpendRepo` has its three methods, stop and report "request: scope the shell check (AEA-10 R-2)". Do not edit it. |
| R-3 | Optional kwargs `monotonic`, `probe_lost_after_s` (PA-2) extend models §6's constructor. | Engineering refinement, backward compatible; not a signed-contract change (the contract's four parameters keep their names, order and defaults). **Request to the orchestrator:** one pointer sentence in `stage7/models.md` §6 at the next docs pass (not this ticket's file). |
| R-4 | Container key names: reads `"uow_factory"` (AEA-10) and `"wall_clock"` (AEA-23); provides `"ledger"`. AEA-32's plan reads `Key[SpendReader]("ledger")`; AEA-20/21/34/40/51/53 must use the same name. | The key is in the hunk docstring. **Request to the orchestrator:** confirm the name with AEA-20, 40, 51, 53 planners. |
| R-5 | `zoneinfo` needs the IANA database. The VPS has `/usr/share/zoneinfo`; the Railway image (AEA-50) is unverified and `tzdata` is not a dependency. | Construction fails loudly (PA-3), not mid-turn. **Request to the integrator:** add `tzdata` to `pyproject.toml` via an AEA-01 follow-up, or have AEA-50 confirm `/usr/share/zoneinfo/America/Chicago` in the image. Not a blocker. |
| R-6 | DO-6 *Storage* mentions a 90-day bound for spend rows; nothing here prunes, and AC-11 forbids a delete method on `SpendRepo`. | Out of scope; noted for the orchestrator (a pruning job needs its own ticket and a reviewed exception to append-only). |
| R-7 | Shared context files: AEA-17, 18, 20, 26 edit the same A2 area-map cell; every slice edits the same ICM row and the DO-3 `**Built:**` line. | Expect textual merge conflicts on those lines; the merge agent keeps every ticket's annotation. |
| R-8 | `record` propagates storage errors to the gateway. AEA-20 decides whether a failed ledger write ends the call; this ticket does not swallow it. | Note for AEA-51's seam check across 20/26. |
| R-9 | AEA-02 / AEA-10 drift: this plan copies AEA-02's **branch** and AEA-10's **plan**. | Merged code wins for names; if a shape differs (e.g. `TempStore.uow` named differently, `last_row_id` absent), use the merged one and report it. If `SpendRepo`'s constructor differs from `(conn)`, stop and report. |
| R-10 | `retryable` and `retry_after_s` are not columns; they are rebuilt (kind-derived / `None`) on read. A `BODY_ERROR` whose inner code was retryable reads back `retryable=False`. | Acceptable: the gateway decides retries from the live failure, never from ledger rows; M-24 uses `attempt`, `failure_kind`, `http_status`. Documented in `_RETRYABLE_KINDS`'s comment. |
| R-11 | When the app is built without a web shell (a bare `FastAPI()`), `register_web` provides no `"wall_clock"` and building the ledger would fail with `ContainerError("not provided: wall_clock")`. | Expected: only `create_app` builds the real container, and it always has the web shell; AEA-01's container tests spy every hunk. No fallback clock in the hunk (it would bypass D-13). |

**What you must not do:** edit any file outside §2.1; touch `schema/*.sql`, `db.py`, `repos_core.py`, `ports/*`,
`domain/*`, `policy/limits.py`, `config.py`, another `register_*` hunk, `test_container.py`, `test_repo_shells.py`,
`tests/journeys/support/`, `tests/fakes/`, `pyproject.toml`, `uv.lock`; import `meridian.web.deps` in the hunk or call a
`deps.get_*` provider; add a method to `SpendRepo` beyond the three; persist circuit state; release a circuit on
midnight or reset; check circuits inside `allow_turn`; read `datetime.now` inside `services/ledger.py` (always the
injected clock); write `30` (or a standalone `60`) in `ledger.py`; log `exc_info`, a message text, a prompt, an output
or a customer sentence; call a paid model; bind ports 4019 or 5184; `git add -A`; push; force-push.

---

## 9. Readiness

**READY**, with two merge prerequisites (earlier waves; neither is a decision):

- **AEA-02** — `CallRecord`, `ProviderFailure`, `ProviderFailureKind`, `ProviderName`, `Role`, `TurnIds`, `RunTag`, ID
  types, `UnitOfWorkFactory`, and the `repos_spend.py` shell (imported by both owned modules). In progress on its branch.
- **AEA-10** — `db.py` (`format_wall`, `parse_wall`, `integrity_errors`, `last_row_id`, `SqliteUnitOfWorkFactory`),
  `20_spend.sql`, `temp_sqlite()`, the `"uow_factory"` key, and the `test_container.py` guard.

Not a prerequisite any more: AEA-23 (the hunk reads the `"wall_clock"` key by name; nothing is imported from
`web/deps.py`). Siblings called only by injection and not waited for: AEA-20 (gateway), AEA-32, AEA-40, AEA-51, AEA-53.
No signed contract changes; no decision D-4…D-15 is answered differently (D-13's wall-clock override reaches the ledger
through the `"wall_clock"` key that `create_app`'s binding feeds).

## Gates

None (no human, paid or live gate).
