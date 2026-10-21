# Coverage repair — group a51 (AEA-51 only)

Ticket edited: `docs/plans/tickets/AEA-51.md`. Checker re-run 2026-10-21 against a fresh concat of every ticket
(`cat docs/plans/tickets/AEA-*.md`): every AEA-51 problem is gone except the DC-13 WF-1 row (audit line 488), which
must be re-pointed from AC-3 to AC-44 (row below). AC-3 is a fixture-level contract test and is deliberately **not**
labelled WF-1.

Final AC numbering: AC-1…AC-32 unchanged; **AC-33…AC-51 new**; the regression/context AC moved from AC-33 to **AC-52**.

## Matrix rows

New rows (7-column audit format). The first row **replaces** audit line 488.

| Req | Workflow | Component / contract | Implementing ticket | Integration owner | Acceptance criterion | Evidence |
|---|---|---|---|---|---|---|
| DC-13 | WF-1 | Model adapters (`adapters/models/anthropic.py`, `openrouter_jev.py`) bound behind CON-2 over recorded HTTP fixtures | AEA-17 | AEA-51 | AEA-51 AC-44 | `test_real_adapters_through_con2`: one HTTP request and one `spend_ledger` row with its `ProviderCall` per attempt, failures included; nothing raised; no forced `tool_choice` |
| NFR-5 | WF-1 | `JevAdapter` request body `provider.data_collection = deny` | AEA-18 | AEA-51 | AEA-51 AC-44 | `test_real_adapters_through_con2`: every Jev request body carries `provider.data_collection = deny` |
| R-2 | WF-1 | Chat-words person request (`decide_gate` → front node → `HandoffService`) | AEA-12 | AEA-51 | AEA-51 AC-33 | `test_wf1_person_words_first_ask`: `person_requested` / `handed_off` turn and one case on the first ask; 0 model calls before it |
| R-16 | WF-1 | Identity failure → handoff without revealing the account (`IdentityService`, identity node) | AEA-27 | AEA-51 | AEA-51 AC-34 | `test_wf1_identity_failure_reveals_nothing`: byte-identical replies for existing and non-existent customers; `identity_unverified` P3 cases |
| R-22 | WF-1 | Fee-bearing cancel refused (`SchedulingService`, `request_change`) | AEA-28 | AEA-51 | AEA-51 AC-35 | `test_wp4_fee_bearing_cancel_never_written`: `Refused(fee_bearing)`; rows unchanged; P2 case; 0 `cancelled` actions |
| R-23 | WF-1 | Estimate slots with a Comfort Advisor (`find_windows`, booking) | AEA-28 | AEA-51 | AEA-51 AC-36 | `test_estimate_books_comfort_advisor`: only `estimate` slots offered; `estimate` appointment row; confirmation names the Comfort Advisor |
| R-44 | WF-1 | Quick checks offered, never required (`SpecialistRunner` `qc-<turn_id>` search) | AEA-35 | AEA-51 | AEA-51 AC-37 | `test_wf1_quick_checks_offered_never_required`: one troubleshooting search; booking after decline; no offer on urgent and safety turns |
| R-30 | WF-1 | Staffing read on CON-1 and presence in `HandoffService` (`DemoService`) | AEA-30 | AEA-51 | AEA-51 AC-39 | `test_wf1_staffing_and_no_live_queue`: `nobody_online` default; 0 live-queued handoffs while nobody online; `R26.staffed` when on shift |
| R-3 | WF-3 | Code expiry and CON-6 status on the demo clock (`DemoClock`, `IdentityService`) | AEA-30 | AEA-51 | AEA-51 AC-40 | `test_wf3_code_expiry_follows_demo_clock`: CON-6 `expired` after CON-8 `plus_1h`; CON-2 `CODE_EXPIRED`; wall clock under a minute |
| R-41 | WF-1 | Daily spend guard and provider-cap circuit at the turn (`LedgerService`, gateway) | AEA-26 | AEA-51 | AEA-51 AC-24 | `test_spend_caps`: `SPEND_CAP_REACHED` with no model call; safety still answered; circuit trips on a provider cap |
| R-41 | WF-2 | CON-4 / CON-5 never limited (`PersonRequestService`: no admission, spend guard or rate limit) | AEA-42 | AEA-51 | AEA-51 AC-45 | `test_person_request_never_limited`: CON-4 opens a case and CON-5 is never 429 with the cap reached and buckets exhausted |
| NFR-1 | WF-1 | Failure → handoff mapping (escalation rule 6, DO-4 §11) | AEA-39 | AEA-51 | AEA-51 AC-25 | `test_brake_and_deadline`: brake, model error and tool error each end `degraded_handoff` with a handoff reply or person offer; never a dead end |
| OBS-15 | WF-1 | Brake / failure turns recorded as `degraded_handoff`, never resolved | AEA-39 | AEA-51 | AEA-51 AC-25 | `test_brake_and_deadline`: `outcome` / `degrade_reason` per turn; no conversation `resolved` |
| NFR-2 | WF-1 | Lookup snapshot holds only the fields shown (`LookupEntry.result_seen`, dispatch) | AEA-22 | AEA-51 | AEA-51 AC-30 | `test_record_consistency_over_dev_set`: 0 snapshot fields outside the tool result; no free text over 80 characters |
| NFR-4 | WF-1 | 20 conversations without queueing; booking writes serialized (admission, `SchedulingService`) | AEA-40 | AEA-51 | AEA-51 AC-43 | `test_twenty_concurrent_conversations`: 20 completed turns; 0 `BUSY` / `RATE_LIMITED`; one booking and one `SLOT_TAKEN` |
| OBS-2 | WF-1 | `thread_id` on every turn, lookup and case row; checkpointer key; trace `session_id` | AEA-40 | AEA-51 | AEA-51 AC-17 | `test_required_records_present`: equality per row |
| OBS-5 | WF-1 | `run_id` honoured only with the eval key (`web/middleware.py`, `TurnService`) | AEA-23 | AEA-51 | AEA-51 AC-41 | `test_run_id_honoured_only_with_eval_key`: keyless rows `live` with no `run_id`; keyed rows carry it |
| OBS-11 | WF-2 | `agent_version` on the CON-4 `turn` row (`PersonRequestService`) | AEA-42 | AEA-51 | AEA-51 AC-46 | `test_wf2_turn_records`: `agent_version` on the CON-4 turn |
| OBS-13 | WF-1 | Status values on CON-1/CON-2 records | AEA-40 | AEA-51 | AEA-51 AC-42 | `test_status_values_within_lists`: 0 out-of-list values; `degrade_reason` only with `degraded_handoff`; `error_kind` on a forced 5xx |
| OBS-13 | WF-2 | Status values on CON-4/CON-5 records | AEA-42 | AEA-51 | AEA-51 AC-42 | `test_status_values_within_lists`: CON-4 / CON-5 turn, conversation and request values within the lists |
| OBS-14 | WF-2 | CON-4 `turn.server_ms` and its turn span (`PersonRequestService`, `trace.turn`) | AEA-42 | AEA-51 | AEA-51 AC-46 | `test_wf2_turn_records`: `server_ms`; turn span and timed children with `elapsed_ms` |
| OBS-36 | WF-2 | Spend rows vs model calls per CON-4 `turn_id` | AEA-26 | AEA-51 | AEA-51 AC-46 | `test_wf2_turn_records`: 0 ledger rows and 0 model calls on the CON-4 turn |
| OBS-21 | WF-1 | Allow-list log formatter on the chat turn | AEA-23 | AEA-51 | AEA-51 AC-18 | `test_forbidden_values_absent`: 0 log records with a key outside the web §10 allow-list |
| OBS-22 | WF-1 | Code never raw outside CON-6 (intake, identity store) | AEA-27 | AEA-51 | AEA-51 AC-18 | `test_forbidden_values_absent`: 0 hits for the code in columns, spans, logs and bodies |
| OBS-23 | WF-1 | Card-like number masked at intake (`parse_intake`) | AEA-12 | AEA-51 | AEA-51 AC-18 | `test_forbidden_values_absent`: 0 hits for the card-like number anywhere |
| OBS-24 | WF-1 | Key and cookie values never stored, traced or logged | AEA-23 | AEA-51 | AEA-51 AC-18 | `test_forbidden_values_absent`: 0 hits for the sentinel key and cookie values |
| OBS-24 | WF-2 | Key and cookie values on CON-4 / CON-5 | AEA-23 | AEA-51 | AEA-51 AC-47 | `test_wf2_forbidden_values_absent`: 0 hits in CON-4/CON-5 records, spans, logs, bodies |
| OBS-24 | WF-3 | Key and cookie values on CON-6 | AEA-23 | AEA-51 | AEA-51 AC-31 | `test_wf3_inbox_records_and_scope`: 0 hits in CON-6 records and logs |
| OBS-25 | WF-1 | Phone and introduced name masked in spans, absent from logs (mask hook) | AEA-19 | AEA-51 | AEA-51 AC-18 | `test_forbidden_values_absent`: 0 log hits; spans hold only masked forms (phone's last two digits) |
| OBS-25 | WF-2 | WP-7 customer's name and phone on CON-4 / CON-5 | AEA-19 | AEA-51 | AEA-51 AC-47 | `test_wf2_forbidden_values_absent`: 0 log hits; masked in the CON-4 turn span only |
| OBS-25 | WF-3 | CON-6 records and logs carry no phone or email (body exclusion) | AEA-43 | AEA-51 | AEA-51 AC-31 | `test_wf3_inbox_records_and_scope`: 0 hits for phone and email |
| OBS-26 | WF-1 | Message and reply text: length only in logs, TRACE-masked in spans | AEA-19 | AEA-51 | AEA-51 AC-18 | `test_forbidden_values_absent`: sentinel phrase 0 log hits, masked in spans |
| OBS-26 | WF-2 | WP-7 message text on the CON-4 path | AEA-19 | AEA-51 | AEA-51 AC-47 | `test_wf2_forbidden_values_absent`: 0 log hits; masked in the CON-4 turn span only |
| OBS-27 | WF-1 | Intake placeholders before state, model, storage and trace (`parse_intake`, front node) | AEA-12 | AEA-51 | AEA-51 AC-20 | `test_intake_never_in_state`: 0 raw hits per store; placeholders present |
| OBS-28 | WF-1 | `mask_otel_spans` over graph and model-call spans | AEA-19 | AEA-51 | AEA-51 AC-18 | `test_forbidden_values_absent`: the scan covers node and gateway model-call spans after the hook |
| OBS-28 | WF-2 | `mask_otel_spans` over the CON-4 turn span | AEA-19 | AEA-51 | AEA-51 AC-47 | `test_wf2_forbidden_values_absent`: masked forms only in the CON-4 span |
| OBS-29 | WF-1 | Model inputs leave only after the intake masks, per role profile (gateway) | AEA-20 | AEA-51 | AEA-51 AC-19 | `test_model_requests_redacted`: 0 seeded values in recorded request bodies per role |
| OBS-29 | WF-2 | CON-4 / CON-5 send nothing out but the masked span | AEA-42 | AEA-51 | AEA-51 AC-47 | `test_wf2_forbidden_values_absent`: scripted-adapter call count 0; only the masked span exported |
| OBS-29 | WF-3 | CON-6 makes no outbound connection | AEA-43 | AEA-51 | AEA-51 AC-31 | `test_wf3_inbox_records_and_scope`: socket guard sees 0 outbound connections |
| M-17 | WF-1 | `classifier` and `gate` `check_event` per run and turn, `pass` included | AEA-37 | AEA-51 | AEA-51 AC-17 | `test_required_records_present`: event counts equal classifier-run and turn counts |
| DC-16 | WF-2 | `events(case_created)` in the handoff's commit (`HandoffService` / `CaseService.open_case`) | AEA-29 | AEA-51 | AEA-51 AC-48 | `test_con4_event_in_handoff_commit`: both rows or neither (503 `HANDOFF_FAILED` under a held lock); the poll returns the event once |
| M-12 | WF-9 | WF-1 `check_event` rows (R-46) tagged `eval` under the runner | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: R-46 `check_event` rows carry `run_tag = eval` and the `run_id` |
| M-14 | WF-9 | `turn.gate_result` tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: turn rows tagged with the run |
| M-15 | WF-9 | `turn` `gate_result` / `outcome` tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: turn rows tagged with the run |
| M-16 | WF-9 | `gate_result` and `classifier` events tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: `classifier` events tagged with the run |
| M-17 | WF-9 | `classifier` `check_event` and `gate_result` tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: `classifier` and `gate` events tagged with the run |
| M-18 | WF-9 | `conversation` outcome tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: conversation row tagged with the run |
| M-19 | WF-9 | `turn.outcome` tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: turn rows tagged with the run |
| M-20 | WF-9 | `turn.outcome` tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: turn rows tagged with the run |
| M-21 | WF-9 | R-46 completion `check_event` tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: R-46 events tagged with the run |
| M-25 | WF-9 | `spend_ledger` rows tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: ledger rows tagged with the run |
| M-26 | WF-9 | `spend_ledger` rows tagged `eval` | AEA-24 | AEA-51 | AEA-51 AC-49 | `test_eval_runner_against_app_wf9`: ledger rows tagged with the run |
| M-21 | WF-10 | WF-1 records tagged `load` under the load suite | AEA-24 | AEA-51 | AEA-51 AC-50 | `test_load_runner_against_app_wf10`: records tagged `load` with the `run_id` |
| M-23 | WF-10 | Client timing lines and `turn.server_ms` tagged `load` | AEA-24 | AEA-51 | AEA-51 AC-50 | `test_load_runner_against_app_wf10`: one timing line per CON-2 call; `server_ms` on tagged turns |
| M-24 | WF-10 | Model-call spans (status, retries) and `outcome` / `degrade_reason` tagged `load` | AEA-24 | AEA-51 | AEA-51 AC-50 | `test_load_runner_against_app_wf10`: spans and turn fields on tagged turns |
| M-25 | WF-10 | `spend_ledger` rows tagged `load` | AEA-24 | AEA-51 | AEA-51 AC-50 | `test_load_runner_against_app_wf10`: ledger rows tagged with the run |
| M-26 | WF-10 | `spend_ledger` rows tagged `load` | AEA-24 | AEA-51 | AEA-51 AC-50 | `test_load_runner_against_app_wf10`: ledger rows tagged with the run |
| M-26 | WF-12 | Experiment run's model calls in `spend_ledger`, counted in `spend_today()` | AEA-24 | AEA-51 | AEA-51 AC-51 | `test_experiment_run_spend_wf12`: rows tagged `eval` with the experiment `run_id`; `spend_today()` rises |

## Reworded

Existing ACs (same numbers) that now name their workflow, and the clauses added:

- **AC-1** names **WF-1** (composition behind CON-1/CON-2; the `FastembedIndex` retriever) — R-11.
- **AC-2** names **WF-13** (app start-up) and **WF-1** — DC-14 WF-13.
- **AC-4, AC-5** name **WF-1** (CON-1, CON-2) — R-48, R-1, R-3.
- **AC-6** names **WF-1**; adds: the fact `check_event` holds claim kinds and counts only, never `$149` (DC-11 WF-1).
- **AC-7, AC-8, AC-9, AC-12, AC-13, AC-14, AC-15, AC-16** name **WF-1** (CON-2).
- **AC-10** names **WF-1** (CON-2 turns 3 and 4) — DC-4.
- **AC-11** names **WF-1**; adds the R-6 contact offer after the instruction, never a gate, with the P0 case kept.
- **AC-17** adds OBS-2 (`thread_id` = checkpointer key = trace `session_id` on every row) and M-16/M-17 (one `gate` and
  one `classifier` `check_event` per turn and per classifier run, `pass` included).
- **AC-18** retitled **CAP-1 forbidden values, WF-1**; adds the log key-set allow-list (OBS-21), the introduced-name
  sentinel and span masking (OBS-25), the message/reply sentinel phrase (OBS-26), cookie values (OBS-24), and that the span
  scan covers node and gateway model-call spans after `mask_otel_spans` (OBS-28).
- **AC-19** names **WF-1** — OBS-29, DC-7.
- **AC-20** names **WF-1**; adds a card-like number and the placeholders each store receives (OBS-27).
- **AC-22** loses the chat-words clause ("can I talk to a person" on the first ask), now AC-33 (WF-1); points there.
- **AC-23** names its customer half **WF-1** (CON-2) beside WF-4 — R-31 WF-1.
- **AC-24** names **WF-1** — R-41, DC-12, DC-14.
- **AC-25** names **WF-1**; adds a scripted model error and tool error (NFR-1), and the recorded outcomes: brake →
  `ai_failure` case, timeout → no case (graph-core §5), none counted `resolved` (OBS-15, M-18, M-24) — DC-9.
- **AC-27** names **WF-1** (CON-2 turns 1, 2, 5) — R-45.
- **AC-30** names **WF-1 and WF-2** up front and makes the CON-4 turns explicit (0 model calls, 0 ledger rows); adds the
  planner `topic` (M-3, M-4) and the snapshot field check (NFR-2).
- **AC-31** adds key and cookie sentinels (OBS-24), no phone or email (OBS-25) and a socket guard (OBS-29) on CON-6.
- **New:** AC-33 (R-2 WF-1), AC-34 (R-16), AC-35 (R-22), AC-36 (R-23), AC-37 (R-44), AC-38 (R-13 no-source and R-17
  warranty partials), AC-39 (R-30 WF-1), AC-40 (R-3 WF-3), AC-41 (OBS-5 WF-1), AC-42 (OBS-13 WF-1, WF-2), AC-43 (NFR-4),
  AC-44 (DC-13, NFR-5 WF-1), AC-45 (R-41 WF-2), AC-46 (OBS-11, OBS-14, OBS-36 WF-2), AC-47 (OBS-24…OBS-29 WF-2), AC-48
  (DC-16 WF-2), AC-49 (CAP-7 app side, WF-9), AC-50 (WF-10), AC-51 (WF-12).
- **AC-33 → AC-52** (regression/context), text unchanged.
- *Observability → Capture evidence* lists the new capture ACs.

## Blocked-by edits

Added as hard edges: **AEA-02, AEA-12, AEA-22, AEA-24**. All are wave 0–1 and none is blocked by AEA-51 (AEA-22 names
AEA-51 only as a non-merge journey-record note), so AEA-51 stays in wave 3 with no cycle. Clears "integrates AEA-22's
component" (DC-5, DC-8) and "integrates AEA-02's component" (DC-14 WF-13); AEA-12 for OBS-23/OBS-27 (part-4); AEA-24 for
AC-49…AC-51 (part-7).

## Decisions

1. **CON-4 makes no model call and writes no brief, but seven scope cells assume it does.** web.md §8 says
   `PersonRequestService` runs "no admission, no SpendGuard, no rate limit, no model". AEA-42's Metrics section adds that
   "CON-4 calls no model and writes no brief text". The brief is built only in the graph's reply node, on a chat-turn
   handoff (graph-nodes §3). The WF-2 scope cells of **R-28, M-11, M-12, DC-11, DC-13, NFR-1 and NFR-5** were written as if
   a handoff brief and its Sonnet call ran on CON-4. The part-2/3/7/8 proposals (brief headings on a CON-4 case, a
   scripted brief-model failure, the brief's request body, its R-46 check) would test behaviour the signed contract
   rules out.
   - Option A: drop WF-2 from those seven cells. Reason: CON-4 calls no model and assembles no brief (web.md §8).
   - Option B: change the contract so a CON-4 case gets a brief built from state (with or without the extraction). This
     changes AEA-42 and web.md §8 and adds a model call, spend and latency to the person button.
   - **R-28 is the one with product weight.** Under A, a staff member who opens a case raised by the button sees no
     triage brief.
   - **Decision needed:** For a case opened by "Talk to a person" (CON-4), should staff get a brief (B), or do we drop WF-2
     from these seven requirements (A)?
2. **WF-9/10/12 owner.** The slice plan gives WF-8–10 and 12 to AEA-24, and parts 3, 5 and 6 send their other WF-9 pairs
   there. Part-7 sends the WF-1 record pairs to AEA-51. I applied part-7 (AC-49…AC-51) for two reasons: AEA-24 AC-14 hands
   "the app-side half … end to end" to AEA-51, and AEA-24 (wave 1) cannot reach the real app. The orchestrator should
   confirm. Innocent does not need to decide this unless the two are reconciled differently.

## Not fixed

- **R-30 WF-1, banner by stream.** The `staffing_changed` event to open chats is AEA-52's (AEA-52 AC-7; S-11's
  customer-stream half belongs to AEA-52). Part-2's proposal used AEA-52's file `tests/integration/test_staff_streams.py`.
  AC-39 covers the WF-1 records half: the CON-1 `staffing` field and no live queue while nobody is online.
- **R-1 "are you a person?" (partial).** No contract says which component renders the answer. AEA-03 marks the text as
  a proposal. Asserting a fixed reply would invent behaviour, so it is left to AEA-03/AEA-38 or Stage 9 E-1. The R-1 WF-1
  row is satisfied by AC-5.
- **R-4 brevity (partial).** This is Stage 9 E-1 with real models, or a reply-length check in AEA-38. It is not
  AEA-51's.
- **The part-4 OBS-15 wording.** It said "the timeout turn ends in a handoff with a case", which contradicts
  graph-core §5 (`DEADLINE`: no case). AC-25 follows the contract.
- **Part-8's DC-16 WF-2 wording.** It said "replayed on CON-3", but api-con-mapping CON-3 sends no `case_created` to the
  customer. AC-48 proves the same commit and the `events` poll instead.
- **Test-design flags for the orchestrator.** AC-44 binds the real adapters, fed recorded HTTP fixtures, through
  `ContainerOverrides`. It is still an override, but it is a third kind beyond the ticket's "only two things are
  substituted"; the What-to-build paragraph was left unedited. The `risk::security` question in the ticket's Risk line
  is still open. AEA-51 now carries more redaction proofs (AC-18, AC-20, AC-31, AC-47).

## Audit rows to update after this repair

- **No audit row cites the old regression AC-33.** The number AC-33 now names the R-2 WF-1 criterion.
- **Line 488 (DC-13 WF-1):** replace it with the first row above (AC-3 → AC-44).
- **Line 240 (R-24 WF-2) and line 439 (M-15 WF-2):** the evidence text mentions the chat-words clause that moved to
  AC-33. Drop "chat 'talk to a person' hands off on the first ask" and "chat words hand off on the first ask (R-2,
  M-15)" from their Evidence cells. AC-22 still proves the CON-4 first press.
