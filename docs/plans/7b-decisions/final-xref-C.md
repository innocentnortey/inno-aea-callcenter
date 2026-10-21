# Final cross-reference pass — slice C (graph-tools, graph-nodes, data), 2026-10-21

One line per fix: file — what — why.

- stage7/graph-nodes.md opening example — the turn row now comes from `GraphOutcome.turn_trace` (`TurnTrace.gate_result`, `outcome`) — item 1: graph-core §2 GRC-20/21 is the carrier.
- stage7/graph-nodes.md §1 table, `brake` row — `RECURSION_LIMIT` event: `run_graph` reads the last checkpoint's events and appends its own in `GraphOutcome.check_events` — matches graph-core §11 (the old "beside compose's halt reply" wording predated GraphOutcome).
- stage7/graph-nodes.md §1 `from_gate` — `rule_ids` → `gate.rules.rule_ids` — DO-4 `GateDecision.rules: RuleMatches`; there is no `GateDecision.rule_ids`.
- stage7/graph-nodes.md §5 — `degrade_reason = model_error` cited to DO-4 §11 and `TurnTrace.degrade_reason`, not cases §3.4 — cases §3.4 row 6 sets reason, priority and rule id only.
- plans/7b-decisions/graph-nodes.md merge notes — the "still open: RunGraph -> ComposedReply" item marked settled by GRC-20/21; GRN-7 citation note — the gap is closed in graph-core.
- stage7/data.md §2 — new `identity` group entry: `INBOX_CODE_BODY` / `INBOX_CODE_GONE` (`identity.inbox_code_*`, placeholder `digits`, SCR-2 R2 wording) — graph-tools C-5 and web.md (AEA-43) use them, but data.md, which owns the texts, did not list them.
- plans/7b-decisions/data.md DAT-29 — adds (f) and the AEA-03 ticket line for the two inbox texts — the row changed.
- stage7/graph-tools.md C-5 — `{code}` → `{digits}`, marked settled by data.md §2 — data's placeholder list has `digits`, not `code`.
- stage7/graph-tools.md §6 — quick-check `ToolCall` name is `"kb_search"` (data.md §4), args capped by `KbSearchArgs.query` ≤ 300 — data.md §4 fixes the name; the placeholder wording is gone.
- stage7/data.md §7 — `ResetGate` cited to web.md §7; `reset` signature still cites cases.md §7 — `ResetGate` is web's (AEA-23), not cases'.
- stage7/data.md §9 item 3 — `load_eval_reports(reports_dir: Path, uow: UnitOfWorkFactory)` in `services/health.py` — cases.md §8's exact signature.
- stage7/data.md §9 item 1 — points to the owner's Settings field list (graph-core cross-topic row "models 3, data 1 (MC-21)", which includes `LANGFUSE_PROJECT_ID`) and web WEB-9's four settings — item 5: shows where the AEA-02 list lives.
- stage7/data.md §6 consumers — "start-up loader (cases topic, §9)" → cases.md §8 `load_eval_reports` — wrong section.

Checked, no change needed: item 2 (`LoginSessionId` defined once, staff.md §1; graph-tools §5 cites it); item 4 (graph-nodes names only `SpecialistRunner.run`, mentioning `run_specialist` solely as what it replaces; data.md §4 already says there is no self-registration); `Refused.code` ↔ `ToolErrorCode`; `SCHEDULE_FEES`; cases §1.1–§1.3, §3.4, §5, §7 signatures; models §1/§4/§5/§7; web §4 headers, §9, §10; staff §5 `redact_store`, STF-19; OpenAPI `QuickChecksBlock`, `getMonitoring`, `getLatestEval`.

Reported, not edited (owner gap): `LookupRow` (DO-4 `BriefAssembler.assemble`, `build_evidence`; cases.md §1.2 `core.lookup_log.for_thread`) has no field definition in any addendum or in DO-4.
