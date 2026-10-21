## [AEA-19] tracing: Langfuse sink, null sink, project-key check

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

> **US-27.** As a **reviewer** (and the business owner), I need a monitoring page … and the evaluation report …, with no
> codes or card numbers in what's shown, so that I can check the claims myself. *(Acceptance: redaction holds on seeded
> data; traces stay in Langfuse on Innocent's VPS and are not exposed on the public pages.)*

**What it does in practice.** Every turn becomes one trace (the turn, each node and each model attempt nested under it),
sent to **this app's own project** in the Langfuse v4 on Innocent's VPS (Q-050/Q-062, R-36). Two things must never
happen: a private value reaching that trace, and tracing slowing or failing a customer's turn. So the sink masks in our
process before export, exports on a background thread through a bounded queue that drops (and counts) instead of
waiting, and at start-up asks Langfuse which project its keys belong to. If they belong to any other project (for
example YourAI's), export stays off for the life of the process and an alert fires (DO-6 *Missing instrumentation*,
CAP-9). Until Innocent says yes to the deployed route (SDQ-3, DAT-4) the deployed app has no Langfuse settings, runs the
**null sink**, and every turn's `trace_export` reads `off`.

**How it works: `adapters/tracing_langfuse.py`** (A10a; DO-3 §4.2, §4.3; DO-4 §13 `TraceSink` as amended by
stage7/models.md §4):

- **The port it implements** (stage7/models §4, MOD-9): `turn(ids) -> ContextManager[SpanHandle]` (one trace per turn;
  `thread_id` as the Langfuse session id; `SpanHandle(turn_id, trace_id, native)` with the 32-hex trace id),
  `model_call(parent, record: CallRecord, masked_input, masked_output)`, `node(parent, name, elapsed_ms, status)`, and
  **`export_status(turn: SpanHandle) -> ExportStatus`** (`"off" | "sent" | "failed"`; the handle is needed because up
  to 30 turns run at once, SDQ-9). `SpanHandle` is AEA-02's (`domain/turn.py`, re-exported by `ports/runtime.py`).
- **Types owned here** (stage7/models §4, MOD-7, MOD-8): `TraceAlertReason = Literal["wrong_project",
  "project_check_failed"]`; `TraceAlert = Callable[[TraceAlertReason], None]` (the reason code only, never a key, URL or
  body); `LangfuseExportSettings(public_key: SecretStr, secret_key: SecretStr, base_url: str, project_id: str,
  queue_max_spans=1024, batch_interval_s=5.0, export_timeout_s=5.0, check_timeout_s=5.0, recheck_after_s=600.0)`, every
  number [A]; `LangfuseTraceSink(settings, redact: Redactor, on_alert: TraceAlert)` with `start()` (runs the project
  check; never raises) and `dropped_spans() -> int` (`trace_export_dropped`, DO-1 §8.2); `NullTraceSink` (`turn()`
  yields `SpanHandle(turn_id, trace_id=None)`; `model_call`/`node` do nothing; `export_status` → `off`). `Redactor` is
  data.md §1's `Callable[[str, RedactionProfile], Redacted]` (MC-23).
- **The mask hook:** Langfuse Python SDK v5's `mask_otel_spans` (research §6, S-215) applies
  `redact(text, RedactionProfile.TRACE)` to every exported span, a second layer after the gateway's own masking
  (system design §10 "Applied again at export"; DO-6 *Content and redaction* step 2). The TRACE profile (data.md §1)
  replaces card-like numbers (`[card number removed]`), six-digit codes (`[code]`), phones (`[phone ending NN]`, last two
  digits kept), emails, street addresses and introduction-pattern names; it leaves `MHC-`/`INV-` IDs and account facts
  (fictional; the fact check needs them). IDs, statuses, timings, tokens and cost pass unchanged.
- **The start-up project check** (MOD-6, stage7/models §4 steps 1–5):
  1. `GET {LANGFUSE_BASE_URL}/api/public/projects` with HTTP Basic auth (public key as user, secret key as password),
     timeout `check_timeout_s`.
  2. Export turns on **only if** the response is 200 and `data` holds **exactly one** project whose `id` equals
     `LANGFUSE_PROJECT_ID`. IDs are compared, never names; an organisation-scoped key listing several projects fails.
  3. Any other answer (another ID, several projects, 401/403) → export off for the life of the process,
     `on_alert("wrong_project")` once, no re-check.
  4. Unreachable, a timeout or a 5xx → export off, `on_alert("project_check_failed")` once, and the check runs again
     every `recheck_after_s` on the exporter thread until it passes or finds the wrong project. Spans created while
     export is off are not queued.
  5. Any of the four settings missing → the container builds `NullTraceSink`; `on_alert` is not called; every turn
     records `off`, and AEA-32's evaluator shows `trace_export_failed` from that (MC-24, cases.md §8).
- **The export queue** (MOD-8): a `BatchSpanProcessor`-style queue of `queue_max_spans` spans between the mask hook and
  the OTLP exporter. Adding a span never blocks; when full the span is dropped and `dropped_spans()` rises; a turn never
  waits on export (DO-1 §11 decision 8). If SDK v5 exposes no queue-size setting, this module wraps its own processor
  with these values (stage7/models §4).
- **What each status means** (MOD-9): `off` = export switched off (null sink, keys missing, check failed or found
  another project); `sent` = every span of this turn was accepted into the queue, none was dropped, and the exporter's
  most recent batch before the turn closed did not fail; `failed` = a span of this turn was dropped, or the most recent
  batch failed or timed out. `sent` means "handed to a healthy exporter", not "stored in Langfuse"; the sink never
  writes to the database (`turn` is AEA-40's).
- **This ticket's `register_<area>()` hunk:** when `Settings.langfuse_complete()` (all four `LANGFUSE_*` values set;
  graph-core.md §12), the container builds `LangfuseExportSettings(public_key=…, secret_key=…, base_url=…,
  project_id=…)` from `Settings`' four `langfuse_*` fields (models.md §7; `Settings` has no `langfuse_export()`, because
  `config.py` may not import an adapter, DO-3 §2.1; R-G-6) and then `LangfuseTraceSink(export_settings, redact,
  on_alert)`; else `NullTraceSink()`; calls `start()`. `on_alert` is an injected `TraceAlert`; AEA-51's container binds it to AEA-32's
  `AlertWriter.fire("trace_export_failed", reason)` (cases.md §8, models cross-topic 6).

**Example pair (WP-2, the CAP-1 seed).** Input: a turn whose model-call span carries "my name is Omar Patel, phone
512-555-0102", a six-digit verification code and a synthetic card-like number. Expected: the span the exporter receives
holds none of the full phone number, the code, the card-like number or the name; the phone appears only as
`[phone ending 02]`, as the UI's "phone ending 02" does; the invoice facts (INV-204411, $478.00) stay readable.

### Source
- stage7/models.md §4 (trace types, `LangfuseExportSettings`, the sink, the project check, the export queue, status
  meanings), §7 (container wiring), cross-topic 3 and 6; decision ledger `docs/plans/7b-decisions/models.md` MOD-6,
  MOD-7, MOD-8, MOD-9; merge-clashes MC-21 (`LANGFUSE_PROJECT_ID`, `config.py` owner AEA-02), MC-23 (`Redactor`), MC-24
  (missing keys → `off` → alert via the evaluator).
- stage7/data.md §1 (`redact`, `RedactionProfile.TRACE`, placeholders, what TRACE replaces); stage7/graph-core.md §12
  (`Settings.langfuse_*`, `langfuse_complete()`; no `langfuse_export()`, residual R-G-6 in
  `docs/plans/7b-decisions/residuals-graph.md`); stage7/cases.md §8 (`AlertWriter.fire`,
  `trace_export_failed` fires and clears).
- PRD R-36, R-35 (alerts on the page), §6.2 *Tracing*; US-27.
- DO-6 *Storage and access* (VPS Langfuse, own project, keys never YourAI's, deployed route only with Innocent's yes),
  *Content and redaction* (table and steps 2–3), *Missing instrumentation* rows "Traces are not exported" and "Records
  were written but to the wrong Langfuse project", *Alerts* row "Trace export", CAP-1, CAP-9, WF-1, WF-13, WF-17.
- DO-1 §8.2 row *Langfuse on the VPS*, §8.3 (traces: drop rather than block), §10 *Redaction* and *The Langfuse route*,
  §11 decision 8; SDQ-3; SDQ-9.
- DO-3 §4.2 (`TraceSink`: off, Langfuse, in-memory), §4.3, §6 S-10; DO-4 §13 (`TraceSink` and its Stage 7 superseded
  note), §16.
- Research §6 (SDK v5 ↔ server v4.59.0+, env vars, `mask_otel_spans`, collector-side masking too late); Langfuse Public
  API page (https://langfuse.com/docs/api-and-data-platform/features/public-api, read 2026-10-21), registered by this
  ticket as S-233.
- DO-7 M-29 (with the Stage 7 note on `sent`).
- **Brief check:** serves "Add observability so the business can see how the agent is performing after launch: volume,
  containment, escalations, failures, latency."; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [negative] Seeded values never reach an exported span, even when a caller passes them unmasked: the full phone `512-555-0102`, the name "Omar Patel" (introduced as "my name is Omar Patel"), a six-digit code, a synthetic card-like number and a fake key value are absent from every span the in-memory exporter receives; `[phone ending 02]` and the invoice facts remain — verify: `tests/contract/test_trace_sink_contract.py::test_mask_hook_strips_seeded_values` (real Langfuse SDK client, in-memory span exporter so the hook runs as in production, DO-6 *Capture verification*; the real `redact` from AEA-04) — evidence: assertions over the exported span attributes.
- [ ] AC-2 [invariant] The mask runs on **every** exported span, whatever created it (turn, node and model-call spans, and a span created directly through the Langfuse client) — verify: `::test_mask_applies_to_all_span_kinds` — evidence: a sentinel code set on each kind is `[code]` in all of them.
- [ ] AC-3 [failure/refusal] Export never blocks or fails a turn: with an exporter that hangs or errors, and with the queue full, `turn`/`model_call`/`node` each return within 50 ms [A] (MOD-8); filling the queue past `queue_max_spans` (1,024) drops the excess and `dropped_spans()` equals the spans refused — verify: `tests/unit/adapters/test_tracing_langfuse.py::test_export_never_blocks` — evidence: measured call times under 50 ms; drop counter equals the spans refused; no exception reaches the caller.
- [ ] AC-4 [failure/refusal] Start-up with keys that are not this app's project (a response listing another `id`; a response listing several projects, one of them this app's; a 401): export stays off, `export_status` is `off` for every turn, `on_alert` is called exactly once with `"wrong_project"`, **no span is sent**, and no re-check runs — verify: `::test_wrong_project_keys_turn_export_off` (stubbed `/api/public/projects` responses; the in-memory exporter receives nothing) — evidence: per fixture, zero exported spans, one alert call, status `off`, one request to the projects endpoint.
- [ ] AC-5 [failure/refusal] Langfuse unreachable at start-up (connection error, timeout, a 503): `start()` returns without raising, export is off, `on_alert("project_check_failed")` is called once, and after `recheck_after_s` on a fake clock the check runs again; when it then passes, export turns on — verify: `::test_unreachable_at_start_rechecks` — evidence: one alert; a second request after the fake 600 s; spans exported only after the passing re-check.
- [ ] AC-6 [invariant] Start-up with this app's project keys (exactly one project whose `id` equals `LANGFUSE_PROJECT_ID`; same name as another project does not matter): export on; the spans for one turn nest under one trace whose session id is the `thread_id`, and `SpanHandle.trace_id` is that 32-hex trace id — verify: `::test_one_trace_per_turn_with_session_id` — evidence: exported spans share one trace id equal to the handle's; parent links as asserted; the check compares `id`, shown by a fixture whose `name` differs.
- [ ] AC-7 [capture] `export_status(span)` yields exactly one of `off`, `sent`, `failed` per turn handle, with MOD-9's meanings, and two concurrent turns get their own status — verify: `::test_export_status_values` (a healthy turn → `sent`; a turn with one dropped span → `failed`; a turn after the exporter's last batch failed → `failed`; the null sink and an off sink → `off`; two interleaved turns where only one drops → `sent` and `failed`) — evidence: the expected value in each case, and no value outside `off`, `sent`, `failed`.
- [ ] AC-8 [invariant] `NullTraceSink` honours the same Protocol, sends nothing, yields `SpanHandle` with `trace_id=None` and reports `off`; both sinks pass the same Protocol-conformance test — verify: `tests/contract/test_trace_sink_contract.py::test_sinks_conform` — evidence: both parametrised cases pass.
- [ ] AC-9 [invariant] This ticket's container hunk builds `LangfuseTraceSink` only when all four `LANGFUSE_*` settings are set and `NullTraceSink` otherwise, without calling `on_alert` (MOD-6 step 5, MC-24); the Langfuse sink's `LangfuseExportSettings` is built from `Settings`' four `langfuse_*` fields, never through a `Settings.langfuse_export()` method (models.md §7, R-G-6) — verify: `tests/unit/web/test_register_tracing.py::test_sink_choice_by_settings` (each one of the four missing in turn, then all four set with a stubbed check) — evidence: four null sinks with zero alert calls; one Langfuse sink whose export settings carry the four configured values.
- [ ] AC-10 [negative] No key value reaches logs, alerts or spans: the Langfuse secret and public keys (fake values) are absent from captured log output, from every `on_alert` argument (whose only argument is the reason code) and from exported spans; the project-check response body is not logged — verify: `::test_keys_never_logged` — evidence: keys absent everywhere searched; `on_alert` call args equal `("wrong_project",)` or `("project_check_failed",)`.
- [ ] AC-11 [journey] No deterministic journey reaches this code (journeys run with `NullTraceSink`), so this issue extends none: the affected-journey command (AEA-01) run on this diff selects no journey and exits 0, and the record `docs/testing/journeys/YYYY-MM-DD-AEA-19.md` says so and names where it is proved instead (this issue's own tests, CAP-9 and AEA-61's trace records) (pattern D, `docs/plans/ux-join/backend-amendments.md` §3) — verify: the command's output and the record — evidence: "0 journeys affected"; the record's Level and Blocked-by fields.
- [ ] AC-12 [regression/context] In the same change: `.claude/reference/area-map.md` A10a row (`adapters/tracing_langfuse.py` planned → actual + commit); `.claude/state/icm-progress.md` A10a evidence replaced; `docs/design/code-design.md` A10a status for this file (planned → built); the Langfuse Public API page registered as **S-233** (or the next free `S-N`) in `docs/source/source-register.md` before it is cited (context-maintenance rule 5); a dev-log entry per `.claude/reference/dev-log.md` — verify: `git diff --stat` on those paths — evidence: the diff.

### Observability
- Responsibilities: for WF-1 (and WF-9 / WF-10 runs tagged `eval` / `load`): the trace per turn with nested node and
  model-call spans, masked with the TRACE profile; `turn.trace_export` via `export_status(span)` (MOD-9); the
  dropped-span count `trace_export_dropped`. For WF-13 (start-up): export on or off, which AEA-50/AEA-32 stamp on the
  `deploy_record`. For WF-17: the `wrong_project` / `project_check_failed` alert, recorded as a `trace_export_failed`
  `health_event` by AEA-32's `AlertWriter`.
- Capture evidence: AC-1, AC-4, AC-6 and AC-7 drive the sink through the real Langfuse client with an in-memory
  exporter; AEA-51's CAP-1 (CON-2 with the seeded values) and AEA-50's CAP-9 ("with the wrong project's keys, export off
  and an alert") prove it at the real entry points.

### Evaluation
- Checks: none added to E-1…E-8; traces are read in Stage 9 error analysis (evaluation plan, *Error analysis comes
  first*), never scored. "It ran" is not "it was right" (DO-6 *Two questions*).
- Expected-answer authority: DO-6 *Content and redaction* and data.md §1's TRACE row decide what a span may hold; CAP-1's
  seeded values decide the negative checks.

### Metrics
- References: M-29 (trace export completeness = turns with `trace_export` = `sent` ÷ turns).
- Acceptance conditions: M-29 stays computable from `turn.trace_export`, with `off` shown as off while the deployed
  route awaits Innocent's yes, and `sent` meaning "handed to a healthy exporter" (DO-7 M-29 Stage 7 note; blind window
  about one batch interval plus the export timeout, ~10 s [A]). Measurement-only; no target.

### Blocked by
- AEA-02 (`TraceSink`, `ExportStatus`, `SpanHandle`, `TurnIds`, `CallRecord`; `Settings.langfuse_*`), AEA-04
  (`privacy/redact.py`: `redact`, `Redactor`, `RedactionProfile.TRACE`).

### Agent handoff
- Area / owner: A10a Ops; file `src/meridian/adapters/tracing_langfuse.py`, tests `tests/contract/test_trace_sink_contract.py`
  (DO-3 §9 names this file; no other ticket owns it), `tests/unit/adapters/test_tracing_langfuse.py` and
  `tests/unit/web/test_register_tracing.py`; only its own `register_<area>()` stub in `web/container.py`.
- Contracts and shared surfaces: **consumes** `ports/runtime.py` `TraceSink`, `ExportStatus`, `domain/turn.py`
  `SpanHandle`, `TurnIds`, `ports/models.py` `CallRecord`, `config.py` `Settings` (AEA-02; its four `langfuse_*` fields and `langfuse_complete()`, no `langfuse_export()`, R-G-6),
  `privacy/redact.py` (AEA-04).
  **Produces** both sinks, `TraceAlert`, `TraceAlertReason` and `LangfuseExportSettings` for AEA-20 (model-call spans
  through `ctx.span`), AEA-21 (node spans), AEA-40 and AEA-42 (open the turn span, call `export_status(span)` after it
  closes, write `trace_id` / `trace_export`), AEA-51 (wiring; binds `on_alert` to `AlertWriter`; CAP-1), AEA-50 (CAP-9
  start-up check), AEA-32 (receives the alert), AEA-53 (M-29 on CON-19). AEA-11's `InMemoryTraceSink` implements the
  same Protocol (stage7/models cross-topic 2). **Must not edit:** `privacy/redact.py` (AEA-04), `services/health.py` and
  `repos_ops.py` (AEA-32), `config.py`, `ports/*`, `domain/*` (AEA-02), `tests/fakes/*` (AEA-11), `tests/capture/*`
  (AEA-50, AEA-51).
- Scope boundary / refusal: no Langfuse hosting, no public route, no proxy (SDQ-3; DAT-4; AEA-09/56); no collector-side
  masking (too late, research §6); never uses YourAI's Langfuse keys or project; no database write; no live call to the
  VPS Langfuse in a default test (a `live`-marked check is optional).
- Wave and gates: wave 1; gates None for the build. Turning export on in the deployed app is a deploy-time
  `gate::human` step outside this ticket (Innocent creates the project and sets `LANGFUSE_PROJECT_ID`; models
  cross-topic 7).
- Lane: `lane::build-loop` — source and tests.
- Risk: **security** (`risk::security`, slice plan row AEA-19): a bug here sends a code, card-like number, contact
  detail or key to a trace store, or sends spans to another project. Frozen failing tests first; `security-privacy-agent`
  at the wave merge.
- Awaiting Innocent: DAT-1 — built on the recommended option A (introduction and street-address patterns in the TRACE
  profile; the limit written into DO-6). If he picks B, AEA-04's `redact` gains a keyword-only `known` argument that the
  gateway passes (data.md §1); for the export-time layer to match, the mask hook would need the turn's located-customer
  values as well (a signature question for AEA-02 and AEA-20 at that point); if C, only AEA-04 changes and AC-1 gains loose-name cases.
- Awaiting Innocent: DAT-4 — built on the recommended option A (the ingestion-only route opened on a hostname he names).
  If he picks B, nothing in this ticket changes: the deployed app never gets the four `LANGFUSE_*` values, always runs
  `NullTraceSink`, and M-29 reads `off` with `trace_export_failed` firing for as long as the app runs.
- Workflows fed (not entry points): WF-1 traces and `trace_export`, WF-13 start-up export on/off, WF-17 alert record.
- Entry points added or changed: None
