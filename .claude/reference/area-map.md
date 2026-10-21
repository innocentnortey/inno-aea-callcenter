# Area map — inno-aea-callcenter

> Extracted from: [`docs/design/code-design.md`](../../docs/design/code-design.md) (DO-3, revision 2) and
> [`docs/design/contracts/`](../../docs/design/contracts/README.md) (DO-4).
> As of: 2026-10-21 (Stage 6, System track; DO-3 revised after the metz review and reconciled with the UX-3 contracts, awaiting Innocent).
> Authority: **DO-3 wins.** This file only routes; when it disagrees with DO-3, fix this file.

**Every code path below is planned.** No product code exists yet; the parked `src/meridian/` is read for shapes only
and is replaced by the planned tree (DO-3 §2.4). When a slice lands, change its row from *planned* to *actual* with
the commit, in the same change (`rules/context-maintenance.md`).

## How the code is layered (one line)

`web/` → `services/` and `agent/` → pure core (`domain/`, `policy/`, `gates/`, `checks.py`, `privacy/`) and `ports/`;
external adapters implement `ports/`; storage is a `UnitOfWork` port over concrete SQLite repositories; `web/container.py`
is the only place that wires concretes. Detail: DO-3 §2.

## Areas and waves

**Rule:** an area depends only on files it owns or on earlier waves; the area that writes a table owns its repository
and DDL file; a table with several writers lives in A0 (DO-3 §8).

| Wave | Area | Responsibility | Owns (all planned) | Status |
|---|---|---|---|---|
| 0 | **A0 Foundation** | Shared types, shared policy, ports, SQLite core, checkpointer, composition root | `src/meridian/config.py`, `domain/*` (incl. `tools.py`), `policy/{texts,limits}.py`, `privacy/redact.py`, `ports/{models,runtime}.py`, `adapters/sqlite/{db,migrate,repos_core}.py`, empty class stubs of `adapters/sqlite/repos_{spend,identity,booking,cases,staff,ops}.py` wired into `SqliteUnitOfWork`, `adapters/sqlite/schema/00_core.sql`, `adapters/checkpointer.py`, `web/container.py` (all `register_<area>()` stubs), `tests/fakes/` | planned |
| 1 | **A1 Gates** | Decide the turns that never reach a model | `gates/{rules,gate}.py` | planned |
| 1 | **A2 Models** | One adapter per provider; the role-typed gateway; the cost ledger | `adapters/models/{anthropic,openrouter_jev}.py`, `agent/gateway.py`, `services/ledger.py`, `adapters/sqlite/repos_spend.py`, `schema/20_spend.sql` | planned |
| 1 | **A3 Retrieval** | Build the KB index at image build; answer passage searches | `retrieval/{manifest,ingest}.py`, `adapters/retrieval_fastembed.py`, `agent/tools/knowledge.py` | planned |
| 1 | **A4 Identity** | One-time code; account reads | `services/identity.py`, `adapters/sqlite/repos_identity.py`, `schema/40_identity.sql`, `agent/tools/account.py` | planned |
| 1 | **A5 Scheduling** | Valid bookings, fee-free changes, fee-bearing change requests | `policy/booking.py`, `services/scheduling.py`, `adapters/sqlite/repos_booking.py`, `schema/50_booking.sql`, `agent/tools/scheduling.py` | planned |
| 1 | **A6 Cases and handoff** | Cases, promises, brief assembly, demo clock and staffing, scheduler job, reset | `policy/handoff.py`, `services/{cases,handoff,demo,scheduler,reset}.py`, `adapters/sqlite/repos_cases.py`, `schema/60_cases.sql` | planned |
| 1 | **A10a Ops** | Traces, health and watchdog, ops records | `adapters/tracing_langfuse.py`, `services/health.py`, `adapters/sqlite/repos_ops.py`, `schema/95_ops.sql` | planned |
| 1 | **A11 Eval harness** | Score the agent through its HTTP API; frozen per scored run | `eval/harness/`, `eval/cases/{dev,heldout,retrieval}/`, `eval/reports/` | planned |
| 2 | **A7a Graph spine** | Graph skeleton, routers, context, load and compose; stubs of the node groups | `agent/{graph,routers,context}.py`, `agent/nodes/{load_context,compose}.py`, stubs of `agent/nodes/{front,plan,act,reply}.py` | planned |
| 2 | **A8 Customer API** | Customer and demo routes (CON-1…CON-7, CON-8 read, CON-9), turn and session services, CON-3 SSE (polls `events`); serves `apps/web/dist` with fallback to `index.html` (planned) | `web/{app,middleware}.py`, `web/schemas/customer.py`, `web/routes/{chat,events,demo}.py`, `services/{turn,session}.py` | planned |
| 2 | **A9 Staff console** | Staff routes (CON-8 advance, CON-10…CON-17, CON-21 staff SSE), live takeover, staff sessions with `require_staff`, flags | `web/routes/staff.py`, `web/schemas/staff.py`, `services/{live_chat,staff}.py`, `adapters/sqlite/repos_staff.py`, `schema/90_staff.sql` | planned |
| 2 | **A12 Deploy** | Image build (index built here; Node build stage for `apps/web` with `docs/ux/03-structure/ui-contracts.openapi.yaml` in the build context), Railway config, reset command | `Dockerfile`, `railway.json`, `scripts/` | planned |
| 3 | **A7b Act** | Specialists, tool dispatch, escalation, handoff nodes | `agent/nodes/act.py`, `agent/specialists/{specs,runner}.py`, `agent/tools/dispatch.py`, `policy/escalation.py`, `agent/prompts/specialists.py` | planned |
| 3 | **A7c Reply** | Turn facts, responder, brief extraction, R-46 checks | `agent/nodes/reply.py`, `checks.py`, `agent/prompts/reply.py` | planned |
| 3 | **A7d Front** | Gate, safety, identity, planner and classifier nodes | `agent/nodes/{front,plan}.py`, `agent/prompts/routing.py` | planned |
| 3 | **A10b Reads** | Owner metrics, monitoring and eval pages (CON-18…CON-20); wave 3 because CON-18 needs A9's `require_staff` | `services/metrics_reader.py`, `web/routes/reads.py` | planned |

**Critical path:** A0 → A7a → A7b / A7c / A7d (A10b also in wave 3). **Shared files** and how collisions are avoided: DO-3 §8 collision map.
**Repo stubs:** each `repos_<area>.py` is an A0 stub after wave 0, then its body belongs to the owning area in the table
above (spend A2, identity A4, booking A5, cases A6, staff A9, ops A10a); `db.py` and `ports/runtime.py` stay frozen.
**Screens** are the React 19 + Vite + TypeScript + Tailwind + shadcn/ui app `apps/web/` (UX-4 prototype, **built 2026-10-21; UX-4 gate not yet signed**; it replaces the earlier server-rendered `web/templates` + `web/static` plan). A8 and A9 are API only (no templates, static files or Jinja pages); `jinja2` is therefore no longer needed and is **droppable** from `pyproject.toml` (not edited here). A8/A12 (AEA-49) serve the built `apps/web/dist` with a fallback to `index.html` (**planned**); A12's image needs a Node build stage with `docs/ux/03-structure/ui-contracts.openapi.yaml` in the build context (**planned**). Route files are split one per ticket (`routes/{chat,handoff,events,demo,auth}.py`, `routes/staff_{session,cases,live,clock}.py`), per [slice plan](../../docs/plans/slice-plan.md) §0 (AEA-08, 2026-10-21).

## Where to look

| Question | Go to |
|---|---|
| Which module does X, and what does it import? | DO-3 §3 (tree, area and wave per file), §4 (per module) |
| Which seams are interfaces, and which are deliberately not? | DO-3 §6 (S-1…S-24) |
| What the conversation state holds and who writes each key (R-45) | DO-3 §5 |
| Where requirement R-n lives | DO-3 §7 |
| Thread, deadline and admission sizing (60 s deadline, 30 in flight) | DO-3 §2.3 |
| What changed after the code-design review | DO-3 §11; `docs/design/reviews/2026-10-21-code-design-review.md` |
| Exact types and Protocol signatures | `docs/design/contracts/internal-components.md` |
| What each endpoint serves and the open requests to the UX session | `docs/design/contracts/api-con-mapping.md` (fields: `docs/ux/03-structure/ui-contracts.openapi.yaml`) |
| Test layout and which tests each role runs | DO-3 §9; `rules/build-loop-test-scope.md` |
| Architecture, failure behaviour, decided SDQs | `docs/design/system-design.md` (DO-1, DO-2) |
