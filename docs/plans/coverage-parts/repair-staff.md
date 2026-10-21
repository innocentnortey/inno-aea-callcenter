# Coverage repair — group `staff` (AEA-45, AEA-47, AEA-48, AEA-52, AEA-53)

Brief: `/home/linuxuser/.claude/jobs/9461dd3d/tmp/repair-brief.md`. Only the five tickets above were edited.
Check run on a temporary copy of `coverage-audit.md` with the rows below appended to the matrix and the current tickets
(`cat docs/plans/tickets/AEA-*.md`): every finding that named these tickets, or a pair whose owner is one of them, is gone
(20 "does not name" findings, 24 missing rows); no new finding appeared; 0 findings name AEA-45/47/48/52/53 afterwards.

## Matrix rows

New rows, audit 7-column format, final AC numbers. Append to the *Coverage matrix* table (no blank line before them).

| R-21 | WF-4 | Fee-bearing change request shown to staff at once: P2, case due at the window start apart from the promise due, original appointment unchanged, windows shown not held (CON-12, CON-17) | AEA-29 | AEA-52 | AEA-52 AC-19 | `test_staff_cases.py::test_fee_bearing_request_reaches_staff_at_once`: oversight lane and case body with no clock advance; appointment row unchanged (the immediate supervisor alert beyond the lane rule is a Decision, see repair-staff) |
| R-30 | WF-4 | Staffing state and banner on CON-11 and CON-17; no live queue while nobody is online (`DemoService` staffing) | AEA-30 | AEA-52 | AEA-52 AC-20 | `test_staff_streams.py::test_staff_banner_follows_staffing`: `staffing`, `live` and `live_queue_length` per mode |
| NFR-2 | WF-4 | Least-privilege staff views: role × operation matrix from `x-roles`; display name only on queue and oversight rows (`routes/staff_cases.py`) | AEA-45 | AEA-52 | AEA-52 AC-21 | `test_staff_composition.py::test_least_privilege_matrix`: role × operation status table; 0 contact values in queue and oversight bodies |
| OBS-13 | WF-4 | `request` record `status` and `error_kind` on 5xx (web middleware, web.md §10) | AEA-23 | AEA-52 | AEA-52 AC-22 | `test_cap4_staff_console.py::test_wf4_status_values`: (`route`, `status`, `error_kind`) per record |
| OBS-24 | WF-4 | `StaffSessionStore` keeps only the keyed token hash; key values kept out of logs, staff bodies and frames | AEA-44 | AEA-52 | AEA-52 AC-23 | `test_cap4_staff_console.py::test_no_key_values_anywhere`: 0 hits per sentinel in logs, bodies, frames and rows |
| OBS-25 | WF-4 | Log allow-list on staff actions keeps the customer's name out of logs (`CaseService`) | AEA-29 | AEA-52 | AEA-52 AC-3 | `test_cap4_staff_console.py::test_no_customer_pii_in_logs`: 0 log hits for the WP-7 customer's name |
| OBS-26 | WF-4 | Representative message text stored redacted and never logged (`LiveChatService`) | AEA-46 | AEA-52 | AEA-52 AC-3 | `test_cap4_staff_console.py::test_no_customer_pii_in_logs`: 0 log hits for the message text; card-like number stored as "[card number removed]" |
| OBS-29 | WF-4 | Contact attempts recorded, never sent; no outbound client (CON-15) | AEA-29 | AEA-52 | AEA-52 AC-10 | `test_staff_cases.py::test_contact_attempt_recorded_not_sent`: "recorded, not sent"; no network access attempted |
| OBS-24 | WF-5 | `DemoService` writes ids, roles and times only to `demo_events` | AEA-30 | AEA-52 | AEA-52 AC-24 | `test_cap5_clock_and_scheduler.py::test_wf5_no_key_values_or_outbound`: 0 sentinel hits in `demo_events`, bodies and logs |
| OBS-29 | WF-5 | Demo controls (CON-7, CON-8) make no outbound call | AEA-30 | AEA-52 | AEA-52 AC-24 | `test_cap5_clock_and_scheduler.py::test_wf5_no_key_values_or_outbound`: 0 connection attempts |
| CAP-5 | WF-7 | `SchedulerJob.tick()`: `job_runs` per tick, `overdue` events with `job_run_id`, missed promise, `scheduler_stale` `health_event` | AEA-30 | AEA-52 | AEA-52 AC-25 | `test_cap5_clock_and_scheduler.py::test_wf7_ticks`: the rows, events, promise status and `health_event` |
| OBS-13 | WF-7 | `job_runs.status` `started` → `completed` / `failed` with `error_kind` | AEA-30 | AEA-52 | AEA-52 AC-25 | `test_cap5_clock_and_scheduler.py::test_wf7_ticks`: `status` and `error_kind` per tick, including the forced failure |
| OBS-21 | WF-7 | Scheduler log lines through the allow-list formatter | AEA-30 | AEA-52 | AEA-52 AC-26 | `test_cap5_clock_and_scheduler.py::test_wf7_logs_keys_and_network`: log key sets within web.md §10; 0 sentinel hits |
| OBS-24 | WF-7 | No key value in `job_runs` or scheduler logs | AEA-30 | AEA-52 | AEA-52 AC-26 | `test_cap5_clock_and_scheduler.py::test_wf7_logs_keys_and_network`: 0 sentinel key hits |
| OBS-29 | WF-7 | Scheduler ticks make no outbound call | AEA-30 | AEA-52 | AEA-52 AC-26 | `test_cap5_clock_and_scheduler.py::test_wf7_logs_keys_and_network`: 0 connection attempts |
| OBS-29 | WF-15 | `ResetService` behind CON-9 makes no outbound call | AEA-31 | AEA-52 | AEA-52 AC-27 | `test_demo_reset.py::test_reset_makes_no_outbound_connection`: 0 connection attempts |
| OBS-13 | WF-6 | `request` record `status` and `error_kind` on the read routes (web middleware) | AEA-23 | AEA-48 | AEA-48 AC-13 | `test_reads_routes.py::test_wf6_request_status_values`: (`status`, `error_kind`) per response |
| R-41 | WF-6 | Read rate limit (429) and reset gate (503) from AEA-23's middleware; `getOwnerMetrics` never limited | AEA-23 | AEA-48 | AEA-48 AC-8 | `test_reads_routes.py::test_reads_429_and_503`: 429 and 503 bodies validate; one 200 for `getOwnerMetrics` each time |
| OBS-18 | WF-6 | `MetricsReader` CON-19 `trace_export` (M-29) with export off; pages work without Langfuse | AEA-53 | AEA-53 | AEA-53 AC-13 | `test_cap6_reads.py::test_monitoring_says_export_off_and_no_outbound`: `trace_export` 0 of N; alert state as stored |
| OBS-29 | WF-6 | Read pages make no outbound call (no trace-backend call) | AEA-53 | AEA-53 | AEA-53 AC-13 | `test_cap6_reads.py::test_monitoring_says_export_off_and_no_outbound`: 0 connection attempts |
| OBS-24 | WF-6 | `MetricsReader` aggregates carry no key value | AEA-53 | AEA-53 | AEA-53 AC-14 | `test_cap6_reads.py::test_no_key_values_or_message_text`: 0 sentinel key hits in bodies and logs |
| OBS-26 | WF-6 | Message text only as stored redacted dev failure examples (CON-20) | AEA-53 | AEA-53 | AEA-53 AC-14 | `test_cap6_reads.py::test_no_key_values_or_message_text`: 0 phrase hits; examples equal the stored redacted ones |
| OBS-25 | WF-6 | No names or phones on CON-19 and CON-20; case references only on CON-18 | AEA-53 | AEA-53 | AEA-53 AC-6 | `test_cap6_reads.py::test_no_pii_codes_cards_or_trace_links`: 0 sentinel hits |
| OBS-31 | WF-6 | Zero-traffic alert state and its 22:00–06:00 quiet window shown from `AlertEvaluator` rows (CON-19) | AEA-32 | AEA-53 | AEA-53 AC-4 | `test_metrics_reader_alerts.py`: `zero_traffic` state equals its stored row; `alert_config` 4 h outside 22:00–06:00 Chicago |

The 20 existing rows that were flagged "does not name WF-n" keep their AC citations unchanged; the ACs now name the
workflow (see *Reworded*). That includes OBS-40 WF-4 (line 375) and OBS-40 WF-6 (line 376): their "(… see Gaps)" notes in
the Acceptance-criterion column can be dropped by whoever edits the audit.

## Reworded

Wording only (the workflow id added; no behaviour change):

| Ticket | AC | Added | Clears |
|---|---|---|---|
| AEA-45 | AC-9 | `**WF-4:**` | DC-1 WF-4 |
| AEA-45 | AC-12 | `**WF-4:**` | R-3 WF-4 |
| AEA-45 | AC-15 | `**WF-4:**` | R-48 WF-4 |
| AEA-47 | AC-5 | `**WF-5:**` | DC-21 WF-5 |
| AEA-47 | AC-6 | `**WF-5:**` | R-48 WF-5 |
| AEA-48 | AC-7 | `**WF-6:**` | R-48 WF-6, DC-1 WF-6 |
| AEA-48 | AC-8 | `**WF-6:**` | R-41 WF-6 (new row) |
| AEA-52 | AC-3 | `**CAP-4 forbidden, WF-4:**` | R-36 WF-4; OBS-25, OBS-26 WF-4 (new rows) |
| AEA-52 | AC-4 | `**WF-4:**` | R-31 WF-4, DC-16 WF-4 |
| AEA-52 | AC-5 | `**WF-4:**` | DC-21 WF-4, DC-22 WF-4 |
| AEA-52 | AC-6 | "CON-17 (WF-4, the supervisor-view alert)" | OBS-40 WF-4 |
| AEA-52 | AC-7 | `**WF-5:**` | R-26 WF-5, R-30 WF-5 |
| AEA-52 | AC-9 | `**WF-4:**` | R-29 WF-4 |
| AEA-52 | AC-10 | `**WF-4:**` | R-34 WF-4; OBS-29 WF-4 (new row) |
| AEA-52 | AC-13 | `**WF-4:**` | DC-10 WF-4 |
| AEA-52 | AC-15 | `**J-6, J-7, J-8; WF-4 (staff queue, case view and actions)**` | R-32 WF-4 |
| AEA-53 | AC-4 | `**OBS-40, OBS-31, WF-6 (CON-19 alerts):**` | OBS-40 WF-6; OBS-31 WF-6 (new row) |
| AEA-53 | AC-6 | `**CAP-6 forbidden, WF-6:**` | OBS-25 WF-6 (new row) |

New ACs (inserted before the regression AC, which stays last and is renumbered; no other AC renumbered):

| Ticket | New AC | Proves | Regression AC |
|---|---|---|---|
| AEA-52 | AC-19 [capture] WF-4 | R-21 (fee-bearing request at the staff console, no clock advance) | AC-19 → **AC-28** |
| AEA-52 | AC-20 [invariant] WF-4 | R-30 (staffing banner, no live queue while nobody online) | |
| AEA-52 | AC-21 [failure/refusal] WF-4 | NFR-2 (least privilege: role × operation matrix, no contact values on rows) | |
| AEA-52 | AC-22 [invariant] WF-4 | OBS-13 (`request.status`, `error_kind` on a forced 500) | |
| AEA-52 | AC-23 [negative] WF-4 | OBS-24 (sentinel keys, password, cookie value nowhere) | |
| AEA-52 | AC-24 [negative] WF-5 | OBS-24, OBS-29 | |
| AEA-52 | AC-25 [capture] CAP-5, WF-7 | CAP-5 WF-7 (split from AC-6, which stays the WF-5 proof), OBS-13 WF-7 | |
| AEA-52 | AC-26 [negative] WF-7 | OBS-21, OBS-24, OBS-29 | |
| AEA-52 | AC-27 [negative] WF-15 | OBS-29 | |
| AEA-48 | AC-13 [invariant] WF-6 | OBS-13 | AC-13 → **AC-14** |
| AEA-53 | AC-13 [capture] CAP-6, WF-6 | OBS-18, OBS-29 | AC-13 → **AC-15** |
| AEA-53 | AC-14 [negative] WF-6 | OBS-24, OBS-26 | |

Also updated in the same tickets (consistency only): the *Capture evidence* lines of AEA-48, AEA-52 and AEA-53 now list
the new ACs.

**Audit rows citing a renumbered regression AC:** none. No row, part file or other document cites AEA-52 AC-19,
AEA-48 AC-13 or AEA-53 AC-13 (`grep -rnE` over `docs/` and `.claude/`). AEA-45 AC-21 and AEA-47 AC-13 were not renumbered.

## Blocked-by edits

- **AEA-52 += AEA-23** (hard edge): the new OBS-13 WF-4 row's component is AEA-23's `request` middleware. AEA-23 is wave 1
  and already upstream of AEA-52 through AEA-45, so AEA-52 stays wave 3; no cycle. Written as a new bullet in AEA-52's
  *Blocked by*.
- No other edge needed: every other new row's implementing ticket (AEA-29, 30, 31, 32, 44, 45, 46 for AEA-52; AEA-23 for
  AEA-48; AEA-32 or AEA-53 itself for AEA-53) was already a blocker.

## Decisions

1. **R-21 WF-4, "a supervisor alert at once".** R-21 says a fee-bearing change is handed off "P2 due at window start with
   a supervisor alert at once". The signed contracts have no mechanism for an immediate alert on a P2 case: the OpenAPI
   `Alert.type` enum is `p0_p1_created`, `unowned`, `due_soon`, `overdue`, `stuck_waiting`, `shift_ended_with_queued`, and
   the cases.md §5 lane rule puts a P2 case in *Due soon* only when its case due is within `DUE_SOON_WINDOW` (4 h).
   part-2's proposed wording (a `supervisor_now` alert in a "P0/P1-and-alerts lane") names an alert type and a lane that
   do not exist, so it was **not** used. AEA-52 AC-19 proves what the contracts do give (WP-4's 12:00 window start is 2 h
   after the 10:00 start, so the case is in *Due soon* with no clock advance) plus P2, both dues, original stays, windows
   not held. **Decision needed:** for a fee-bearing change whose window start is more than 4 h away, should the supervisor
   view alert at once (an OpenAPI change: a new alert type or lane rule, which goes to Innocent per the conventions), or
   is "at once" satisfied by the *Due soon* lane once the window start is within 4 h?

## Not fixed

- **Evidence-only ticket ids inside *Blocked by* sections** (checker parse, not a coverage finding): the checker reads
  every ticket id in a *Blocked by* section as a blocker, so it sees AEA-45 → AEA-52, AEA-47 → AEA-52 and AEA-48 → AEA-53
  (each a cycle with the real edge the other way), AEA-45/47/48 → AEA-57, AEA-59, and AEA-52 and AEA-53 blocked by
  themselves (their "Slice plan row AEA-5x:" lead-in). The texts say "evidence level only, not a build blocker", so no
  real edge is wrong, but an orchestrator that parses ids the same way would compute a cycle. Left as written: moving the
  evidence notes out of *Blocked by* is a convention change for every ticket that uses that bullet, not just these five;
  whoever owns the conventions should decide it (e.g. move them to *Wave and gates*).
- **AEA-48 "extend AC-9" (OBS-13 WF-6) and the part-4 "amend AC-3/6/8/10/12" proposals** were applied as **new** ACs (and
  wording-only renames where the existing AC already proved the pair), not by changing what an existing AC asserts, so no
  existing matrix row's proof changed.
- **Pairs in the gap tables owned by other tickets** were left alone, including OBS-13 WF-5 / WF-15 (AEA-43), OBS-24
  WF-15 (AEA-50), OBS-40 WF-17 (AEA-32). No gap owner proposed for these five tickets conflicts with
  `docs/plans/slice-plan.md` (AEA-52: WF-4, 5, 7, plus WF-15 through CON-9 as its entry-point line states; AEA-53 and
  AEA-48: WF-6; AEA-45: WF-4; AEA-47: WF-5).
