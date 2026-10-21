# Final cross-reference pass, slice B (staff, cases, models), 2026-10-21

One line per fix: file, what, why.

- Known items already done before this run (checked, not redone): staff.md §1 defines `LoginSessionId` once (item 2); cases.md cites STF-6, not STF-8 (item 3); cases.md §7 `reset(…, session_id: LoginSessionId | None, role: DemoRole | None)` (item 5); `SpendLimits.daily_cap_usd` is defined in models.md §6, where web.md §5 already points (item 5); `LANGFUSE_PROJECT_ID` is in AEA-02's `Settings` list, accepted in graph-core.md's GRC-19 table and in data.md §9 item 1 (item 5).
- staff.md §5: defined `StoredChatLine`. `LiveView.message` used it, but no file defined it. Its fields now follow the OpenAPI `ChatLine` (`message_id`, `speaker`, `at`, `text`). The old comment listed a `name` field, which the wire does not have.
- staff.md §11: moved `streamCaseEvents` (connect) out of the "waits `reset_wait_s`" row. web.md §7 and STF-7 both say the SSE streams never wait.
- staff.md §2: added that AEA-44 binds `get_flag_service()` and AEA-46 binds `get_live_chat()` (web.md §4 declares both providers). This file never named who binds them.
- staff.md cross-topic CAS: dropped the stale "(cases.md calls them "web topic")". cases.md §5 now cites staff.md §1.
- cases.md §1.1: added a `turns` row holding the `TurnRecord` / `TurnTrace` fields (graph-core §2, GRC-21). Item 1 introduced the type, and §8's evaluator reads `turn.trace_export`.
- cases.md §1.2: `core.turns.begin(ids, received_at) / finish(turn_id, record: TurnRecord)` is now the signature web.md §8–§9 and graph-core §2 call.
- cases.md §5: the staff-guidance `lookup_log` row now uses DO-4 §5 `LookupEntry` field names (`passage_ids`, `result_seen`, `turn_id`). It previously used `record` and `result`. **Open:** `LookupEntry.message_id` is a required int that `HandoffService.open` has no source for (see report).
- cases.md §4: added that the executors register through `scheduling_tools(scheduling)` and map `Refused.code` to `ToolErrorCode` (graph-tools §1, C-7). This states the registration item 4 asks about from this file's side.
- cases.md §9: `MetricsReader` gains `daily_cap_usd: float`, with no default. CON-19 `spend.cap_cents` had no source: `LedgerService` does not expose its cap. This follows MC-22 (ledger row extended).
- cases.md header and §8: cite `SpendLimits` in models.md §6 as the owner of `limits.spend.daily_cap_usd`.
- models.md §7: replaced `settings.langfuse_complete()`, a method no file declares, with the plain four-key condition.
- models.md §6: the `SpendLimits` consumers now include AEA-53 (`MetricsReader`).
- models.md cross-topic 3: marked settled against graph-core's GRC-19 `Settings` row.
- models.md cross-topic 5: the trace values land as `TurnRecord.trace_id` / `trace_export` (graph-core §2).
- Ledger `plans/7b-decisions/cases.md`: extended the MC-22 row and added a GRC-21 row.
