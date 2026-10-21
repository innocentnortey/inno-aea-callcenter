## [AEA-52] integration B: staff and demo end to end

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

The staff console API and the demo controls were built in wave 2 against DO-4 signatures with doubles. This issue wires
the **real services behind CON-7…CON-17 and CON-21** (and the CON-3 events those services write) and proves, through the
HTTP API of the app `create_app()` builds, the reviewer's staff story end to end:

> sign in once (CON-22) → switch to the demo representative (CON-10) → see the queue with the four seed cases (CON-11) →
> open the WP-7 refund case (CON-12) → claim it (CON-13) → join the live chat (CON-14), reply, hand back → record a contact
> attempt (CON-15) → flag an AI mistake (CON-16) → as the supervisor, advance the demo clock past WP-4's 12:00 case due
> (CON-8) → the scheduler writes `overdue` and oversight shows it (CON-17) → reset the demo (CON-9).

**The integration harness** (the real entry point; slice plan Amendment 1: "AEA-51 / 52 run on the harness (AEA-57), not
on fakes at the TestClient"): AEA-57's `tests/journeys/support/` builds the real app from `web/container.py` on a
disposable copy of the issued DB, first boot loads the four seed cases MHC-C-0005…MHC-C-0008 (cases.md §7), the login
helper signs in (CON-22), and the DB-state reader checks stored rows. The real `DemoClock` starts at `DEMO_START`
(Fri 2026-10-16 10:00 America/Chicago). Live cases come from the **real** `HandoffService` (AEA-29) driven through CON-2 or
CON-4 with the scripted model adapter (WP-7: refund, P3, MHC-C-0009 onwards; WP-4: `fee_bearing_change`, P2, case due 12:00
today, promise due Mon Oct 19, 7:00 pm, CAS-10; one live-queued case opened while staffed). No model is called by any staff
route. Every response is checked with `tests/api/openapi_check.py::assert_response_matches` (web.md §13).

**Seams this issue proves (double in the consumer's own tests → real object wired here):**

| # | Consumer (ticket) | Double it was built against | Real object (ticket) | DO-3 seam | Proven by |
|---|---|---|---|---|---|
| 1 | `require_staff(*roles)` in `web/deps.py` (23), used by routes 45, 46, 47, 48 | `get_staff_access` override | `StaffSessionStore.actor_for` and `switch_role` (44) | S-18 | AC-1, AC-5 |
| 2 | CON-11…13, 15…17 routes (45) | provider overrides | `CaseService` (29); `FlagService` (44) | S-7 | AC-2, AC-5, AC-9, AC-10, AC-11, AC-16 |
| 3 | CON-14, CON-21 (46) | `CaseService` double | `LiveChatService` (46) over `CaseService` (29); `conversations.controller`, `live_state` and `events` in `repos_core` (10); the customer `submitTurn` relay and `getChatThread` history (40) | S-7, S-11 | AC-2, AC-3, AC-4, AC-17, AC-18 |
| 4 | CON-8 advance (47) | `DemoService` double | `DemoService.advance_clock(step, actor=…, request_id=…)` (30, MC-13) | S-8 | AC-6 |
| 5 | CON-7, CON-8 read, CON-9 (43) | provider overrides | `DemoService` (30), `ResetService` (31) with `ResetGate` (23) | S-8, S-20 | AC-7, AC-8 |
| 6 | CON-3 customer stream (41) | `events` rows from its fixture | events written by 30 (`clock_changed`, `staffing_changed`, `shift_ended`), 46 (`representative_joined`, `staff_message`, `ai_paused`, `ai_resumed`, `chat_closed`), 31 (`demo_reset`) | S-11 | AC-4, AC-6, AC-7, AC-8 |
| 7 | `SchedulerJob` (30) | `CaseService` double; prune callable double | `CaseService` (29), `DemoClock` (30), `Checkpointer.prune(keep=2)` (10); the stale-tick `health_event` from `AlertEvaluator` (32, CAS-22) | S-19, S-20 | AC-6, AC-12 |
| 8 | `ResetService` (31) | injected callable doubles | `restore_working_copy(tx)`, `Checkpointer.clearing()`, `clear_demo_tables` (10), `seed_demo` (31), `ResetGate` (23) | S-20 | AC-8 |

Not proven here: the relayed customer turn (`outcome = to_staff`) is AEA-51's (CAS-28). S-1…S-6, S-9, S-10, S-12…S-15,
S-24 belong to the customer path (AEA-51); S-5, S-16, S-17, S-21…S-23 are deferred.

User stories closed: **US-15, US-18, US-19, US-20, US-21, US-22, US-23, US-25, US-28**. Example pairs: **WP-7** (the case a
representative claims, contacts and flags), **WP-4** (the P2 change request whose 12:00 case due the clock passes).
Hard problems: **HP-3** (the fee-bearing change request reaches staff with its due time), **HP-4** (the case view's brief
facts open their sources, R-29).

### Source

- PRD R-25…R-27, R-29…R-34, R-37, R-48; consolidated direction §6, §8, §10 (lifecycle, simulated time, seeds).
- UI contracts (read only): `docs/ux/03-structure/UI_CONTRACTS.md` CON-3, CON-7…CON-17, CON-21, CON-22;
  `docs/design/contracts/api-con-mapping.md` §0–§1.
- stage7/staff.md §1 (roles, `StaffActor`; "you" is the role, STF-1), §2 (`StaffSessionStore`, `FlagService`), §4 (what a
  reset does to staff state), §5 (`LiveChatService` checks and writes), §6 (route rules, `result_line`), §7 (CON-21 start
  point, MC-8), §8 (CON-8), §11 (during the reset); cases.md §1.3 (what a reset restores, clears, keeps), §3.2 (two dues),
  §5 (`CaseService`), §6 (`DemoService`, `SchedulerJob`, abandonment sweep), §7 (`ResetService`, the seed set), §8
  (`scheduler_stale`); web.md §6–§7 (gate, `ResetGate`, 503 set), §11 (CON-3 rules).
- Decision ledgers (`docs/plans/7b-decisions/`): CAS-10, CAS-20, CAS-21, CAS-22, CAS-24, CAS-28, CAS-29, CAS-30; STF-1,
  STF-6, STF-7, STF-11, STF-12, STF-16; WEB-13, WEB-27, WEB-33; merge MC-8, MC-13, MC-16, MC-25.
- DO-4 §11 (`ApiErrorCode`), §13, §14. DO-3 §2.3 rule 4, §6 S-7, S-11, S-18, S-19, S-20, §8 (A9).
- DO-1 §8.2 (*Scheduler job*, *Staff actions*, *Demo reset*, *Event stream*), §9 (SDQ-10 prune), §10 (*Staff console*).
- DO-6: WF-4, WF-5, WF-7 (and WF-15's CON-9 entry point); *Missing instrumentation* (overdue job); **CAP-4, CAP-5**.
- DO-7: M-13, M-18, M-27 (and M-3's flag input). DO-5: WF-4's note (flags never enter the eval set unreviewed).
- UX ↔ backend join: `docs/plans/ux-join/backend-amendments.md` AEA-52-1…5 (staff audit A1, A2, A4, E1; customer audit
  A-1); residual rulings `docs/plans/7b-decisions/residuals-web.md` R-W-13 (`ROLE_ACTIONS`, `allowed_actions`) and R-W-16
  (live actions never change the case version).
- Project rule `.claude/rules/integrated-journeys.md` (§3, §4); slice plan row AEA-52 and Amendment 1 (J-6, J-7, J-8);
  collision map `tests/capture/` (CAP-4, CAP-5 are this issue's), `tests/journeys/`.
- **Brief check:** serves "hands off with enough context that a human can pick up without starting over" and "Would the
  business know if it broke?"; touches nothing out of scope (no real SMS, email or phone: R-34); weakens nothing →
  proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] `create_app()` built by the real container serves CON-7…CON-17 and CON-21 with the real services in the seam table and no provider override; the app lifespan starts the scheduler thread (60 s runner, cases.md §6) and stops it on shutdown — verify: `tests/integration/test_staff_composition.py::test_real_objects_bound` — evidence: each seam row resolves to its real class; the thread alive after start-up, gone after shutdown.
- [ ] AC-2 [capture] **CAP-4, WF-4:** sign in (CON-22) → role switch to representative (CON-10) → claim the WP-7 case (CON-13, `result_line` "Claimed · Riley (demo)") → join, send a reply, hand back (CON-14) → flag a message (CON-16). Present: one `case_event` per action with the actor role and reason; the representative's message stored in the **same thread** as the customer's, STORE-redacted; a `flags` row; a `request` record per call carrying the staff role — verify: `tests/capture/test_cap4_staff_console.py::test_staff_actions_recorded` — evidence: event rows in order (claimed, joined, message, handed back, flagged) with role and reason.
- [ ] AC-3 [negative] **CAP-4 forbidden, WF-4:** the WP-7 customer's name and the representative's message text appear in no log line during the CAP-4 run (logs carry ids, statuses and timings only; DO-6 *Content and redaction*); a staff `send` with a sentinel card-like number generated at test time stores it as "[card number removed]" — verify: `tests/capture/test_cap4_staff_console.py::test_no_customer_pii_in_logs` (captures every log record; the values are read from the case at run time) — evidence: 0 hits; the stored message text.
- [ ] AC-4 [invariant] **WF-4:** Live takeover events and replay (CON-3, CON-21; staff.md §5, §7): after join, the customer's CON-3 stream delivers `representative_joined` then `ai_paused`; the reply arrives as `staff_message`; hand back delivers `ai_resumed`; close delivers `chat_closed` and the server closes the CON-3 stream while the CON-21 stream stays open; the staff CON-21 stream delivers `controller_changed` on join and on hand back and **no** `case_changed` for any live action (a `case_changed` arrives only after a CON-13 action, such as the resolve that follows); a `resolve` sent after hand back with the `version` read before the join is accepted (AEA-52-2; R-W-16, staff.md §5); a client that reconnects with `Last-Event-ID` gets every missed event once, in order, and a `stream_reconnect` record is written — verify: `tests/integration/test_staff_streams.py::test_takeover_events_and_replay` — evidence: event names and ids in order; replay equals the missed slice.
- [ ] AC-5 [failure/refusal] **WF-4:** Role and state rules at the real routes (staff.md §5–§6): the demo owner can read a case but gets 403 `ROLE_NOT_ALLOWED` on every action (R-32); a representative gets `ROLE_NOT_ALLOWED` on the CON-8 advance and on flag review; a customer role on any staff route gets `ROLE_NOT_ALLOWED` `{role: customer, needs: […], reason: wrong_role}`; a stale `expected_version` on CON-13 gets 409 `VERSION_CONFLICT` with `changed_by`, `changed_at`, `current_version`; a claim of a case the supervisor holds gets `CASE_ALREADY_CLAIMED`; joining an unowned case gets 403 `NOT_CLAIMED_BY_YOU` `{owner: null}`; joining a case another role owns gets 409 `CASE_ALREADY_CLAIMED`; a blank `send` text gets 400 `VALIDATION_ERROR` field `text`; no session gets 401 `UNAUTHENTICATED` — verify: `tests/integration/test_staff_composition.py::test_role_and_state_refusals` — evidence: each status and code, valid against the OpenAPI; error bodies carry no rejected value.
- [ ] AC-6 [capture] **CAP-5, WF-5 and WF-7:** the supervisor advances the clock (CON-8, `plus_4h`, 10:00 → 14:00) past WP-4's 12:00 case due; then `SchedulerJob.tick()` runs. Present: a `demo_events` row (`clock_advanced`, before and after, `became_overdue` 1, request id, role `supervisor`); `clock_changed` on CON-3; a `job_runs` row per tick with its `job_run_id` on every `case_event` it writes (`overdue` from the case due); WP-4's promise (due Mon Oct 19, 7:00 pm) still open; CON-17 (WF-4, the supervisor-view alert) lists the case in the Overdue lane; advanced past Mon 7:00 pm, the next tick marks that promise missed; with ticks stopped for more than 180 s of wall time, `AlertEvaluator` writes a `scheduler_stale` `health_event` (CAS-22), shown as the CON-19 "Overdue job last ran" tile, not an alert (CAS-30) — verify: `tests/capture/test_cap5_clock_and_scheduler.py::test_clock_past_due_and_scheduler` (drives CON-8, then the container-built `SchedulerJob.tick()`, with an injected wall clock) — evidence: the rows and the oversight lane.
- [ ] AC-7 [invariant] **WF-5:** Staffing (CON-7; R-30, N-12): the default after start-up is nobody online; switching on writes a `demo_events` row and emits `staffing_changed` to every open chat; a handoff while staffed carries the `R26.staffed` text and is live-queued; switching off converts every live-queued case (same reference, same creation time) to the unstaffed promise and emits `shift_ended` with the same reference and a new `settled`; the same mode twice writes nothing — verify: `tests/integration/test_staff_streams.py::test_staffing_on_and_shift_end` — evidence: events; the converted case's reference and creation time unchanged; promise text from `policy/handoff.py`.
- [ ] AC-8 [invariant] **CON-9 reset through the real `ResetService` (WF-15, live entry point):** all-or-nothing under the exclusive transaction and `ResetGate`; afterwards the five issued tables equal the issued file row for row, the cleared tables of cases.md §1.3 hold only the four seeds again, flags are gone (a stale flag id answers 404 `FLAG_NOT_FOUND`), and the clock reads `DEMO_START`; open chats get `demo_reset` and their next call gets 410 `SESSION_ENDED` (MC-16); every non-customer session's role returns to customer while the login stays (the next staff call gets 403 `ROLE_NOT_ALLOWED` with `details.reason: role_reset`; `ResetResponse.roles_reset` counts them); while the gate is held, `submitTurn` answers 503 `RESET_IN_PROGRESS` with `retry_after_ms` 5000 and a second CON-9 gets 409 `RESET_IN_PROGRESS`; one `reset_event` (asked-by role and session) and one `seed_event` are written; `spend_ledger`, `health_events`, `deploy_records`, `eval_runs`, `job_runs` and `demo_events` are kept; a forced failure in the middle leaves nothing half-reset (`RESET_FAILED`) — verify: `tests/integration/test_demo_reset.py::test_reset_all_or_nothing` — evidence: before/after row counts; event names; status codes.
- [ ] AC-9 [invariant] **WF-4:** Case view sources (CON-12; R-29, HP-4): the WP-4 case shows the case due and the promise due separately and each pertinent lookup as a snapshot plus the current value read through `core.reads.appointment` (CAS-19); after the appointment row changes in the working copy, the source shows the "changed since" marker; every brief fact links to a `lookup_log` row — verify: `tests/integration/test_staff_cases.py::test_case_view_snapshot_vs_current` — evidence: both dues; snapshot, current and marker fields.
- [ ] AC-10 [invariant] **WF-4:** Contact attempts are recorded, never sent (CON-15; R-34; CAS-21): the attempt is an activity row with actor and outcome, the response says "recorded, not sent", and no outbound call, email or SMS client is invoked (none exists to call); a `left_message` attempt before the promise due marks the WP-7 promise `kept`, a `no_answer` attempt leaves it open — verify: `tests/integration/test_staff_cases.py::test_contact_attempt_recorded_not_sent` — evidence: the activity rows; the response text; promise status per outcome; no network access attempted.
- [ ] AC-11 [invariant] Flags reach the review list and nothing else (CON-16; R-37): a flag appears on the supervisor's review list (newest first); reviewing it changes no file under `eval/cases/`, no prompt and no KB file (DO-5 WF-4 note) — verify: `tests/integration/test_staff_cases.py::test_flag_review_changes_nothing_else` — evidence: review list entry; `eval/cases/`, `src/meridian/agent/prompts/` and the KB unchanged (hash before and after).
- [ ] AC-12 [capture] **WF-7 sweeps:** the once-a-wall-day tick prunes each thread's checkpoints to its last 2 (SDQ-10) through the injected callable and records `pruned` on its `job_runs` row, leaving the `messages` table untouched; a `live` conversation with no customer message for 30 wall-clock minutes is marked `abandoned`, ended at its last message + 30 min, while `seed`, `eval` and `load` threads never are (CAS-29) — verify: `tests/capture/test_cap5_clock_and_scheduler.py::test_daily_prune_and_abandonment` — evidence: checkpoint counts per thread ≤ 2; message counts unchanged; conversation outcomes per tag.
- [ ] AC-13 [negative] **WF-4:** Staff routes never open a case (DO-4 §13; DO-3 S-7): no staff route module calls `open_case` — verify: `grep -rn "open_case" src/meridian/web/routes/staff_*.py` — evidence: no output.
- [ ] AC-14 [invariant] A case view opened after a reset does not close at once (MC-8): after CON-9, a CON-21 connection to MHC-C-0005 with no `Last-Event-ID` receives no `demo_reset` frame and stays open, while a connection resumed from before the reset receives `demo_reset` and closes — verify: `tests/integration/test_staff_streams.py::test_case_stream_after_reset` — evidence: frames per connection.
- [ ] AC-15 [journey] **J-6, J-7, J-8; WF-4 (staff queue, case view and actions)** (slice plan Amendment 1, landed here; AEA-52-5): `tests/journeys/j6/test_aea_52.py` (WP-7 and WP-8: escalation → case → staff queue → case opened with the eight-heading brief and promise, every brief `source_ids` entry resolving to a source of the case), `j7/test_aea_52.py` ("Talk to a person" and live takeover: staff joins the same chat, the relayed customer line identical on CON-21 and in `getCase`, Riley's lines in the customer's `getChatThread` after a reload, hand back, then resolve with the pre-join version accepted), `j8/test_aea_52.py` (customer ↔ staff role switch seen by a second client on the same cookie, a reset sending both clients' staff calls to `role_reset` until a switch, refresh, signed-out and expired session), each asserting what the user sees **and** what is stored on AEA-57's harness — verify: `uv run pytest -m journey tests/journeys/j6 tests/journeys/j7 tests/journeys/j8` plus `docs/testing/journeys/<date>-AEA-52.md` (integrated-journeys §4) — evidence: pass per journey at level `integrated with a scripted model`; the record's fields filled.
- [ ] AC-16 [invariant] `allowed_actions` holds at the real routes (AEA-52-1; R-W-13, staff.md §1 `ROLE_ACTIONS`): on the seeded MHC-C-0007 and on a WP-7 case taken through claim → join, `getCase` as representative, supervisor and owner returns lists for which every listed action, sent next, is accepted, and one unlisted action of each operation is refused; the owner's list is `[]`; the supervisor's never holds a live-chat or contact key — verify: `tests/integration/test_staff_allowed_actions.py::test_listed_iff_accepted_per_role` — evidence: per role, the list and each action's accept or refuse result printed.
- [ ] AC-17 [invariant] The relayed customer message is the same on both staff surfaces (AEA-52-3; AEA-40-5): with Riley joined, a customer `submitTurn` produces one `customer_message` frame on CON-21 whose payload equals, field for field, the line `getCase` then returns in `conversation` for that `message_id` (customer `display_name` null); the customer's own `getChatThread` shows that message and Riley's reply in order — verify: `tests/integration/test_staff_streams.py::test_relayed_message_same_on_stream_and_case_view` — evidence: the two JSON objects printed and equal.
- [ ] AC-18 [invariant] The customer's reload after a takeover shows it (AEA-52-4; AEA-40-1): after join, a staff `send` and hand back, `getChatThread` holds in order the joined and paused lines, Riley's message (`speaker.kind: representative`, `display_name: "Riley"`) and the resumed line, and its `last_event_id` equals the newest event id of the thread's stream, so a CON-3 connection from it receives no frame already shown — verify: `tests/integration/test_staff_streams.py::test_reload_after_takeover_shows_staff_lines` — evidence: the entry list printed; 0 replayed frames.
- [ ] AC-19 [capture] **WF-4:** the fee-bearing change request reaches the staff console at once (R-21, HP-3): right after WP-4's `request_change` through CON-2 opens its P2 `fee_bearing_change` case, with no clock advance, `getOversight` as the supervisor lists the case in the lane the cases.md §5 lane rule gives it (Due soon: its 12:00 case due is within `DUE_SOON_WINDOW` of 10:00) and `getCase` shows priority P2 "Time-sensitive", the case due at the window start apart from the customer promise due, the original appointment unchanged in the working copy, the wanted windows shown with "Windows are shown, not held.", and no "charged", "waived" or "sent" in any staff-visible text — verify: `tests/integration/test_staff_cases.py::test_fee_bearing_request_reaches_staff_at_once` — evidence: the oversight lane and the case body printed; the appointment row before and after.
- [ ] AC-20 [invariant] **WF-4:** the staff views follow the staffing state (R-30, N-12): after CON-7 switches simulated staff on, `getQueue` and `getOversight` carry `staffing.mode` `simulated_on_shift` and the same `banner` text `getStaffing` returns; after it switches them off, `banner` is null, the queue's `live` list is empty, `live_queue_length` is 0 and no case shows `live_queued` — verify: `tests/integration/test_staff_streams.py::test_staff_banner_follows_staffing` — evidence: `staffing` object, `live` list and `live_queue_length` printed per mode.
- [ ] AC-21 [failure/refusal] **WF-4:** least-privilege staff views at the real routes (NFR-2; `x-roles`, staff.md §1): through the container-built app and the real `StaffSessionStore`, each role gets exactly the operations its `x-roles` grant: a representative gets 403 `ROLE_NOT_ALLOWED` on `getOversight` and `reviewFlag`; the owner reads `getCase` and `listFlags` only and gets 403 on `getQueue`, `getOversight` and every write; a customer role gets 403 on all eight case operations; queue and oversight rows carry no phone number, email or street address of any seeded customer (D2) — verify: `tests/integration/test_staff_composition.py::test_least_privilege_matrix` — evidence: the role × operation status table printed; 0 contact-value hits in the queue and oversight bodies.
- [ ] AC-22 [invariant] **WF-4:** status values (OBS-13, DO-6 *Status values*): over the CAP-4 run of AC-2 every `request` record's `status` equals the HTTP status of its response; with `CaseService.apply` patched to raise once, the 500 answer's `request` record carries `error_kind` and the body is an `ApiError`; no status value outside DO-6's list is stored — verify: `tests/capture/test_cap4_staff_console.py::test_wf4_status_values` — evidence: (`route`, `status`, `error_kind`) per record printed.
- [ ] AC-23 [negative] **WF-4:** key values never leave their store (OBS-24): with sentinel provider, Langfuse and eval keys and a sentinel demo password set in the test settings, over the CAP-4 run the sentinels and the raw `mhc_session` cookie value appear in no log record, no CON-11…CON-17 body, no CON-21 frame and no text column of the DB copy (`staff_sessions` holds only the keyed hash, STF-5) — verify: `tests/capture/test_cap4_staff_console.py::test_no_key_values_anywhere` — evidence: 0 hits per sentinel across logs, bodies, frames and rows.
- [ ] AC-24 [negative] **WF-5:** the demo controls keep keys in and make no outbound call (OBS-24, OBS-29): during CON-7 on and off and the CON-8 advance of AC-6, sentinel key values and the raw `mhc_session` cookie value appear in no `demo_events` row, no CON-7 or CON-8 body and no log record, and a socket guard records 0 outbound connection attempts — verify: `tests/capture/test_cap5_clock_and_scheduler.py::test_wf5_no_key_values_or_outbound` — evidence: 0 sentinel hits; 0 connection attempts.
- [ ] AC-25 [capture] **CAP-5, WF-7:** the scheduler's own entry point, apart from the CON-8 proof in AC-6: with the demo clock past WP-4's 12:00 case due, the container-built `SchedulerJob.tick()` writes one `job_runs` row per tick whose `status` goes `started` → `completed`, `overdue` `case_event`s carrying that `job_run_id`, and, past Mon 7:00 pm, WP-4's promise `missed`; a tick whose `CaseService` call is patched to raise ends `failed` with an `error_kind` and the next tick still runs (OBS-13); with ticks stopped for more than 180 s of injected wall time, `AlertEvaluator` writes one `scheduler_stale` `health_event` — verify: `tests/capture/test_cap5_clock_and_scheduler.py::test_wf7_ticks` — evidence: the `job_runs` rows with `status` and `error_kind`; the case events with their `job_run_id`; the promise status; the `health_event`.
- [ ] AC-26 [negative] **WF-7:** scheduler logs and network (OBS-21, OBS-24, OBS-29): over the ticks of AC-25 and the daily sweep of AC-12, every log record the scheduler thread emits is a structured record whose keys are within web.md §10's allow-list (ids, statuses, timings, counts); a sentinel phrase stored in a swept case's messages and sentinel key values set in the test settings appear in no log record and no `job_runs` row; a socket guard records 0 outbound connection attempts — verify: `tests/capture/test_cap5_clock_and_scheduler.py::test_wf7_logs_keys_and_network` — evidence: the key sets printed; 0 sentinel hits; 0 connection attempts.
- [ ] AC-27 [negative] **WF-15:** the CON-9 reset sends nothing out (OBS-29): the reset of AC-8, run under a socket guard, opens 0 outbound connections from the request until the seed completes — verify: `tests/integration/test_demo_reset.py::test_reset_makes_no_outbound_connection` — evidence: 0 connection attempts recorded.
- [ ] AC-28 [regression/context] Context updated in the same change: area-map A9 and A6 rows note "integrated (AEA-52)" with the commit; `.claude/state/icm-progress.md` routes-verified row; DO-3 §6 S-7, S-11, S-19, S-20 annotated with the proving test — verify: `git diff --name-only` — evidence: those files only, beside this issue's owned files.

### Observability

- Responsibilities: **WF-4** (staff console: `request` with the staff role on every action, `case_event` with actor role,
  action and reason, `flag`, `stream_reconnect`); **WF-5** (demo controls: `request`, a `demo_events` row per staffing or
  clock change); **WF-7** (scheduler: `job_runs` per tick, `case_event` `due_soon`/`overdue` with `job_run_id`, promise
  status change, abandonment, prune count, the `scheduler_stale` `health_event` from the evaluator); and the CON-9 entry
  point of **WF-15** (`reset_event`, `seed_event`). Logs carry ids, statuses and timings only.
- Capture evidence: AC-2 and AC-3 (CAP-4, WF-4), AC-6 (CAP-5, WF-5 and WF-7), AC-25 (CAP-5, WF-7 ticks), AC-12 (WF-7
  sweeps), AC-8 (WF-15 via CON-9); status values AC-22 (WF-4) and AC-25 (WF-7); negatives AC-23 (WF-4), AC-24 (WF-5),
  AC-26 (WF-7), AC-27 (WF-15).

### Evaluation

- Checks: no scored suite runs here. WF-4 carries DO-5's rule that flags feed the review list (R-37) and **never** the eval
  set unreviewed (AC-11). WF-5 and WF-7 have no suite of their own (DO-6: their effect is measured through WF-1 and WF-6).
  The promise texts staff and customers see stay equal to the policy table (E-6's promise invariant) across staffing
  changes (AC-7).
- Expected-answer authority: the R-26 policy table and D4 priorities (`policy/handoff.py`, cases.md §3) for promises; the
  UI contracts' guarantees (CON-7…CON-17, CON-21) for state rules; consolidated direction §6 for the case lifecycle.

### Metrics

- References: **M-13** (promises kept on time: `promise` status and due time, contact activities, `case_event`), **M-27**
  (unowned and overdue cases: `case`, `promise`, WF-7 `job_runs`), **M-18** (abandoned conversations, written by the WF-7
  sweep), and the flag input to **M-3** (staff flags, R-37).
- Acceptance conditions: M-13 and M-27 stay computable from the rows AC-6 and AC-10 prove (overdue and missed status,
  kept on contact, `job_runs` per tick); M-18 from AC-12's stored `abandoned` outcome; M-3's "not flagged wrong" filter has
  a `flags` row to read (AC-2). No target is set here.

### Blocked by

- Slice plan row AEA-52: AEA-29, AEA-30, AEA-31, AEA-32, AEA-41, AEA-43 (WEB-33), AEA-44, AEA-45, AEA-46, AEA-47,
  AEA-57 (journey harness), AEA-59 (contract boundary checks).
- Added by the UX-join amendments: **AEA-40** (wave 2) for AC-17 and AC-18 (the `submitTurn` relay and `customer_message`
  payload, AEA-40-5; `getChatThread` full history with staff lines and `last_event_id`, AEA-40-1). No wave moves (AEA-52
  stays wave 3). AC-16 also reads `ROLE_ACTIONS` (AEA-02, wave 0; R-W-13) through AEA-29's `allowed_actions` (AEA-29-1).
- Added by the coverage repair: **AEA-23** (wave 1; the `request` record middleware whose `status` and `error_kind` AC-22
  proves on WF-4; already upstream through AEA-45, so no wave moves).

### Agent handoff

- Area / owner: integration of A9 (staff console) and the A6 demo services (DO-3 §8). Owns
  `tests/integration/test_staff_composition.py`, `test_staff_streams.py`, `test_staff_cases.py`, `test_demo_reset.py`,
  `test_staff_allowed_actions.py`,
  `tests/capture/test_cap4_staff_console.py`, `test_cap5_clock_and_scheduler.py`,
  `tests/journeys/j{6,7,8}/test_aea_52.py` and its journey evidence record. Registers nothing new: each service's own
  `register_<area>()` hunk (29, 30, 31, 32, 44, 46) binds it; a missing binding is a fix on its owner, recorded as
  `blocked-on AEA-NN`.
- Contracts and shared surfaces: consumes `CaseService`, `DemoService`, `SchedulerJob`, `ResetService`, `ResetGate`,
  `StaffSessionStore`, `FlagService`, `LiveChatService`, `AlertEvaluator`, `ROLE_ACTIONS` (staff.md §1, R-W-13), AEA-40's
  `submitTurn` and `getChatThread` routes and the `events` methods (addenda sections in *Source*) and the CON contracts
  above; live actions leave the case `version` alone (staff.md §5, R-W-16); produces the bound staff and demo API that AEA-55, AEA-58 and AEA-62 drive from
  the UI.
  **Must not edit** route, schema, service or `register_<area>()` code owned by 40, 41, 43–47, 29–32, nor
  `tests/journeys/support/` (AEA-57's).
- Scope boundary / refusal: no model calls by staff routes; no customer-turn logic, including the relayed `to_staff` turn
  (AEA-51, CAS-28); no reads pages (AEA-53); nothing is sent to a real phone or inbox (R-34).
- Wave and gates: wave 3; no human gate. The wave-3 merge runs `seam-audit-agent` across 50–53, executing all journeys
  (integrated-journeys §5).
- Lane: `lane::build-loop` — tests (code-read).
- Risk: None (slice plan; the role switch is a demo label, CON-10; the login gate is AEA-23's and AEA-44's security work,
  exercised here only as a precondition).
- Entry points added or changed: WF-4, WF-5, WF-7, WF-15 (wires the real services behind them; WF-15 through CON-9).
