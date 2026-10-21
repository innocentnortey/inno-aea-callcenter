# Coverage matrix — part 2 (R-20 … R-39, audit lines 46–67)

Checked with `coverage_audit.py check` against `drafts3.md` and the observability contract (19 workflows).

## Scope fixes

| Req | Replacement Applies-to cell | Reason |
|---|---|---|
| R-20 | WF-1; excludes WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (confirmations are given only on the customer chat turn), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving make no booking and give no confirmation) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-21 | WF-1, WF-4; excludes WF-2, WF-3, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (the change request is raised only on the chat turn and its supervisor alert shows only in the staff console), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving move no appointment and show no case) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-22 | WF-1; excludes WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (cancellations are requested only on the customer chat turn), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving cancel nothing) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-23 | WF-1; excludes WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (estimates are booked only on the customer chat turn), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving book nothing) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-24 | WF-1, WF-2; excludes WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (handoffs are triggered only by a chat turn or the person button), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving trigger no handoff) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-25 | WF-1, WF-2; excludes WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (handoffs are opened only by a chat turn or the person button), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving open no case) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-26 | WF-1, WF-2, WF-5, WF-16; excludes WF-3, WF-4, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-17 (promise text is written only when a handoff opens a case, a shift end converts live-queued cases, or demo seed cases load), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving write no promise) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-27 | WF-2; excludes WF-1, WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (the preference is saved only through the follow-up call (CON-5)), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving save no follow-up preference) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-28 | WF-1, WF-2, WF-4; excludes WF-3, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (the brief is assembled when a chat turn or the person button opens a case and read only in the staff case view), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving assemble and show no brief; the case view's data comes through CON-12 (WF-4)) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-46 | WF-1, WF-2; excludes WF-3, WF-4, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (model words are produced only for chat replies and handoff briefs), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving produce no model words) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-29 | WF-1, WF-4; excludes WF-2, WF-3, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (tools run only on the chat turn and sources are shown only in the staff case view), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving run no tool and show no source) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-30 | WF-1, WF-2, WF-4, WF-5, WF-15; excludes WF-3, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-16, WF-17 (presence is set by the staffing control, restored by reset and read only by the chat, the person request and the staff console), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving read no presence state; screens get it through CON-7 (WF-5)) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-31 | WF-1, WF-4; excludes WF-2, WF-3, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (takeover happens only between the staff console and the customer chat), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving take over no chat) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-48 | WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-9, WF-10, WF-15, WF-18, WF-19; excludes WF-17 (the health check is exempt by the requirement itself), WF-7, WF-13, WF-14, WF-16 (no HTTP route: a background job, start-up or build step), WF-8 (calls the retriever directly, through no HTTP route), WF-12 (experiments score through the end-to-end eval runs, which sign in), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | adds WF-18 (the login itself and its env credentials) and WF-19 (unsigned page requests answer 303 to /login), registered at §7 after this row was written |
| R-32 | WF-4, WF-6; excludes WF-1, WF-2, WF-3, WF-5, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (the views are served only by the staff console and the owner page), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (page serving delivers only the built shell and the login shows no case; the views' items come through CON-11…CON-18 (WF-4, WF-6)) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-33 | WF-1, WF-2, WF-4, WF-5, WF-7, WF-15, WF-16; excludes WF-3, WF-6, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-17 (these never create, move or seed a case), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving create, move or seed no case) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-34 | WF-2, WF-4; excludes WF-1, WF-3, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (follow-ups and contact attempts are recorded only by the follow-up call and the staff console), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving record no follow-up or contact attempt) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-35 | WF-6, WF-17; excludes WF-1, WF-2, WF-3, WF-4, WF-5, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16 (the page and the restarting health check are the only places this lives), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (page serving delivers only the built shell; the monitoring numbers come through CON-19 (WF-6)) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-36 | WF-1, WF-2, WF-3, WF-4, WF-9, WF-10, WF-12, WF-13, WF-18, WF-19; excludes WF-5, WF-6, WF-7, WF-8, WF-14, WF-15, WF-16, WF-17 (they never handle a code, card-like number, contact value or message text: their records hold ids, kinds, counts and times only (AEA-30 AC-13, AEA-31 AC-13, AEA-32 AC-10, AEA-48 AC-9) and they export no span; their log lines still pass OBS-21's allow-list formatter), WF-11 (archived SP-1 spike, never merged; no ticket changes it) | WF-18 and WF-19 were registered at §7 after the table was written and handle a password, cookie and raw paths, so they are in; the eight excluded workflows carry no secret or customer value, so per-workflow redaction proof there is vacuous (replaces 'all; excludes WF-11') |
| R-37 | WF-4; excludes WF-1, WF-2, WF-3, WF-5, WF-6, WF-7, WF-8, WF-9, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (flags are created and reviewed only in the staff console), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving raise and review no flag) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-38 | WF-8, WF-9, WF-10, WF-12; excludes WF-1, WF-2, WF-3, WF-4, WF-5, WF-6, WF-7, WF-13, WF-14, WF-15, WF-16, WF-17 (only eval, load and experiment runs read the case files), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving read no case file) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |
| R-39 | WF-6, WF-8, WF-9; excludes WF-1, WF-2, WF-3, WF-4, WF-5, WF-7, WF-10, WF-12, WF-13, WF-14, WF-15, WF-16, WF-17 (the report is produced by the eval runs and shown only on the evaluation page), WF-11 (archived SP-1 spike, never merged; no ticket changes it), WF-18, WF-19 (the demo login and page serving produce and show no eval report; CON-20 (WF-6) shows it) | WF-18 and WF-19 were registered at §7 (observability contract) after this row was written; without them the row is a narrowed guarantee |

## Matrix rows

| R-20 | WF-1 | Booking confirmation block: date, window, technician and the tier fee note (`SchedulingService.book`, `fee_note`) | AEA-28 | AEA-62 | AEA-62 AC-6 | J-3 confirmation card fields (date, 8:00 am → 12:00 pm, technician, member fee waiver, no $89 due), row ids and issued-DB hashes printed; screenshot |
| R-21 | WF-1 | Fee-bearing refusal of `move` and the staff change request (`SchedulingService`, `request_change` → P2 case) | AEA-28 | AEA-51 | AEA-51 AC-9 | `Refused(fee_bearing)`; appointment row unchanged; case due 12:00 and promise due Mon 7:00 pm; promise lines from `policy/handoff.py`; completion-check removal |
| R-24 | WF-1 | Escalation decision in the act node (`decide_escalation` → `HandoffService.open`) | AEA-39 | AEA-51 | AEA-51 AC-13 | WP-7 refund: P3 case, promise and due rows, reference appended by code |
| R-24 | WF-2 | "Talk to a person" handoff on the first request (CON-4) | AEA-42 | AEA-51 | AEA-51 AC-22 | case, `case_event` and promise rows after CON-4; second press `already_open`; chat "talk to a person" hands off on the first ask |
| R-25 | WF-1 | `HandoffService.open`: one case per handoff, priority by `priority_for` | AEA-29 | AEA-51 | AEA-51 AC-30 | 0 turns with `outcome = handed_off` and no case over the dev-set runs |
| R-25 | WF-2 | `HandoffService.open` from CON-4 | AEA-29 | AEA-51 | AEA-51 AC-22 | CAP-3 rows: case, `case_event`, promise; same reference on a second CON-4 |
| R-26 | WF-1 | Promise from the policy table (`promise_for`, stored by `HandoffService`) | AEA-29 | AEA-51 | AEA-51 AC-13 | promise text exactly the R-26 refund line plus "I can't promise an outcome.", due Tue 7:00 pm |
| R-26 | WF-2 | Promise from the policy table on CON-4 | AEA-29 | AEA-51 | AEA-51 AC-22 | `promise.text` equals the `policy/handoff.py` entry; no promise text from the model |
| R-26 | WF-5 | Shift end converts live-queued cases to the unstaffed promise (`convert_live_queued`) | AEA-29 | AEA-52 | AEA-52 AC-7 | converted case's reference and creation time unchanged; promise text from `policy/handoff.py` |
| R-26 | WF-16 | Seed promises from `promise_for(reason, "nobody_online", created_at)` | AEA-14 | AEA-31 | AEA-31 AC-9 | four seeds with promises equal to `promise_for`, never free text |
| R-27 | WF-2 | Follow-up preference (CON-5, `CaseService.set_followup`) | AEA-29 | AEA-51 | AEA-51 AC-22 | CON-5 stores channel, destination and window; unverified `on_record` answers 409 `NOT_ALLOWED_IN_STATE` |
| R-28 | WF-1 | Triage brief, eight fixed headings (`BriefAssembler`) with the R-46 brief fact check | AEA-29 | AEA-51 | AEA-51 AC-13 | the brief's eight headings; fact-check `check_event` for the invented amount |
| R-28 | WF-4 | Brief on the staff case view (CON-12) | AEA-29 | AEA-62 | AEA-62 AC-11 | headings, claims and chip → source pairs printed; screenshot of the brief |
| R-46 | WF-1 | Completion and fact checks in the reply node | AEA-38 | AEA-51 | AEA-51 AC-14 | removal `check_event`; reply without the false "auto-renew is off" claim |
| R-46 | WF-2 | Handoff block, promise and reference built by code (`ReplyComposer.handoff_block` on CON-4) | AEA-42 | AEA-51 | AEA-51 AC-22 | handoff block equals `ReplyComposer.handoff_block`'s; no promise text from the model |
| R-29 | WF-1 | Lookup log, one row per tool call (dispatch, AEA-22, through `SpecialistRunner`) | AEA-35 | AEA-51 | AEA-51 AC-30 | per `turn_id`, `lookup_log` rows equal the tool-call count: 0 mismatches |
| R-29 | WF-4 | Case view sources: snapshot plus current value with "changed since" (CON-12) | AEA-29 | AEA-52 | AEA-52 AC-9 | both dues; snapshot, current and marker fields; every brief fact links to a `lookup_log` row |
| R-30 | WF-2 | Staffing: a person request live-queues only while staffed; shift end converts | AEA-30 | AEA-30 | AEA-30 AC-14 | J-7 steps pass at `integrated with a scripted model` (until AEA-57 and AEA-52 land: mock-tested record naming them as blockers) |
| R-30 | WF-5 | Staffing control (CON-7): default nobody online, shift end | AEA-30 | AEA-52 | AEA-52 AC-7 | events; default nobody online; converted case's reference unchanged |
| R-30 | WF-15 | Reset restores `nobody_online` (`demo_state.reset`) | AEA-10 | AEA-31 | AEA-31 AC-7 | `demo_state` equals a fresh store's; clock labels match |
| R-31 | WF-1 | Relayed customer turn while the AI is paused (CON-2) | AEA-46 | AEA-51 | AEA-51 AC-23 | `AI_PAUSED` notice, CON-21 frame, `turn.outcome = to_staff`, 0 model calls, controller still human |
| R-31 | WF-4 | Live takeover (CON-14) with CON-3 and CON-21 events | AEA-46 | AEA-52 | AEA-52 AC-4 | `representative_joined`, `ai_paused`, `staff_message`, `ai_resumed`, `chat_closed` in order; replay on reconnect |
| R-48 | WF-1 | Demo-login middleware on CON-1 and CON-2 | AEA-23 | AEA-51 | AEA-51 AC-4 | 401 bodies with code only, valid against the OpenAPI |
| R-48 | WF-2 | Demo-login middleware on CON-4 and CON-5 | AEA-23 | AEA-42 | AEA-42 AC-17 | 401 bodies; 200 under a staff role |
| R-48 | WF-4 | Demo-login middleware on the eight staff case operations | AEA-23 | AEA-45 | AEA-45 AC-15 | eight 401 bodies; `role_reset` 403 unchanged |
| R-48 | WF-5 | Demo-login middleware on CON-8 | AEA-23 | AEA-47 | AEA-47 AC-6 | 401 body valid against `Unauthenticated`; zero service calls |
| R-48 | WF-6 | Demo-login middleware on CON-18…CON-20 | AEA-23 | AEA-48 | AEA-48 AC-7 | 401 without `mhc_session` on all three reads |
| R-48 | WF-9 | Eval runner signs in once per run and reuses the cookie | AEA-24 | AEA-24 | AEA-24 AC-1 | stub request log shows one `login` then the case sequence and headers |
| R-48 | WF-15 | Demo-login middleware on CON-9 reset (and CON-6…CON-8 reads) | AEA-23 | AEA-43 | AEA-43 AC-12 | six 401 bodies; 2xx under each role |
| R-48 | WF-18 | Login and logout routes; credentials from Settings | AEA-23 | AEA-23 | AEA-23 AC-25 | `request` and `auth_event` records `ok`, `rejected`, `logged_out`; protected call 401 |
| R-48 | WF-19 | Page gate: unsigned page paths answer 303 to `/login` | AEA-23 | AEA-49 | AEA-49 AC-3 | status and `Location` per path printed; `/login` and assets 200 |
| R-32 | WF-4 | Representative queue and case view (`CaseService.queue`, `detail`) | AEA-29 | AEA-52 | AEA-52 AC-15 | J-6, J-7, J-8 pass at `integrated with a scripted model`; journey record filled |
| R-32 | WF-6 | Business-owner panel (CON-18, `MetricsReader`) | AEA-53 | AEA-53 | AEA-53 AC-2 | every owner measure's numerator and denominator equal a direct SQL count |
| R-33 | WF-1 | Case and promise record created from a chat handoff | AEA-29 | AEA-51 | AEA-51 AC-13 | case, promise (open) and due rows for WP-7 |
| R-33 | WF-2 | Case and promise record created from CON-4 | AEA-29 | AEA-51 | AEA-51 AC-22 | case, `case_event` and promise rows |
| R-33 | WF-4 | Lifecycle moves from staff actions (claim, join, hand back) | AEA-29 | AEA-52 | AEA-52 AC-2 | event rows in order (claimed, joined, message, handed back, flagged) with role and reason |
| R-33 | WF-5 | Simulated-time control past a case due (CON-8) | AEA-30 | AEA-52 | AEA-52 AC-6 | `demo_events` row, `job_runs` per tick, `overdue` case event, case in the Overdue lane |
| R-33 | WF-7 | Scheduler tick: overdue, missed, stuck, due soon on the demo clock | AEA-30 | AEA-30 | AEA-30 AC-8 | one `case_event` per condition; promise statuses as stated |
| R-33 | WF-15 | Reset re-seeds the four labelled demo-seed cases | AEA-31 | AEA-52 | AEA-52 AC-8 | before/after row counts; only the four seeds remain |
| R-33 | WF-16 | First-boot seed load labelled "demo seed" | AEA-31 | AEA-50 | AEA-50 AC-11 | `seed_event` row; the four seed refs; one seed event after two starts |
| R-34 | WF-2 | CON-4 and CON-5 bodies never claim a send | AEA-42 | AEA-42 | AEA-42 AC-15 | no body contains "was sent", "we sent", "emailed you" or "called you" |
| R-34 | WF-4 | Contact attempts recorded, never sent (CON-15) | AEA-29 | AEA-52 | AEA-52 AC-10 | activity rows; "recorded, not sent"; no network access attempted |
| R-35 | WF-6 | Monitoring page (CON-19) from stored records | AEA-53 | AEA-53 | AEA-53 AC-3 | per-tile equality with stored counts; eval, load and seed tags excluded |
| R-35 | WF-17 | Health check and restart (`Watchdog`, `/healthz`, restart policy) | AEA-32 | AEA-50 | AEA-50 AC-12 | `/healthz` 200 unsigned; container restart count 1; failure and restart `health_event` rows |
| R-36 | WF-1 | Span mask hook and log allow-list on the chat turn | AEA-19 | AEA-51 | AEA-51 AC-18 | 0 hits for the code, card-like number, full phone and key values in DB, spans, logs and bodies |
| R-36 | WF-2 | Log allow-list formatter and masked trace on CON-4 and CON-5 | AEA-23 | AEA-42 | AEA-42 AC-16 | full phone and email absent from bodies, logs and spans; only "ending in 02" |
| R-36 | WF-3 | CON-6 body excluded from logging; code stored as hash only | AEA-43 | AEA-51 | AEA-51 AC-31 | code row holds hash and expiry only; 0 log hits for the code |
| R-36 | WF-4 | STORE redaction and log allow-list on staff actions | AEA-46 | AEA-52 | AEA-52 AC-3 | 0 log hits for the customer name and message text; card-like number stored as "[card number removed]" |
| R-36 | WF-9 | Harness run logs and reports carry no code, password, eval key or held-out output | AEA-24 | AEA-24 | AEA-24 AC-11 | absence asserted in run logs, case results, JSON and Markdown reports and timings |
| R-36 | WF-13 | Trace export only to this app's VPS Langfuse project (start-up key check) | AEA-19 | AEA-50 | AEA-50 AC-8 | export state per case; alert row; 0 spans received by the stub for wrong-project keys |
| R-36 | WF-18 | Login records never carry username, password or token | AEA-23 | AEA-23 | AEA-23 AC-25 | `auth_event` rows with opaque `session_id` only |
| R-36 | WF-19 | Page-serving records carry the route template, never the raw path, query or cookie | AEA-23 | AEA-49 | AEA-49 AC-8 | 0 hits for the raw path, query string and cookie value in logs and spans |
| R-37 | WF-4 | Flags to the review list, nothing changed automatically (CON-16) | AEA-44 | AEA-52 | AEA-52 AC-11 | review-list entry; `eval/cases/`, prompts and KB hashes unchanged |
| R-38 | WF-8 | Retrieval queries from the case files (`run_retrieval_suite`) | AEA-06 | AEA-24 | AEA-24 AC-10 | computed numbers equal hand-counted fixture values |
| R-38 | WF-9 | Sealed held-out split checked before scoring | AEA-06 | AEA-24 | AEA-24 AC-6 | refusal naming both hashes, no scores |
| R-38 | WF-10 | Load suite plays 20 conversations at once | AEA-06 | AEA-24 | AEA-24 AC-9 | 20 concurrent conversations at the stub; one timing line per turn |
| R-38 | WF-12 | Experiments run on the dev split only; held-out refused | AEA-06 | AEA-24 | AEA-24 AC-15 | report with `experiment_id`; refusal names the split only |
| R-39 | WF-6 | Evaluation page (CON-20) shows the stored report | AEA-53 | AEA-53 | AEA-53 AC-5 | response per scenario (both splits, dev only, stale, no run, incomplete) |
| R-39 | WF-8 | Retrieval hit rate @3 in the report | AEA-24 | AEA-24 | AEA-24 AC-10 | hit @3 and excluded-file hits equal hand-counted fixture values |
| R-39 | WF-9 | R-39 report: "n of N" per split, held-out headline, targets only in a Target column | AEA-24 | AEA-24 | AEA-24 AC-4 | `EvalReportFile` validates; Markdown structure snapshot |

## Gaps

### Missing coverage and blockers

| Requirement | Workflow | Proposed ticket | Proposed AC wording |
|---|---|---|---|
| R-21 | WF-4 | AEA-52 (blocked by AEA-29 already) | New AC-20 [capture] **WF-4:** right after WP-4's `request_change` through CON-2, with no clock advance, `getOversight` as the supervisor lists the P2 `fee_bearing_change` case in the P0/P1-and-alerts lane (the `supervisor_now` alert shows at once) and `getCase` shows the appointment as "original stays" with the wanted slots shown but not held — verify: `tests/integration/test_staff_cases.py::test_fee_bearing_alert_at_once` — evidence: the oversight lane and case body printed. |
| R-22 | WF-1 | AEA-51 (implementing AEA-28; already a blocker) | New AC [invariant] **WF-1 (CON-2), WP-4 cancel leg:** a scripted specialist that calls `cancel` on MHC-57204's appointment 1 inside 24 h (even after a yes) is refused `fee_bearing`; the appointment and slot rows are unchanged, a P2 staff request opens, the reply says the $49 fee "applies under current policy" and that the appointment stays; 0 `cancelled` actions — verify: `tests/graph/test_worked_pairs_api.py::test_wp4_fee_bearing_cancel_never_written` — evidence: `Refused(fee_bearing)`; rows unchanged; P2 case. (AC-9 cites R-22 but drives `move` only.) |
| R-23 | WF-1 | AEA-51 (implementing AEA-28) | New AC [invariant] **WF-1 (CON-2):** a verified customer's estimate request offers only `estimate` slots, booking one writes an `estimate` appointment on the working copy, and the confirmation names the Comfort Advisor — verify: `tests/graph/test_worked_pairs_api.py::test_estimate_books_comfort_advisor` — evidence: offered slot service types; the appointment row; the confirmation text. (Today only AEA-28 AC-13 proves it, at the service.) |
| R-28 | WF-2 | AEA-51 (implementing AEA-29) | New AC [capture] **WF-2 (CON-4):** a person request opens a case whose brief has the eight `BRIEF_TITLES` headings, facts, promise, AI actions and identity from state, headings 2, 4 and 7 extracted or `not_generated`, a link to the full chat, and 0 invented facts after the R-46 brief check (this also proves R-46's brief fact check on WF-2) — verify: `tests/capture/test_cap3_handoff.py::test_con4_case_has_brief` — evidence: headings and their origins printed. |
| R-30 | WF-1 | AEA-51 (implementing AEA-30; already a blocker) | New AC [invariant] **WF-1 (CON-1/CON-2/CON-3):** with staffing on, the chat receives `staffing_changed` and the "Demo: simulated staff on shift" banner text; with nobody online no chat-raised handoff is live-queued (0 `live_queued` cases over the dev-set run) — verify: `tests/integration/test_staff_streams.py::test_chat_staffing_banner_and_no_live_queue` — evidence: event and banner text; live-queued count 0. |
| R-30 | WF-4 | AEA-52 (implementing AEA-30) | New AC [invariant] **WF-4:** while staffed, the staff queue and case responses carry the simulated-staffing banner text from `policy/texts.py`; while nobody is online they carry none and no case shows `live_queued` — verify: `tests/integration/test_staff_streams.py::test_staff_banner_follows_staffing` — evidence: banner field per mode printed. (Screen rendering stays AEA-55's.) |
| R-36 | WF-10 | AEA-24 | Split AC-11 per suite. New AC [negative] **WF-10 (load run):** the code, demo password and eval key are absent from the load run's log, its `client_side_turn_timings.jsonl` and its report — verify: `eval/harness/tests/test_secrets.py::test_load_run_outputs_clean` — evidence: 0 hits per value. |
| R-36 | WF-12 | AEA-24 | New AC [negative] **WF-12 (experiment run):** the same values are absent from an `--experiment XP-1` run's log and report — verify: `eval/harness/tests/test_secrets.py::test_experiment_outputs_clean` — evidence: 0 hits per value. |
| R-48 | WF-10 | AEA-24 | Extend AC-9: **WF-10:** the load run signs in once (`login`) and every CON-2 call carries the session cookie; a call without it is answered 401 by the stub and counted as a failure — evidence: the stub's request log shows one `login` first. |
| R-48 | WF-3 | AEA-43 | Split AC-12: new AC [failure/refusal] **WF-3:** `listDemoInbox` without `mhc_session` answers 401 `UNAUTHENTICATED` from the real AEA-23 middleware and 200 under each role; keep AC-12 for CON-7…CON-9 (WF-5, WF-15) — verify: `tests/api/test_demo_routes.py::test_inbox_login_gate` — evidence: the 401 body. |
| R-20 | WF-1 | AEA-62 (Blocked by) | Not a missing AC: add AEA-28 to AEA-62's *Blocked by* (already transitive through AEA-51; no wave change), so the integration owner is directly blocked by the component it proves. |

### Criteria that prove the workflow but do not name it (checker: "does not name WF-n")

Each AC below drives the named workflow's real entry point, so the matrix row stands; the checker needs the AC text to name the workflow. Fix: prefix the AC body with `**WF-n:**` (no behaviour change).

| AC | Add | Proves for |
|---|---|---|
| AEA-24 AC-1 | `WF-9` | R-48 |
| AEA-24 AC-4 | `WF-9` | R-39 |
| AEA-24 AC-6 | `WF-9` | R-38 |
| AEA-24 AC-9 | `WF-10` | R-38 |
| AEA-24 AC-10 | `WF-8` | R-38, R-39 |
| AEA-24 AC-11 | `WF-9` | R-36 |
| AEA-24 AC-15 | `WF-12` | R-38 |
| AEA-30 AC-8 | `WF-7` | R-33 |
| AEA-30 AC-14 | `WF-2` | R-30 |
| AEA-31 AC-7 | `WF-15` | R-30 |
| AEA-31 AC-9 | `WF-16` | R-26 |
| AEA-42 AC-15 | `WF-2` | R-34 |
| AEA-42 AC-16 | `WF-2` | R-36 |
| AEA-42 AC-17 | `WF-2` | R-48 |
| AEA-43 AC-12 | `WF-15` | R-48 |
| AEA-45 AC-15 | `WF-4` | R-48 |
| AEA-47 AC-6 | `WF-5` | R-48 |
| AEA-48 AC-7 | `WF-6` | R-48 |
| AEA-49 AC-3 | `WF-19` | R-48 |
| AEA-51 AC-4 | `WF-1` | R-48 |
| AEA-51 AC-9 | `WF-1` | R-21 |
| AEA-51 AC-13 | `WF-1` | R-24, R-26, R-28, R-33 |
| AEA-51 AC-14 | `WF-1` | R-46 |
| AEA-51 AC-18 | `WF-1` | R-36 |
| AEA-51 AC-23 | `WF-1` | R-31 |
| AEA-52 AC-3 | `WF-4` | R-36 |
| AEA-52 AC-4 | `WF-4` | R-31 |
| AEA-52 AC-7 | `WF-5` | R-26, R-30 |
| AEA-52 AC-9 | `WF-4` | R-29 |
| AEA-52 AC-10 | `WF-4` | R-34 |
| AEA-52 AC-15 | `WF-4` | R-32 |
| AEA-62 AC-6 | `WF-1` | R-20 |
| AEA-62 AC-11 | `WF-4` | R-28 |

## Notes

Residual checker findings on this slice: 49 (10 missing rows and 1 blocker above, 38 "does not name" covered by 33 wording fixes); 0 narrowed guarantees, 0 ticket-level findings. Partial rows: R-24 WF-1 cites the refund trigger (safety, fee-bearing, D4 and failure triggers are AEA-51 AC-11, AC-9, AC-14, AC-16); R-32 WF-4 covers queue and case view (supervisor list: AEA-52 AC-6). R-29 WF-1 names AEA-35 as implementing because AEA-51 is not directly blocked by AEA-22. R-36's narrowing is a proposal for Innocent; keeping `all` instead turns eight exclusions into gaps.
