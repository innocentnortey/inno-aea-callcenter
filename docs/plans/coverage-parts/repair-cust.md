# Coverage repair — group `cust` (AEA-40, AEA-42, AEA-43)

Scope: the checker problems in `full-check.txt` that concern AEA-40, AEA-42 and AEA-43. That is 20 criteria that did not
name their workflow, plus 8 missing rows where one of these tickets is the integration owner (part-2 R-48 WF-3; part-3
R-41 WF-3/WF-5/WF-15 and OBS-13 WF-3/WF-5/WF-15; part-4 OBS-32 WF-1). Only the three ticket files were edited.

Check: the audit with the 8 rows below inserted after the DC-18 WF-1 row (temp copy only), run against a fresh concat of
`docs/plans/tickets/AEA-*.md` → 338 → 310 problems, with **0 problems naming AEA-40, AEA-42 or AEA-43**. The remaining
R-41 WF-1 and OBS-13 WF-1 gaps belong to AEA-51.

## Matrix rows

Insert these into the coverage matrix. They use the final AC numbers.

| Req | Workflow | Component / contract | Implementing ticket | Integration owner | Acceptance criterion | Evidence |
|---|---|---|---|---|---|---|
| OBS-32 | WF-1 | `turn` row begun on receipt with `outcome` empty (`core.turns.begin` in `services/turn.py`); start-up sweep `core.turns.fail_running()` | AEA-10 | AEA-40 | AEA-40 AC-14 | `test_con1_con2_records_written`: the `turn` row exists on receipt with `outcome` empty, then is finished (sweep of `running` rows to `degraded_handoff` / `timeout`: AEA-40 AC-12) |
| R-48 | WF-3 | Demo-login middleware on CON-6 `listDemoInbox` | AEA-23 | AEA-43 | AEA-43 AC-17 | `test_wf3_inbox_login_gate_and_request_status`: 401 body valid against `Unauthenticated`, no service call; 200 under each role |
| R-41 | WF-3 | Read-bucket rate limit (web §5, WEB-3) on `listDemoInbox` | AEA-23 | AEA-43 | AEA-43 AC-11 | `test_inbox_request_rate_limited`: 429 `REQUEST_RATE_LIMITED` with `details.retry_after_ms`, valid against `TooManyRequests` |
| R-41 | WF-5 | Read buckets on `getStaffing` / `getDemoClock`; `setStaffing` never limited (web §5, WEB-3) | AEA-23 | AEA-43 | AEA-43 AC-18 | `test_wf5_read_limits_and_request_status`: two 429 bodies valid against `TooManyRequests`; `setStaffing` 200 |
| R-41 | WF-15 | `RESET_IP` per-IP reset throttle (web §5, WEB-27) on `resetDemo` | AEA-23 | AEA-43 | AEA-43 AC-8 | `test_reset_throttle_per_ip`: eleventh reset from one IP 409 `RESET_IN_PROGRESS`; `ResetService.reset` called 10 times; another IP unaffected |
| OBS-13 | WF-3 | `request.status` with `error_kind` on 5xx (middleware `request` record, web §10) on `listDemoInbox` | AEA-23 | AEA-43 | AEA-43 AC-17 | recorded `status` equals the response status for 200, 401, 429, 503; `error_kind` on the forced 500 |
| OBS-13 | WF-5 | `request.status` with `error_kind` on 5xx (web §10) on CON-7 and the CON-8 read | AEA-23 | AEA-43 | AEA-43 AC-18 | recorded `status` equals the response status for 429, 200, 400; `error_kind` on the forced 500 |
| OBS-13 | WF-15 | `request.status` with `error_kind` on 5xx (web §10) on `resetDemo` | AEA-23 | AEA-43 | AEA-43 AC-19 | recorded `status` equals the response status for 200, 400, 409, 500; `error_kind` on the 500 only |

**Existing rows whose evidence cell is now stale.** The AC id each row cites is unchanged; only the evidence text needs
updating:

- Line 465 (DC-1 WF-3, AEA-43 AC-11): the test is renamed `test_inbox_request_rate_limited`, and AC-11 now covers
  `listDemoInbox` only. Suggested evidence: "`test_inbox_request_rate_limited`: the 429 body validates against
  `TooManyRequests`".
- Line 265 (R-48 WF-15, AEA-43 AC-12): AC-12 now covers the four CON-7…CON-9 operations, and `listDemoInbox` moved to
  AC-17. Suggested evidence: "one 401 body per operation (four); 2xx under each role".

## Reworded

Most rewordings only add a `**WF-n** (operation):` prefix after the kind tag. Where the AC used to test only at
service level, a route-level (TestClient) leg was added to verify, so it really drives the entry point. Those are marked "+ route leg".

- **AEA-40:** AC-1 (WF-1 `startChatSession`); AC-7 (WF-1 `submitTurn`, + route leg
  `tests/api/test_chat.py::test_timeout_and_exception_notices_via_submit_turn`); AC-9 (WF-1); AC-11 (WF-1, + route leg
  `tests/api/test_chat.py::test_customer_message_event_via_submit_turn`); AC-14 (WF-1 CON-1 → CON-2; also tagged OBS-32
  receipt row); AC-21 (WF-1, + route leg `tests/api/test_chat_capture.py::test_conversation_outcome_via_submit_turn`).
- **AEA-42:** AC-3 (WF-2 `requestPerson`, + route leg `tests/api/test_handoff_routes.py::test_request_person_passes_handoff_request`);
  AC-6 (WF-2); AC-13 (WF-2 both operations, + route leg `tests/api/test_handoff_routes.py::test_both_responses_carry_settled`;
  `saveFollowUp` is a direct route, so the service test alone could not prove its `settled`); AC-14, AC-15, AC-16, AC-17 (WF-2).
- **AEA-43:**
  - AC-7, AC-8 (WF-15; AC-8 also tags R-41) and AC-10 (WF-5).
  - **AC-11 split:** it is now WF-3 `listDemoInbox` only, with its test renamed `test_inbox_request_rate_limited`. The
    staffing and clock half moved to the new AC-18.
  - **AC-12 split:** it now names WF-15 and WF-5 for the four CON-7…CON-9 operations. The `listDemoInbox` half moved to
    the new AC-17.
  - **New ACs:** AC-17 (WF-3: R-48 + OBS-13), AC-18 (WF-5: R-41 + OBS-13), AC-19 (WF-15: OBS-13).
  - **Renumbered:** the regression AC moved from AC-17 to **AC-20**.
  - The Observability "Capture evidence" line now names AC-17…AC-19.
- No other AC was renumbered. AEA-40's regression AC stays AC-23, and so does AEA-42's.

**Audit rows that cite a regression AC of these tickets:** none. No row cites AEA-40 AC-23, AEA-42 AC-23 or the old
AEA-43 AC-17.

## Blocked-by edits

None needed. Every new row's implementing ticket (AEA-10, AEA-23) is already in its owner's *Blocked by*, so no wave
changes.

## Decisions

None raised by these three tickets.

## Not fixed

- **R-41 WF-2:** part-3 proposes AEA-51 as the owner, so this pair was left to that group. AEA-42 AC-6 already drives
  `requestPerson` through the real middleware with the buckets exhausted and `allow_turn()` false. If the AEA-51 owner
  prefers, AEA-23 → AEA-42 / AEA-42 AC-6 would close the CON-4 half without a new AC. CON-5 "never 429" has no AC on
  AEA-42.
- **OBS-14 WF-2, DC-16 WF-2, DC-11 / DC-13 WF-2:** the proposed owner is AEA-51, and DC-11 / DC-13 are flagged as
  decisions in part-8. Not touched here.
- **OBS-32 WF-13 / WF-17:** AEA-40 is the implementer and AEA-50 the owner. Part-4 says AEA-50's *Blocked by* must add
  AEA-40. That edit belongs to AEA-50's group.
