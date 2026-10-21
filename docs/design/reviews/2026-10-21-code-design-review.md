# Code design review: DO-3 and DO-4 (Meridian AI service agent)

**Date:** 2026-10-21. **Reviewer:** `metz-code-design-agent` (workspace rule `code-design-solid-modularity`).
**Reviewed:** `docs/design/code-design.md` (DO-3), `docs/design/contracts/{README,internal-components,api-con-mapping}.md`
(DO-4), `.claude/reference/area-map.md`; context from `system-design.md` (SDQ-1…10 decided) and PRD 0.4.
**Not reviewed:** the parked `src/meridian/` beyond its size (17 modules, ~1,960 lines, untracked). `git log` has one
snapshot commit, so there is no churn signal yet; the judgement below rests on the build plan, not on history.

---

## 1. The story in three sentences

This design turns the parked one-loop agent into a two-layer LangGraph turn whose memory of "what we already did" lives
in one table, so the SP-1 bug (WP-4F: "Yes, please." answered as if the move never happened) cannot recur. The changes
it most needs to absorb are not future features: they are **its own construction, in parallel, within hours** (internal
target 06:00 CT today has passed; interview Thu 2026-10-22), then provider swaps and the written 10× path. The core is
right; the build plan is too finely cut and has ownership arrows pointing backwards across waves.

---

## 2. Module table (by package; 113 modules are summarised, not listed)

| Package | One-sentence responsibility | Depends on | Direction |
|---|---|---|---|
| `domain/` | Declare the typed hand-offs every component agrees on. | pydantic | OK |
| `policy/` | Hold the tables the business changes (texts, promises, priorities, zones, fees, limits). | domain | OK |
| `gates/`, `checks/`, `privacy/` | Make the pure safety decisions (gate, R-46, redaction). | domain, policy | OK |
| `ports/` | Own the interfaces the core needs from the outside world. | domain | OK |
| `adapters/models/` | Make one provider request and report it as a typed attempt. | SDK / httpx, ports | OK |
| `adapters/sqlite/`, `checkpointer.py` | Store rows in one transaction; build the LangGraph saver. | sqlite3, ports | OK |
| `adapters/` (fastembed, langfuse, events, clock) | Wrap the index, the tracer, the event crossing, the demo clock. | libs, ports, `repos_ops` | OK |
| `services/` | Run one workflow each over ports. | ports, core | **Not OK for two:** `scheduler.py` imports `adapters/checkpointer.py`; `reset.py` imports `adapters/sqlite/migrations.py` (finding S-3) |
| `agent/` | Run one turn as a static graph; every model call through the gateway. | services, ports, core | OK |
| `web/` + `container.py` | Translate HTTP to services; the one place concretes are built. | services, agent; container → adapters | OK |
| `eval/` | Score the agent through its HTTP API only. | HTTP | OK |

---

## 3. Seams: keep cut, defer, merge

| Seam | Call | Why |
|---|---|---|
| S-1 three model ports (`ChoiceModel`, `StructuredModel`, `ToolCallingModel`) | **Keep cut** | The reasoning is exactly right: Jev can only choose, so one `ModelClient` would make Jev raise `NotImplementedError` for text and tools, a Liskov break every caller must check for. Tighten the gateway's typing (finding S-4). |
| S-2 one gateway by role | **Keep cut** | One place for deadline, retry, ledger, span and redaction profile. |
| S-3 policy apart from mechanism | **Keep cut, regroup files** | The seam is right; eight files in wave 0 is not (B-2). |
| S-4 `RetrievalIndex` | **Keep cut** | External ONNX model; tests need a fake that loads nothing. |
| S-8 `Clock`, S-10 `TraceSink` | **Keep cut** | Two and three real implementations exist today. |
| S-12 specialists as data, S-13 tools from Pydantic + one dispatcher, S-14 prompts apart, S-15 pure core | **Keep cut** | Three real specialists sharing one braked loop is a pattern, not a guess. |
| S-6 storage | **Merge down:** keep `UnitOfWork` as the transaction boundary; **drop the 19 repository Protocols** | One implementation; tests use a temp SQLite file, not fakes (DO-3 says so). Postgres is 10× step 5, written not built. **Trigger to cut:** step 5 starts. |
| S-7 case store as three Protocols | **Merge:** one concrete `CaseService` | One implementation, and S-20 already decided services need no Protocols. The split is not even by caller (S-1 finding below). **Trigger:** a second case store, or an area that must build against a case fake. |
| S-11 event bus Protocols | **Defer the Protocols, keep the module** | One implementation; the module boundary (thread → event loop) is the value, and it has a gap (S-5). |
| S-5, S-9, S-16…S-23 | **Defer, agreed** | Each names a real trigger. S-20 is the best call in the document. |

---

## 4. Findings, most costly first

### Blocking

**B-1. Three wave-1 areas depend on files owned by later areas or by a sibling.** Where: DO-3 §8, area map.
§7 cuts waves along A0–A12, and DO-3 says areas build "against fakes", but storage has no fake (temp SQLite only), so an
area needs the *real* repo file of whoever owns that table. As written:

| Wave-1 area | Needs | Owned by |
|---|---|---|
| A3, A4, A5 (`agent/tools/{knowledge,account,scheduling}.py`) | `ToolDef`, `ToolCallScope`, `ToolResult` from `agent/tools/registry.py` | **A7, wave 2** |
| A2 (`services/ledger.py`: `spend_ledger`), A6 (`clock_demo.py`, `presence.py`, `clock_control.py`: `demo_state`) | `adapters/sqlite/repos_ops.py` | **A10, wave "1–2"**; A8 (`events`) and A9 (`staff_sessions`) also write into it |
| A4 (`identity.locate` reads customers; `tools/account.py` reads invoices) | `repos_working_copy.py` | **A5**, same wave |
| A6 (`scheduler.py` prune, `reset.py`) | `adapters/checkpointer.py` | **A7, wave 2** |

*Change it makes expensive:* every wave-1 ticket above either waits or invents a stand-in that A7/A10 must later
reconcile. *Fix (small, do it before §7):* move `ToolDef`/`ToolCallScope`/`ToolResult` into `domain/tools.py` (A0); split
`repos_ops.py` by owner (`spend` → A2, `demo_state` → A6, `events` → A8, `staff_sessions` → A9, health/job/reset → A10);
split `repos_working_copy.py` (customers + invoices → A4, slots + appointments → A5); move the checkpointer factory and
`prune()` to A0 or A6. Rule of thumb for the collision map: **the area that writes a table owns its repo file.**

**B-2. Wave 0 (A0) is a ~30-module critical path for a build measured in hours.** Where: DO-3 §3, §8.
A0 owns `config`, 11 `domain/` files, 8 `policy/` files, 7 `ports/` files (with 19 repo Protocols inside
`ports/storage.py`), 4 SQLite files, the container skeleton and every test fake; "everything waits on it". *Change it
makes expensive:* the whole parallel plan. Nothing in wave 1 starts until A0 transcribes ~33 Protocols and every policy
table word for word. *Fix:* keep in A0 only what two or more areas read: `domain/` (merged, see S-1 merges), `ports/`
**without** repo Protocols, `policy/texts.py`, `policy/limits.py`, connection + UoW + schema, container stubs, fakes.
Move each other policy table to its one consumer: `zones` + `fees` → A5 (`policy/booking.py`); `promises` +
`priorities` → A6 (`policy/handoff.py`); `escalation` → A7 whole (today it is split "A0 rules / A7 wiring", an
ownership nobody can act on); `claims` lexicon → inline in `checks/completion.py` (its only reader).

### Should

**S-1. About 40 files hide nothing; merge them.** Where: DO-3 §3. A boundary must hide a decision that might change; a
10-line node in its own file hides none, and each file is one more import line and one more owner row in the collision
map. Concrete merges (113 → roughly 70; each line is one change):

| Merge | Into | Why it is safe |
|---|---|---|
| `domain/{base,ids,errors}.py` | `domain/common.py` | Base is 5 lines; all three change only with the contract |
| `domain/checks.py` | `domain/turn.py` | Same reader set (A7) |
| `ports/{models,retrieval,clock,events,tracing,cases,storage}.py` | `ports/models.py` + `ports/__init__.py` | A0 owns all; models is the only port with real churn |
| `checks/{evidence,completion,facts}.py` | `checks.py` | One area (A7), one requirement (R-46), ~150 lines |
| `agent/nodes/{gates,escalation,handoff,checks}.py` (each "calls X; writes key Y") | their neighbours (`front.py`, `plan.py`, `reply.py`) | Thin wrappers; §5.3's key table is the real contract |
| `adapters/models/classify.py` | inline into each adapter | See S-2 |
| `services/{staff_sessions,flags}.py` | `services/staff.py` | Both are tiny, both A9 |
| `web/schemas/{chat,demo,errors}.py` | `web/schemas/customer.py` | One owner (A8) |
| `web/routes/pages.py` (owned "A8/A9") | page routes inside `routes/chat.py` and `routes/staff.py` | Removes the one shared route file |
| 19 repo Protocols + `tests/contract/test_uow_contract.py` | delete | One implementation; a contract test with one subject proves nothing about substitution |

**S-2. `adapters/models/classify.py` is a shared function waiting to grow a flag per provider.** Where: DO-3 §4.3.
Its own notes already branch by provider: "429 without retry-after → spend cap *on Anthropic*", "402 → spend cap *on
OpenRouter*". Anthropic arrives through SDK exceptions, Jev through raw `httpx` responses, so the inputs differ too.
That is the wrong-abstraction shape. *Fix:* each adapter classifies its own failures; **the shared promise lives in
`tests/contract/test_choice_model_contract.py`**, which already runs both adapters against recorded fixtures. Liskov is
enforced by the contract test, not by sharing code.

**S-3. Two services import adapters, against DO-3's own rule.** Where: DO-3 §4.4 (`scheduler.py` → `checkpointer`,
`reset.py` → `migrations`). *Fix:* inject what they need as plain callables built in the container:

```python
class ResetService:
    def __init__(self, uow: UnitOfWorkFactory, restore_working_copy: Callable[[], None],
                 clear_checkpoints: Callable[[], None], events: EventPublisher) -> None: ...
```

**S-4. The gateway can be configured into a Liskov break.** Where: DO-4 §12. `RoleSpec.provider` allows
`"openrouter_jev"` for `RESPONDER`, so the gateway would have to check what it got before calling `structured`. *Fix:*
the container builds the gateway with three typed maps, and `Settings` rejects a role/provider mismatch at start-up:

```python
ModelGateway(choice={Role.PLANNER: jev, Role.CLASSIFIER: jev, Role.PLANNER_FALLBACK: sonnet},
             structured={Role.RESPONDER: sonnet, Role.BRIEF: sonnet},
             tools={Role.SPECIALIST: sonnet}, ledger=..., trace=..., limits=...)
```

**S-5. The event bus needs an after-commit hook the UoW doesn't offer.** Where: DO-4 §13. `publish(tx, event)` writes the
row in the caller's transaction and "wakes subscribers after commit", but `UnitOfWork` has no commit callback, so the
builder of A8 will reach into A0's UoW. *Fix (pick one):* add `UnitOfWork.after_commit(fn)` in wave 0; **or** drop the
push path entirely: the SSE endpoint polls `events WHERE id > last_id` about once a second. At 20 conversations that is
trivial, it is still SSE with replay (SDQ-5 holds), the replay path becomes the only path, and the thread-to-loop
crossing disappears. The second is simpler; it costs up to ~1 s on a staff-join event.

**S-6. Transaction ownership is inconsistent across services.** Where: DO-4 §14. `IdentityService.locate/send_code/verify`
take a `tx` from the caller; `SchedulingService` opens its own. A7's identity node then has to open a UoW, which puts a
transaction in the graph layer that DO-3 §2.3 rule 1 keeps out. *Fix:* services own their transactions; `IdentityService`
writes its own `actions(verified)` row. Only `CaseService.open_case(tx, …)` keeps a `tx`, because `HandoffService` must
commit case + promise + action + event together.

**S-7. A7 is one wave-2 area of ~27 modules.** Where: DO-3 §8. That is the long pole after wave 0. §5.3's "who writes which
key" table already makes a split safe. *Fix:* A7a spine (`graph`, `routers`, `context`, `load_context`, `compose`, node
stubs) first; then in parallel A7b specialists and tools (`runner`, `specs`, `registry`, `dispatch`, specialist prompts),
A7c reply (`facts`, `respond`, brief extraction, `checks`, responder and brief prompts), A7d front (gates, safety,
identity, plan nodes, planner and classifier prompts).

**S-8. The case store's three role interfaces are not split by caller.** Where: DO-4 §13. `CaseLifecycle` serves the
staff console (`apply`), the customer's follow-up (CON-5, `set_followup`) and the shift-end job (`convert_live_queued`):
three callers in one "role". With one implementation and S-20's reasoning, the Protocols buy nothing. *Fix:* one
concrete `CaseService`; if "the staff console must not call the write path" matters, enforce it with an import check in
`code-review-agent`, not three interfaces.

### Could

**C-1. Delete the `scope` flag on `check_completion`.** DO-4 §10 keeps `scope="turn"` "only as an eval option". The
difference is in the data, not the function: the eval passes `settled.only_turn(turn_id)` to the same function. One
flag for one caller is how wrong abstractions start.

**C-2. Don't oversell S-12's open/closed claim.** A fourth specialist is a new spec *plus* edits to `PlannerChoices`,
`join_plan`, `SpecialistResult`, `TurnFacts`, `facts.py`, `compose.py` and the escalation rules. That is fine (no
fourth is planned); just say so. Keep the runner free of `if spec.kind == …`; the first such branch is the signal to
inline.

**C-3. Make `web/container.py` collision-proof in wave 0.** The per-area `register_*` idea is right; A0 should create
every stub up front so later areas edit separate hunks instead of appending at the end of the file. Same for the
schema: one DDL file per owning area beats one `migrations.py` every area must edit.

**C-4. `GraphDeps` has ten fields.** Acceptable as a parameter object, but it shows the graph knows every service.
If it grows, that is the place to look.

---

## 5. What's good (keep it)

- **R-45 done right.** "What we already did" has one authority, the `actions` table, read at the start of the turn and
  again after writes; the words (R-46 check) and the panel (`SettledView`) read the same rows. That is the WP-4F fix in
  the structure, not in a prompt.
- **The pure core** (`gates/`, `checks/`, `policy/`, `privacy/`, `join_plan`, `decide_escalation`) keeps every safety
  invariant unit-testable in milliseconds.
- **Ports owned by the core, one composition root**, no module-level clients; the parked `SETTINGS`/`_client()` go.
- **The three model ports** and their written contract (one attempt, never raises, same failure kinds, contract tests
  run against both adapters).
- **No transaction across a model call**, checked in review. That protects SQLite's single writer from a 60 s turn.
- **The deferred list** (S-5, S-9, S-16…S-23) names a trigger for each. S-20 (no Protocols over our own services) is
  the right instinct; apply it to S-6 and S-7 too.
- **§5.3, one writer per state key**: it makes the graph safe to split across builders.

---

## 6. Verdict

**FAIL (revise before §7).** Blocking:

1. **B-1:** fix area ownership so no wave-1 area depends on a file owned by a later area or a sibling (`ToolDef` → A0;
   split `repos_ops` and `repos_working_copy` by writer; checkpointer prune out of A7).
2. **B-2:** shrink A0 to what two or more areas read; move single-consumer policy tables to their consumers; drop the
   19 repository Protocols.

Both are edits to DO-3 §3, §6 and §8, the area map and DO-4 §13; no architecture changes. Should items S-1…S-8 can land
in the same pass or as notes for the planners.

## 7. Questions for the orchestrator (Innocent's calls, not mine)

1. **Scope against the clock.** The internal target (Wed 06:00 CT) has passed and the interview is Thursday. Even at
   ~70 modules this is a large build. Does the full staff console (CON-10…CON-17), presence and scheduler job ship
   for the interview, or is there a cut line? That decides how many areas §7 should cut.
2. **Event delivery (S-5).** Poll-backed SSE (simpler, ~1 s staff-join delay) or push with an after-commit hook? Both
   satisfy SDQ-5 as decided.

---

## Re-review (2026-10-21)

**Read:** DO-3 revision 2 (§2.1, §3, §4, §6, §8, §10 C-10/C-11, §11), DO-4 `internal-components.md` (§2, §5 tools,
§13, §14), `api-con-mapping.md` CON-3, and the area map. Result: 80 modules plus 5 in the eval harness, in waves 0–3.

### B-1 (cross-wave and sibling dependencies): cleared, except one file

I traced every area's imports against the wave table:

- **Wave 1 depends on A0 only.** The tool types are in `domain/tools.py`. Each repo file is owned by the area that writes
  its tables. Customers and invoices sit with identity (A0/A4), and the checkpointer `prune`/`clear` and
  `restore_working_copy` are A0 callables. `BriefAssembler.attach_extraction` receives the check result rather than
  importing `checks.py`, and the lookup-log rule gives each row exactly one writer (dispatch for reads, the scheduling
  service for writes).
- **Wave 2:** A8 reaches the graph through an injected `run_graph`, so it doesn't wait on its sibling A7a.
- **Wave 3:** A7b, A7c and A7d meet only through §5.3's state keys and A7a's stubs.

**Remaining Blocking, RB-1: `SqliteUnitOfWork` in A0 must hold six repository classes that later waves create.**
DO-4 §13 gives the `UnitOfWork` port the attributes `spend` (A2), `identity` (A4), `booking` (A5), `cases` (A6),
`staff` (A9) and `ops` (A10a). `adapters/sqlite/db.py` (A0) must construct them. As written, A0 either imports
modules that don't exist in wave 0, or six wave-1/2 areas each edit A0's frozen `db.py` (and the port's type list in
`ports/runtime.py`) in parallel. Neither file is on the collision map. This is the same class of problem as B-1, and
the fix uses the stub pattern you already use for the nodes and `register_<area>()`:

- **A0 creates every `repos_<area>.py` in wave 0** as an empty class with its constructor
  (`class BookingRepos: def __init__(self, conn): ...`). It wires all seven into `SqliteUnitOfWork` and types the
  port's attributes against those names, imported under `TYPE_CHECKING` so the port does not import adapters at
  runtime.
- **Each area then owns its repo file's body.** `db.py` and `ports/runtime.py` stay frozen.
- **Add one collision-map row:** "`repos_*.py`: A0 stub, then the owning area".

### B-2 (A0 critical path): cleared

A0 is now 20 modules plus one DDL file and the fakes. Most of it is transcription of types DO-4 already sketches nearly
as code. The single-consumer policy tables, the repo Protocols and the case Protocols are gone. That is a reasonable
wave 0 for an hours-scale build.

**Could:** cut A0 into two parallel tickets so neither waits on the other:
- types, policy and `redact`;
- config, storage, checkpointer and container.

### The two departures

1. **`events` in A0: sound.** With polling there is no bus left. What remains is one table with two methods
   (`append`, `after`) and three writers (A6, A8, A9), so it belongs in the foundation under your own rule. The event
   kinds are already a closed list in CON-3, which means `StreamEvent` can be frozen in wave 0.
   - **Could:** name `StreamEvent`'s home module in DO-3 §3.
   - **Could:** run one process-wide poller (`events WHERE id > max_seen`, once a second) that fans out to subscribers
     in memory, rather than one query per open stream. That keeps the stream reads well inside the
     `CapacityLimiter(4)` as chats multiply.
2. **`privacy/redact.py` in A0: sound.** It is a pure function with four consumers across waves 1–2 (A1, A2, A8,
   A10a). Putting it anywhere else would recreate B-1. It is probably a `risk::security` ticket (test-first), so keep
   it in the first A0 ticket above. Only A1, A2, A8 and A10a wait on it; A3–A6 don't.

### Other notes (Could, none blocking)

- **The storage exception is now stated honestly in §2.1:** services call concrete repos through `tx` and never import
  `sqlite3`. Give `code-review-agent` that same wording so it doesn't flag every service for importing a repo type.
- **The §8 "Depends on" cell for A7a says "A0" only.** `load_context` reads the open case and promise (A6) and the
  identity status (A4). Both are earlier waves, so the wave is right; fix the cell so a planner doesn't schedule A7a
  into wave 1.
- **The S-1…S-8, C-1 and C-3 fixes match what I asked for.** The open/closed note in §4.5 is honest.

### Updated verdict

**FAIL, with one remaining Blocking item (RB-1), small.** A0 must create stubs for the per-area repo files and wire
them into `SqliteUnitOfWork`. Then add the `repos_*.py` row to the collision map. Once that edit is made, this design
is a **PASS** without another review round: B-2 and both departures are sound.

**Final verdict: PASS**
