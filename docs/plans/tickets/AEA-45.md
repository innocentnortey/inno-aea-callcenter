## [AEA-45] staff API: queue, case, actions, contact log, flags, oversight (CON-11…13, 15…17)

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

> **US-19:** "As a **representative**, I need an eight-heading brief that keeps facts and customer claims apart, the
> pertinent sources (what the AI saw and the current value), the promise with the follow-up preference beside it, and the
> full chat one click away, so that I can act without re-asking the customer."
> **US-22:** "As a **supervisor**, I need one view of P0/P1, unowned, due-soon, overdue and stuck-waiting cases with owner,
> age and follow-up preference, and to assign or reassign with a reason, so that no promise is missed."

The staff console's case routes in `web/routes/staff_cases.py`, with wire models in `web/schemas/staff_cases.py` whose
fields are copied from the OpenAPI schemas. Each route is thin: it checks the role, validates the request, takes **one
demo-clock reading** for `now`, makes **one** service call, maps a rejection to its documented status and serialises the
result. Lifecycle rules, ordering, due states, lanes, `allowed_actions`, promise marking and the "Demo: recorded, not
sent" label are all `CaseService`'s (AEA-29, cases.md §5) or `FlagService`'s (AEA-44, staff.md §2); the route decides
none of them.

| Operation | CON | Service call (injected through `web/deps.py`) | Role check (`require_staff`, web.md §3) |
|---|---|---|---|
| `getQueue` `GET /api/staff/queue` | CON-11 | `CaseService.queue(actor.role, now)` | `(REPRESENTATIVE, SUPERVISOR)` |
| `getCase` `GET /api/staff/cases/{reference}` | CON-12 | `CaseService.detail(case_ref, actor.role, now)` | `(REPRESENTATIVE, SUPERVISOR, OWNER)` |
| `applyCaseAction` `POST …/{reference}/actions` | CON-13 | `CaseService.apply(case_ref, action, actor, expected_version, now)` | `(REPRESENTATIVE, SUPERVISOR)`; for `assign` and `change_priority` a second `actor_for` call with `(SUPERVISOR,)` (STF-3, MC-4) |
| `recordContactActivity` `POST …/{reference}/activities` | CON-15 | `CaseService.record_activity(case_ref, activity, actor, now)` | `(REPRESENTATIVE,)` |
| `createFlag` `POST /api/staff/flags` | CON-16 | `FlagService.flag(FlagIn, actor)` | `(REPRESENTATIVE, SUPERVISOR)` |
| `listFlags` `GET /api/staff/flags` | CON-16 | `FlagService.list_flags()` | `(REPRESENTATIVE, SUPERVISOR, OWNER)` |
| `reviewFlag` `PATCH /api/staff/flags/{flag_id}` | CON-16 | `FlagService.review(flag_id, note, actor)` | `(SUPERVISOR,)` |
| `getOversight` `GET /api/staff/oversight` | CON-17 | `CaseService.oversight(now)` | `(SUPERVISOR,)` |

**Identity (STF-1).** The acting identity is the **role**: `require_staff` returns `StaffActor(role, name, signature)`
from `domain/staff.py` (staff.md §1, AEA-02). Two login sessions acting as Riley are the same actor and share Riley's
claims. **`now`:** web.md §4 declares no separate demo `Clock` provider, so the route reads
`get_demo_service().clock_view().now` once per request (cases.md §6, `ClockView` = OpenAPI `DemoClock`) and never the
server clock (R-3). Flag routes pass no `now`: `FlagService` stamps the demo clock itself (staff.md §2).

**Rejection mapping.** `CaseActionRejected` codes map to the statuses the OpenAPI documents: `CASE_NOT_FOUND` → 404;
`VERSION_CONFLICT`, `CASE_ALREADY_CLAIMED`, `NOT_ALLOWED_IN_STATE` → 409; `REASON_REQUIRED`, `WAKE_UP_REQUIRED`,
`OUTCOME_REQUIRED` → 422, raised as `ApiProblem` (web.md §1), so AEA-23's request-schema 422 → 400 handler never
touches them. `FlagRejected` (staff.md §2) maps `CASE_NOT_FOUND` → 404, `FLAG_NOT_FOUND` → 404, `VALIDATION_ERROR` →
400 with its `field` and `constraint` (STF-10). `details` never carries a rejected value (DO-4 §0).

**`result_line` (STF-9, staff.md §6),** composed in `schemas/staff_cases.py` from the action, the returned case summary
and the actor, times in America/Chicago as "Mon Oct 19 · 9:00 am": claim `Claimed · {actor.signature}`; wait
`Waiting until {wake_up_at}`; resolve `{reference} resolved.`; assign `Assigned to {STAFF_PERSONAS[owner].signature}.`;
change_priority `Priority is now {level} · {word}.` (these five are the OpenAPI examples word for word); release
`Released back to Unassigned.`, start `In progress · {actor.signature}`, close_unresolved `{reference} closed
unresolved.` (proposals, constants in the schema file).

**Request rules (staff.md §6).** Flag `note`, `reason` and review `note`: stripped, blank → null, more than 2,000
characters → 400 `VALIDATION_ERROR` with the field named and constraint "at most 2000 characters"; never echoed.

**During a reset (staff.md §11, STF-7).** None of these eight operations documents 503: AEA-23's middleware waits
`limits.web.reset_wait_s` (5 s [A]) for `ResetGate` to clear and the route then runs against the post-reset state
(typically 403 `ROLE_NOT_ALLOWED` `role_reset`, or 404 for a cleared case or flag). The route adds no reset check.

**Example pair (seeded case MHC-C-0007, tied to WP-2).** MHC-C-0007 is the seeded billing dispute whose source card
shows WP-2's record-vs-policy mismatch ("Changed since the AI saw it: was $144.00, now $149.00", SCREEN_SPECS SCR-6).
Acting as the representative, `POST /api/staff/cases/MHC-C-0007/actions` `{"action": "claim", "expected_version": 3}` →
200 (OpenAPI example `CLAIMED`): `case.lifecycle` "claimed", `owner` "Riley", `version` 4, `result_line` "Claimed · Riley
(demo)". If the supervisor (a second browser) claimed it first, the same request answers 409 `CASE_ALREADY_CLAIMED` with
`details.claimed_by` "Demo supervisor"; with a stale version, 409 `VERSION_CONFLICT` with `details.changed_by`,
`changed_at`, `current_version` 4. A release without a reason answers 422 `REASON_REQUIRED` (`field` "reason",
`constraint` "required for release, assign and change_priority"). The same representative sending `{"action": "assign",
"assignee": "riley", "reason": "…", "expected_version": 4}` gets 403 `ROLE_NOT_ALLOWED` with `details.needs`
`["supervisor"]` and the service is never called.

**Produced for other issues:** CON-11…13 and CON-15…17 for AEA-52 (binds the real `CaseService` and `FlagService`,
proves CAP-4 end to end) and AEA-55 (the UI against the real backend).

### Source

- PRD R-25, R-28, R-29, R-30, R-32, R-33, R-34, R-37, R-48; US-18, US-19, US-20, US-21, US-22, US-23; WP-2.
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml`: `getQueue`, `getCase`, `applyCaseAction`,
  `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag`, `getOversight`; schemas `QueueResponse`, `QueueRow`,
  `CaseDetail`, `CaseSummary`, `CaseActionRequest`, `CaseActionResponse`, `ActivityRequest`, `ActivityResponse`,
  `FlagRequest`, `Flag`, `FlagsResponse`, `FlagReviewRequest`, `OversightResponse`, `ApiError`; responses
  `Unauthenticated`, `RoleNotAllowed`, `CaseNotFound`, `ValidationError`; each operation's `x-roles`.
- `UI_CONTRACTS.md` CON-11, CON-12, CON-13, CON-15, CON-16, CON-17, *Data classes* (D2, D4), *Access*, *Named errors*.
- `docs/design/contracts/stage7/staff.md` §1 (`StaffRole`, `StaffActor`, `STAFF_PERSONAS`, `ASSIGNEE_ROLES`), §2
  (`FlagService`, `FlagIn`, `FlagRecord`, `FlagRejected`), §6 (request rules, `result_line`), §10 (time sources), §11
  (during a reset); `stage7/web.md` §1 (`ApiProblem`), §3 (`require_staff`, `StaffAccess.actor_for`), §4 (providers
  `get_case_service`, `get_flag_service`, `get_demo_service`, `get_staff_access`), §7 (`ResetGate`), §10 (`request`
  record), §13 (`openapi_check.py`); `stage7/cases.md` §5 (`CaseService` rules and view types), §6 (`clock_view`).
  Decisions: `docs/plans/7b-decisions/staff.md` STF-1, STF-2, STF-3, STF-7, STF-8, STF-9, STF-10, STF-26; merge
  MC-2, MC-4, MC-12, MC-14; graph-core *cases A-2* row (view types in `domain/`, accepted).
- DO-4 §7 (`Brief`, eight headings), §13 (`CaseService` signatures; "Staff routes never call `open_case`"); DO-3 §6 S-7;
  system design §8.2 *Staff actions (CON-13)*.
- DO-6 WF-4, CAP-4, *Content and redaction*; DO-7 M-3, M-13, M-27.
- SCREEN_SPECS SCR-5…SCR-8 (states only).
- Slice plan §0a (journey map, J-6) and rule `.claude/rules/integrated-journeys.md` §3–§4; UX-join amendments
  `docs/plans/ux-join/backend-amendments.md` AEA-45-1, AEA-45-3 and §3 (AEA-45-2 waits on Innocent's Decision 2); residual
  R-W-13 (`docs/plans/7b-decisions/residuals-web.md`: `allowed_actions` is `CaseService`'s, the route passes it through).
- **Contract notes (OpenAPI wins; listed, not edited; AEA-08 reconciles the documents, STF-26):** (1) api-con-mapping §1
  serves these from `web/routes/staff.py`; the slice plan gives them `web/routes/staff_cases.py`. (2) The OpenAPI
  `getCase` description still says "Owner role: read only [open: …]"; UI_CONTRACTS CON-12 settles it (only the customer
  role is refused; the owner gets `allowed_actions: []`, computed by `CaseService.detail`). (3) `getCase` documents no
  400: a `reference` that fails `^MHC-C-[0-9]{4}$` answers 404 `CASE_NOT_FOUND` there; `applyCaseAction` and
  `recordContactActivity` document 400 and answer 400 `VALIDATION_ERROR` field `reference`. (4) System design §8.2 says
  `CONFLICT_STALE`; the decided name is `VERSION_CONFLICT`. (5) SCR-6's flag-form wording and api-con-mapping UXR-22's
  fixed labels are superseded by UXR-22 as adopted: `reason` is optional free text and `target` carries the kind.
- **Brief check:** serves "Escalation must be graceful: … hands off with enough context that a human can pick up without
  starting over." (Part B §4) and "Include a feedback or learning loop. Logged conversations, flagged failures, or human
  corrections should feed back into improving the system over time." (Part B §7); touches nothing out of scope; weakens
  nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Every 2xx body validates against its OpenAPI response for each named example shape (`getQueue`: SEEDED, STAFFED_WITH_WAITING, ALL_CAUGHT_UP, BRIEF_BEING_WRITTEN; `getCase`: DEFAULT, BRIEF_BEING_WRITTEN, TRIMMED_STOP, SAFETY_CASE, LIVE_JOINED, WAITING, FEE_BEARING_CHANGE; `applyCaseAction`: CLAIMED, WAITING, RESOLVED, ASSIGNED, PRIORITY_CHANGED; `recordContactActivity`: CALL_REACHED, EMAIL_LEFT_MESSAGE; `createFlag`: ANSWER; `listFlags`: THREE, EMPTY; `reviewFlag`: REVIEWED; `getOversight`: SEEDED, AFTER_ADVANCE, SHIFT_ENDED_WITH_WAITING, NOTHING_URGENT), with each service double returning that example's content — verify: `tests/api/test_staff_cases_routes.py::test_<operationId>_matches_openapi` (eight tests, each using AEA-23's `tests/api/openapi_check.py::assert_response_matches`, STF-8; no validator of its own) — evidence: every listed shape validates.
- [ ] AC-2 [invariant] `result_line` follows staff.md §6: the five sourced lines equal the OpenAPI examples word for word ("Claimed · Riley (demo)", "Waiting until Mon Oct 19 · 9:00 am", "MHC-C-0007 resolved.", "Assigned to Riley (demo).", "Priority is now P2 · Time-sensitive."), and release, start and close_unresolved give "Released back to Unassigned.", "In progress · Riley (demo)", "MHC-C-0007 closed unresolved." — verify: `…::test_result_lines` (parametrised over the eight actions) — evidence: eight equality asserts pass.
- [ ] AC-3 [failure/refusal] Role matrix from `x-roles`, enforced before any service call: the customer role gets 403 `ROLE_NOT_ALLOWED` on all eight operations; the owner reads `getCase` and `listFlags` and gets 403 on every write and on `getQueue` / `getOversight`; a representative gets 403 on `reviewFlag` and `getOversight`; the supervisor gets 403 only on `recordContactActivity`; every 403 carries `details.role`, `details.needs` in the operation's x-roles order (e.g. `["representative", "supervisor"]` on `getQueue`) and `details.reason` `wrong_role` (STF-20, MC-4) — verify: `…::test_role_matrix` (parametrised; `get_staff_access` overridden with a double over real `RoleRefusal` values; service doubles record calls) — evidence: every 403 body validates against `RoleNotAllowed`; refused cells record zero service calls.
- [ ] AC-4 [failure/refusal] Per-action roles (STF-3): a representative sending `assign` or `change_priority` gets 403 `ROLE_NOT_ALLOWED` with `details.needs` `["supervisor"]` from the second `actor_for(session, (SUPERVISOR,))` call and `CaseService.apply` is never called; the supervisor passes both — verify: `…::test_assign_and_priority_supervisor_only` — evidence: two 403 bodies validate; zero `apply` calls; two supervisor 200s.
- [ ] AC-5 [invariant] The acting identity is the role (STF-1): two login sessions both acting as representative hand `CaseService.apply` equal `StaffActor(role=representative, name="Riley", signature="Riley (demo)")` values, so a claim made through one is "claimed by you" for the other — verify: `…::test_actor_is_the_role` (two cookies, one double) — evidence: the two recorded actors compare equal.
- [ ] AC-6 [invariant] `getCase` never answers `ROLE_NOT_ALLOWED` to a staff role and passes the service's `CaseDetail` through unchanged: the brief's eight headings in order, `trimmed` flags, per-source `changed_since`, `current_unavailable`, nullable `version_date` with `version_label` (UXR-24), staff-only sources with `audience: "staff_only"`, and the owner's `allowed_actions: []` as the service returns it — verify: `…::test_case_detail_passthrough` — evidence: body equals the double's `CaseDetail` field for field.
- [ ] AC-7 [failure/refusal] `CASE_NOT_FOUND` (404) for an unknown reference on `getCase`, `applyCaseAction`, `recordContactActivity` and an unknown `case_ref` on `createFlag`; a malformed reference answers 404 on `getCase` and 400 `VALIDATION_ERROR` field `reference` on `applyCaseAction` and `recordContactActivity` (contract note 3) — verify: `…::test_case_not_found_and_malformed_reference` — evidence: bodies validate against `CaseNotFound` / `ValidationError`.
- [ ] AC-8 [failure/refusal] `applyCaseAction` maps each `CaseActionRejected`: stale `expected_version` → 409 `VERSION_CONFLICT` with `details.changed_by`, `changed_at`, `current_version`; claimed by another role → 409 `CASE_ALREADY_CLAIMED` with `claimed_by`, `claimed_at`; wrong state → 409 `NOT_ALLOWED_IN_STATE` with `state`, `needs` — verify: `…::test_case_action_409s` — evidence: three bodies carry the codes and `details` keys of the OpenAPI examples and validate.
- [ ] AC-9 [failure/refusal] **WF-4:** Named 422s stay 422 and schema failures are 400: `REASON_REQUIRED` (field `reason`), `WAKE_UP_REQUIRED` (field `wake_up_at`) and `OUTCOME_REQUIRED` (field `outcome`) returned by the service double answer 422 with the OpenAPI constraint text, while a body missing `expected_version` answers 400 `VALIDATION_ERROR` field `expected_version` from AEA-23's handler — verify: `…::test_named_422_vs_400` — evidence: three 422 bodies and one 400 body validate against their documented responses.
- [ ] AC-10 [invariant] `recordContactActivity` returns 201 with the service's `activity.label` unchanged ("Demo: recorded, not sent", R-34) and maps `NOT_ALLOWED_IN_STATE` and `VERSION_CONFLICT` to 409 — verify: `…::test_contact_activity` — evidence: label equality; two 409 bodies validate.
- [ ] AC-11 [failure/refusal] Flags (STF-10, staff.md §6): `createFlag` returns 201 with `reason` null when omitted or blank; a `note`, `reason` or review `note` of 2,001 characters → 400 field named, constraint "at most 2000 characters"; a `FlagRejected` with field `message_id` → 400 field `message_id`, constraint "not a message of this case"; `reviewFlag` with `status` other than "reviewed" → 400 field `status`; an unknown `flag_id` → 404 `FLAG_NOT_FOUND`; `listFlags` returns the service's order unchanged — verify: `…::test_flags` — evidence: bodies validate; order equals the double's; no 400 body contains the rejected text.
- [ ] AC-12 [invariant] **WF-4:** Every case operation passes one demo-clock reading as `now`, never the server clock: with `DemoService.clock_view().now` fixed at 2026-10-19 07:00 −05:00 the doubles of `queue`, `detail`, `apply`, `record_activity` and `oversight` receive exactly that instant, and `routes/staff_cases.py` contains no `datetime.now`, `time.time` or `date.today` — verify: `…::test_now_is_demo_clock` plus `grep -nE "datetime\.now|time\.time|date\.today" src/meridian/web/routes/staff_cases.py src/meridian/web/schemas/staff_cases.py` — evidence: received `now` equals the fixed value on all five; grep prints nothing.
- [ ] AC-13 [negative] Queue and oversight rows carry the display name only (D2; `QueueRow` has no contact field): a double whose rows also carry the seeded customer MHC-10002's email and street address as extra attributes produces `getQueue` and `getOversight` bodies containing neither — verify: `…::test_queue_and_oversight_carry_no_contact` — evidence: both strings absent from both bodies.
- [ ] AC-14 [negative] Staff free text stays out of logs (D4; DO-6 *Content and redaction*): a distinctive release reason, resolve outcome, activity note, flag note and flag reason reach the service doubles' arguments and are absent from every captured log record (all loggers, the `request` record included); no 400 body echoes a rejected value — verify: `…::test_staff_text_never_logged` — evidence: the five strings present in the recorded calls and absent from captured logs.
- [ ] AC-15 [invariant] **WF-4:** Login gate and reset behaviour come from AEA-23's real middleware: without `mhc_session` all eight operations answer 401 `UNAUTHENTICATED`; a session whose role a reset sent back gets 403 `ROLE_NOT_ALLOWED` with `details.reason` `role_reset` unchanged; with a fake `ResetGate` held for less than `reset_wait_s`, `getQueue` waits and answers 200, never 503 (staff.md §11) — verify: `…::test_login_gate_role_reset_and_reset_wait` — evidence: eight 401 bodies; one 403 with `role_reset`; one 200 and no 503.
- [ ] AC-16 [invariant] Staff routes never open a case (DO-4 §13): `grep -n "open_case" src/meridian/web/routes/staff_cases.py src/meridian/web/schemas/staff_cases.py` prints nothing — verify: the grep, run by `code-review-agent` — evidence: empty output.
- [ ] AC-17 [capture] Driving each of the eight entry points through the app the container builds (services overridden with doubles) leaves one `request` record per call (web.md §10: `request_id` = the `X-Request-ID` header, `route` the template such as `/api/staff/cases/{reference}/actions`, `status`, `caller_role`), and every write hands its service the `StaffActor` (role and name) plus the reason, outcome or note, so AEA-29 and AEA-44 can write `case_event` with actor role and reason and the flag row (DO-6 WF-4) — verify: `…::test_wf4_case_entry_points_emit_records` — evidence: eight records and the captured actors printed; no raw path or case reference in any `route` field. The full CAP-4 is AEA-52's.
- [ ] AC-18 [invariant] The routes add, drop and rewrite nothing in a case view: `allowed_actions` and every display field of `QueueRow`, `CaseSummary` and `CaseDetail` (`reason`, `priority.word`, `due_label`, `age_label`, `follow_up_short`, `queued_at`, `identity.line`, `BriefItem.source_ids`, `CaseSource.source_id`, `version_label`) reach the client exactly as the `CaseService` double returns them, for each staff role; the owner's `[]` comes from the double, not from the route (AEA-45-1; staff audit A1, A2; `allowed_actions` = cases.md §5's table ∩ `ROLE_ACTIONS`, computed by `CaseService`, staff.md §1, R-W-13) — verify: `tests/api/test_staff_cases_routes.py::test_views_pass_through_unchanged` (a double returning distinctive values per field and per role) — evidence: the response JSON equals the double's serialised view for representative, supervisor and owner.
- [ ] AC-19 [contract] `tests/contract/cases/staff_cases.py` holds the server cases for `getQueue`, `getCase`, `applyCaseAction`, `recordContactActivity`, `createFlag`, `listFlags`, `reviewFlag` and `getOversight`: preconditions (a role per operation's x-roles; a seeded case reference), every named request example, and each documented error status the routes can produce (401, 403 `ROLE_NOT_ALLOWED`, 404, 400, 409 `VERSION_CONFLICT` / `CASE_ALREADY_CLAIMED` / `NOT_ALLOWED_IN_STATE`, 422 `REASON_REQUIRED` / `WAKE_UP_REQUIRED` / `OUTCOME_REQUIRED`) (AEA-45-3) — verify: `CONTRACT_STRICT=1 uv run pytest tests/contract/test_openapi_server.py -k "Queue or Case or Contact or Flag or Oversight" -rs` once AEA-59's runner is merged — evidence: one pass per case; skips only as `not bound: <name>` for a later issue's provider.
- [ ] AC-20 [journey] Extends J-6 (slice plan §0a journey map): the representative claims the escalated case (`result_line` "Claimed · Riley (demo)"), the queue and case view carry `allowed_actions` and the display fields unchanged, and a stale `expected_version` answers `VERSION_CONFLICT`; asserting what the user sees and what is stored, in `tests/journeys/j6/test_aea_45.py` with the scripted model adapter on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j6/test_aea_45.py` — evidence: the steps pass at level `integrated with a scripted model`; until AEA-57 and AEA-52 land, the record `docs/testing/journeys/YYYY-MM-DD-AEA-45.md` states level `mock-tested` and *Blocked by* AEA-57 and AEA-52 (`integrated-journeys.md` §4).
- [ ] AC-21 [regression/context] Same change updates `.claude/reference/area-map.md` (this issue's row, planned → actual with the commit), `.claude/state/icm-progress.md` (the A9 staff-console row's evidence link) and DO-3 §3's status for `web/routes/staff_cases.py` and `web/schemas/staff_cases.py` — verify: `git diff --stat` — evidence: only those rows change.

### Observability

- Responsibilities: WF-4 (DO-6 registry) — the middleware's `request` record per call with `caller_role` and the route
  template (AC-17); a `StaffActor` plus the reason or outcome handed to every write so `case_event` rows carry actor
  role, action and reason and flag rows keep case and message references (written by AEA-29 and AEA-44); no D2 contact
  value or D4 free text in any log (AC-13, AC-14).
- Capture evidence: AC-17 (the eight entry points through the app), AC-18 (views passed through unchanged), AC-13 and
  AC-14 (negative). CAP-4 end to end is AEA-52's.

### Evaluation

- Checks: none added. WF-4's evaluation duty (DO-6: "flags feed the review list (R-37), never the eval set unreviewed")
  is kept: `createFlag` and `reviewFlag` reach only `FlagService`, which touches only `flags` (staff.md §2, AEA-44
  AC-11), and the route writes no eval file or row (AC-11, AC-17). The route serialises the brief and the promise
  without changing them (AC-6), so E-6's "promise equal to the table" and "every brief number in the lookup log or chat"
  stay scorable from the stored records.
- Expected-answer authority: the policy table and the D4 priority table for promises; the hand-written required-item
  list for briefs (DO-5 *Expected-answer authority*). Nothing in this issue decides a correct answer.

### Metrics

- References: M-13 (promises kept on time), M-27 (unowned and overdue cases), M-3 (live AI-resolved rate, not flagged).
- Acceptance conditions: M-13 and M-27 stay computable because every action reaches `CaseService` with the demo-clock
  `now` and the actor (AC-12, AC-17), so a resolve or a CON-15 contact before or after the promise due is recorded and
  marked by `CaseService` (cases.md §5 *Promise kept / missed*); M-3 stays computable because flags keep their case and
  message references (AC-11). No target is set here.

### Blocked by

- AEA-23 (web app, middleware, `web/deps.py` with `require_staff`, `get_case_service`, `get_flag_service`,
  `get_demo_service`, `openapi_check.py`).
- Evidence only, not a merge edge (wave unchanged): AC-19's strict run waits for AEA-59's runner, and AC-20's journey
  record stays `mock-tested` with *Blocked by* AEA-57 and AEA-52 until they land (`integrated-journeys.md` §4).

### Agent handoff

- **Area / owner:** A9 Staff console (DO-3 §8); files `src/meridian/web/routes/staff_cases.py`,
  `src/meridian/web/schemas/staff_cases.py`, this issue's `register_…()` hunk in `web/container.py` (includes the router
  only; the services are bound by AEA-29 and AEA-44's hunks), tests under `tests/api/`,
  `tests/contract/cases/staff_cases.py` (AC-19) and `tests/journeys/j6/test_aea_45.py` (AC-20; `tests/journeys/support/`
  is AEA-57's, never edited here).
- **Contracts and shared surfaces:** consumes `CaseService.queue/detail/apply/record_activity/oversight` (AEA-29,
  injected), `FlagService` (AEA-44, injected), `DemoService.clock_view` (AEA-30, injected), `require_staff` and
  `StaffAccess` (AEA-23 declares, AEA-44 implements), `domain/staff.py` (AEA-02), and the case view types of cases.md
  A-2 (`QueueView`, `CaseDetail`, `OversightView`, `CaseAction`, `CaseActionRejected`, `ActivityIn`, `Activity`: fields
  from the OpenAPI schemas, homed in `domain/` by an AEA-02 follow-up, graph-core *cases A-2* row). If that follow-up has
  not merged when the planner starts, the plan records `blocked-on` it; the wire models here are this issue's own either
  way. Produces CON-11…13 and CON-15…17 for AEA-52 and AEA-55. Must not edit: `web/{app,middleware,deps,errors}.py`,
  `routes/auth.py`, `routes/staff_session.py`, `routes/staff_live.py`, `routes/staff_clock.py`, `routes/reads.py`,
  `services/*`, `domain/*`, `tests/api/openapi_check.py`, the OpenAPI.
- **Scope boundary / refusal:** no case lifecycle rules, ordering, due-state, lane or `allowed_actions` logic in the
  route; no live join or messages (AEA-46); no clock advance (AEA-47); no owner metrics (AEA-48); never calls
  `open_case`; no reset check of its own.
- **Decisions applied:** STF-1 (identity is the role), STF-2 / MC-2 (types in `domain/staff.py`), STF-3 / MC-4 (second
  `actor_for` for assign and change_priority; `needs` in x-roles order), STF-7 / MC-14 (no 503; middleware waits), STF-8
  (shared validator), STF-9 (`result_line` table), STF-10 (`FlagService` and its rejections), STF-26 (contract notes are
  AEA-08's to reconcile).
- **Wave and gates:** wave 2; no gate.
- **Lane:** `lane::build-loop` — route, schema and test code (ticket-lanes: changes code).
- **Risk:** None (slice plan). Roles are demo labels behind the login (R-48); the login gate itself is AEA-23/AEA-44.
- **Entry points added or changed:** WF-4 (`getQueue`, `getCase`, `applyCaseAction`, `recordContactActivity`,
  `createFlag`, `listFlags`, `reviewFlag`, `getOversight`).
