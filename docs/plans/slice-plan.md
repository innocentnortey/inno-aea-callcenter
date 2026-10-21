# Slice plan (Stage 7a): inno-aea-callcenter — recut

**Status:** Recut 2026-10-21 on Opus 5.5 with the `to-tickets` skill (v2.0.0) at Innocent's instruction ("recreate the
slices … with max parallelization in mind … using our ticketing skill"). This replaces the first draft of the same day
(critical path 9, widest wave 12). The breakdown is shown to Innocent with the 7b–7c results before publishing.
**Skill §0:** `design_outputs.py check docs/prd/inno-aea-callcenter-interview.md --gate tickets` → *holds at the tickets gate*.
**Publishing surface:** GitLab project `innocentnortey/inno-aea-callcenter` (id 2318, public by R-42, `main` has a starter
README; no labels, no issues). Run `glab` as `env -u GITLAB_TOKEN glab … --hostname labs.gauntletai.com` (the shell's
`GITLAB_TOKEN` is stale; the glab config login works).
**Skip on record:** Stage 7 runs before UX-5 (checklist *Skips*). Nothing here touches `apps/web/**` or `docs/ux/**`.
**Sources:** DO-3 [code design](../design/code-design.md) §2–§9, DO-4 [internal components](../design/contracts/internal-components.md)
§0–§14 and [API ↔ CON](../design/contracts/api-con-mapping.md), DO-5 [evaluation plan](../design/evaluation-plan.md), DO-6
[observability contract](../design/observability-contract.md) (WF-1…WF-17, CAP-1…CAP-9), DO-7 [metrics](../design/key-metrics-registry.md),
[PRD](../prd/inno-aea-callcenter-prd.md) R-1…R-48, US-1…US-28, WP-1…WP-8.

## 0. The result in one screen

**62 tickets in 7 waves (0–6) (56 plus six journey tickets from Amendment 1). Lanes: 56 build-loop, 4 direct, 2 human, 0 spike. `risk::security`: 17** (added during 7b: AEA-43, because CON-6 returns verification codes; AEA-36, because code digits pass through the identity node and must never enter state; AEA-40, because it stores redacted customer text and admits untrusted input; AEA-02, because the typed settings hold every secret; AEA-24, because it carries the eval key and must keep held-out answer keys out of every log; AEA-12, because `parse_intake` keeps codes and card-like numbers out of stored text; AEA-29, because it stores follow-up contact details; AEA-17, 18, 20, because the adapters hold the provider keys and the gateway applies redaction before text leaves for a provider).
**Critical path: 7 tickets** (AEA-02 → 10 → 29 → 51 → 62 → 55 → 56). **Widest wave: wave 2, 26 tickets.**
Wave sizes: W0 9 · W1 16 · W2 26 · W3 6 · W4 3 · W5 1 · W6 1 (W4 corrected from 4 at the 2026-10-21 reconciliation: 54, 61, 62).

What makes it flat — three rules every ticket follows:

1. **Build against the signature, prove against the real thing at integration.** DO-4 §12–§14 fix every service, port and
   node signature. A ticket that *calls* another ticket's service receives it by constructor or FastAPI dependency
   (DO-3 S-20: "callers that need a service before it exists get an injected callable"), tests with a double that honours
   the DO-4 signature, and does not wait for it. The integration tickets (AEA-51, 52, 53) wire the real objects and prove
   every seam at the real entry point. A planner who finds a ticket needs *more* than the DO-4 signature of a sibling
   records `blocked-on AEA-NN` and the ticket moves one wave later; it never invents the sibling's behaviour.
2. **Shells and shared contracts land first.** Domain types and ports (02), every `register_<area>()` stub (01), every
   FastAPI dependency provider in `web/deps.py` including `require_staff` (23), and every table that several tickets write
   (10) exist before any consumer starts. After their wave they are frozen; a missing method is a small follow-up ticket.
3. **Routes are proven against the OpenAPI, not against the services.** Each route ticket owns one route file and one
   schema file, tests every operation, named error and cookie with dependency overrides, and changes nothing else.
   The service ticket's own `register_<area>()` hunk binds the real service.

**Three deliberate deviations from DO-3 §8**, recorded by AEA-08 in DO-3 and the area map:
- **AEA-10 writes every DDL file** (`00_core`, `20_spend`, `40_identity`, `50_booking`, `60_cases`, `90_staff`, `95_ops`;
  still one file per area, applied by number) from the DO-4/DO-6 field lists, and owns `repos_cases.py` whole. The owning
  tickets write only their repository method bodies. So no wave-2 ticket waits for a sibling's schema.
  For the cases repository specifically: DO-3's own rule: "a table written by
  several areas lives in A0"; in tickets, the cases tables are written by five (cases/handoff, demo/scheduler, reset,
  live chat, seed), so the storage they share lands first.
- **Cross-ticket reads and the reset's table clearing land in storage (AEA-10)** (found while writing the 7b specs). Wave-2
  tickets read tables a sibling in the same wave owns: AEA-29 re-reads invoices and appointments (owned by 27, 28), AEA-34
  reads a thread's identity state (27), AEA-31 clears identity, staff and case demo state (27, 44, 10). AEA-10 adds these
  as read-only (and reset-clear) methods on `repos_core` (`reads.invoice`, `reads.appointment`, `reads.identity_state`,
  `reset.clear_demo_tables(tx)`), over the DDL AEA-10 itself writes. Write methods stay with their owners. Which tables a reset clears is a needs-decision AEA-10 carries.
- Route and schema files are split one per ticket (`routes/{auth,chat,events,handoff,demo,staff_session,staff_cases,
  staff_live,staff_clock,reads}.py`, one `schemas/<route>.py` each). No Jinja templates or `web/static/`: the screens are
  UX-4's React app in `apps/web`; AEA-49 serves its build.

## 0a. Amendment 1 — journey protection (Riverside lesson, 2026-10-21)

**Status: proposed, not yet signed.** Innocent asked for this to be part of ticket planning "now, within our existing approval
gates". Nothing is published, so it goes to him with the rest of 7a at the breakdown review. Rule: `.claude/rules/integrated-journeys.md`.

**Why.** Riverside's tests passed while real journeys failed (prompt outputs vs schemas, frontend vs backend state, guards that
broke navigation outside mock mode, API responses missing fields the UI expected), because components were tested against fakes and
reviews read code without running the journeys.

**What changes.**
- **Five new tickets** (above): AEA-57 harness + J-1 (wave 2), AEA-59 contract boundary (wave 2), AEA-58 browser journeys (wave 3,
  needs UX-4 signed), AEA-60 prompt ↔ consumer checks (wave 3), AEA-61 live smoke (wave 4, `gate::paid`).
- **Every build-loop ticket gets one `[journey]` acceptance criterion**: it extends or runs the journeys in the map below that its
  code touches, in `tests/journeys/j<N>/test_aea_<NN>.py` (one file per ticket, so tickets in a wave never edit the same file), and
  the criterion cites the journey ids. A bug fix first reproduces the failure as a journey step, and when it changes a guard also
  asserts the intended success path. The conventions paragraph gets one sentence to say so.
- **Integration tickets AEA-51 / 52** run on the harness (AEA-57), not on fakes at the TestClient, and wait for it. AEA-55 also waits for AEA-58.
- **Merge gate:** affected journeys at ticket merge, all journeys at wave merge and before deploy (`build-loop-test-scope.md`, AEA addition).
  Reviewers and seam audits execute the relevant journeys. After each wave reaches the integrated branch, a focused browser walkthrough
  is recorded (evidence table in the rule).
- **Verification levels** are always stated: `mock-tested`, `integrated with a scripted model`, `verified with live models`.

**Journey map** (J-n; a ticket's `[journey]` AC names the ones it touches):

| J | Journey (assert what the user sees AND what is persisted) | First landed by | Extended by |
|---|---|---|---|
| J-1 | Login → start session → one turn → refresh/resume the same thread; guards redirect when signed out | AEA-57 | 23, 40, 58 |
| J-2 | Membership, billing and warranty questions: retrieval → grounded answer with source; stale twin never cited (WP-1, WP-2) | AEA-51 | 33, 35, 38 |
| J-3 | Booking → confirmation → stored appointment → a follow-up turn ("yes, please") that remembers the completed action; DB re-read in the same transaction (WP-3, WP-4F) | AEA-51 | 28, 34, 39; *proposed:* 27, 43 |
| J-4 | Fee-bearing change (inside 24 h): no write, staff request created, honest promise (WP-4) | AEA-51 | 28, 39 |
| J-5 | Safety: CO alarm and danger path give the approved instruction first, P0/P1 case (WP-5, DANGER, NODANGER) | AEA-51 | 36, 37 |
| J-6 | Escalation → case created → appears in the staff queue → opened with the eight-heading handoff brief and promise (WP-7, WP-8) | AEA-52 | 29, 45; *proposed:* 30, 47 |
| J-7 | "Talk to a person" and live takeover: staff joins the same chat, relayed message visible both ways, hand back | AEA-52 | 42, 46; *proposed:* 29, 30, 41 |
| J-8 | Role switch and session: customer ↔ staff roles, refresh, signed-out and expired session | AEA-52 | 44, 58; *proposed:* 31, 43 |
| J-9 | Empty, missing-data, timeout, busy, degraded and rate-limited states | AEA-51 | 40, 41, 58; *proposed:* 26 |
| J-10 | Read pages (owner metrics, monitoring, latest eval) show stored values with their labels | AEA-53 | 48; *proposed:* 32 |

*Proposed* ids are additions from the UX ↔ backend join (`docs/plans/ux-join/`; list in
`docs/plans/ux-join/backend-amendments.md` §3), carried by those tickets' `[journey]` criteria (amendment pass of 2026-10-21). The join
package's unconditional amendments go into the tickets in that pass; its conditional ones (marked *If Innocent picks …*) wait on his answers in
`docs/plans/ux-join/decisions-for-innocent.md`. No ticket, wave or count in this plan changed.

**Decisions taken while writing the journey specs** (engineering; the specs carry them):
- **J-1 runs in two stages.** AEA-57's harness runs the login, guard and resume steps from wave 2; the turn steps run when AEA-51
  lands the graph, and until then are reported as *blocked*, never as passed.
- **AEA-59 has no dependency on the harness.** Each route ticket adds its own operations to `tests/contract/cases/<route>.py`
  (one file per route ticket); AEA-51 switches on the strict mode in which an operationId with no case fails the suite.
  AEA-23's `openapi_check` loads the YAML so that timestamps stay strings and `yes`/`ON`/`OFF` stay strings (a plain `safe_load`
  turns 371 example timestamps into datetimes).
- **The scripted model reaches the container through one test-only argument** on the app factory (`create_app(settings,
  overrides=ContainerOverrides(...))`, owned by AEA-23, used by AEA-57 and AEA-51); nothing in production reads it.
- **AEA-62 (new, wave 4)** puts J-2, J-3, J-6 and J-8 in a browser, because they need the integrated graph. AEA-58 (wave 3) does
  J-1 in a browser. The other journeys (J-4, 5, 7, 9, 10) are covered at API level and by the per-wave browser walkthrough.
- **The live smoke set is AEA-61** (not AEA-60); each paid run needs Innocent to state the day's spend so far, because the app's
  cap only sees its throwaway database.
- **Open for Innocent / the UX session** (`docs/plans/ux-join/`): WEB-1; `CaseDetail.events.last_event_id` in the OpenAPI; whether
  a chat resumes after signing in again (SCR-1 says yes, `owned_thread` returns 404 for an earlier session's thread).

**Where the two tracks connect** (details and the UX session's deliverables: `docs/plans/ux-join/`): UX-4 signed → AEA-49 serves
`dist` → AEA-58 runs the browser journeys → UX-5 reruns its suite against the real backend → AEA-55. The UX session must provide:
a production build command and output path, stable selectors for each state a journey asserts, types generated from the signed
OpenAPI with a drift check, mock fixtures that pass the same contract checks, a real-backend mode (proxy/base URL, cookie credentials)
with no mock-only code in `dist`, and its Playwright configuration to reuse.

## 1. Tickets

Lane: **B** build-loop · **D** direct · **H** human. **Sec** = `risk::security`. Blockers are ticket numbers.
"Calls (injected)" names the siblings a ticket uses through a DO-4 signature without waiting for them.

### Wave 0 — nothing outside wave 0 blocks them (02 and 05 carry in-wave merge-order edges: 04 → 02 → 05)

| ID | Ticket | Lane | Sec | Blocked by | Owns | Links |
|---|---|---|---|---|---|---|
| AEA-01 | foundation: scaffold, limits, composition-root stubs | B | | — | `pyproject.toml`/`uv.lock` (**every** dependency the design names), package skeleton (imports nothing from other tickets), `policy/limits.py`, `web/container.py` with one `register_<area>()` stub per ticket that registers anything, `tests/conftest.py`, the `tests/journeys/` skeleton and `journey` pytest marker, the one command the merge gate runs for affected journeys, lint/type config | R-40, R-41; DO-3 §2.1, §2.3 |
| AEA-02 | foundation: domain types, ports, typed settings, repository shells | B | **Sec** | 04 + *in wave 0, merge order* | `domain/*` (9 files, incl. `TurnContext` in `domain/turn.py` so services never import `agent/`), `ports/{models,runtime}.py`, exactly DO-4 §0–§14; `config.py` (`Settings`: typed per-role model maps keyed by `Role`, rejected on mismatch, DO-3 S-2; every secret a `SecretStr`); the seven `adapters/sqlite/repos_*.py` as empty classes with constructors so `UnitOfWork`'s type imports resolve | R-45; DO-3 §4.1–4.2, §5 |
| AEA-03 | foundation: every fixed customer sentence | B | | — | `policy/texts.py`, word for word from SCREEN_SPECS copy notes, with a fixture test (UXR-18, UXR-26, C-13) | US-1, 3, 25; R-1, R-5, R-26 |
| AEA-04 | privacy: one redaction function, five profiles | B | **Sec** | — | `privacy/redact.py` (STORE, SONNET, JEV, TRACE, LOG) | R-13, R-16, R-36; CAP-1 |
| AEA-05 | gates: typo-tolerant word rules | B | | 02 + *in wave 0, merge order* | `gates/rules.py` `match_rules` (safety, burning, danger, person, policy) and its own `RuleMatches` type; pure, no imports (DO-3 §4.1 "depends on: none") | US-2…5; R-5, R-7, R-8, R-47; HP-2; WP-5, 6 |
| AEA-06 | eval: dev, sealed held-out and retrieval cases from the transcripts | B | | — | `eval/cases/{dev,heldout,retrieval}/`; EVQ-1 = A split; held-out key hash; synthetic cases labelled | R-12, R-38; E-2…E-5; WP-1…8 |
| AEA-07 | docs: technical documentation | D | | — | Discovery (drivers, method, scope), chunking and retrieval reasoning, escalation design, from the decision records | R-43; D-4 |
| AEA-08 | docs: reconcile DO-3, DO-4 and the area map with this plan | D | | — | The deviations in §0; stale names in `api-con-mapping.md` and DO-4 (old CON-10 operationIds, cookie names, `STAFF_AUTH_REQUIRED`, `build_index.py`, `domain/base.py`) brought to the OpenAPI, which wins; templates/static removed (partly applied 2026-10-21, uncommitted) | rule `context-maintenance` |
| AEA-09 | human: Railway project, variables, Langfuse route | H | | — | Dedicated Railway project (R-40); demo login pair, model keys, session secret as variables; Innocent's yes on the ingestion-only Langfuse route (R-36, SDQ-3); `gate::human` | R-36, R-40, R-48 |

### Wave 1 — needs wave-0 shells only

| ID | Ticket | Lane | Sec | Blocked by | Owns | Calls (injected) | Links |
|---|---|---|---|---|---|---|---|
| AEA-10 | storage: SQLite core, shared case tables, migrations, checkpointer | B | | 01, 02 | `db.py`, `migrate.py` (first-boot copy, `restore_working_copy`), **every `schema/*.sql`**, `repos_core.py` (incl. the cross-ticket reads, reset clearing in §0, and `settled_for(thread_id)`, the one builder of `Settled` from the rows that both `load_context` (34) and the reply node's `facts` step (38) call), **`repos_cases.py`**, `SqliteUnitOfWork` constructing all seven repositories (shells from 02), `checkpointer.py` (prune keep=2, clear), `temp_sqlite()` in `tests/fixtures/sqlite.py` | — | R-19, R-33, R-45; WF-16 |
| AEA-11 | test support: scripted fakes | B | | 01, 02 | `tests/fakes/` (three model fakes, FixedClock, FakeIndex, InMemoryTraceSink) | — | DO-3 §9 |
| AEA-12 | gates: intake parsing and the gate decision | B | **Sec** | 01, 02, 04, 05 | `gates/gate.py` `parse_intake` (text, choice, code, form) + `decide_gate` | — | US-2…5, 8; R-2, R-5, R-7, R-15, R-31; CAP-2 |
| AEA-13 | policy: booking rules | B | | 02, 03 | `policy/booking.py` (zones incl. 78620/Manor, 24-hour rule, fee by tier) | — | US-10…13; R-18, R-20…23; HP-3; WP-3, 4 |
| AEA-14 | policy: promises, priorities, escalation decision | B | | 02, 03 | `policy/handoff.py` (R-26 table, due rule, P0–P4, D4 rows), `policy/escalation.py` | — | US-14; R-21, R-22, R-24…26; WP-4, 7, 8; M-10 |
| AEA-15 | checks: completion and fact checks (R-46) | B | | 02 | `checks.py` | — | US-16; R-46; HP-4; M-8 |
| AEA-16 | retrieval: manifest and ingestion of the 17 KB files | B | | 02 | `retrieval/{manifest,ingest}.py` (MD, TXT, fee PDF, price-book CSV rows, holiday file; exclusions; staff-only notes) | — | US-6, 7; R-9, R-10; WF-14; CAP-9 |
| AEA-17 | models: Anthropic adapter | B | **Sec** | 02 | `adapters/models/anthropic.py` + `tests/contract/test_anthropic_adapter.py` (fixtures, no paid call) | — | R-41; HP-1; DO-3 §4.3 |
| AEA-18 | models: Jev adapter | B | **Sec** | 02 | `adapters/models/openrouter_jev.py` + `tests/contract/test_jev_adapter.py` (error inside a 200; `data_collection: deny`) | — | HP-1; SP-1 mix B |
| AEA-19 | tracing: Langfuse sink, null sink, project-key check | B | **Sec** | 02, 04 | `adapters/tracing_langfuse.py` (mask hook, bounded queue, export off + alert on another project's keys) | — | R-36; M-29; WF-1 (export per turn), WF-13 (export on/off stamped at deploy), WF-17; CAP-9 |
| AEA-20 | models: the gateway | B | **Sec** | 01, 02, 04 | `agent/gateway.py` (role maps, the role → redaction-profile map, timeout = min(cap, time left), ≤ 2 attempts, span) | ledger `record`, `models_disabled`, `trip_provider_cap` (26) | R-41; HP-1; M-23…26 |
| AEA-21 | graph: spine, routers, context, compose | B | | 02, 03 | `agent/{graph,routers,context}.py` (`GraphDeps` fields typed by DO-4 §14), `nodes/compose.py`, stubs of `nodes/{load_context,front,plan,act,reply}.py`; recursion limit 25; the two-node parallel timing test (DO-3 §2.2) | every node's services | US-17; R-45; HP-1; DO-3 §5 |
| AEA-22 | tools: dispatch, guard, lookup log | B | **Sec** | 02, 04 | `agent/tools/dispatch.py` (schemas from `ToolDef`, `requires_verified` guard, every branch, lookup-log entries) | executors by name (27, 28, 33) | R-14, R-29; CAP-1 |
| AEA-23 | web: app, middleware, demo login, dependency providers | B | **Sec** | 01, 02, 04 | `web/logging.py` (structured logs through the LOG redaction profile), `web/app.py` (lifespan, 422 → 400 handler, async `/healthz` on the heartbeat), `web/middleware.py` (request_id, rate limits per session/IP, eval-key tag, login gate on every route but login and `/healthz`), `routes/auth.py` + `schemas/auth.py` (CON-22), **`web/deps.py`** (one provider per service incl. `require_staff(roles)`), `tests/api/openapi_check.py` (the one response validator against `ui-contracts.openapi.yaml` every route ticket uses) | heartbeat (32), staff sessions (44) | US-26, 28; R-41, R-48; WF-17 |
| AEA-24 | eval: harness | B | **Sec** | 01 | `eval/harness/*` (runner, scoring, judge, report, load, experiment record; HTTP only; frozen by digest; DB-copy check) | — | R-12, R-38, R-39; E-1…E-8; WF-8…10, 12; CAP-7, 8 |
| AEA-25 | docs: README (how to run) | D | | 01 | Run instructions and structure; the containment-number line waits for Stage 9 | — | R-43; D-3 |

### Wave 2 — services, executors, nodes and routes, all in parallel

| ID | Ticket | Lane | Sec | Blocked by | Owns | Calls (injected) | Links |
|---|---|---|---|---|---|---|---|
| AEA-26 | spend: ledger and spend guard | B | | 10 | `repos_spend` body, `services/ledger.py` (Chicago day, $30/day, provider-cap circuit) | — | R-41; M-25, M-26 |
| AEA-27 | identity: one-time code, inbox, account reads | B | **Sec** | 04, 10, 13 | `repos_identity` body, `services/identity.py` (HMAC code, 10 min, 3 tries, ≤ 3 sends, identical `NotVerified`), `agent/tools/account.py` | — | US-8, 9; R-15…17; WP-2; CAP-1 |
| AEA-28 | scheduling: windows, writes, change requests | B | | 10, 13 | `repos_booking` body, `services/scheduling.py` (one tx: re-read + write + action + lookup row), `agent/tools/scheduling.py` | — | US-10…13; R-18…23; HP-3; WP-3, 4; E-7; M-9 |
| AEA-29 | cases and handoff: case service, handoff service, brief | B | **Sec** | 10, 11, 14, 16 | `services/cases.py` (all DO-4 §13 methods), `services/handoff.py` (`HandoffService`, `BriefAssembler`; case + promise + action + event in one tx, idempotent) | demo clock, staffing (30) | US-2, 14, 18…22; R-6, R-25…29, R-33, R-34; WP-7, 8; WF-2; M-10…12 |
| AEA-30 | demo: clock, staffing, scheduler job | B | | 10, 11, 14 | `services/demo.py` (DemoClock, staffing, advance), `services/scheduler.py` (tick: due-soon, overdue, stuck, unowned; marks idle conversations `abandoned` for M-18; daily prune) | `CaseService` (29) | US-25; R-3, R-30, R-33; WF-5, 7; CAP-5; M-13, M-27 |
| AEA-31 | reset: all-or-nothing reset and demo seed | B | | 10, 14, 23 | `services/reset.py`, the demo seed loader | restore/clear callables (10) | R-19, R-33; WF-15, 16; CAP-9 |
| AEA-32 | ops: health events, heartbeat, watchdog, alerts | B | | 10, 23 | `repos_ops` body, `services/health.py` | — | US-27; R-35; WF-17; M-28; CAP-9 |
| AEA-33 | retrieval: vector index and the knowledge tool | B | | 16 | `adapters/retrieval_fastembed.py` (relevance floor, readiness), `agent/tools/knowledge.py` | — | US-6, 7; R-11, R-13; E-2; M-6, M-7; WP-1 |
| AEA-34 | graph: load-context node | B | | 10, 21 | `nodes/load_context.py` (settled, controller, identity, window from the DB) | — | US-17; R-45 |
| AEA-35 | specialists: specs, braked tool loop, wording | B |  | 11, 20, 22 | `agent/specialists/{specs,runner}.py`, `prompts/specialists.py` (brakes; quick checks R-44) | executors (27, 28, 33) | US-6, 9…13; R-13, R-41, R-44; HP-3 |
| AEA-36 | graph: front node (gates, safety, identity) | B | **Sec** | 11, 12, 14, 21 | `nodes/front.py` | identity (27), handoff (29) | US-2…5, 8; R-5…7, R-15; HP-2; WP-5, 6; CAP-2 |
| AEA-37 | graph: plan node (planner, danger classifier, join) | B |  | 11, 12, 21 | `nodes/plan.py`, `prompts/routing.py` (raise-only classifier; `classifier_fallback`) | gateway (20) | US-5; R-8, R-47; HP-2; WP-3; M-16, M-17 |
| AEA-38 | graph: reply node (facts, responder, brief, checks) | B |  | 10, 11, 15, 21 | `nodes/reply.py`, `prompts/reply.py` | gateway (20), brief assembler (29) | US-4, 16, 17; R-4, R-28, R-45, R-46; HP-1, 4; WP-1, 2 |
| AEA-39 | graph: act node (fan-out, escalation, handoff) | B |  | 11, 14, 21 | `nodes/act.py` | specialist runner (35), handoff (29), scheduling (28) | US-12, 14; R-21, R-22, R-24; WP-4, 7, 8; HP-3 |
| AEA-40 | customer API: sessions and turns (CON-1, CON-2) | B | **Sec** | 03, 10, 11, 12, 23 | `routes/chat.py`, `schemas/chat.py`, `services/{session,turn}.py` (admission 30, idempotent `turn_id`, 60 s deadline, restart sweep, the chat RATE_LIMITED notice) | `run_graph` (51), spend guard (26), demo clock (30) | US-1, 26; R-1, R-3, R-41; WF-1; CAP-1 |
| AEA-41 | customer API: chat event stream (CON-3) | B |  | 10, 11, 23 | `routes/events.py`, `schemas/events.py` (event payload models) (poll `events`, replay by `Last-Event-ID`, 15 s heartbeat, `CapacityLimiter(4)`) | — | US-15; WF-1, WF-4 (DO-6 lists the CON-3 stream under the takeover workflow) |
| AEA-42 | customer API: person request and follow-up (CON-4, CON-5) | B | | 23 | `routes/handoff.py`, `schemas/handoff.py` (`already_open`) | handoff, cases (29) | US-2, 14; R-2, R-27; WF-2; CAP-3 |
| AEA-43 | customer API: inbox, staffing, clock read, reset (CON-6…CON-9) | B | **Sec** | 23 | `routes/demo.py`, `schemas/demo.py` (inbox excluded from body logging) | identity (27), demo (30), reset (31) | US-8, 25; R-30, R-34; WF-3, 5, 15 |
| AEA-44 | staff: sessions, role switch, flags (CON-10) | B | **Sec** | 10, 23 | `repos_staff` body, `services/staff.py` (implements `require_staff`), `routes/staff_session.py`, `schemas/staff_session.py` | — | US-28; R-32, R-37, R-48; WF-4 |
| AEA-45 | staff API: queue, case, actions, contact log, flags, oversight (CON-11…13, 15…17) | B | | 23 | `routes/staff_cases.py`, `schemas/staff_cases.py` (`expected_version`; owner gets no actions) | cases (29), flags (44) | US-18…23; R-32, R-33, R-37; WF-4; CAP-4 |
| AEA-46 | staff API: live takeover and case stream (CON-14, CON-21) | B | | 10, 23 | `services/live_chat.py`, `routes/staff_live.py`, `schemas/staff_live.py` | cases (29) | US-15, 20; R-31; WF-4; CAP-4 |
| AEA-47 | staff API: advance the demo clock (CON-8) | B | | 23 | `routes/staff_clock.py`, `schemas/staff_clock.py` (supervisor only) | demo (30) | US-22, 25; R-3, R-33; WF-5 |
| AEA-48 | reads API: owner metrics, monitoring, latest eval (CON-18…20) | B | | 23 | `routes/reads.py`, `schemas/reads.py` | metrics reader (53) | US-24, 27; R-35, R-39; WF-6 |
| AEA-49 | web: serve the built `apps/web/dist` | B | | 23 + **UX-4 signed** | `web/frontend.py` + its `register_frontend()` hunk: static mount, SPA fallback, which assets are public before login; `gate::ux4` | — | R-48 |
| AEA-57 | journey harness: real server + disposable DB + scripted model | B |  | 02, 10, 11, 23 | `tests/journeys/support/` (fixtures: build the real app from `web/container.py` on a disposable copy of the issued DB via `temp_sqlite`, a deterministic scripted model adapter, a server-in-thread/ephemeral-port launcher, a login helper, a DB-state reader for persisted-effect assertions, evidence-record writer), journey **J-1** (login → session → one turn → refresh/resume) over HTTP with auth, guards, validation and persistence on; later tickets add `tests/journeys/j<N>/test_aea_<NN>.py` and never edit `support/` | — | Amendment 1; R-48, R-41; WF-1, WF-18 |
| AEA-59 | contract boundary: server and mock responses vs the signed OpenAPI | B |  | 02, 23 | `tests/contract/test_openapi_server.py` (every operationId driven through the real app, response validated with AEA-23's `openapi_check`; fails when an operationId has no case), `tests/contract/test_openapi_fixtures.py` (every Prism example and a generated edge set: omitted optionals, nulls, empty lists, error bodies), `tests/contract/test_types_gen_drift.py` (regenerates `apps/web/src/api/types.gen.ts` into a temp dir with the pinned `openapi-typescript` and fails on diff; reads, never writes, `apps/web`) | — | Amendment 1; CON-1…22; WF-1…6, 18 |

### Waves 3–5 — integration, deploy

| ID | Wave | Ticket | Lane | Sec | Blocked by | Owns / proves | Links |
|---|---|---|---|---|---|---|---|
| AEA-50 | 3 | deploy: Dockerfile, Railway config, scripts | B | **Sec** | 16, 31, 32, 33, 19, 23 | `Dockerfile` (index built here; a stage that runs `apps/web`'s own build when present, reading only), `railway.json` (restart policy, 65 s proxy check), `scripts/` (reset command); no secret in the image; CAP-9 | R-40; WF-13…17 |
| AEA-51 | 3 | integration A: the customer path end to end | B |  | 17, 18, 20, 26…29, 33…40, 42, 43, 11, 19, 30, 44, 46, 57, 59 | Completes `register_graph` (real services, `SqliteSaver`) and binds `run_graph`; `tests/contract/test_model_ports_contract.py` across both adapters; WP-1…WP-8, WP-4F, DANGER, NODANGER through the HTTP API with fake models; CAP-1, CAP-2, CAP-3; the relayed `to_staff` turn through the real graph (moved from 52); seams S-1…S-24 that cross tickets | WF-1…3; E-1; US-1…17 |
| AEA-52 | 3 | integration B: staff and demo end to end | B |  | 29, 30, 40, 41, 44…47, 31, 32, 43, 57, 59 | Real services behind CON-7…17, 21; claim, live reply, hand back, flag; clock past a due time; CAP-4, CAP-5 | WF-4, 5, 7 |
| AEA-53 | 3 | reads: metrics reader | B |  | 26, 29, 32, 48, 44 | `services/metrics_reader.py` (stored counts, never recomputed); CAP-6 through CON-18…20 | US-24, 27; R-35, R-38, R-39; WF-6; M-1…M-29 |
| AEA-54 | 4 | docs: deployment guide | D | | 50 | Railway steps, variables, restart behaviour, reset | R-43; D-5 |
| AEA-55 | 5 | UI integration: `apps/web` against the real backend | B |  | 49, 51, 52, 53, 58, 62 + **UX-5 signed** | Prism proxy mode; the UX-5 suite reruns; `gate::ux5` | checklist §8 |
| AEA-56 | 6 | human: deploy to Railway and smoke test | H |  | 09, 50, 55, 61, 62 | Full suite green first; public URL; smoke with the demo login; `gate::live` | R-40; D-1 |
| AEA-58 | 3 | browser journeys: Playwright against the production build | B |  | 40, 49, 57 + **UX-4 signed** | `tests/journeys/browser/` (pytest-playwright, one runner for backend and browser journeys): serves `apps/web/dist` through the real app (AEA-49) on a disposable DB; J-1 in a browser (login, guard redirect, refresh/resume); later tickets add their journeys; `gate::ux4`. Selectors come from the UX session's contract (`docs/plans/ux-join/`) | Amendment 1; R-48; WF-18, WF-19 |
| AEA-60 | 3 | prompt ↔ consumer checks | B |  | 20, 22, 35, 37, 38, 39, 17, 18, 27, 28, 33, 57 | `tests/contract/test_prompts_vs_consumers.py`: render every prompt the graph sends (routing, specialists, reply) with fake inputs and check the ids, enums, tool names, arguments and output schemas offered against the parsers and `ToolDef`s that consume them; malformed and unsupported outputs through each consumer; fails when a prompt offers a value no consumer accepts | Amendment 1; HP-1, HP-4; R-46, R-47 |
| AEA-61 | 4 | live-model smoke set through the real app | B |  | 51, 57, 60, 06, 50 | `tests/live/` marked `live` (never in the default run): a small development-case set (one per selected driver: membership, billing, warranty; one booking with follow-up; one safety; one fee-bearing change) through the real server with real models; records failures, versions, traces, cost against the $30/day cap; dev split only, sealed holdout untouched; `gate::paid`. Proves limited compatibility only | Amendment 1; R-41, R-38; M-23…26 |
| AEA-62 | 4 | browser journeys for integrated capabilities | B |  | 58, 51, 52, 29, 40, 57 | `tests/journeys/browser/` browser legs of J-2 (membership, billing, warranty with source), J-3 (booking → confirmation → follow-up memory), J-6 (escalation → staff list → case with brief), J-8 (role switch, refresh/resume): production build, real server, disposable DB, scripted model, real auth and guards; the rest of the map (J-4, 5, 7, 9, 10) is covered at API level by its tickets and by each wave's recorded browser walkthrough | Amendment 1; US-6…14, 18…20, 28 |

**Not tickets:** Stage 9 (E-1…E-8 runs, error analysis, XP-N, README number, test results, load re-measure) and Stage 10
(demo video, submission).

## 2. Parallelism audit (skill §2a)

**Critical path (7 waves):** AEA-02 → 10 → 29 → 51 → 62 → 55 → 56; paths of equal length run through any wave-2 ticket
into 51 or 52, and through 23 → 49 → 58 → 62. Counting the two in-wave merge-order edges as steps, the longest chain is
9 tickets (AEA-04 → 02 → 05 → 12 → 40 → 58 → 62 → 55 → 56), but 04, 02 and 05 build in parallel, so the wave count
stays 7. **Widest wave:** W2, 26 tickets (25 build-loop + 1 gated on UX-4). Recomputed 2026-10-21 after the ticket
amendment pass (edges below); no wave changed.

**Edges added at the 2026-10-21 reconciliation** (each named as a blocker or a named import in the amended ticket; every
one sits below the blocked ticket's wave, except the two wave-0 merge-order edges):

| Edge added | Why (ticket's *Blocked by*) |
|---|---|
| AEA-04 → 02, AEA-02 → 05 (in wave 0) | `RoleSpec.redaction` is `RedactionProfile` (04); `rules.py` imports `RuleMatches`, `SafetyKind` from `domain/turn.py` (02). Build in parallel, merge **04 → 02 → 05** |
| AEA-01 → 11, 12 | The `journey` marker and affected-journey command their journey criteria run |
| AEA-03 → 13 | `render` with `amount`, `format_usd`, the booking fee texts |
| AEA-13 → 27 | `SCHEDULE_FEES`, `MEMBER_ALLOWANCE_ROWS` |
| AEA-16 → 29; AEA-11 → 29, 30 | The `StaffGuidance` type; `FixedClock` in `tests/fakes/clock.py` |
| AEA-14 → 30, 31 | `is_business_day`, `DUE_SOON_WINDOW`, `UNOWNED_AFTER`; `promise_for` |
| AEA-23 → 31, 32 | `ResetGate`, `ResetAlreadyRunning`, `owned_thread`; AC-12 drives the app |
| AEA-40 → 52, 58, 62 | Full thread history and the relay payload (52); greeting after reload (58, 62) |
| AEA-29, 57 → 62 | Display values and the `source_id` scheme; AEA-57 AC-17's wall-clock control |

**Not edges** (named in tickets for evidence only): AEA-57, 59, 51, 52, 53 where a ticket's `[journey]` or strict-contract
record lists them as *Blocked by* for its integrated level (`integrated-journeys.md` §4); same-wave collaborators used
through an injected double (e.g. 28 for 39, 29 for 46, 57 for 59).

**Edges removed** (each failed "does the blocked ticket need the blocker's *result*?"):

| Edge removed (first draft → recut) | Why |
|---|---|
| sqlite core → graph spine | Spine compiles with LangGraph's in-memory saver in its tests; only `load_context` (34) reads the DB, so it is its own ticket |
| model adapters, ledger, tracing → gateway | The gateway calls the `ChoiceModel`/`StructuredModel`/`ToolCallingModel` and `TraceSink` ports (02) and an injected ledger `record`; adapters are wired at 51 |
| gateway, dispatch, services → every node | Nodes receive services through `GraphDeps` (21), typed by DO-4 §14; doubles in tests |
| services → every route | Routes resolve services through `web/deps.py` (23); tests override the providers |
| staff sessions → staff routes | `require_staff` is declared in `web/deps.py` (23); 44 implements it |
| executors → dispatch | Dispatch looks executors up by `ToolDef` name; the three executors register their own |
| case service → handoff service | One ticket (29): `open_case(tx, …)` is HandoffService's own transaction, so they are one invariant |
| A6 persistence → demo, scheduler, reset, live chat | `repos_cases` and `60_cases.sql` are in storage (10) |
| traffic → reads | CON-18…20 are proven on seeded rows |
| deploy → docs | Technical docs in W0, README in W1, deployment guide after the deploy files; only measured numbers wait for Stage 9 |
| AEA-02, AEA-04 → AEA-01, AEA-05 (found in 7b) | Settings moved into 02 (it needs `Role`); the role → redaction map moved to the gateway (20, already after 04). *Superseded in part:* `RuleMatches` moved to `domain/turn.py` (R-G-1), so 02 → 05 returns as an in-wave merge-order edge, as does 04 → 02 (edges added, above). No edge to 01 |
| Wave-0 merge order (found at the residual pass) | AEA-02 needs `RedactionProfile` from AEA-04 (via `RoleSpec.redaction`) and AEA-05 needs AEA-02's domain types. The three still build in parallel; they merge **AEA-04 → AEA-02 → AEA-05**, now written in the 02 and 05 blocker cells. No wave changes |
| AEA-06 → AEA-24 | The harness is built and tested on its own fixture cases in the DO-5 case format; 06's real cases are evidence data, not a dependency (skill §2a) |
| UX track → anything but 49, 55 | The API depends only on the signed contracts |
| A7a spine → `policy/escalation.py`, `checks.py` | DO-3 §8 puts them in wave 3 with their nodes; both are pure functions over domain types (DO-3 §4.1), so they move to wave 1 (AEA-14, AEA-15). Ownership is unchanged |

**Human gates:** AEA-09 in wave 0; only its *use* (AEA-56) waits. The GitLab project was created by Innocent on 2026-10-21.

**Large tickets on the critical path:** AEA-10 (storage incl. the shared case tables) and AEA-29 (cases + handoff). Both
are cohesive invariants; their planners may split implementation steps inside the ticket but not the ticket.

**Execution note:** 26 ready tickets is 52 agents (planner + implementer). Run wave 2 in two batches of ~12 if CPU or
disk (`df -h /home`, 89% on 2026-10-21) is tight; the waves do not change.

## 3. Collision map

| Shared file or surface | Touched by | Rule |
|---|---|---|
| `pyproject.toml`, `uv.lock` | 01 | 01 lists every dependency the design names. A later addition is one line plus a regenerated lock at merge; that merge runs the full suite |
| `web/container.py` | 01 creates one `register_<x>()` stub per registering ticket; each of 10, 17–20, 22, 23, 26–33, 40–48, 53 fills **only its own function**; 51 completes `register_graph` | No ticket edits another's hunk; routers are included from their own hunk, so `web/app.py` never changes after 23 |
| `web/deps.py` | 23 only | Declares every provider; a new provider is a follow-up on 23 |
| `domain/*`, `ports/*`, `config.py`, `policy/texts.py`, `policy/limits.py`, `adapters/sqlite/{db,repos_core,repos_cases}.py`, `migrate.py` | owners 02, 02, 02, 03, 01, 10 | Frozen after their wave; a missing method or sentence is a small ticket merged before its dependants |
| `adapters/sqlite/repos_*.py` | 02 creates the empty shells; 10 fills `repos_core`, `repos_cases`; bodies: 26, 27, 28, 44, 32 | One owner per file after wave 1 |
| `adapters/sqlite/schema/*.sql` | 10 only | A column a wave-2 ticket finds missing is a small follow-up on 10, merged first |
| `web/routes/*.py`, `web/schemas/*.py` | one route file and its schema file each: auth 23, chat 40, events 41, handoff 42, demo 43, staff_session 44, staff_cases 45, staff_live 46, staff_clock 47, reads 48 | No ticket edits another's route or schema file |
| `agent/nodes/*.py` | stubs from 21; then load_context 34, front 36, plan 37, act 39, reply 38 | One owner each; stubs replaced in place |
| `agent/prompts/*.py`, `agent/tools/*.py` | specialists 35, routing 37, reply 38; dispatch 22, account 27, scheduling 28, knowledge 33 | One file per ticket |
| `tests/fakes/`, `tests/conftest.py`, `tests/fixtures/sqlite.py` | 11, 01, 10 | DO-3 §9 lists `temp_sqlite()` under `tests/fakes/`; it moves to `tests/fixtures/sqlite.py` (owned by 10) so 10 and 11 never share a folder. Other tickets put fixtures in their own test folder |
| `tests/contract/` | 17, 18 (one file each), 51 (the cross-adapter file) | — |
| `tests/journeys/` | 01 (skeleton, marker), 57 (`support/`, J-1), 58 (`browser/`), every build ticket adds only `j<N>/test_aea_<NN>.py` | One file per ticket per journey; `support/` is 57's alone; a missing helper is a follow-up on 57, merged first |
| `tests/contract/` (prompt and OpenAPI files) | 59 (`test_openapi_*`, `test_types_gen_drift`), 60 (`test_prompts_vs_consumers`), 17/18/51 (adapters) | One file each |
| `tests/live/` | 61 | Never in the default run |
| `tests/capture/` | 51 (CAP-1…3), 52 (CAP-4, 5), 53 (CAP-6), 24 (CAP-7, 8), 50 (CAP-9) | One file per CAP |
| `.claude/reference/area-map.md`, `.claude/state/icm-progress.md`, `docs/design/code-design.md` | 08 first; then every ticket's `[regression/context]` criterion | After 08, each ticket changes only its own row (planned → actual + commit) |
| `README.md`, `SUBMISSION.md`, `docs/` | 07, 25, 54 | One owner per document; others add one line per ticket |
| `apps/web/**`, `docs/ux/**`, `ui-contracts.openapi.yaml` | nobody (49 reads `dist/`; 55 changes `apps/web` config only after UX-5) | A needed contract change stops the ticket and goes to Innocent |

## 4. Where each user story lands

| US | Tickets | US | Tickets | US | Tickets |
|---|---|---|---|---|---|
| 1 | 03, 40, 51 | 11 | 28, 35 | 21 | 29, 45 |
| 2 | 05, 12, 29, 36, 42 | 12 | 28, 39 | 22 | 29, 30, 45, 47 |
| 3 | 03, 05, 36 | 13 | 28, 35 | 23 | 44, 45 |
| 4 | 05, 36, 38 | 14 | 14, 29, 39, 42 | 24 | 48, 53 |
| 5 | 05, 37 | 15 | 41, 46 | 25 | 03, 30, 43, 47 |
| 6 | 16, 33, 35 | 16 | 15, 38 | 26 | 23, 26, 35, 40 |
| 7 | 33, 38 | 17 | 21, 34, 38 | 27 | 24, 32, 53 |
| 8 | 12, 27, 36, 43 | 18 | 29, 45 | 28 | 23, 44 |
| 9 | 27, 35 | 19 | 29, 45 | | |
| 10 | 13, 28, 35 | 20 | 46 | | |

HP-1 → 20, 21, 37, 38 · HP-2 → 05, 12, 36, 37 · HP-3 → 13, 28, 35, 39 · HP-4 → 15, 38.
The coverage audit (`docs/plans/coverage-audit.md`, skill §4a) traces every R-n, WF-n and CAP-n to a criterion.

## 5. Questions raised while writing the 7b specs

| # | From | Question | Handling |
|---|---|---|---|
| Q-1 | AEA-07, AEA-54 | Where the technical documentation and deployment guide live | Claude's default: `docs/technical-documentation.md`, `docs/deployment-guide.md` |
| Q-2 | AEA-09, AEA-02 | Railway variable names (only `MERIDIAN_DEMO_USERNAME`, `MERIDIAN_DEMO_PASSWORD` are named) | AEA-02 (owner of `config.py`) fixes every `Settings` env name; AEA-09 lists them by name |
| Q-3 | AEA-09 | Which VPS hostname carries the ingestion-only Langfuse route (ports 80/443 are held by a process the writer could not identify) | **Innocent** (part of his AEA-09 yes) |
| Q-4 | AEA-25 | R-48 puts the demo login in the README, but R-42 makes the repo public: anyone could sign in and spend model budget (the $30/day cap still holds) | **Innocent** |
| Q-5 | AEA-08 | PRD §6.2 still says server-rendered pages; the UX track chose the React app in `apps/web` | Recorded as a known PRD discrepancy; the PRD is not edited without Innocent |
| — | AEA-08 | AEA-08 also updates DO-4 `api-con-mapping.md` route paths to the split files; AEA-09 adds the Railway `/data` volume | In those tickets' scope |
