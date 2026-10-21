# Signatures and types added at Stage 7 (2026-10-21), cases

**Topic:** cases (AEA-10, 13, 14, 28, 29, 30, 31, 32, 52, 53). **Status:** Stage 7b resolution, planned, nothing built.
**Decisions behind each entry:** `docs/plans/7b-decisions/cases.md` (IDs `CAS-n`). **Style:** the sketch style of
[internal-components.md](../internal-components.md) (DO-4): field names, types and validators are the agreement; bodies
are not. A builder may add a private helper, never a field another ticket reads, without changing this file first.

**Labels.** `[Decided §7, engineering]`: an interface, name, home or internal type decided at Stage 7 (system-design-
questioning rule 3). `[A]`: an engineering default a measurement replaces (the measurement is named). `[Source: …]`: a
source settles it. **Consumers** names the tickets that call or read the entry.

**What changes in DO-4.** Five DO-4 sketches are revised here, because the sources DO-4 cites, or a finished sibling
topic, disagree with them: `ResetService`'s constructor (two callables, CAS-1, CAS-2; web's `ResetGate`, CAS-3),
`SchedulerJob`'s constructor (CAS-29), `HandoffService`'s constructor (staff guidance, CAS-33),
`CaseService.convert_live_queued` (CAS-18) and the rule-4/6/7 rows of the escalation table (CAS-12, CAS-13, CAS-15).
Every other DO-4 signature stands as written.

**Finished sibling topics this file follows (read, not edited):** [staff.md](staff.md) (STF: `StaffRole`, `StaffActor`,
`DemoRole`, `STAFF_PERSONAS`, `ASSIGNEE_ROLES` in `domain/staff.py` (AEA-02, merge MC-2), the `staff_sessions` and
`flags` columns, what a reset does to staff state, the CON-21 start rule), [web.md](web.md) (WEB: `ResetGate`,
`ResetAlreadyRunning`, event-id rule, the `MetricsReads` Protocol, `get_wall_clock`), [models.md](models.md) (MOD:
`LedgerService`, `spend_ledger`, `SpendLimits.daily_cap_usd`, the trace `on_alert` hook), [data.md](data.md) (DAT: eval report files and their
start-up loader, `StaffGuidance`, no `ingest_runs` table), and the graph addenda [graph-core.md](graph-core.md),
[graph-tools.md](graph-tools.md), [graph-nodes.md](graph-nodes.md) (the `repos_core` methods and tables they ask
AEA-10 for, §1.1–§1.2; escalation rule 6, §3.4). Merge clashes applied here: `docs/plans/7b-decisions/merge-clashes.md`
MC-2, 3, 5, 6, 8, 9, 11, 12, 15, 19, 20, 22, 26.

---

## 1. Storage (AEA-10): schema facts, repository methods, reset callables

### 1.0 Module: adapters/sqlite/db.py — connections, the unit of work, the one wall-time formatter (CAS-35)

**What it does.** Every service opens a unit of work, reads and writes through its repositories, and calls `commit()`.
`SqliteUnitOfWork` is that object for `meridian.sqlite`: one connection, one transaction, all seven repositories built
over the same connection, so a booking, its `actions` row and its `lookup_log` row commit or roll back together (DO-1 §9).

```python
# adapters/sqlite/db.py (AEA-10; frozen after wave 0, code-design RB-1)      [Decided §7, engineering] CAS-35
def connect(path: Path, *, read_only: bool = False) -> sqlite3.Connection: ...
    # journal_mode=WAL, busy_timeout=5000 ms [A, DO-3 §4 adapters/sqlite], foreign_keys=ON, isolation_level=None
    # (transactions are explicit BEGIN statements), check_same_thread=False (a unit of work may finish on a worker
    # thread; it is never shared between two at once). read_only opens `file:…?mode=ro`.
def format_wall(dt: datetime) -> str: ...
    # The ONE wall-time formatter (MC-20): tz-aware in, UTC ISO-8601 with "+00:00" out. A naive datetime → ValueError.
def parse_wall(text: str) -> datetime: ...            # the inverse; always tz-aware UTC

class SqliteUnitOfWork:                               # implements UnitOfWork (DO-4 §13)
    core: CoreRepos; spend: SpendRepo; identity: IdentityRepos; booking: BookingRepos
    cases: CaseRepos; staff: StaffRepos; ops: OpsRepos
    def __init__(self, conn: sqlite3.Connection) -> None: ...
        # Builds all seven repositories as Repo(conn): every repository class has exactly this constructor
        # (`def __init__(self, conn: sqlite3.Connection) -> None`), so AEA-02's shells and the owners' bodies agree.
    def commit(self) -> None: ...                     # COMMIT; a second call is a no-op

class SqliteUnitOfWorkFactory:                        # implements UnitOfWorkFactory (DO-4 §13); built once by the container
    def __init__(self, db_path: Path) -> None: ...
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> ContextManager[SqliteUnitOfWork]: ...
        # A new connection per unit of work, closed on exit. write=False → BEGIN DEFERRED and PRAGMA query_only=ON;
        # write=True → BEGIN IMMEDIATE (the single writer, so a lock wait happens at the start, never mid-transaction);
        # exclusive=True → BEGIN EXCLUSIVE (the reset, §7). On exit: ROLLBACK unless commit() was called; an exception
        # always rolls back and propagates.
```
Consumers: every service ticket (through `UnitOfWorkFactory`), AEA-02 (repository shells use the constructor above),
AEA-26, 27, 28, 32, 44 (repository bodies), AEA-51 (container builds the factory).

### 1.1 Tables and columns other tickets rely on (AEA-10 writes every `schema/*.sql`, slice plan §0)

```sql
-- 00_core.sql
conversations(… , run_tag TEXT CHECK (run_tag IN ('live','eval','load','seed')),   -- 'seed' only for seed threads (CAS-24);
              outcome TEXT CHECK (outcome IN ('ai_resolved','handed_off','safety_reply','abandoned','open')),
              last_customer_wall_at TEXT,            -- wall-clock time of the last customer message (CAS-29); written by the turn path
              controller TEXT, live_state TEXT NOT NULL DEFAULT 'not_live'
                CHECK (live_state IN ('not_live','queued','joined','handed_back','closed')),
              live_since TEXT NULL)                  -- [Source: staff.md CAS assumptions]; HandoffService sets 'queued',
                                                     -- convert_live_queued sets 'not_live'; AEA-46 sets the rest
ended_threads(thread_id TEXT PRIMARY KEY, demo_session TEXT, ended_wall_at TEXT, reason TEXT, reset_id TEXT)
                                                     -- tombstones: survive a reset so a later call answers SESSION_ENDED (CAS-32)
events(id INTEGER PRIMARY KEY AUTOINCREMENT, stream TEXT, …)   -- AUTOINCREMENT: ids never reused after a reset clears rows,
                                                     -- so Last-Event-ID replay never skips the demo_reset event (CAS-1)
lookup_log(id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL, turn_id TEXT NOT NULL,
           message_id INTEGER NOT NULL REFERENCES messages(id),   -- every row names a message (CAS-38)
           tool TEXT NOT NULL, record_ids TEXT NOT NULL, passage_ids TEXT NOT NULL,   -- JSON arrays of strings
           result_seen TEXT NOT NULL)                -- = LookupEntry (DO-4 §5) + id + thread_id; read back as LookupRow (§1.2)
-- 60_cases.sql
cases(… , due_at TEXT NULL,                          -- the CASE due: window start for fee_bearing_change, else the promise due (CAS-10)
          seed INTEGER NOT NULL DEFAULT 0, …)
promises(… , due_at TEXT NULL, status TEXT CHECK (status IN ('open','kept','missed','changed')), …)  -- the CUSTOMER promise due
demo_state(id INTEGER PRIMARY KEY CHECK (id = 1), demo_now TEXT, staffing TEXT)   -- one row; DEMO_START below
demo_events(demo_event_id TEXT PRIMARY KEY, at_wall TEXT, kind TEXT CHECK (kind IN ('clock_advanced','staffing_changed')),
            step TEXT NULL, mode TEXT NULL, demo_before TEXT, demo_after TEXT,
            became_overdue INTEGER NULL, converted_cases INTEGER NULL, request_id TEXT, role TEXT)        -- CAS-5
job_runs(job_run_id TEXT PRIMARY KEY, started_wall_at, finished_wall_at, demo_now, status, error_kind, counts_json)
reset_events(reset_id, at_wall, asked_by_role TEXT NULL, asked_by_session TEXT NULL, request_id, restored_json,
             open_chats_ended, roles_reset, checkpoints_cleared INTEGER)
             -- asked_by_role / asked_by_session: the DemoRole and LoginSessionId of the CON-9 caller; both NULL when the
             -- operator script reset a stopped service (§7, merge MC-9, MC-19). checkpoints_cleared: §7's residual window.
seed_events(seed_event_id, at_wall, reset_id NULL, deploy_id NULL, seed_count, label DEFAULT 'demo seed')
check_events(id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT, at TEXT, … every CheckEvent field …)
                                                     -- 00_core.sql; fields of stage7/graph-nodes.md §1 (its cross-topic 3)
turns(turn_id TEXT PRIMARY KEY, … the TurnIds fields and received_at from core.turns.begin …,
      … every TurnRecord field of stage7/graph-core.md §2, TurnTrace's fields as columns …, response TEXT)
                                                     -- 00_core.sql; GRC-21. trace_export is what §8's evaluator reads
-- 40_identity.sql: identity_threads, identity_codes, demo_inbox exactly as stage7/graph-tools.md §5 lists them (its C-4)
-- 90_staff.sql: staff_sessions and flags exactly as staff.md §3 lists them (role_reset_pending INTEGER 0/1;
--               flags.id AUTOINCREMENT) (merge MC-11)
-- 20_spend.sql: spend_ledger exactly as models.md §6 lists it (the system design's "model_calls" is this table)
-- 95_ops.sql
health_events(id INTEGER PRIMARY KEY AUTOINCREMENT, at_wall TEXT, kind TEXT, alert_type TEXT NULL, reason_code TEXT NULL,
              value REAL NULL, threshold REAL NULL, agent_version TEXT)                               -- §8 HealthEvent
deploy_records(deploy_id TEXT PRIMARY KEY, at_wall TEXT, agent_version TEXT, …)                     -- DO-6 *Records*
eval_runs(run_id TEXT PRIMARY KEY, … every EvalRunRecord field of data.md §6 …, summary_json TEXT, loaded_at TEXT)
eval_case_results(run_id TEXT, case_id TEXT, repeat INTEGER, … EvalCaseResult fields (items as JSON) …,
                  PRIMARY KEY (run_id, case_id, repeat))                                             -- CAS-27
-- No ingest_runs table (data DAT-12). No experiments table: an experiment is eval_runs.experiment_id ("XP-n", data §6).
```

No table a reset keeps (§1.3) carries a `FOREIGN KEY` to a table a reset clears.

**Wall-time storage (merge MC-20).** Every wall-time TEXT column (`recorded_at`, `*_real`, `*_wall*`, `at_wall`) holds
UTC ISO-8601 with `+00:00`, written by one formatter in `adapters/sqlite/db.py`. Chicago is applied only for display,
day bounds and quiet hours (`zoneinfo`). The one wall-clock callable is web.md §4's `get_wall_clock()`
(`datetime.now(UTC)`), passed by the container to every `wall_clock` parameter in this file.

Label: [Decided §7, engineering]; the staff, spend, eval, identity and check-event column lists are the sibling topics'.
Consumers: AEA-27, 29, 30, 31, 32, 38, 40, 44, 46, 52, 53.

```python
# adapters/sqlite/repos_cases.py (AEA-10)
DEMO_START = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
    # [Source: worked-pairs.md header "Friday 2026-10-16, 10:00"; WP-4 "two hours away", Innocent-decided D3] (CAS-23).
    # The OpenAPI mocks' 14:20 is an example value, not this constant.
```
Consumers: AEA-30 (`DemoClock` start), AEA-31 (reset to start), AEA-52.

### 1.2 Repository methods added to DO-4 §13's list

```python
# core (repos_core.py, AEA-10). Cross-ticket reads land here by the slice plan §0 deviation.
core.conversations.lookup(thread_id) -> ConversationRow | EndedThread | None   # EndedThread → SESSION_ENDED (CAS-32)
core.reads.invoice(invoice_id: InvoiceId) -> InvoiceRow | None                 # CON-12 current value (CAS-19)
core.reads.appointment(appointment_id: int) -> AppointmentRow | None           # CON-12 current value (CAS-19)
core.reads.customer(customer_id: CustomerId) -> CustomerRow | None             # CON-12 current value (CAS-19)
core.reads.identity_state(thread_id) -> IdentityState                          # slice plan §0 (AEA-34)
core.reads.new_flags_count() -> int                                            # CON-17 new_flags_count (AEA-29)
core.reset.clear_demo_tables(reset_id: str) -> Cleared                         # slice plan §0; the list in §1.3 (CAS-1, CAS-3)
    # The slice plan writes it `reset.clear_demo_tables(tx)`: the repository is reached THROUGH tx (tx.core.reset), so
    # it always runs inside the caller's transaction; reset_id only labels the tombstones.

# Asked for by sibling addenda, accepted here (AEA-10 body) [Decided §7, engineering; ledger "Merge additions"]
core.events.latest_of(stream: StreamKey, kind: str) -> EventId | None   # CON-21 start point (staff.md §7, merge MC-8)
core.turns.timeouts_for(thread_id) -> int                               # turn rows with degrade reason timeout (graph-core X-3)
core.messages.recent(thread_id, turns: int) -> tuple[MessageRow, ...]   # the chat window (graph-core X-3)
core.check_events.append(event: CheckEvent, thread_id: ThreadId) -> int # graph-nodes cross-topic 3
core.lookup_log.for_thread(thread_id) -> tuple[LookupRow, ...]          # graph-nodes cross-topic 3 (brief assembly); id ascending
core.lookup_log.append(entry: LookupEntry) -> int                       # DO-4 §13, restated: thread_id is copied from the
                                                                        #   messages row entry.message_id names, in the same tx
core.messages.handoff_anchor(thread_id) -> int                          # CAS-38: the newest customer message's id, else the
                                                                        #   greeting row's id (staff.md §12); never None
core.settled_for(thread_id, read_at)                                    # defined in stage7/graph-core.md §6
core.turns.begin(ids, received_at) / finish(turn_id, record: TurnRecord)   # DO-4 §13; TurnRecord is graph-core.md §2's
                                                                        #   (GRC-21). TurnRecord.response is opaque serialised
                                                                        #   JSON, so CON-4 replays like CON-2 (web.md cross-topic)
core.turns.fail_running() -> tuple[TurnId, ...]                         # NEW (R-G-22 = web R-W-4), AEA-40's start-up restart
                                                                        #   sweep, called once before the first request: EVERY
                                                                        #   `running` row becomes status 'failed', path 'degraded',
                                                                        #   outcome 'degraded_handoff', degrade_reason 'timeout' in
                                                                        #   one UPDATE; returns the swept ids. No age test: one
                                                                        #   process on one volume (DO-2), and received_at is demo
                                                                        #   time. 'failed' lets the same turn_id re-run (DO-4 §14)

# In-transaction helpers the staff services need [Source: staff.md CAS assumptions] (AEA-10 body; callers pass tx)
core.cases_ro.owner(case_ref) -> CaseOwnerRow | None        # (thread_id, owner_role: StaffRole | None, owner_since, lifecycle)
core.messages.append(thread_id, role, text_redacted, at) -> int        # returns the message id
core.messages.belongs_to_case(message_id, case_ref) -> bool
# and cases.case_events.append(event) below, whose row carries actor_role (StaffRole | "ai" | "system")

class EndedThread(MeridianModel):              # one ended_threads row; web.md §4 owned_thread answers 410 from it (MC-16)
    thread_id: ThreadId; demo_session: str; ended_wall_at: datetime
    reason: str                                # SessionEnded details.reason, e.g. "demo_reset"
    reset_id: str | None

class Cleared(MeridianModel):
    open_threads: tuple[ThreadId, ...]       # conversations that were open; ResetService appends demo_reset to each stream
    case_streams: tuple[CaseRef, ...]        # every case stream that has events (read BEFORE the events rows go);
                                             #   ResetService appends one demo_reset to each [Source: staff.md CAS assumptions]
    roles_reset: int                         # staff.md §4 step 1 count (OpenAPI ResetResponse.roles_reset)
    rows_cleared: dict[str, int]             # table → rows removed, for reset_event.restored_json

class LookupRow(LookupEntry):                # one stored lookup_log row as read back (CAS-38); THE definition of its
                                             #   fields. MODULE: domain/tools.py (AEA-02, wave 0), beside LookupEntry,
                                             #   NOT repos_core.py (R-G-8): checks.build_evidence (AEA-15) and
                                             #   BriefAssembler.assemble (AEA-29) take it and may not import adapters
                                             #   (DO-3 §2.1); repos_core imports it like every other domain type. Every
                                             #   LookupEntry field (DO-4 §5: tool, record_ids, passage_ids, result_seen,
                                             #   message_id: int, turn_id), so a row and its entry cannot disagree, plus:
    id: int                                  # lookup_log.id; a brief item's SourceRef(kind="lookup_log", ref=str(id))
    thread_id: ThreadId                      # copied by append from the message row (§1.2), the key for_thread reads by

# cases (repos_cases.py, AEA-10): the names AEA-29/30/31 call. Bodies are AEA-10's; semantics are the callers'.
cases.cases.insert / get / get_for_thread_open / list_open / update_versioned(case_ref, expected_version, **changes)
cases.case_events.append(event) ; cases.case_events.exists(case_ref, kind, key: str) -> bool   # scheduler idempotency
cases.promises.insert / set_status(case_ref, status, at, reason) / list_open_past(now) -> list[PromiseRow]
cases.followups.upsert / get ; cases.activities.insert / list_for_case
cases.demo_state.get() -> DemoStateRow ; cases.demo_state.set_now(dt) ; cases.demo_state.set_staffing(mode)
cases.demo_state.reset() -> None                                   # demo_now = DEMO_START, staffing = nobody_online
cases.demo_events.insert(row) ; cases.job_runs.start(job_run_id, …) / finish(job_run_id, status, counts, error_kind)
cases.job_runs.latest() -> JobRunRow | None                        # AEA-32's stale-tick check, AEA-53's "last ran" tile (CAS-22)
cases.records.reset_event(row) ; cases.records.seed_event(row) ; cases.records.seed_rows_present() -> bool
cases.refs.next_case_ref() -> CaseRef                              # max(existing, seeds) + 1; seeds hold MHC-C-0005…0008
```
Label: [Decided §7, engineering] except where a source is cited. Consumers: AEA-29, 30, 31, 32, 34, 52, 53.

### 1.3 What a reset restores, clears, updates and keeps (CAS-1)

| Effect | Tables |
|---|---|
| **Restored** from the issued file, row for row, inside the reset transaction | `customers`, `technicians`, `appointment_slots`, `appointments`, `invoices` (and their `sqlite_sequence` rows set to the issued maximum, so a reset demo books the same next ids) |
| **Cleared** (all rows; AUTOINCREMENT sequences kept, so no id is reused) | `conversations` (each first copied to `ended_threads`), `messages`, `turns`, `actions`, `lookup_log`, `check_events`, `events`, `cases`, `case_events`, `promises`, `followups`, `activities`, the brief rows, `flags`, `identity_threads`, `identity_codes`, `demo_inbox` |
| **Updated** | `staff_sessions`: every row with `role != 'customer'` gets `role = 'customer', role_reset_pending = 1`; no row is deleted (staff.md §4, CON-9; merge MC-11); `demo_state.reset()` |
| **Kept** (never touched by a reset) | `spend_ledger`, `health_events`, `deploy_records`, `eval_runs`, `eval_case_results`, `job_runs`, `demo_events`, `reset_events`, `seed_events`, `ended_threads` (`request` and `auth_event` are log records, not tables: web.md §10, merge MC-15) |

[Source: DO-6 *Storage and access* ("Conversations, turns, lookup log, check events, cases, case events, promises … Demo:
cleared by reset"; "Spend ledger, health events, eval runs and case results, deploy records … tables the demo reset does
**not** clear"); OpenAPI `resetDemo` ("Restores the working DB copy, cases, seeds and codes"); SCREEN_SPECS SCR-1 "The demo was reset, so this
chat has ended. Nothing from it was kept."; staff.md §4; slice plan §0]. Rows DO-6 does not name are [Decided §7, engineering]: operational
records with IDs only are kept, rows a conversation or case created are cleared.

### 1.4 The two reset callables, revised (CAS-1, CAS-2)

```python
# adapters/sqlite/migrate.py (AEA-10)
def restore_working_copy(tx: UnitOfWork) -> None: ...
    # Reads the issued file through a SEPARATE read-only connection (file:…?mode=ro&immutable=1), then, inside the
    # caller's transaction, DELETEs and re-INSERTs the five issued tables. Replaces DO-4's Callable[[], None]: a file
    # copy would also erase the kept tables of §1.3 (DO-6), and could not join the reset's single transaction.
    # First boot still COPIES the file when meridian.sqlite is missing (DO-1 §9); only the reset path rewrites in place.

# adapters/checkpointer.py (AEA-10)
class Checkpointer:
    def prune(self, keep: int = 2) -> int: ...              # [Decided SDQ-10]
    def clear(self) -> None: ...                             # unchanged
    def clearing(self) -> ContextManager[None]: ...
        # Own connection to checkpoints.sqlite; BEGIN IMMEDIATE; DELETE every saver table; yield; COMMIT on a clean
        # exit, ROLLBACK on an exception. ResetService enters it INSIDE its meridian transaction and commits meridian
        # first (§7). Replaces DO-4's clear_checkpoints: Callable[[], None].
```
Label: [Decided §7, engineering]. Consumers: AEA-31 (callables), AEA-52 (wired), AEA-50 (reset script calls `ResetService`).
The issued file's five tables, row for row, are also what AEA-10 AC-4 checks; the kept tables of §1.3 surviving a
`restore_working_copy(tx)` is the same test's second half.

### 1.5 Test fixture home (CAS-4)

`temp_sqlite()` lives in `tests/fixtures/sqlite.py`, owned by AEA-10 [Source: slice plan §3 collision map: "it moves to
`tests/fixtures/sqlite.py` (owned by 10) so 10 and 11 never share a folder"]. Consumers: every service ticket in this
topic, and AEA-34, 40, 41, 44, 46.

---

## 2. Booking policy (AEA-13): `policy/booking.py`

**The two types the policy returns** (CAS-34). Their definitions are owned here; AEA-02 transcribes them into `domain/`
beside `ShownSlot` and `ConfirmationView`, which hold them (domain may not import policy, DO-3 §2.1).

```python
Zone = Literal["north", "central", "south"]
    # [Source: scheduling_db/SCHEMA.md "Zone mapping (city → zone) north: … · central: Austin · south: …" and
    #  appointment_slots.zone; all 528 issued slot rows use exactly these three values (central 216, north 156,
    #  south 156; counted 2026-10-21)]. A slot matches a customer when slot.zone == zone_for(their city or ZIP).

class FeeNote(MeridianModel):                         # what fee_note returns; ConfirmationView.fee_note → the wire `fee_line`
    service_type: ServiceType                         #   (OpenAPI ConfirmationBlock and Settled.visit)
    tier: Literal["none", "standard", "plus"]         # the VERIFIED customer's tier; "none" when unverified (R-14)
    fee_row: str | None                               # the SCHEDULE_FEES key that applies, e.g. "Diagnostic visit" (CAS-7);
                                                      #   None only when the fee schedule has no visit-fee row for the type
    amount_cents: int = Field(ge=0)                   # SCHEDULE_FEES[fee_row][tier]; 0 when waived or when fee_row is None
    waived: bool                                      # fee_row set and the tier's amount is 0 (members: "Waived")
    line: str = Field(min_length=1, max_length=120)   # the customer sentence, from policy/texts.py, never typed here:
                                                      #   "Standard diagnostic fee: $89" (OpenAPI ConfirmationBlock example);
                                                      #   the amount is formatted from SCHEDULE_FEES, never a second literal
```

**This is the one `FeeNote`** (residual pass, R-G-2). graph-core.md §14's earlier field set (GRC-25: `schedule_row`,
`scheduled_cents`, `charged_cents`, `waived_by_membership`) is withdrawn there; AEA-02 transcribes the six fields above
into `domain/records.py`, and AEA-13 fills them. [Decided §7, engineering: the booking policy that builds the type owns
its fields; cases A-1 already pointed AEA-02 here.]

```python
LAKEWAY_ZIPS: frozenset[str] = frozenset({"78734", "78738"})
    # [A] (CAS-8) Lakeway's ZIPs (audit K-11 names these two); each is 787xx, so the exclusion wins over "Austin: 787xx (all)".
    # Replaced by: a check of the full USPS list for Lakeway at Stage 9; a city string "Lakeway" is not served whatever the ZIP.
NOT_SERVED_CITIES = frozenset({"San Marcos", "Bastrop", "Elgin", "Lakeway"})   # [Source: KB policies/service_area.md]

def zone_for(city_or_zip: str) -> Zone | None: ...                 # None = not served; Zone above (CAS-34)
def hours_before(now: datetime, slot_date: date, window: Window) -> float: ...   # may be negative (window started)
def fee_bearing(hours: float) -> bool: return hours < 24.0
    # [Source: pricing/2026_fee_schedule.pdf "Late cancellation (<24h) $49", "Supersedes all prior fee schedules";
    #  FAQ "more than 24 hours before the window are free"]. Exactly 24.0 h → False (free). A started or past window → True (CAS-6).
def fee_note(service_type: ServiceType, tier: Literal["none", "standard", "plus"]) -> FeeNote: ...
    # plumbing → the diagnostic visit row, as for hvac_repair: $89 non-member, waived for standard and plus
    # [Source: fee schedule "Diagnostic visit $89 / Waived / Waived" (no service restriction); membership/comfort_club_overview.md
    #  "Diagnostic fee ($89) waived on all service calls"; FAQ "Diagnostic fee: $89"] (CAS-7). FeeNote above (CAS-34).
    # The $89 is read from SCHEDULE_FEES["Diagnostic visit"], never a second literal.
    # Row per service type (R-G-3): hvac_repair, plumbing → "Diagnostic visit"; hvac_tune_up → "Seasonal tune-up"
    #   ($129 non-member, included for standard and plus) [Source: fee schedule "Seasonal tune-up (per system) $129 /
    #   Included (2/yr)"; price book HV-TUNE; 11 issued invoice lines "Seasonal tune-up" at 12900]; estimate → fee_row
    #   None, amount 0, waived False ("Free in-home estimate", services/service_catalog.md).
    # line: render(<the booking fee text>, amount=format_usd(amount_cents)) (data.md §2: placeholder `amount` and
    #   format_usd, added there at the residual pass, R-W-7); a waived row renders the waived text with the scheduled
    #   amount (format_usd(SCHEDULE_FEES[fee_row]["none"])), never a typed literal.
SCHEDULE_FEES   # defined in stage7/graph-tools.md §4 (its C-3); lives in this file, AEA-13 writes it
MEMBER_ALLOWANCE_ROWS   # defined in stage7/graph-tools.md §4 (R-G-3); lives in this file beside SCHEDULE_FEES
```
Consumers: AEA-28 (service, executors), AEA-14 (`window_start` through `ChangeRequestDraft`), AEA-27 (`SCHEDULE_FEES`), AEA-29.

---

## 3. Handoff policy (AEA-14): `policy/handoff.py` and `policy/escalation.py`

### 3.1 Business days and due times (CAS-9)

```python
HOLIDAYS_CLOSED: frozenset[date] = frozenset({date(2026, 5, 25), date(2026, 7, 4), date(2026, 9, 7), date(2026, 11, 26),
                                              date(2026, 11, 27), date(2026, 12, 25), date(2027, 1, 1)})
    # [Source: KB policies/holiday_hours_2026.png]: "Closed" and "Emergency only" days are not business days.
    # The image says only "New Year's Day (Jan 1)"; 2027-01-01 is the one inside any demo promise's reach [Decided §7].
SHORT_DAYS: dict[date, time] = {date(2026, 12, 24): time(12, 0)}   # [Source: same image, "Christmas Eve 7am - 12pm"]
CLOSE_OF_BUSINESS = time(19, 0)                                     # [Source: FAQ phone support Mon–Fri 7:00am–7:00pm]
PHONE_HOURS = {0..4: (time(7), time(19)), 5: (time(8), time(16))}   # Sunday and HOLIDAYS_CLOSED: closed [Source: FAQ; image]

def is_business_day(d: date) -> bool: ...        # Mon–Fri and not in HOLIDAYS_CLOSED. Saturday is NOT a business day.
def business_due(now: datetime, days: int) -> datetime: ...
    # Close of business on the `days`-th business day strictly AFTER now's calendar date (Chicago); the time of day of
    # `now` never matters. Fri 10:00 +1 → Mon 19:00; +2 → Tue 19:00 (WP-8, WP-7, SCREEN_SPECS SCR-1, Innocent-checked).
    # Fri 20:00 +1 → Mon 19:00; Sat or Sun +1 → Mon 19:00; Mon 08:00 +1 → Tue 19:00; Wed 2026-11-25 +1 → Mon 11-30 19:00.
def phone_support_open(now: datetime) -> bool: ...
def due_label(dt: datetime) -> str: ...           # "Monday, October 19, 7:00 pm" (format owned by UX copy)
```
Label: [Decided §7, engineering] (rule derived from the approved worked pairs and issued KB). Consumers: AEA-29, 30, 31, 36, 39.

### 3.2 The promise table and the two due times (CAS-10, CAS-11)

```python
PolicyRow = Literal["R26.unstaffed", "R26.refund", "R26.staffed", "R26.safety_none", "OD4.danger_review"]

PROMISE_TABLE: Mapping[PolicyRow, str]   # every string imported word for word from policy/texts.py (AEA-03), never typed here
    # "OD4.danger_review" = SCREEN_SPECS SCR-1 copy note, the separate line under the emergency-line card:
    # "No representative is online right now, so someone will review this online request within 1 business day.
    #  That is not the wait for emergency help; for that, please use the emergency line."  [Source: R-8, OD-4 (ii),
    #  SCREEN_SPECS line 147, OpenAPI EmergencyLineBlock.separate_line]

def promise_for(reason: HandoffReason, presence: Presence, now: datetime,
                window_start: datetime | None = None) -> Promise: ...      # DO-4 §7 signature unchanged
    # Row choice (first match):
    #   safety                                   → R26.safety_none, text "", due None
    #   presence == simulated_on_shift           → R26.staffed, due None, live_queued True        (every other reason)
    #   danger, burning_unclear (nobody online)  → OD4.danger_review, due business_due(now, 1)
    #                                              [Source: WP-6 step 4 "a P1 case with the separate one-business-day
    #                                               review line" (Innocent ✓ 2026-10-20)]
    #   refund                                   → R26.refund, due business_due(now, 2), extra "I can't promise an outcome."
    #   anything else                            → R26.unstaffed, due business_due(now, 1)
    #   fee_bearing_change adds extra_lines: the can't-guarantee line when window_start < due_at, and the phone-support
    #   line when phone_support_open(now).
    # Promise.due_at is ALWAYS the customer promise (what the screen shows with due_label). It is never the window start.

def case_due_at(reason: HandoffReason, promise: Promise, window_start: datetime | None) -> datetime | None:
    return window_start if reason is HandoffReason.FEE_BEARING_CHANGE else promise.due_at
    # The case's internal due: R-21 "internal due time at the window start"; consolidated §9.3 "a staff target, not a
    # promise to the customer"; OpenAPI CON-12 FEE_BEARING_CHANGE mock (case due_at 12:00, promise.due_at Mon 19:00).
```
Label: rows and texts [Source: as cited]; names `OD4.danger_review`, `case_due_at` [Decided §7, engineering].
Consumers: AEA-29 (stores both dues), AEA-30 (overdue uses the case due, missed uses the promise due), AEA-31 (seeds),
AEA-36 (safety, danger), AEA-39, AEA-24 (M-10 imports `PROMISE_TABLE`), AEA-52, AEA-53.

### 3.3 Priority (CAS-12, CAS-13, CAS-14, CAS-16)

```python
def priority_for(reason: HandoffReason, *, promise_due: datetime | None = None,
                 renewal_date: date | None = None) -> Priority: ...
    # safety P0 · danger, burning_unclear P1 · fee_bearing_change, late_technician P2 ·
    # membership_cancel: P2 if renewal_date is not None and renewal_date <= promise_due.date(), else P3 (CAS-14);
    #   decide_escalation passes promise_due = business_due(inputs.now, 1) (§3.4 residual note, R-G-15) ·
    # unsupported_action P4 (CAS-12) [Source: consolidated §9.4 "P4 routine follow-up: an unfinished action, no
    # deadline"] · customer_requested_person, refund, billing_dispute, complaint_or_manager,
    # legal_or_chargeback, commercial, identity_unverified, ai_failure P3 ·
    # the "burning smell, both ruled out" case: PENDING Innocent (CAS-16); the planner must not guess it.

DUE_SOON_WINDOW = timedelta(hours=4)    # [A] CAS-20. Replaced by: the Stage 9 staff walkthrough (lane neither empty nor crowded)
UNOWNED_AFTER = timedelta(minutes=30)   # [A] CAS-20. Same measurement. Both on the DEMO clock.
```
Consumers: AEA-29, 30 (thresholds), AEA-39 (via `decide_escalation`), AEA-31.

### 3.4 Escalation rule table, rows 4, 6 and 7 revised (CAS-12, CAS-13, CAS-15)

| # | When | Outcome | Reason → priority, `rule_id` |
|---|---|---|---|
| 4 | Plan `handoff_request` = `membership_cancel` | escalate | `membership_cancel` → `priority_for(…, renewal_date)`; `D4.membership_cancel` |
| 4 | Plan `handoff_request` = `unsupported_action` (the planner's `unsupported_other`) | escalate | `unsupported_action` → P4; `D4.unsupported` |
| 4 | Plan `handoff_request` = `late_technician` | escalate | `late_technician` → P2; `D4.late_technician` (producer: cross-topic A-6) |
| 6 | `halt` set (only brake halts reach here: graph-core.md §5, X-5), **or** any `SpecialistResult.status == "failed"` (a failure after its one retry, DO-1 §8.2), **or** `models_disabled`, **or** `plan.planner_failed and not plan.tasks` (graph-nodes.md §5) | escalate, `degraded=True` | `ai_failure` → P3; `AI.halt` / `AI.specialist_failed` / `AI.models_disabled` / `AI.planner_failed` |
| 7 | `failed_answers ≥ 2` or `corrections ≥ 2` or `timeouts ≥ 2` | offer | `OD6.two_misses` / `OD6.two_timeouts` [A: threshold 2, OD-6] |

`decide_escalation` reads the renewal date from `results`' `AccountResult.membership` (AEA-02's `MembershipView`).
Label: [Decided §7, engineering], aligning DO-4's proposal rows with decided DO-1 §8.1–§8.2 and D4. Consumers: AEA-39, 51.

**Residual pass (R-G-14, R-G-15)** [Decided §7, engineering]:

- **`EscalationInputs` gains `now: datetime`** (DO-4 §6; AEA-02 adds the field, the escalation node fills it from
  `ctx.now`, AEA-39). For `membership_cancel`, `decide_escalation` passes `promise_due = business_due(inputs.now, 1)`
  to `priority_for`: the `R26.unstaffed` due, the latest promise this reason can carry, used whatever the presence (a
  staffed promise has no due, and P2 should not depend on who is online). So the escalation node needs no presence
  read and `HandoffService` never re-derives a priority. WP-8: Fri 2026-10-16 10:00 → due Mon 10-19; renewal
  2026-11-03 is later → P3; a renewal on 2026-10-19 or earlier → P2.
- **Stable `rule_id`s for rules 1, 2 and 5** (DO-4 §6 named only examples; AEA-14 asked the plan to name them):
  rule 1 `R2.person`; rule 2 `R24.<reason value>` (`R24.refund`, `R24.billing_dispute`, `R24.complaint_or_manager`,
  `R24.legal_or_chargeback`, `R24.commercial`); rule 5 `R16.identity_unverified`.
- **The person-gate `HandoffRequest`**: when the gate is `PERSON` the handoff node (AEA-39) builds the request itself
  (the gate path skips `decide_escalation`) with `reason=customer_requested_person`, `priority=priority_for(reason)`
  (P3), `rule_id="R2.person"`, `trigger="gate"`: the same id rule 1 returns, so a person request has one id whichever
  path built it. CON-4's request keeps `CON4.person` (web.md §8), because it is a different trigger.

---

## 4. Scheduling service types (AEA-28): homed in `services/scheduling.py` (CAS-17)

Only AEA-28's own files read these (the executors fold them into AEA-02's `SchedulingResult` / `ToolResult`), so they live
beside the service, not in `domain/`, and AEA-28 does not wait on an AEA-02 follow-up.

```python
class WindowQuery(MeridianModel):
    zone_hint: str                                    # city or ZIP as the customer gave it (validated by zone_for, never echoed)
    service_type: ServiceType
    member_tier: Literal["none", "standard", "plus"]  # from the VERIFIED customer; "none" when unverified (R-14)
    wanted_text: str = ""                             # the customer's words; never parsed into a hold
    earliest: date | None = None; latest: date | None = None; window: Window | None = None
    limit: int = Field(default=3, ge=1, le=6)         # [A] windows offered per search; replaced by Stage 9 transcript replays

class WindowsFound(MeridianModel):
    zone: Zone
    windows: tuple[ShownSlot, ...]                    # requested fit first, then the earliest alternatives
    exact_fit: bool                                   # False → the reply says the request can't be met and offers these (R-18)

class OutOfArea(MeridianModel):
    reason: Literal["not_served", "unknown_location"] # the input string is never stored here

class SlotTaken(MeridianModel):
    slot_id: int
    alternatives: tuple[ShownSlot, ...]               # fresh windows read in the same transaction

class Refused(MeridianModel):
    code: Literal["fee_bearing", "not_shown", "outside_service_area", "wrong_service_type", "booking_cap", "not_owned"]
    hours_before: float | None = None                 # set for fee_bearing (feeds the change-request path)
```
```python
# services/scheduling.py (AEA-28): one read added to DO-4 §14's SchedulingService   [Decided §7, engineering] R-G-19
class SchedulingService:
    def slice_inputs(self, customer_id: CustomerId) -> SchedulingSliceInputs: ...
        # One read-only unit of work: tx.core.reads.customer(customer_id) → zone = zone_for(zip, else city) (§2),
        #   member = membership_tier != "none"; appointments = tx.booking.appointments.views_for_customer(customer_id)
        #   (§4.1). Unknown customer → SchedulingSliceInputs(zone=None, member=False, appointments=()).
        # Caller: the act node (AEA-39, graph-nodes §9.5) for a scheduling task with a VERIFIED customer only; it
        #   fills SchedulingSlice.customer_zone, .member, .appointments (DO-4 §5). SchedulingSliceInputs and
        #   AppointmentView are domain types (graph-tools §3), so act.py imports nothing from services/.
```

Label: [Decided §7, engineering]. Consumers: AEA-28 only (service and `agent/tools/scheduling.py`). The executors are
registered through `scheduling_tools(scheduling)` and map `Refused.code` to the same-named `ToolErrorCode`
(stage7/graph-tools.md §1, its C-7).

### 4.1 Module: adapters/sqlite/repos_booking.py — the booking repository and the two rows it returns (CAS-36)

**In practice (illustrative values).** A booking of slot 56: inside one write transaction `SchedulingService.book`
calls `tx.booking.slots.get_for_update(56)`, sees `status="open"`, calls `set_status(56, "booked")` and
`tx.booking.appointments.insert(56, "MHC-10004", "AC not cooling", created_at=date(2026, 10, 16))`, and gets
appointment id 160 back (the issued file's highest is 159). A second customer racing for slot 56 re-reads `booked` and
gets `SlotTaken`.

```python
# domain/records.py (AEA-02 writes the file; fields = the issued columns, scheduling_db/SCHEMA.md)   CAS-36
class Slot(MeridianModel):
    slot_id: int; slot_date: date; window: Window; tech_id: int; zone: Zone; service_type: ServiceType
    status: Literal["open", "booked", "reserved_members", "blocked"]   # all four occur in the issued rows

class Appointment(MeridianModel):
    appointment_id: int; slot_id: int; customer_id: CustomerId
    issue_description: str                            # stored; never in any model input (audit D-11, DO-4 §5)
    created_at: date                                  # issued rows hold a date; rows we write hold the demo-clock date
    status: Literal["scheduled", "completed", "cancelled", "no_show"]
    is_warranty_visit: bool                           # issued 0/1: no diagnostic fee applies when True

# adapters/sqlite/repos_booking.py (AEA-28 body; AEA-02 shell; 50_booking.sql by AEA-10)   [Decided §7, engineering]
class SlotsRepo:                                      # adapters/sqlite/repos_booking.py; = tx.booking.slots
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def search(self, zone: Zone, service_type: ServiceType, *, member: bool, earliest: date, latest: date,
               window: Window | None, limit: int) -> tuple[Slot, ...]: ...
        # status 'open', plus 'reserved_members' when member; slot_date in [earliest, latest]; the window when given;
        # ordered by slot_date, window, slot_id; at most `limit`. Read-only.
    def get_for_update(self, slot_id: int) -> Slot | None: ...      # DO-4 §13; re-read inside the write tx (R-19)
    def set_status(self, slot_id: int, status: Literal["open", "booked", "reserved_members", "blocked"]) -> None: ...

class AppointmentsRepo:                               # adapters/sqlite/repos_booking.py; = tx.booking.appointments
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def insert(self, slot_id: int, customer_id: CustomerId, issue_description: str, created_at: date) -> int: ...
        # status 'scheduled', is_warranty_visit 0; returns the new appointment_id (issued max + 1 after a reset, §1.3)
    def get(self, appointment_id: int) -> Appointment | None: ...
    def for_customer(self, customer_id: CustomerId) -> tuple[Appointment, ...]: ...   # status 'scheduled', by slot date
    def views_for_customer(self, customer_id: CustomerId) -> tuple[AppointmentView, ...]: ...   # R-G-19
        # the same rows as for_customer, joined to appointment_slots (date, window, service_type) and technicians
        #   (name); never issue_description (audit D-11). AppointmentView: graph-tools §3 (domain/specialists.py)
    def move(self, appointment_id: int, new_slot_id: int) -> None: ...   # the service frees the old slot in the same tx
    def set_status(self, appointment_id: int,
                   status: Literal["scheduled", "completed", "cancelled", "no_show"]) -> None: ...

class TechniciansRepo:                                # adapters/sqlite/repos_booking.py; = tx.booking.technicians
    def __init__(self, conn: sqlite3.Connection) -> None: ...
    def name(self, tech_id: int) -> str | None: ...   # the confirmation's technician name ("Jun Park")

class BookingRepos:                                   # adapters/sqlite/repos_booking.py; = UnitOfWork.booking (DO-4 §13)
    slots: SlotsRepo; appointments: AppointmentsRepo; technicians: TechniciansRepo
    def __init__(self, conn: sqlite3.Connection) -> None: ...   # builds the three over the unit of work's connection (§1.0)
```
Consumers: AEA-28 (bodies and `SchedulingService`), AEA-02 (shell, `Slot`, `Appointment`), AEA-10 (`core.reads.appointment`
reads the same table read-only, §1.2).

---

## 5. Cases and handoff (AEA-29): `services/cases.py`, `services/handoff.py`

```python
class CaseService:
    def __init__(self, uow: UnitOfWorkFactory, clock: Clock) -> None: ...          # CAS-18
        # Staffing for QueueView is read from tx.cases.demo_state, not from DemoService, so CaseService ← DemoService
        # has no cycle. Current values for CON-12 come from tx.core.reads.* (§1.2; slice plan §0), so nothing is injected.
    # DO-4 §13 methods unchanged, except:
    def convert_live_queued(self, now: datetime, tx: UnitOfWork | None = None) -> int: ...
        # tx given → runs inside the caller's transaction (DemoService.set_staffing), so a shift end and its
        # conversions commit together (R-30: 0 live-queued while nobody online). None → its own transaction.
    # attach_brief(case_ref, brief) (DO-4 §13) is an upsert per case: a second call replaces the stored brief
    #   (graph-nodes.md §3 stores a draft, then the checked brief).

class BriefAssembler:
    def __init__(self) -> None: ...                    # pure; DO-4 §7 methods unchanged

class HandoffService:                                  # DO-4 §7 constructor + one argument (CAS-33)
    def __init__(self, uow: UnitOfWorkFactory, cases: CaseService, demo: DemoService, clock: Clock,
                 staff_guidance: Mapping[HandoffReason, tuple[StaffGuidance, ...]] = {}) -> None: ...
    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult: ...
        # Inside its ONE write transaction: presence = demo.presence(tx); promise = promise_for(…);
        # case due = case_due_at(…); cases.open_case(tx, req, promise, now). Reading presence inside the transaction
        # means a shift end cannot interleave between the read and the write. A live-queued case sets the
        # conversation's live_state = 'queued'. For each StaffGuidance mapped to req.reason it appends one lookup_log
        # row, a DO-4 §5 LookupEntry(tool="staff_guidance", record_ids=(), passage_ids=(passage_id,),
        # result_seen=text_sha256, turn_id=req.turn_id, message_id=anchor) through core.lookup_log.append, where
        # anchor = tx.core.messages.handoff_anchor(req.thread_id), read in the same transaction (CAS-38, §1.2):
        #   - graph turn: TurnService step 4 wrote this turn's customer message before run_graph, so the anchor IS
        #     TurnInput.message_id (the message that led to the handoff), with no new field on HandoffRequest or TurnContext;
        #   - CON-4: the newest customer message, or, if the customer tapped "Talk to a person" before typing anything, the
        #     greeting row SessionService.open wrote with the conversation (staff.md §12), so the anchor always exists.
        # LookupEntry.message_id therefore stays a required int (DO-4 §5 unchanged), and the brief item carries
        # source.kind = "lookup_log", ref = the row id (DO-4 §7, heading 7). Idempotent per thread: a second open for the
        # same case writes no second guidance row. Writes no turn row (web.md, AEA-42).

STAFF_GUIDANCE_FOR: Mapping[HandoffReason, tuple[str, ...]] = {        # policy/handoff.py; the bullet's opening words
    HandoffReason.FEE_BEARING_CHANGE: ("Waive the $49 late-cancellation fee once per customer per year",),
    HandoffReason.LATE_TECHNICIAN:    ("Waive the diagnostic fee when the technician arrived more than 30 minutes",),
    HandoffReason.BILLING_DISPUTE:    ("Extend a 10% courtesy discount on a repair invoice under $500",),
    HandoffReason.COMPLAINT_OR_MANAGER: ("Extend a 10% courtesy discount on a repair invoice under $500",),
    HandoffReason.REFUND:             ("Issue refunds of any kind.",),            # the "Agents may NOT" list
}
    # [Source: KB internal/agent_discretion_notes.md, quoted from the file; consolidated §9.3 (staff, never the AI,
    #  may waive)]. The container resolves each prefix to load_staff_guidance()'s passages at start-up; a prefix that
    #  matches none fails start-up. Never in any ResponderInput (R-10, HP-3).
```

**Rules the methods apply** (CAS-10, CAS-20, CAS-21):

| Rule | Value |
|---|---|
| `due_state` (CON-11, CON-12) | `no_due_time` if case due is None · `overdue` if case due < demo now · `due_soon` if case due − now ≤ `DUE_SOON_WINDOW` · else `on_time` |
| Queue order (`needs_my_action`) | P0, then P1, then overdue first, then case due ascending, then `created_at`; no-due rows after dated ones within a priority |
| Oversight lanes (CON-17) | Each open case appears in the **first** lane it qualifies for, in the fixed order P0 and P1 · Overdue · Due soon · Unowned (unassigned and age ≥ `UNOWNED_AFTER` on the demo clock, whatever the staffing) · Stuck waiting (wake-up < now); empty lanes kept |
| Unowned **alert** line | Only while staffing is `simulated_on_shift` [Source: consolidated §6 alerts table "while staff are on shift"] |
| Promise `kept` | resolve at or before promise due; or a CON-15 activity with outcome `reached` or `left_message` at or before promise due; a promise with no due is `kept` on resolve |
| Promise `missed` | resolve after promise due; or the scheduler finds it `open` with promise due < demo now (any case state) |
| Promise `changed` | `convert_live_queued` (new text from the table) |
| Stream events `CaseService` writes | `case_changed` to `case:<ref>` on every version change; on a shift end, `shift_ended` to the thread stream and `chat_closed` (reason `shift_ended`) to the case stream, with `live_state` back to `not_live` [Source: OpenAPI `setStaffing`; staff.md §5] |
| Ownership | stored as a `StaffRole`; every owner / claimed_by / changed_by string is `STAFF_PERSONAS[role].name`; assign maps through `ASSIGNEE_ROLES` (staff.md §1; merge MC-12). `CaseService` never imports `ROLE_CARDS` |
| `allowed_actions` (CON-11, CON-12) | the lifecycle × live-state table's actions **intersected with** `ROLE_ACTIONS[actor.role]` (staff.md §1, `domain/staff.py`; web residual R-W-13). The owner always gets `[]`; the supervisor is never offered claim-and-join, join chat, the live reply or log call / email. Order: the table's order |
| Customer speaker on staff reads (CON-12 `conversation`) | `display_name = CUSTOMER_SPEAKER_NAME` ("Customer", staff.md §1; web residual R-W-14), as CON-21 `customer_message` has it; never the customer view's "You" |

Types these methods return, by name only (graph topic, AEA-02, fields = the OpenAPI schema): `QueueView` = `QueueResponse`,
`CaseDetail` = `CaseDetail`, `OversightView` = `OversightResponse`, `CaseAction` = `CaseActionRequest`,
`CaseActionRejected` = `ApiError` code + details, `FollowUpChoice` = `FollowUpRequest`, `FollowUp` = `FollowUpView`,
`ActivityIn` = `ActivityRequest`, `Activity` = `Activity`. `StaffRole`, `StaffActor`, `DemoRole`, `STAFF_PERSONAS`,
`ASSIGNEE_ROLES`: staff.md §1 (`domain/staff.py`, AEA-02; merge MC-2, MC-12).
`StaffGuidance`: data.md §3 (`retrieval/manifest.py`; merge MC-26).
Consumers: AEA-30, 36, 38, 39, 42, 45, 46, 51, 52, 53.

---

## 6. Demo clock, staffing and scheduler (AEA-30): `services/demo.py`, `services/scheduler.py`

```python
class DemoClock:                                       # implements the Clock port (DO-4 §13)
    def __init__(self, uow: UnitOfWorkFactory) -> None: ...
    def now(self) -> datetime: ...                     # demo_state.demo_now; DEMO_START on a fresh store (§1.1)

# FixedClock: NOT defined here (residual pass, R-G-9). Its one definition is stage7/data.md §8a (DAT-32): immutable,
#   FixedClock(at=WORKED_PAIRS_NOW) (the same instant as DEMO_START), now(), advanced(by) → a NEW clock. AEA-11 is a
#   data-addendum ticket (internal-components §16 table), so data owns the fake's shape; CAS-37's mutating set/advance
#   sketch is withdrawn. This topic's tests build one clock per moment (AEA-29: one before and one after a due time);
#   a test that must hold one clock across scheduler ticks builds a new SchedulerJob per tick (its idempotency is in
#   case_events, not in the object), or records blocked-on AEA-11 for a small follow-up there, never a second fake.

def format_clock(dt: datetime) -> tuple[str, str]: ...
    # ("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)"): the ONE formatter for CON-1, CON-8 read and
    # advance, and clock_changed (answers AEA-43 ND-2 / AEA-47 ND-2 on this topic's side)

ClockStep = Literal["plus_1h", "plus_4h", "next_business_morning"]   # = OpenAPI ClockAdvanceRequest.step (staff.md §8's
                                                                      #   "CAS's step type"); services/demo.py

class DemoService:                                     # CAS-18
    def __init__(self, uow: UnitOfWorkFactory, clock: DemoClock, cases: CaseService) -> None: ...
    def presence(self, tx: UnitOfWork | None = None) -> Presence: ...
    def staffing(self) -> StaffingView: ...                                        # = OpenAPI Staffing
    def set_staffing(self, mode: Literal["nobody_online", "simulated_on_shift"], *,
                     request_id: RequestId, role: DemoRole) -> StaffingChange: ...  # = OpenAPI StaffingResponse
        # any logged-in role may toggle [Source: OpenAPI setStaffing, R-48]
        # One transaction: demo_state, demo_events row, staffing_changed to every open chat, and on → off
        # cases.convert_live_queued(now, tx) (which writes shift_ended per affected chat). Same mode → no write.
    def clock_view(self) -> ClockView: ...                                         # = OpenAPI DemoClock
    def advance_clock(self, step: ClockStep, *, actor: StaffActor,
                      request_id: RequestId) -> ClockAdvanced: ...                 # = OpenAPI ClockAdvanceResponse
        # This signature is the owner's (merge MC-13): staff.md §8 calls
        #   advance_clock(step, actor=actor, request_id=ctx.request_id) and copies now, label, became_overdue unchanged.
        #   demo_events.role stores actor.role.value.
        # next_business_morning: 07:00 on the next business day (is_business_day, §3.1). One transaction:
        # demo_state, demo_events row, clock_changed to every open chat. became_overdue = open cases (not resolved
        # or closed) whose CASE due d satisfies old_now <= d < new_now. Due states recompute on read (CON-8).

class JobRun(MeridianModel):                           # services/scheduler.py; internal, not serialised
    job_run_id: str; started_wall_at: datetime; finished_wall_at: datetime | None; demo_now: datetime
    status: Literal["started", "completed", "failed"]; error_kind: str | None
    overdue: int; promises_missed: int; due_soon: int; stuck_waiting: int; unowned: int
    abandoned: int; pruned: int | None                # pruned set only on the once-a-day tick

class SchedulerJob:                                    # DO-4 §14, constructor revised (CAS-29)
    def __init__(self, uow: UnitOfWorkFactory, cases: CaseService, clock: Clock,
                 prune_checkpoints: Callable[[], int],
                 wall_clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None: ...
        # UTC, as every wall clock (§1.1 wall-time storage, merge MC-20); the container passes get_wall_clock().
    def tick(self) -> JobRun: ...
        # Demo clock: overdue (case due), promises_missed (promise due), due_soon, stuck_waiting, unowned — one
        #   case_event per (case, kind, due or wake-up value), checked with case_events.exists, so catch-up is idempotent.
        # Wall clock: abandonment sweep — conversations with run_tag 'live', outcome 'open' and
        #   last_customer_wall_at <= wall_now − 30 min → outcome 'abandoned', ended at last_customer_wall_at + 30 min
        #   [Source: DO-7 difference 4, Innocent 2026-10-21; slice plan row AEA-30]; once per wall-clock day,
        #   prune_checkpoints() [Decided SDQ-10].
        # Runner: every 60 s [A, system design §8.2] on a thread started by register_demo().
```
`StaffingView`, `StaffingChange`, `ClockView`, `ClockAdvanced`, `Presence`: by name, graph topic (A-2).
Consumers: AEA-29, 31, 36, 40, 43, 47, 51, 52.

---

## 7. Reset and seed (AEA-31): `services/reset.py`

```python
class ResetService:                                    # DO-4 §14, constructor revised (CAS-1, CAS-2, CAS-3)
    def __init__(self, uow: UnitOfWorkFactory, gate: ResetGate,          # web.md §7 (AEA-23), one per process
                 restore_working_copy: Callable[[UnitOfWork], None],
                 clear_checkpoints: Callable[[], ContextManager[None]],
                 seed_demo: Callable[[UnitOfWork], int]) -> None: ...
    def reset(self, now: datetime, *, request_id: RequestId, session_id: LoginSessionId | None,
              role: DemoRole | None) -> ResetDone | ResetFailed: ...
        # Signature owner: this file (merge MC-19). `now` is the wall clock (reset_events.at_wall; merge MC-20).
        # CON-9 passes the caller's session.session_id and session.role. session_id=None, role=None means the operator
        #   script on a stopped service (data.md §7, AEA-50) and is stored as NULL asked_by_role / asked_by_session.
        # LoginSessionId, DemoRole: staff.md §1, domain/staff.py (AEA-02; merge MC-2).
        # with gate.hold():                              # raises web's ResetAlreadyRunning when held → 409 at CON-9;
        #                                                #   while held, web's middleware answers 503 RESET_IN_PROGRESS
        #   with uow(write=True, exclusive=True) as tx, clear_checkpoints():    # turns in flight wait ≤ 5 s [A]
        #                                                #   (limits.web.reset_wait_s, web.md §5)
        #     restore_working_copy(tx)
        #     cleared = tx.core.reset.clear_demo_tables(reset_id)
        #     tx.cases.demo_state.reset()
        #     demo_reset → each cleared.open_threads stream and each cleared.case_streams stream (new, higher ids)
        #       (a seed re-uses MHC-C-0005…0008, so their streams keep this row; CON-21 starts after the newest
        #        demo_reset when no Last-Event-ID is sent: staff.md §7, core.events.latest_of, merge MC-8)
        #     n = seed_demo(tx); reset_event (asked_by_role = role, asked_by_session = session_id, request_id);
        #     seed_event(reset_id, n)
        #     tx.commit()                                # meridian commits first; the checkpoint clear commits on exit
        # any exception before tx.commit() → both roll back → ResetFailed (RESET_FAILED); nothing half-reset.
        # The only residual window: the checkpoint COMMIT failing after meridian committed. Then every stale
        # checkpoint belongs to a tombstoned thread (unreachable: SESSION_ENDED), reset_event records
        # checkpoints_cleared = false, and the next daily prune or reset removes them.

class ResetDone(MeridianModel):                        # = OpenAPI ResetResponse (CAS-31: roles_reset, not staff_sessions_invalidated)
    ok: Literal[True] = True; open_chats_ended: int; roles_reset: int; clock: ClockView
class ResetFailed(MeridianModel): code: Literal["RESET_FAILED"] = "RESET_FAILED"
# No ResetBusy type: "busy" is web's ResetAlreadyRunning from gate.hold(); "in progress" for other routes is gate.held().

def seed_demo(tx: UnitOfWork) -> int: ...              # first boot (when seed_rows_present() is False) and every reset
```

**The seed set** (CAS-24) [Source: SCREEN_SPECS SCR-5 and SCR-7 default states; CON-11/CON-17 `SEEDED` mocks; R-33].
Customers come from the issued DB (AEA-31 AC-8): the two not named below are any issued customers outside MHC-10001…10004
and MHC-57204 (the worked pairs' customers), recorded in the seed file. Each seed is a thread with `run_tag = 'seed'`,
fixed customer messages, `lookup_log` rows, a brief built by the real `BriefAssembler` from a hand-written
`BriefExtraction` (quotes are exact substrings of the seed messages), and a promise from `promise_for` **at the seed's own
`created_at`**, never recomputed at the demo start.

| Ref | Reason, priority | Customer | `created_at` (before DEMO_START) | Promise → case due | State at DEMO_START |
|---|---|---|---|---|---|
| MHC-C-0005 | refund, P3 | issued customer (seed file) | Tue 2026-10-13 10:00 | R26.refund → Thu 10-15 19:00 | unassigned, **Overdue** lane |
| MHC-C-0006 | complaint_or_manager (conduct), P3 | issued customer (seed file) | Fri 2026-10-16 09:14 | R26.unstaffed → Mon 10-19 19:00 | unassigned ≥ 30 min, **Unowned** lane |
| MHC-C-0007 | billing_dispute, P3, INV-204411 | MHC-10002 Omar Patel | Fri 2026-10-16 09:24 | R26.unstaffed → Mon 10-19 19:00 | unassigned ≥ 30 min, **Unowned** lane; follow-up phone, mornings |
| MHC-C-0008 | safety (gas smell), P0 | none (unmatched caller) | Fri 2026-10-16 09:56 | R26.safety_none → no due | unassigned, **P0 and P1** lane |

Live cases then number from MHC-C-0009 (`refs.next_case_ref`). Consumers: AEA-29 (assembler), AEA-43 (CON-9), AEA-50
(reset script), AEA-52, AEA-53 (`seed_count` = 4).

---

## 8. Ops (AEA-32): `services/health.py`, `repos_ops.py`

```python
@dataclass(frozen=True)
class AlertSettings:                                   # the ONE place alert lines live: AEA-32 applies them, AEA-53 shows them
    latency_p95_s: float = 12.5                        # [T] M-23
    failure_rate: float = 0.02                         # [T] M-24
    zero_traffic_after: timedelta = timedelta(hours=4) # [Decided Innocent 2026-10-21] M-22
    quiet_start: time = time(22); quiet_end: time = time(6); tz: str = "America/Chicago"   # [A, configurable] M-22
    turn_window: timedelta = timedelta(minutes=60)     # [A] CAS-25: live turns whose receipt is in the last 60 min (wall)
    min_turns: int = 20                                # [A] below it, latency and failure-rate alerts stay quiet (matches CON-19's null reason)
    evaluate_every_s: int = 60                         # [A] CAS-25
    scheduler_stale_after_s: int = 180                 # [A] CAS-22: three missed 60 s ticks
    heartbeat_every_s: int = 5; heartbeat_stale_after_s: int = 30    # [A] CAS-26
    probe_every_s: int = 15; probe_timeout_s: int = 5; failures_to_exit: int = 3   # [A, system design §8.2]
    # spend cap: not here. It is limits.spend.daily_cap_usd (SpendLimits, models.md §6, in AEA-01's policy/limits.py,
    # $30/day; merge MC-22), passed by the container to LedgerService, AlertEvaluator and MetricsReader (§9). Replaced by: the Stage 9 load re-measure and the first day of
    # live traffic (alert flapping, heartbeat age p99 at 20 conversations at once).

AlertType = Literal["spend_cap_reached", "p95_latency_over_12_5s", "health_check_restart", "zero_traffic",
                    "failure_rate_over_2pct", "trace_export_failed",            # = OpenAPI MonitorAlert.type
                    "scheduler_stale"]                 # stored health_event only; shown on CON-19 as a health tile (CAS-30)
    # No "overdue" alert here: DO-6's Overdue row says "Supervisor view alert (C3)", so it lives on CON-17 through the
    # scheduler's case_events (OpenAPI MonitorAlert has no overdue type) (CAS-30).
    # spend_cap_reached: ledger.spend_today() >= daily_cap_usd (models.md §6). A provider's own cap (an open circuit)
    # is not this alert; MetricsReader shows it as handoff-only mode from ledger.open_circuits().

class AlertWriter:                                     # the writer models.md cross-topic 6 asks for (MOD's on_alert hook)
    def __init__(self, uow: UnitOfWorkFactory, wall_clock: Callable[[], datetime], agent_version: str) -> None: ...
    def fire(self, alert_type: AlertType, reason_code: str) -> None: ...
        # Thread-safe; opens its own short write unit of work; callable from a non-request thread at start-up.
        # Writes alert_fired only when the type's latest stored state is not already firing (no duplicate rows).
        # Container: LangfuseTraceSink(on_alert=lambda reason: alert_writer.fire("trace_export_failed", reason)).
    # trace_export_failed CLEARS in AlertEvaluator: when the latest live turn's turn.trace_export is "sent".
    # It also FIRES there when that value is "failed" or "off" (DO-6 "Export failed on any turn, or off"), so a
    # process with no Langfuse keys shows the alert honestly.

class Heartbeat:
    def beat(self, mono: float) -> None: ...           # advanced every 5 s by a lifespan task that runs a no-op through the
                                                       # worker pool (anyio.to_thread.run_sync): proves the loop AND the pool work
    def fresh(self, mono: float) -> bool: ...          # mono − last_beat ≤ heartbeat_stale_after_s; never touches SQLite

class Watchdog:                                        # a thread started by register_ops()
    def __init__(self, uow: UnitOfWorkFactory, probe: Callable[[], bool], exit: Callable[[int], None],
                 evaluator: AlertEvaluator, settings: AlertSettings, wall_clock: Callable[[], datetime]) -> None: ...
    def run_once(self) -> None: ...                    # probe → check health_event; 3 in a row → restart event, exit(1);
                                                       # every evaluate_every_s → evaluator.evaluate()

class AlertEvaluator:
    def __init__(self, uow: UnitOfWorkFactory, ledger: LedgerService, settings: AlertSettings,
                 wall_clock: Callable[[], datetime], daily_cap_usd: float) -> None: ...
        # daily_cap_usd: limits.spend.daily_cap_usd from the container, no default (merge MC-22)
    def evaluate(self) -> tuple[AlertState, ...]: ...  # from stored rows only; writes alert_fired / alert_cleared ONLY on change
    # zero_traffic: the time since the last live conversation started, NOT counting any part inside 22:00–06:00
    #   Chicago, exceeds 4 h (last start 21:00, now 07:00 → 2 h counted → quiet).
    # scheduler_stale: job_runs.latest().started_wall_at older than scheduler_stale_after_s (CAS-22).
    # health_check_restart (R-G-23) [Decided §7, engineering]: FIRING while ops.health.last_restart().at_wall falls on
    #   the current America/Chicago calendar day; QUIET (alert_cleared written once) at the first evaluation on a later
    #   Chicago day, or when no restart is stored. M-28 counts restarts per Chicago day, so the alert and the tile agree;
    #   a second restart the same day writes no second alert_fired (on change only).

class AlertState(MeridianModel):
    type: AlertType; state: Literal["firing", "quiet"]; fired_at: datetime | None
    value: float | None; threshold: float | None

# repos_ops.py (AEA-32 body)
ops.health.append(event: HealthEvent) -> int
ops.health.latest_alert_states() -> dict[AlertType, AlertState]          # AEA-53 reads this; it never re-applies a line
ops.health.last_restart() -> HealthEvent | None ; ops.health.restarts_by_day(tz: str) -> list[tuple[date, int]]
ops.deploy.insert(record: DeployRecord) -> None ; ops.deploy.latest() -> DeployRecord | None
ops.eval.upsert_report(run: EvalRunRow, results: Sequence[EvalCaseResultRow], summary_json: str) -> bool   # by run_id
ops.eval.latest_completed(suite: Literal["worked-pairs", "retrieval", "e2e", "load"],
                          split: Literal["dev", "held-out"] | None) -> EvalRunRow | None
ops.eval.case_results(run_id) -> list[EvalCaseResultRow]

def load_eval_reports(reports_dir: Path, uow: UnitOfWorkFactory) -> int: ...      # services/health.py (AEA-32), CAS-27
    # [Source: data.md cross-topic 3; DAT-14]. Start-up, beside the deploy_record write: parses every
    # eval/reports/*.json (data's EvalReportFile shape: run, results, summary) and upserts by run_id; returns how many
    # were new. Idempotent; a file that fails to parse is skipped with one health_event (reason "eval_report_invalid")
    # and never half-loaded. src/ never imports eval/: EvalRunRow / EvalCaseResultRow are this topic's row models with
    # data §6's field names, and summary_json is stored as given (AEA-53 reads it, never recomputes).

class HealthEvent(MeridianModel):
    at_wall: datetime; kind: Literal["check_ok", "check_failed", "restart", "alert_fired", "alert_cleared"]
    alert_type: AlertType | None; reason_code: str | None; value: float | None; threshold: float | None; agent_version: str
# DeployRecord: every field DO-6 *Records* lists (deploy_id, at_wall, agent_version, commit, image digest).
# EvalRunRow / EvalCaseResultRow: data.md §6 EvalRunRecord / EvalCaseResult field for field (status
# started/completed/failed/incomplete; split "dev" | "held-out" | None; experiment_id; items stored as JSON).
```
Consumers: AEA-23 (`Heartbeat` for `/healthz`), AEA-24 (writes the report files the loader reads), AEA-50 (deploy record;
copies `eval/reports/` into the image), AEA-52 (stale-tick event in CAP-5), AEA-53, the container in AEA-51 (`AlertWriter`
bound to the trace sink's `on_alert`).

---

## 9. Metrics reader (AEA-53): `services/metrics_reader.py`

```python
class MetricsReader:
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, wall_clock: Callable[[], datetime],
                 ledger: LedgerService, settings: AlertSettings, current_agent_version: str,
                 daily_cap_usd: float) -> None: ...
        # daily_cap_usd: limits.spend.daily_cap_usd (models.md §6), no default, as AlertEvaluator (merge MC-22); it is
        # CON-19's spend.cap_cents (× 100). today_cents is ledger.spend_today() × 100.
    def owner_metrics(self) -> Mapping[str, object]: ...   # OpenAPI OwnerMetricsResponse field names
    def monitoring(self) -> Mapping[str, object]: ...      # OpenAPI MonitoringResponse field names
    def latest_eval(self) -> Mapping[str, object]: ...     # OpenAPI EvalResponse field names, from eval_runs.summary_json
    # MetricsReader satisfies web.md §4 MetricsReads structurally (bound to get_metrics_reads() by AEA-53; merge MC-6);
    # each method returns Mapping[str, object] with OpenAPI field names. The route validates it through
    # web/schemas/reads.py (staff.md §9), and AEA-53's own tests validate with the same models. Handoff-only mode comes
    # from ledger.models_disabled() and ledger.open_circuits() (models.md §6).
    # Opens read-only units of work only. The reader, not the route, stamps every time field (merge MC-5): CON-19
    # as_of from wall_clock; CON-19 demo_now and CON-18 as_of from demo_clock (STF-22). Alert states come from
    # ops.health.latest_alert_states(); alert_config from AlertSettings; it never
    # applies a threshold itself. Adds a health Tile "scheduler_last_run" ("Overdue job last ran n min ago") from
    # cases.job_runs.latest() (DO-6 *Missing instrumentation*). Live counts filter run_tag = 'live' (seed threads are
    # 'seed', so they never inflate M-22). M-18 reads conversation.outcome as stored; AEA-30's sweep writes 'abandoned'.
```
Consumers: AEA-48 (routes, through web.md §4's `MetricsReads` / `get_metrics_reads()`), AEA-55.

---

## 10. Integration (AEA-52)

No new signature. The relayed customer turn (`outcome = to_staff`, CAP-4's relayed half) is AEA-51's [Source: slice plan
row AEA-51 "the relayed `to_staff` turn through the real graph (moved from 52)"] (CAS-28). The slice plan moved the
criterion but did not add its blockers: the proof needs a representative in control (AEA-44 session and role, AEA-46
takeover and the CON-21 stream), so AEA-51 gains AEA-44 and AEA-46 as blockers. Both are wave 2 and AEA-51 is wave 3,
so no wave moves.

---

## Cross-topic assumptions

Each item is another topic's to define; this topic builds against the shape stated and records `blocked-on` if it
differs. Items marked **settled** are already decided in a finished sibling file and are followed above.

| # | Owner topic (ticket) | What this topic assumes |
|---|---|---|
| A-1 | graph (AEA-02) | `Zone` and `FeeNote` are defined in §2 (CAS-34) and AEA-02 transcribes them into `domain/`; `Slot` and `Appointment` likewise from §4 (CAS-36). `Window`, `ServiceType`, `ShownSlot`, `Presence` = `Literal["nobody_online", "simulated_on_shift"]`, `CaseState`, `Promise` (fields only; its text check is `PROMISE_TABLE`'s, AEA-02 needs-decision 2 option a), `MembershipView.renewal_date: date \| None`, `HandoffReason` exist as DO-4 sketches them. |
| A-2 | graph (AEA-02 follow-up) | The case and demo view types get their fields from the OpenAPI schema named beside them and live in `domain/`: `QueueView`, `CaseDetail`, `OversightView`, `CaseAction`, `CaseActionRejected`, `FollowUpChoice`, `FollowUp`, `ActivityIn`, `Activity`, `StaffingView`, `StaffingChange`, `ClockView`, `ClockAdvanced`, `ResetDone`. If graph declines, these services return plain dicts shaped as the OpenAPI schema and the route's schema validates them. The three metrics reads are **settled** as `Mapping[str, object]` behind web.md §4's `MetricsReads` Protocol (merge MC-6). |
| A-3 | graph (AEA-02) | `HandoffReason` gains one value for R-7's "both ruled out" case once Innocent answers CAS-16 (proposed `burning_ruled_out`). |
| A-4 | graph (AEA-02/37) | `CaseSummary` (DO-4 §7) gains `due_at: datetime \| None` (the case due) beside `promise.due_at` (the customer due), matching OpenAPI `QueueRow.due_at` / `PromiseRecord.due_at`. |
| A-5 | graph (AEA-21/40/51) | `FailureCounters.timeouts` counts the thread's `TURN_TIMEOUT` turns; `EscalationInputs.models_disabled` is `ledger.models_disabled()` (models.md §6: our cap or any open provider circuit), read through `GraphDeps.ledger: ModelsStatus` (graph-core §4; **settled**, residual R-G-13). |
| A-6 | graph (AEA-02/37) | Late technicians reach `Plan.handoff_request = late_technician` (a planner `handoff` value or a `join_plan` mapping). Until then they arrive as `unsupported_other` and get P4 instead of D4's P2. |
| A-7 | web (AEA-40), **settled** (web.md §9) | The turn path writes `conversations.last_customer_wall_at` on every customer message and sets `outcome` (`ai_resolved`, `handed_off`, `safety_reply`) at the turn that ends the conversation; AEA-42's CON-4 path sets `handed_off` when a case is created or live-queued (web.md §8, merge MC-18); AEA-30 writes only `abandoned`. `SESSION_ENDED` vs `SESSION_NOT_FOUND` uses `core.conversations.lookup`, read by web.md §4's `owned_thread` (merge MC-16). |
| A-8 | data (AEA-24), **settled** | DAT-14: the harness writes `eval/reports/<run_id>.json`; this topic's `load_eval_reports` (AEA-32) upserts them at start-up; no route accepts results. |
| A-9 | staff (AEA-44), **settled** | STF-6: `staff_sessions.role_reset_pending` is set by `clear_demo_tables` and cleared by `switch_role` (merge MC-11); `StaffAccess.actor_for` (web.md §3, staff.md §2) answers `RoleRefusal(reason="role_reset")` from `LoginSession.role_reset` (merge MC-1). |
| A-10 | web (AEA-23), **settled** | WEB §7: `ResetGate` (`held`, `hold`, `ResetAlreadyRunning`) is built once by the container and passed to `ResetService`; the middleware answers 503. |
| A-11 | data (AEA-03) | `policy/texts.py` holds, word for word: the `OD4.danger_review` line (SCREEN_SPECS SCR-1 copy notes), the can't-guarantee and phone-support lines, the staffing banner, "Demo: recorded, not sent", and the CON-17 / CON-19 decision lines. |
| A-12 | models (AEA-26), **settled** | models.md §6: `LedgerService.spend_today()`, `models_disabled()`, `open_circuits()`, injected into `AlertEvaluator` and `MetricsReader`; the trace sink's `on_alert` is bound to `AlertWriter.fire` (models.md cross-topic 6). |
| A-13 | graph (AEA-38/36) | On the P1 unstaffed path the reply puts the `OD4.danger_review` text in `EmergencyLineBlock.separate_line` and shows no second R26.unstaffed promise. |
| A-14 | data (AEA-16), **settled** | DAT-13: `load_staff_guidance(index_dir)` returns `StaffGuidance` passages; the container maps them to reasons with `STAFF_GUIDANCE_FOR` (CAS-33). |
| A-15 | web (AEA-40), **settled** | The turn path writes a `turn.trace_export` value (`sent`, `failed`, `off`) on every turn (web.md §9; models.md MOD-9); `AlertEvaluator` reads it. |
