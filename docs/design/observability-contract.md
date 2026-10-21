# Observability contract — Meridian AI service agent

<!-- DO-6. Answers "what ran, and can we prove it was captured?" for every workflow. Correctness is not here: it is
docs/design/evaluation-plan.md (DO-5). Contract: Gauntlet AI/.claude/skills/system-design-readiness/DESIGN-OUTPUTS.md →
Observability contract.
Check: python3 "<readiness>/scripts/design_outputs.py" check-obs docs/design/observability-contract.md -->

> Owner: Innocent · Status: draft (Stage 6, System track, written 2026-10-21; Innocent approves) · Sources: SD-1.10,
> SD-2.8, SD-3.7, SD-4.7, SD-6.6, SD-7.6, SD-8.4, SD-8.7; PRD 0.4 R-29, R-35, R-36, R-15, R-41, §5, §6.2; framing §2
> health list; interview Q-010, Q-016, Q-021, Q-022, Q-030, Q-037, Q-045, Q-050, Q-056, Q-062; research §6; draft
> contracts CON-18, CON-19, CON-20 (`docs/ux/01-planning/USER_FLOWS.md`, read-only)

**What this document owns.** Every workflow's record of what ran, the IDs that link a run end to end, where records
live and for how long, what they may hold, how a silent failure shows, and the tests that prove capture. **What it
links to instead of restating:** metric formulas and targets are in [`key-metrics-registry.md`](key-metrics-registry.md)
(DO-7); correctness and scoring are in [`evaluation-plan.md`](evaluation-plan.md) (DO-5); the signed health list and its
decision lines are in the [framing doc §2](../delivery/2026-10-20-angle-and-demo-framing.md).

**Number labels:** [T] a target Innocent set · [A] an assumption, with what would measure it · [C] calculated · [M]
measured.

## What this looks like for one message

**Input.** A customer types "My carbon monoxide detector is going off" (WP-5) into the public chat.

**Process.** The API gives the request a `request_id` and the turn a `turn_id`, inside the conversation's `thread_id`.
The code gate matches the safety rule and writes the fixed instruction with no model call. Code writes a P0 case. The
app stores a `turn` record (`gate_result = safety`, `outcome = safety_reply`, timings), a `case` and `case_event` row,
and a `check_event` for the gate. The trace for the turn, with the customer's text masked, goes to this app's own
project in the Langfuse on Innocent's VPS. The Railway log line carries only IDs, status and timings.

**Output.** On the monitoring page: one more conversation, one safety reply, a P0 case, the turn's latency. On the
evaluation page: nothing, because a live conversation has no gold label. **Whether the reply was right is never read
from these records:** "it ran" and "it was right" are different questions with different evidence (rule 22; framing
§2, "It's up never stands in for it's right").

## Two questions, kept apart

| Question | Evidence | Where it shows |
|---|---|---|
| **Did it run?** (this document) | Turn, request and job records; status values; latency; errors and retries; brake and spend-cap handoffs; restarts; trace export | Monitoring page **Health** group (SCR-10, CON-19); Railway logs; Langfuse |
| **Was it right?** (DO-5) | Eval runs against gold labels; staff flags (R-37) | Evaluation page (SCR-11, CON-20); owner page outcome tiles (SCR-9, CON-18), labelled as stored outcomes |

A run that fails or hits a brake **ends in a handoff and is counted as a health event, never as a resolution**
(interview Q-021; PRD §5 *Reliability*). On the monitoring page, health and correctness never share a tile group
(R-35; SCR-10 copy note).

**Status values (resolves Q-022, deferred here).**

| Record | Field | Values |
|---|---|---|
| `turn` | `gate_result` | `clear`, `safety`, `burning_unclear`, `danger`, `person_requested`, `ai_paused` |
| `turn` | `outcome` | `answered` (just talk), `acted` (a specialist ran and finished), `safety_reply`, `handed_off`, `to_staff` (AI paused; the message went to the representative), `degraded_handoff` |
| `turn` | `degrade_reason` (only with `degraded_handoff`) | `model_error`, `tool_error`, `timeout`, `brake`, `spend_cap`, `rate_limit` |
| `conversation` | `outcome` | `ai_resolved`, `handed_off`, `safety_reply`, `abandoned`, `open`; the end rule is in DO-7 (M-18) |
| `request` | `status` | the HTTP status, plus `error_kind` on 5xx |
| `job_run`, `eval_run`, `ingest_run`, `deploy_record` | `status` | `started`, `completed`, `failed`, `incomplete` |

**Where per-turn timing starts and stops (resolves the DO-6 half of Q-016).**
- `turn.server_ms`: from the API receiving the turn request (CON-2) to the reply body being written. This feeds the
  monitoring page's p50 and p95.
- **Load re-measure (Stage 9):** client-side wall clock per customer turn, the same boundary SP-1's harness used. The
  12.5 s line [T] was set against that boundary (SP-1 §4), so the re-measure uses it. Server time is never larger than
  client time, so a server p95 alone would flatter the result.
- Inside a turn, each node, model call and tool call is a timed span in the trace (rule 18), so a slow turn can be
  broken down step by step (SP-1 found the responder was the slow tail at 20 at once [M]).

## Covered workflows

Workflow registry, compiled from interview Q-030 ("all of these are covered; none is excluded"). Record names are
defined in *Records* below; capture checks `CAP-n` in *Capture verification*. Contract IDs are the draft UX contracts
(read-only here).

| Workflow | Entry point | Class | Emitting components | Correlation | Required records | Capture verification | Eval and metrics |
|---|---|---|---|---|---|---|---|
| WF-1 | Customer chat turn: `POST /api/chat/sessions` (CON-1) then `POST /api/chat/sessions/{id}/turns` (CON-2), including code entry (R-15) | user-operation | API, code gates, planner, danger classifier, specialists, escalation check, responder, R-46 checks, lookup log, case store | `request_id` per HTTP call; `thread_id` minted at CON-1; `turn_id` minted at CON-2 receipt | request, conversation, turn, model_call spans, lookup_log, check_event, spend_ledger; case and promise when handed off | CAP-1, CAP-2 | EV: E-1, E-3, E-4, E-5, E-7; M-1, M-3, M-4, M-6 to M-9, M-14, M-16 to M-26, M-29 (trace export per turn; added 2026-10-21 at §7) |
| WF-2 | "Talk to a person" and follow-up preference: `POST …/handoff` (CON-4), `PUT …/follow-up` (CON-5) | user-operation | API, handoff node, case store, promise table | `thread_id`; `turn_id` of the request; `case_ref` minted at the handoff | request, turn (`person_requested`), case, case_event, promise | CAP-3 | EV: E-6; M-10 to M-13, M-15 |
| WF-3 | Demo delivery inbox: `GET /api/demo/inbox` (CON-6) | user-operation | API, identity code sender | `request_id`; `thread_id` of the code request | request; code-sent event (hash and expiry only) | CAP-1 | n/a — reading the simulated inbox decides nothing; its code-sent event is covered by WF-1's identity checks |
| WF-4 | Staff console: sign-in (CON-10), queue and case views (CON-11, CON-12, CON-17), case actions (CON-13), takeover and live chat (CON-14, CON-3 stream), contact attempts (CON-15), flags (CON-16) | user-operation | API, staff session, case store, live-chat relay | `request_id`; `case_ref`; `thread_id` for the joined chat; staff role on every action | request, case_event (actor role, action, reason), turn (`to_staff`) for relayed messages, flag | CAP-4 | EV: flags feed the review list (R-37), never the eval set unreviewed; M-13, M-27 |
| WF-5 | Demo controls: staffing (CON-7) and clock (CON-8) | user-operation | API, presence state, demo clock | `request_id`; a `demo_event` row per change | request, demo_event | CAP-5 | n/a — demo controls change the simulation, not an outcome; their effect is measured through WF-1 and WF-6 |
| WF-6 | Read-only measure pages: owner metrics (CON-18), monitoring (CON-19), latest eval (CON-20) | user-operation | API, metrics reader | `request_id` | request (page reads are counted, never recomputed into outcomes) | CAP-6 | Displays M-1 to M-29; computes none of them on read |
| WF-7 | Due-soon and overdue job on the fixed clock (consolidated direction §10) | background-job | Scheduler, case store, promise records | `job_run_id` per tick; `case_ref` per case touched | job_run, case_event (`due_soon`, `overdue`), promise status change, health_event when the job misses a tick | CAP-5 | M-13, M-27 |
| WF-8 | Retrieval eval (R-12) | validation | Eval runner, retriever | `run_id` per run; `case_id` per query | eval_run, eval_case_result (top-3 documents and version dates) | CAP-7 | EV: E-2; M-6, M-7 |
| WF-9 | End-to-end eval, dev split and sealed held-out split (R-38, R-39) | validation | Eval runner, the whole agent (WF-1 path), DB-copy checker | `run_id` + `case_id`; each case gets its own `thread_id`; `agent_version` stamped | eval_run, eval_case_result, plus every WF-1 record tagged `eval` | CAP-7 | EV: E-1, E-3 to E-7; M-1, M-2 (dev split; added 2026-10-21 at §7), M-5, M-8 to M-12, M-14 to M-17, M-19 to M-21 |
| WF-10 | Load re-measure, 20 conversations at once (Stage 9; Q-055) | validation | Load harness, deployed app | `run_id`; one `thread_id` per scripted conversation | eval_run (kind `load`), client-side turn timings, every WF-1 record tagged `load` | CAP-7 | EV: E-8; M-23, M-24, M-25 |
| WF-11 | SP-1 spike (finished 2026-10-21; archived, never merged) | development-experiment | SP-1 harness and throwaway build on the VPS | `run_id` per run; spend ledger per paid call | `var/sp1-runs/*.json` run records and `ledger.jsonl` on the VPS (gitignored); results in SP-1 §3 | Harness digest `41c46ad927b3d6ca` printed per run and a tamper check (SP-1 §2–§3) | Informed M-23 and M-25 baselines; HP-1 status |
| WF-12 | Stage 9 error analysis and experiments `XP-N` (checklist §9) | development-experiment | Eval runner, trace reader, experiment log | `experiment_id` (`XP-N`) linking its `run_id`s to its configuration | experiment (model mix, prompt versions as git SHA, retrieval settings, split, one changed variable), eval_run per scored run | CAP-8 | EV: E-1, E-3 on the dev split only; the FT-N it targets; before-and-after score and cost |
| WF-13 | Deploy to Railway (R-40) | runtime-operation | Railway build, app start-up | `deploy_id` (Railway deployment) + git SHA; `agent_version` | deploy_record (SHA, deployment ID, agent_version, config hash, trace export on or off) | CAP-9 | Stamps `agent_version` on every turn and eval run, so SCR-11 can show a stale run |
| WF-14 | Knowledge-base ingestion and index build (R-9, R-11) | runtime-operation | Ingestion step, embedder, index writer | `ingest_run_id`; manifest hash | ingest_run, ingestion manifest (17 files, status and parse method each), index record (embedding model, chunk count, manifest hash) | CAP-9 | EV: E-2 runs on the index this records; M-6, M-7 |
| WF-15 | Working-copy reset (R-19; CON-9 and the reset command) | runtime-operation | Reset script, case store, demo clock | `reset_id` | reset_event (what was restored, who asked, open chats ended) | CAP-9 | n/a — a reset restores the demo state; it is logged so a drop to zero on the pages is explained |
| WF-16 | Case-store table creation and demo seed load (R-25, R-33) | runtime-operation | Migration step, seed loader | `deploy_id` or `reset_id` | seed_event (seed case count, labelled "demo seed") | CAP-9 | Seed cases are a named segment: SCR-9's basis line counts them, and M-3, M-13 and M-27 report with and without them |
| WF-17 | Health check and restart (R-35; Q-045 = A) | runtime-operation | Health endpoint, Railway restart policy, start-up hook | `health_check_id`; `deploy_id` | health_event (each check result, each restart with time and reason) | CAP-9 | M-28; the "last health-check restart" line on SCR-10 |
| WF-18 | Demo login and logout (R-48, CON-22); registered 2026-10-21 at §7 because no row covered it (to-tickets: entry points are registered, not discovered) | user-operation | API, demo-login session check in middleware | `request_id`; demo session id (opaque) minted at login | request; auth_event (outcome `ok` / `rejected` / `logged_out`, time; never the username or password). **Note (Stage 7, 2026-10-21, MC-9; WEB-11):** `auth_event` carries the opaque demo session id (this row's correlation id), never the cookie token; it also has outcome `rate_limited` | CAP-10 | n/a — the login gates access and decides no outcome; rejected attempts feed the rate limit (R-41) |
| WF-19 | Page serving: the built frontend (`apps/web/dist`), its assets and the SPA fallback (R-48; registered 2026-10-21 at §7, WEB-31, because AEA-49 adds the entry point) | user-operation | API middleware | `request_id` | request (route template `spa_fallback` or `/assets/{file}`, never the raw path or query string) | CAP-11 | n/a — serving files decides no outcome |

Workflow classes:

| Class | Present | Workflows or reason |
|---|---|---|
| user-operation | yes | WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-18, WF-19 |
| background-job | yes | WF-7 |
| validation | yes | WF-8, WF-9, WF-10 |
| development-experiment | yes | WF-11, WF-12 |
| runtime-operation | yes | WF-13, WF-14, WF-15, WF-16, WF-17 |

**Records.**

| Record | Holds | Written by |
|---|---|---|
| `request` | `request_id`, route, status, duration, caller role (anonymous or staff role), `thread_id` when present | API middleware |
| `conversation` | `thread_id`, start and end time, `outcome`, staffing mode, `agent_version`, tag (`live`, `eval`, `load`) | API, handoff node, end rule |
| `turn` | `turn_id`, `thread_id`, `request_id`, sequence, received and replied times, `server_ms`, `gate_result`, planner decision, specialists run, `outcome`, `degrade_reason`, counts of model and tool calls, tokens, cost, `trace_id`, `trace_export` | Graph runner |
| `model_call` (span) | role (planner, classifier, specialist, responder, brief), model, latency, input, output and thinking tokens, cost, retries, HTTP status, provider request ID, the full rendered context and raw output **after masking** (rule 21) | Langfuse instrumentation; a cost row also goes to `spend_ledger` |
| `lookup_log` (R-29) | tool, record or passage ID, time, the result seen (snapshot), the message that used it, `turn_id` | Each tool |
| `check_event` | which gate or check fired (code gate, R-46 completion or fact check, R-47 classifier raise, brake), its input IDs and result. **Columns (Stage 7, 2026-10-21, GRN-5):** `check` adds `gate`, `classifier`, `brake`; `result` adds `fired`, `raised`; a new `codes` field holds stable codes (gate kind and rule ids; classifier label or failure kind; halt reason and node). One `gate` event every turn and one `classifier` event every classifier run, `pass` included, so M-17 has a per-turn denominator | Gates and checks |
| `signal` (added Stage 7, 2026-10-21, GRN-4) | the DO-1 §8.2 failure signals with no record of their own: `safety_reply_sent`, `case_write_failed`, `classifier_fallback`, `planner_fallback`, `specialist_failed`, `brake_fired`, `responder_fallback`, `brief_failed`; name, cause code and IDs only, never message text. A brake also writes a `brake` check event; M-24 still reads `turn.degrade_reason` | Graph nodes through `emit_signal` (gates and safety, plan, act, reply nodes); the specialist runner emits none |
| `case`, `case_event`, `promise` | PRD §6.2 case-store tables: priority, promise text and due time, lifecycle events with actor role | Handoff node, staff actions, WF-7 |
| `spend_ledger` | per model call cost, running daily total against the cap | Model client wrapper |
| `health_event` | health check results, restarts, alerts firing and clearing, missed job ticks | Health check, alert evaluator, WF-7 |
| `job_run`, `eval_run`, `eval_case_result`, `experiment`, `ingest_run`, `deploy_record`, `reset_event`, `seed_event`, `demo_event` | the run records named in the registry | Their workflows |

## Correlation across boundaries

**The IDs, where each is created, and what it links.**

| ID | Created | Links |
|---|---|---|
| `request_id` | API middleware, on every HTTP request; returned in a response header | One HTTP call to its log lines and, for a turn, to its `turn` record |
| `thread_id` | CON-1, when the conversation starts | The whole conversation: the LangGraph checkpointer key (consolidated direction §10), every turn, case and lookup-log row, and the Langfuse `session_id` |
| `turn_id` | CON-2, when the customer message arrives | One turn: its trace (one Langfuse trace per turn, with each node, model call and tool call nested under it, rule 21), its lookup-log rows and check events, and the case if it handed off |
| `case_ref` | The handoff node, when a case is created; shown to the customer as the reference | The case, its events and promise, back to the `thread_id` and `turn_id` that created it |
| `run_id` | The eval runner or load harness, per run | Every case result and every conversation the run created (tagged `eval` or `load`) |
| `experiment_id` (`XP-N`) | When an experiment is registered (WF-12) | Its configuration (model mix, prompt versions by git SHA, retrieval settings, the one changed variable) to its `run_id`s |
| `job_run_id`, `ingest_run_id`, `reset_id`, `health_check_id` | At the start of each job, ingestion, reset or check | That run's records and every case or file it touched |
| `deploy_id` and `agent_version` | At deploy: Railway's deployment ID; `agent_version` = git SHA plus a hash of model configuration and prompt versions | Stamped on every conversation, turn, eval run and trace, so a result always names the code that produced it |

**How each boundary is crossed.**
- **Browser → API:** `thread_id` is in the path; `request_id` comes back in a header; staff calls carry `case_ref`.
- **API → graph:** `thread_id` as the checkpointer key; `turn_id`, `run_id` and `agent_version` in the run metadata,
  which the Langfuse handler copies onto the trace (`langfuse_session_id` = `thread_id`, research §6).
- **Graph → model providers (Anthropic for Sonnet 5.5; OpenRouter for Jev):** each call is a span under the turn's
  trace, and the provider's own request ID is stored on the span for support cases.
- **Graph → tools and the case store:** every lookup-log row and case row carries `turn_id` and `thread_id`.
- **App → Langfuse:** spans export in the background after masking; the trace ID is stored on the `turn` record.
- **Event stream (CON-3) and staff takeover:** relayed messages carry `thread_id` and the staff `case_ref`.
- **Eval runner and load harness → app:** each scripted conversation is a new `thread_id`; the `run_id` header is
  honoured **only with the eval key** (a Railway variable), so public traffic cannot label itself as test traffic and
  drop out of the live numbers.
- **Background job:** `job_run_id` on every case event it writes.

## Storage and access

**The constraint that chose it.** Business numbers come only from our own stored records (Q-050: "our own tables for
the monitoring page and evals"), so the pages never depend on the trace backend. Traces go to the **Langfuse v4 already
running on Innocent's VPS** (`localhost:3100`), in **its own Langfuse project for this app** (Q-050 revised by Q-062,
Innocent 2026-10-20; PRD §6.2, R-36). That meets project rule 18 (an LLM-aware trace backend), adds nothing to host or
pay for, and keeps traces on his own server. Alerts stay on the monitoring page with a health check that restarts the
service; there is **no push channel** (Q-045 = A, Innocent 2026-10-20; push alerts are roadmap).

| Record kind | Where | Kept | Who can read |
|---|---|---|---|
| Conversations, turns, lookup log, check events, cases, case events, promises | SQLite on the Railway volume, beside the working DB copy (PRD §6.2) | Production: 90 days after the case closes (D6, PRD §5 *Privacy*). Demo: cleared by reset (WF-15) | Staff roles through their views, least privilege (D6); the owner page reads aggregates with case links |
| Spend ledger, health events, eval runs and case results, deploy records | The same SQLite file, in tables the demo reset does **not** clear | Spend: the current and previous day are needed for the cap; kept with the 90-day bound. Eval and deploy records: kept for the life of the deployment | Monitoring page (aggregates), evaluation page, Innocent |
| Traces | Langfuse v4 on the VPS, this app's own project; never YourAI's project or keys | No longer than the 90-day bound (D6). How the VPS instance enforces it is checked when the project is created; research §6 advises a short retention because ClickHouse storage grows | Innocent only (his Langfuse login) |
| Application logs | Railway logs, structured JSON | 7 days on Hobby [M, `gauntlet-hosting-default.md`] | Innocent (Railway dashboard) |
| Eval reports | The repository (public, R-42) | Permanent | Anyone: fictional data only, already redacted |
| SP-1 run records | `var/sp1-runs/` on the VPS, gitignored | Until Innocent deletes them | Innocent |

**Note (Stage 7, 2026-10-21, WEB-11, WEB-18, GRN-4, DAT-12, CAS-5, CAS-27, MC-15): where the records with no row
above live.** `request`, `auth_event`, `stream_reconnect` and `signal` are structured log records only (the log
allow-list formatter, Railway logs), with no table and no DDL. `ingest_run` is `ingest_run.json` beside the index in
the image, not a database row. `demo_event` is the table `demo_events`, kept by a reset. `experiment` has no table: an
experiment is `eval_runs.experiment_id`; eval runs reach `eval_runs` and `eval_case_results` from committed
`eval/reports/<run_id>.json` files loaded at start-up (DO-5).

**Local runs and the deployed app reach Langfuse differently.**
- **Local and VPS runs:** use `localhost:3100` directly; the Mac reaches it through an SSH tunnel (PRD §6.2).
- **The deployed Railway app:** needs a public HTTPS route to that Langfuse. **That route is a deploy-time step done
  only with Innocent's yes** (Q-062). Until he says yes, the deployed app runs with trace export **off**, every
  `turn.trace_export` reads `off`, and the monitoring page says so. The app and its pages work fully without traces.
- **When he is asked,** the question should cover how much of Langfuse the route exposes (only what the app's export
  needs, or the whole web interface). Exposing it is his decision, not the design's.

**The Langfuse keys** for this project are new keys, held in Railway variables and the local `.env`, never in the
repository. They are not the YourAI keys. That holds even though the model keys come from the YourAI `.env` (PRD R-40).

## Content and redaction

**What each record may hold.**

| Content | App database | Staff views | Monitoring and eval pages | Traces (Langfuse) | Logs (Railway) |
|---|---|---|---|---|---|
| Verification codes (R-15) | Never raw: hash and expiry only | Never | Never | Never | Never |
| Card-like numbers (13–19 digits, with or without spaces or dashes) | Never: masked at intake | Never (masked) | Never | Never | Never |
| Key values: API keys, Langfuse keys, the eval key, staff demo passwords, session cookies | Never | Never | Never | Never | Never |
| Names, phone numbers, emails, addresses | Raw, where the case needs them | Raw, by role (D6) | Never: aggregates only | Masked (a phone keeps its last two digits, as the UI's "phone ending 02") | Never: IDs only |
| Customer and agent message text | Raw, after the intake masks above | Raw, by role (D6) | Never, except redacted dev-split failure examples on SCR-11 | Masked as above, in the full rendered context (rule 21) | Never: length only |
| Account facts (invoice lines, appointment windows, tier, dates) | Raw | Raw, by role | Aggregates only | Raw: fictional, and needed to debug the fact check | Never |
| IDs, statuses, timings, token counts, cost | Yes | Yes | Yes | Yes | Yes |

**Where redaction happens, in order.**
1. **At intake, before anything stores or sees the message.** A code-entry turn is handled by code: the message text is
   replaced by "[code entered]" before state, model, storage or trace. Card-like numbers in any message are replaced by
   "[card number removed]" before the model sees them; the agent never asks for one (R-13, audit K-17, L-4).
2. **Before export to Langfuse,** in our process: Langfuse's `mask_otel_spans` hook (Python SDK v5, research §6, S-215).
   It must cover the graph spans from the LangChain callback handler **and** the model-call spans from the direct
   Anthropic and OpenRouter instrumentation, which the callback handler does not see. Collector-side masking is not
   used, because it runs after the data has left the app (research §6).
3. **In the log formatter:** an allow-list of fields (IDs, statuses, timings, counts). Free text never reaches a log.
4. **On the pages:** the monitoring page shows aggregates only and no trace links (SCR-10); the evaluation page shows
   dev-split failure examples only, redacted.

**Name-masking limit (DAT-1, Innocent 2026-10-21: option A).** `privacy/redact.py` finds names only by
introduction patterns ("my name is …", "this is …", "I'm …" followed by capitalised words) and street lines
only by a number, street-name and suffix pattern. Loose names in free chat ("Omar here", "my mother Jane")
may therefore reach Jev, under `data_collection: deny`, and the project's own Langfuse. Codes, card-like
numbers, phones, emails and customer and invoice IDs have fixed shapes and are always replaced for their
profiles.

**What leaves the environment.** (a) Model inputs to Anthropic (Sonnet 5.5: specialists, responder, brief) and to
TypeSafe through OpenRouter (Jev: planner and danger classifier), each after the intake masks. Raw caller text goes to
Jev only after redaction, a condition of Innocent's SP-1 decision (SP-1 §4). (b) Masked spans to the Langfuse on
Innocent's own VPS. Nothing else.

## Missing instrumentation

Silence must never look like "no traffic". Each check below makes a missing or partial record visible on the monitoring
page or in a run report.

| What could go missing | How it shows |
|---|---|
| The whole service stops | The health check writes a `health_event` on every check, so "no recent health events" means "not running". Railway restarts it (Q-045 = A), and SCR-10 shows the last restart |
| Traffic stops while the service is up | The zero-traffic alert from the framing health list. **The "expected window" is not set yet** (open item 2 below) |
| A turn starts but never finishes (crash mid-turn) | The `turn` row is written on receipt with `outcome` empty; on restart, rows left open past the turn deadline become `degraded_handoff` / `timeout` and are counted as failures |
| Traces are not exported | `turn.trace_export` is `sent`, `failed` or `off` on every turn. SCR-10 shows "traces exported: n of N turns". Export is in the background, so a Langfuse outage never slows or fails a turn |
| A tool call left no lookup-log row | The `turn` record counts its tool calls. A check compares that count with the lookup-log rows for the `turn_id` and flags any mismatch |
| A handoff left no case | A check counts turns with `outcome = handed_off` and no `case` row for that `turn_id`. The expected count is 0 |
| A model call left no cost row | Spend-ledger rows per turn are checked against the turn's model-call count. At Stage 9, the ledger's daily total is compared once by hand with the providers' usage pages |
| The overdue job stopped ticking | Each tick writes a `job_run`. SCR-10 shows "overdue job last ran n minutes ago", and a missed tick writes a `health_event` |
| An eval run stopped early | An `eval_run` whose case count differs from its case manifest is marked `incomplete` and never reported as a result |
| Records were written but to the wrong Langfuse project | At start-up, the app asks Langfuse which project its keys belong to. If it is not this app's project, export is switched off and an alert fires (CAP-9) |

**Alerts on the monitoring page** (decision lines from the framing health list; values and approvals in DO-7):

| Alert | Fires when | What to do |
|---|---|---|
| Zero traffic | No new live conversation for **4 hours**, not counted during late-night hours (Innocent, 2026-10-21: "4 hours outside of the late night hours"); late night = 10pm–6am Austin time [A, a config value he can change] | Check the health events and the public URL |
| Latency | p95 per turn above 12.5 s [T, PRD §5; Innocent 2026-10-21] | Check the model and retrieval spans in the traces |
| Failures | Tool and model failure rate above 2% [T, framing health list] | The agent already falls back to handoff; read the failing spans |
| Spend | The daily cap of $30 is reached [T, Q-061] | The agent hands off and stops calling models (a design brake) |
| Overdue | Any overdue case | Supervisor view alert (C3) |
| Restart | The health check restarted the service | Read the logs around the restart time |
| Trace export | Export `failed` on any turn, or `off` | Check the VPS route; never blocks the service |

## Capture verification

Each check drives the **real entry point**, not the shared adapter, and fails if a required record is missing or a
forbidden value appears. In tests, spans go to an exporter that keeps them in memory instead of sending them, so the
masking hook runs exactly as in production. Test file names are set in the code design (DO-3).

| Check | Drives | Asserts present | Asserts absent |
|---|---|---|---|
| CAP-1 | WF-1 and WF-3: CON-1, then CON-2 through WP-2 (seeded MHC-10002 Omar Patel, phone 512-555-0102, the code read from the demo inbox), plus one turn containing a synthetic card-like number | `request`, `conversation`, `turn` per message with `gate_result`, `outcome` and timings; nested model and tool spans under one trace per turn; `lookup_log` rows for the invoice read; `check_event` for R-46; spend rows | The code in any DB text, span or log; the card-like number anywhere; the full phone number in spans or logs; any key value anywhere |
| CAP-2 | WF-1 with WP-5 (CO alarm) and DANGER | `turn` with `gate_result = safety` or `danger`, `outcome = safety_reply`; P0 or P1 case; no model span before the safety reply. **Correction (Stage 7, 2026-10-21, GRN-9):** that holds for WP-5 (rule gate); DANGER is reached only through the classifier (R-47, HP-2 C), so before its reply it has exactly the two parallel Jev routing spans (`planner`, `classifier`) and no specialist, responder, brief or Sonnet span | Any identity or lookup step before the instruction |
| CAP-3 | WF-2: CON-4 and CON-5 after WP-7 (refund) | Case, case events, promise with due time and text from the policy table; `turn.outcome = handed_off` | A promise text from the model |
| CAP-4 | WF-4: staff sign-in, claim, live reply, hand back, flag (CON-10, CON-13, CON-14, CON-16) | `case_event` per action with actor role and reason; relayed turns with `outcome = to_staff`; flag row | Customer PII in logs |
| CAP-5 | WF-5 and WF-7: advance the demo clock past a promise's due time | `demo_event`; a `job_run` per tick; the promise marked overdue; overdue `health_event` when a tick is skipped | — |
| CAP-6 | WF-6: CON-18, CON-19, CON-20 after CAP-1 to CAP-3 | Each page's numbers equal the stored records' counts (no recomputation on read) | Names, codes, card-like numbers or trace links on CON-19 and CON-20 |
| CAP-7 | WF-8, WF-9, WF-10: one retrieval query, one dev case, a two-conversation load run | `eval_run` with `run_id` and `agent_version`; `eval_case_result` per case; WF-1 records tagged `eval` or `load`; a run without the eval key is tagged `live` | Held-out answer keys in any run log |
| CAP-8 | WF-12: register an experiment and run it once | `experiment` with its configuration and the `run_id` it produced | A run with no `experiment_id` reported as an experiment |
| CAP-9 | WF-13 to WF-17: start-up with this app's Langfuse keys and with another project's keys; ingestion; reset; seed load; a forced health-check failure | `deploy_record`; manifest with 17 file rows; `reset_event`; `seed_event`; `health_event` for the restart; with the wrong project's keys, export off and an alert | Any span sent to a project that is not this app's |
| CAP-10 | WF-18: log in with the right pair, with a wrong password, then log out; call a protected route without the session (added 2026-10-21 at §7) | `request` per call; `auth_event` per attempt with its outcome; the protected call refused with the login error | The username or password (right or wrong) in any response body, log line, span or DB text |
| CAP-11 | WF-19: request the app root, a deep link and one asset, signed in and signed out (added 2026-10-21 at §7) | `request` per call with the route template, not the raw path; signed-out requests answered with the login page or refused per WEB-1 | The query string or raw path in any log line or span |

**The redaction test drives real flows** with seeded names and numbers, as rule 19 requires; it is CAP-1, run on every
change that touches the masker, the instrumentation or a prompt.

## Registering a new workflow

Before a new entry point, job, script or experiment runs, its author:

1. adds a `WF-n` row above with its class, emitters, correlation and required records;
2. names the evaluation suites (DO-5) and metrics (DO-7) it inherits, or `n/a — <reason>`;
3. adds its capture check, which fails if the records are missing or a forbidden value appears;
4. cites the `WF-n` in the ticket's *Entry points added or changed* line;
5. if it sends anything new out of the environment (a new model, provider or export), adds it to *What leaves the
   environment* and asks Innocent first.

## Open items for Innocent

1. **The public HTTPS route from Railway to the VPS Langfuse:** method decided (SDQ-3, 2026-10-21): a TLS proxy exposing only
   the ingestion paths. Turning it on is still his yes at deploy time; until then, deployed trace export stays off.
2. **The zero-traffic window: decided** (Innocent, 2026-10-21): no new live conversation for **4 hours**, not counted during late-night hours (Innocent, 2026-10-21: "4 hours outside of the late night hours"); late night = 10pm–6am Austin time [A, a config value he can change].
3. **Trace retention on the VPS instance: decided** (Innocent, 2026-10-21, accepting the recommendations): the 90-day
   bound (D6) applies to traces.
